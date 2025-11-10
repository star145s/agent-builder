"""Playbook service for extracting and managing insights from human feedback using LLM."""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.playbook_models import PlaybookEntry, PlaybookOperation
from src.core.database import engine
from sqlmodel import Session, select, and_, or_

logger = logging.getLogger(__name__)


class PlaybookService:
    """Service for managing playbook entries and extracting insights using LLM."""
    
    MAX_PLAYBOOK_ENTRIES = 50  # Maximum entries per conversation
    
    EXTRACTION_PROMPT = """You are an expert at extracting CONCISE, ACTIONABLE insights from human feedback.

The user's playbook can store a MAXIMUM of 50 entries. Each entry must be:
- **Concise** (1-2 sentences max)
- **Actionable** (clear preference, instruction, or fact)
- **Useful** (helps improve future interactions)

CURRENT PLAYBOOK ({playbook_count}/50 entries):
{existing_playbook}

NEW FEEDBACK:
{feedback}

CONTEXT:
{context}

Your task: Extract insights and decide operations intelligently.

**OPERATION RULES:**
1. **insert**: Add NEW knowledge not in playbook (only if valuable)
2. **update**: REPLACE existing entry if new feedback contradicts or refines it
3. **delete**: Remove entry if user says "forget", "ignore", or it's no longer relevant

**EXTRACTION RULES:**
- Extract ONLY the most important, actionable insights
- Keep "value" CONCISE (1-2 sentences, <100 chars preferred)
- Check existing playbook to AVOID duplicates
- Use "update" instead of "insert" if similar key exists
- Consolidate related insights when possible
- If playbook is near 50 entries, be VERY selective or use "update"/"delete"

**OUTPUT FORMAT:**
```json
[
  {{
    "insight_type": "preference|instruction|fact|correction|context|constraint",
    "key": "short_topic_key",
    "value": "Concise insight in 1-2 sentences",
    "operation": "insert|update|delete",
    "confidence_score": 0.7-1.0,
    "tags": ["tag1", "tag2"]
  }}
]
```

**EXAMPLE (GOOD - Concise):**
```json
[
  {{
    "insight_type": "preference",
    "key": "response_style",
    "value": "Prefers concise answers with code examples",
    "operation": "insert",
    "confidence_score": 0.9,
    "tags": ["communication"]
  }}
]
```

**EXAMPLE (BAD - Too verbose):**
❌ "value": "The user has indicated that they prefer responses that are concise and to the point, and they also mentioned that including code examples would be very helpful for understanding..."

Extract insights now:"""

    def __init__(self, llm_service):
        """
        Initialize playbook service.
        
        Args:
            llm_service: LLM service instance for insight extraction
        """
        self.llm_service = llm_service
    
    async def extract_insights(
        self,
        feedback: str,
        cid: str,
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to extract structured insights from human feedback.
        
        Args:
            feedback: Human feedback text
            cid: Conversation ID
            context: Optional conversation context
            
        Returns:
            List of extracted insight dictionaries
        """
        try:
            # Get existing playbook entries
            existing_entries = await self.get_playbook(cid)
            playbook_count = len(existing_entries)
            
            # Format existing playbook for LLM
            if existing_entries:
                playbook_lines = []
                for entry in existing_entries:
                    playbook_lines.append(
                        f"  [{entry.key}] ({entry.insight_type}): {entry.value}"
                    )
                existing_playbook = "\n".join(playbook_lines)
            else:
                existing_playbook = "  (empty - no entries yet)"
            
            # Build prompt with existing playbook
            prompt = self.EXTRACTION_PROMPT.format(
                playbook_count=playbook_count,
                existing_playbook=existing_playbook,
                feedback=feedback,
                context=context or "No previous context"
            )
            
            # Call LLM
            logger.info(f"[PlaybookService] Extracting insights from feedback: {feedback[:100]}...")
            logger.info(f"[PlaybookService] Current playbook: {playbook_count}/{self.MAX_PLAYBOOK_ENTRIES} entries")
            result = await self.llm_service.generate_response(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=2000
            )
            
            # Get response text
            response_text = result.get("response", "")
            
            # Parse JSON response
            insights = self._parse_llm_response(response_text)
            logger.info(f"[PlaybookService] Extracted {len(insights)} insights")
            
            return insights
            
        except Exception as e:
            logger.error(f"[PlaybookService] Error extracting insights: {e}", exc_info=True)
            return []
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract JSON array of insights."""
        try:
            # Try to find JSON in response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            # Parse JSON
            insights = json.loads(response)
            
            # Validate structure
            if not isinstance(insights, list):
                logger.warning("[PlaybookService] LLM response is not a list")
                return []
            
            # Validate each insight
            validated = []
            for insight in insights:
                if self._validate_insight(insight):
                    validated.append(insight)
                else:
                    logger.warning(f"[PlaybookService] Invalid insight: {insight}")
            
            return validated
            
        except json.JSONDecodeError as e:
            logger.error(f"[PlaybookService] Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response}")
            return []
        except Exception as e:
            logger.error(f"[PlaybookService] Error parsing LLM response: {e}", exc_info=True)
            return []
    
    def _validate_insight(self, insight: Dict[str, Any]) -> bool:
        """Validate insight structure."""
        required_fields = ["insight_type", "key", "value", "operation"]
        
        # Check required fields
        if not all(field in insight for field in required_fields):
            return False
        
        # Validate operation
        if insight["operation"] not in ["insert", "update", "delete"]:
            return False
        
        # Validate insight_type
        valid_types = ["preference", "instruction", "fact", "correction", "context", "constraint"]
        if insight["insight_type"] not in valid_types:
            return False
        
        # Validate confidence_score if present
        if "confidence_score" in insight:
            score = insight["confidence_score"]
            if not isinstance(score, (int, float)) or not 0 <= score <= 1:
                return False
        
        # Validate value conciseness (warn if too long)
        value = insight.get("value", "")
        if len(value) > 200:
            logger.warning(
                f"[PlaybookService] Value too long ({len(value)} chars): {value[:50]}... "
                "Consider making it more concise."
            )
        
        return True
    
    async def apply_operations(
        self,
        insights: List[Dict[str, Any]],
        cid: str,
        source_feedback: str,
        llm_response: Optional[str] = None
    ) -> List[PlaybookEntry]:
        """
        Apply extracted insights to the playbook database.
        Enforces maximum of 50 entries per conversation.
        
        Args:
            insights: List of extracted insights
            cid: Conversation ID
            source_feedback: Original human feedback
            llm_response: Full LLM response for logging
            
        Returns:
            List of created/updated playbook entries
        """
        entries = []
        
        with Session(engine) as session:
            # Check current entry count
            current_count = session.exec(
                select(PlaybookEntry).where(
                    and_(
                        PlaybookEntry.cid == cid,
                        PlaybookEntry.is_active == True
                    )
                )
            ).all()
            active_count = len(current_count)
            
            for insight in insights:
                try:
                    operation = insight["operation"]
                    
                    if operation == "insert":
                        # Enforce 50-entry limit
                        if active_count >= self.MAX_PLAYBOOK_ENTRIES:
                            logger.warning(
                                f"[PlaybookService] Playbook limit reached ({self.MAX_PLAYBOOK_ENTRIES}). "
                                f"Skipping insert for key: {insight['key']}. "
                                "Consider using 'update' or 'delete' operations instead."
                            )
                            self._log_operation(
                                session, insight, cid, source_feedback,
                                operation, False, 
                                f"Playbook limit reached ({self.MAX_PLAYBOOK_ENTRIES} entries)",
                                llm_response
                            )
                            continue
                        
                        entry = await self._insert_entry(session, insight, cid, source_feedback)
                        entries.append(entry)
                        active_count += 1
                        
                    elif operation == "update":
                        entry = await self._update_entry(session, insight, cid, source_feedback)
                        entries.append(entry)
                        
                    elif operation == "delete":
                        deleted = await self._delete_entry(session, insight, cid, source_feedback)
                        if deleted:
                            active_count -= 1
                    
                    # Log operation
                    self._log_operation(
                        session, insight, cid, source_feedback,
                        operation, True, None, llm_response
                    )
                    
                except Exception as e:
                    logger.error(f"[PlaybookService] Error applying operation {operation}: {e}")
                    # Log failed operation
                    self._log_operation(
                        session, insight, cid, source_feedback,
                        operation, False, str(e), llm_response
                    )
            
            session.commit()
            
            # Log final count
            logger.info(f"[PlaybookService] Playbook now has {active_count}/{self.MAX_PLAYBOOK_ENTRIES} entries")
        
        return entries
    
    async def _insert_entry(
        self,
        session,
        insight: Dict[str, Any],
        cid: str,
        source_feedback: str
    ) -> PlaybookEntry:
        """Insert new playbook entry."""
        entry = PlaybookEntry(
            cid=cid,
            insight_type=insight["insight_type"],
            key=insight["key"],
            value=insight["value"],
            operation="insert",
            source_feedback=source_feedback,
            confidence_score=insight.get("confidence_score", 0.8),
            tags=insight.get("tags", []),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1,
            is_active=True
        )
        
        session.add(entry)
        session.flush()  # Get ID
        
        logger.info(f"[PlaybookService] Inserted entry: {entry.key} = {entry.value[:50]}...")
        return entry
    
    async def _update_entry(
        self,
        session,
        insight: Dict[str, Any],
        cid: str,
        source_feedback: str
    ) -> PlaybookEntry:
        """Update existing playbook entry or insert if not found."""
        # Find existing entry
        statement = select(PlaybookEntry).where(
            and_(
                PlaybookEntry.cid == cid,
                PlaybookEntry.key == insight["key"],
                PlaybookEntry.is_active == True
            )
        )
        existing = session.exec(statement).first()
        
        if existing:
            # Update existing
            existing.value = insight["value"]
            existing.insight_type = insight.get("insight_type", existing.insight_type)
            existing.source_feedback = source_feedback
            existing.confidence_score = insight.get("confidence_score", 0.8)
            existing.tags = insight.get("tags", existing.tags)
            existing.updated_at = datetime.utcnow()
            existing.version += 1
            existing.operation = "update"
            
            session.add(existing)
            session.flush()
            
            logger.info(f"[PlaybookService] Updated entry: {existing.key} (v{existing.version})")
            return existing
        else:
            # Insert new if not found
            logger.info(f"[PlaybookService] Entry not found for update, inserting: {insight['key']}")
            return await self._insert_entry(session, insight, cid, source_feedback)
    
    async def _delete_entry(
        self,
        session,
        insight: Dict[str, Any],
        cid: str,
        source_feedback: str
    ) -> bool:
        """Soft delete playbook entry. Returns True if entry was deleted."""
        statement = select(PlaybookEntry).where(
            and_(
                PlaybookEntry.cid == cid,
                PlaybookEntry.key == insight["key"],
                PlaybookEntry.is_active == True
            )
        )
        existing = session.exec(statement).first()
        
        if existing:
            existing.is_active = False
            existing.operation = "delete"
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            session.flush()
            
            logger.info(f"[PlaybookService] Deleted entry: {existing.key}")
            return True
        else:
            logger.warning(f"[PlaybookService] Entry not found for deletion: {insight['key']}")
            return False
    
    def _log_operation(
        self,
        session,
        insight: Dict[str, Any],
        cid: str,
        source_feedback: str,
        operation: str,
        success: bool,
        error_message: Optional[str],
        llm_response: Optional[str]
    ):
        """Log playbook operation to history table."""
        try:
            op_log = PlaybookOperation(
                cid=cid,
                operation=operation,
                extracted_data=insight,
                success=success,
                error_message=error_message,
                source_feedback=source_feedback,
                llm_response=llm_response,
                timestamp=datetime.utcnow()
            )
            
            session.add(op_log)
            session.flush()
        except Exception as e:
            logger.error(f"[PlaybookService] Error logging operation: {e}")
    
    async def get_playbook(
        self,
        cid: str,
        insight_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[PlaybookEntry]:
        """
        Retrieve active playbook entries for a conversation.
        
        Args:
            cid: Conversation ID
            insight_type: Optional filter by insight type
            tags: Optional filter by tags
            
        Returns:
            List of active playbook entries
        """
        with Session(engine) as session:
            statement = select(PlaybookEntry).where(
                and_(
                    PlaybookEntry.cid == cid,
                    PlaybookEntry.is_active == True
                )
            )
            
            if insight_type:
                statement = statement.where(PlaybookEntry.insight_type == insight_type)
            
            entries = session.exec(statement).all()
            
            # Filter by tags if provided
            if tags:
                entries = [e for e in entries if e.tags and any(tag in e.tags for tag in tags)]
            
            return list(entries)
    
    def format_playbook_context(self, entries: List[PlaybookEntry]) -> str:
        """Format playbook entries as context string for LLM."""
        if not entries:
            return "No playbook entries yet."
        
        context_parts = ["=== USER'S PLAYBOOK (Knowledge Base) ==="]
        
        # Group by type
        by_type = {}
        for entry in entries:
            if entry.insight_type not in by_type:
                by_type[entry.insight_type] = []
            by_type[entry.insight_type].append(entry)
        
        # Format each type
        for insight_type, type_entries in by_type.items():
            context_parts.append(f"\n## {insight_type.upper()}:")
            for entry in type_entries:
                context_parts.append(f"  • {entry.key}: {entry.value}")
                if entry.tags:
                    context_parts.append(f"    Tags: {', '.join(entry.tags)}")
        
        context_parts.append("\n=== END PLAYBOOK ===")
        return "\n".join(context_parts)
