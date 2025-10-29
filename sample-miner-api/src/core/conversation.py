"""Conversation context management for the miner."""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque

from src.core.playbook import PlaybookManager

logger = logging.getLogger(__name__)


class ConversationMessage:
    """Represents a single message in a conversation."""
    
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content
        }


class ConversationContext:
    """
    Manages conversation context for a single conversation ID.
    
    NOTE: This class no longer stores message history. All conversation insights
    are extracted and stored in the playbook. The messages deque is kept for
    backward compatibility but should not be used for LLM context.
    """
    
    MAX_MESSAGES = 0  # Disabled - we don't store conversation history anymore
    
    def __init__(self, cid: str):
        self.cid = cid
        self.messages = deque(maxlen=1)  # Keep only last message for debugging
        self.playbook = PlaybookManager()  # Playbook is the source of truth
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def add_message(self, role: str, content: str):
        """
        DEPRECATED: Messages are no longer stored. Use playbook instead.
        This method is kept for backward compatibility only.
        """
        # Skip if content is None or empty
        if not content or not content.strip():
            logger.warning(f"Skipping empty message for conversation {self.cid}")
            return
        
        # Store only for debugging purposes
        message = ConversationMessage(role, content)
        self.messages.append(message)
        self.last_updated = datetime.utcnow()
        logger.debug(f"[DEBUG ONLY] Added {role} message to conversation {self.cid}")
    
    def add_user_message(self, content: str):
        """DEPRECATED: Use playbook updates instead."""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str):
        """DEPRECATED: Use playbook updates instead."""
        self.add_message("assistant", content)
    
    def get_messages(self) -> List[Dict]:
        """
        DEPRECATED: Returns empty list. Use get_playbook_context() instead.
        All conversation context is now stored in the playbook.
        """
        logger.warning("get_messages() is deprecated. Use get_playbook_context() instead.")
        return []  # Return empty - playbook is the source of truth
    
    def get_playbook_context(self) -> str:
        """Get playbook preferences formatted for LLM context."""
        return self.playbook.to_context_string()
    
    def add_human_feedback(self, feedback: str):
        """
        DEPRECATED: Use apply_playbook_actions instead.
        This method is kept for backward compatibility.
        """
        logger.warning("add_human_feedback is deprecated. Use apply_playbook_actions instead.")
        # Simple fallback: insert as a new node
        self.playbook.insert(content=feedback, category="feedback")
        self.last_updated = datetime.utcnow()
    
    def get_context_summary(self) -> str:
        """
        Get a summary of the conversation context.
        Now returns only playbook preferences since conversation history is not stored.
        """
        # Return only playbook preferences
        playbook_str = self.playbook.to_context_string()
        if playbook_str:
            return playbook_str
        else:
            return "No user preferences stored yet."
    
    def clear(self):
        """Clear debug messages. Playbook is preserved."""
        self.messages.clear()
        self.last_updated = datetime.utcnow()
        logger.info(f"Cleared debug messages for conversation {self.cid}. Playbook preserved.")


class ConversationManager:
    """Manages all conversation contexts."""
    
    MAX_CONVERSATIONS = 100  # Maximum number of conversations to keep in memory
    
    def __init__(self):
        self.conversations: Dict[str, ConversationContext] = {}
    
    def get_or_create(self, cid: str) -> ConversationContext:
        """Get an existing conversation or create a new one."""
        if cid not in self.conversations:
            # If we're at max capacity, remove the oldest conversation
            if len(self.conversations) >= self.MAX_CONVERSATIONS:
                oldest_cid = min(
                    self.conversations.keys(),
                    key=lambda k: self.conversations[k].last_updated
                )
                logger.info(f"Removing old conversation {oldest_cid} to make room")
                del self.conversations[oldest_cid]
            
            self.conversations[cid] = ConversationContext(cid)
            logger.info(f"Created new conversation context for {cid}")
        
        return self.conversations[cid]
    
    def get(self, cid: str) -> Optional[ConversationContext]:
        """Get an existing conversation context."""
        return self.conversations.get(cid)
    
    def delete(self, cid: str):
        """Delete a conversation context."""
        if cid in self.conversations:
            del self.conversations[cid]
            logger.info(f"Deleted conversation context for {cid}")
    
    def get_stats(self) -> Dict:
        """Get statistics about conversations."""
        return {
            "total_conversations": len(self.conversations),
            "max_conversations": self.MAX_CONVERSATIONS,
            "conversations": [
                {
                    "cid": cid,
                    "messages": len(ctx.messages),
                    "created_at": ctx.created_at.isoformat(),
                    "last_updated": ctx.last_updated.isoformat()
                }
                for cid, ctx in self.conversations.items()
            ]
        }


# Global conversation manager instance
conversation_manager = ConversationManager()
