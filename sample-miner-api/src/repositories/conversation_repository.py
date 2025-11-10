"""Conversation repository for database operations."""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlmodel import Session, select, func, delete
from src.models.db_models import Conversation, Message
from src.core.database import get_db_session

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for conversation database operations."""
    
    MAX_MESSAGES = 10  # Store up to 10 recent messages per conversation
    MAX_MESSAGE_AGE_DAYS = 7  # Auto-delete messages older than 1 week
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository with optional session.
        If no session provided, will create one per operation.
        """
        self._session = session
        self._owns_session = session is None
    
    def _get_session(self) -> Session:
        """Get session (existing or create new)."""
        if self._session:
            return self._session
        return get_db_session()
    
    def get_or_create_conversation(self, cid: str) -> Conversation:
        """Get existing conversation or create new one."""
        session = self._get_session()
        try:
            # Try to find existing conversation
            statement = select(Conversation).where(Conversation.cid == cid)
            conversation = session.exec(statement).first()
            
            if not conversation:
                # Create new conversation
                conversation = Conversation(cid=cid)
                session.add(conversation)
                session.commit()
                session.refresh(conversation)
                logger.info(f"Created new conversation: {cid}")
            
            return conversation
        finally:
            if self._owns_session:
                session.close()
    
    def get_conversation(self, cid: str) -> Optional[Conversation]:
        """Get conversation by CID."""
        session = self._get_session()
        try:
            statement = select(Conversation).where(Conversation.cid == cid)
            return session.exec(statement).first()
        finally:
            if self._owns_session:
                session.close()
    
    def add_message(
        self,
        cid: str,
        role: str,
        content: str,
        extra_data: Optional[dict] = None
    ) -> Message:
        """
        Add a message to conversation.
        Automatically manages message limits and cleanup.
        """
        session = self._get_session()
        try:
            # Get or create conversation
            conversation = self.get_or_create_conversation(cid)
            
            # Clean up old messages first
            self._cleanup_old_messages(session, conversation.id)
            
            # Enforce max messages limit
            self._enforce_message_limit(session, conversation.id)
            
            # Create new message
            message = Message(
                conversation_id=conversation.id,
                role=role,
                content=content,
                extra_data=extra_data or {}
            )
            session.add(message)
            
            # Update conversation metadata
            conversation.last_updated = datetime.utcnow()
            conversation.message_count = self._count_messages(session, conversation.id)
            
            session.commit()
            session.refresh(message)
            
            logger.info(
                f"Added {role} message to conversation {cid}. "
                f"Total messages: {conversation.message_count}"
            )
            
            return message
        finally:
            if self._owns_session:
                session.close()
    
    def get_messages(
        self,
        cid: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """
        Get messages for a conversation.
        Returns most recent messages first.
        """
        session = self._get_session()
        try:
            conversation = self.get_conversation(cid)
            if not conversation:
                return []
            
            # Clean up old messages
            self._cleanup_old_messages(session, conversation.id)
            
            # Query messages
            statement = (
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(Message.timestamp.desc())
                .offset(offset)
            )
            
            if limit:
                statement = statement.limit(limit)
            
            messages = session.exec(statement).all()
            return list(reversed(messages))  # Return in chronological order
        finally:
            if self._owns_session:
                session.close()
    
    def get_recent_messages(self, cid: str, count: int = 5) -> List[Dict]:
        """
        Get N most recent messages as dictionaries.
        Format suitable for LLM context.
        """
        messages = self.get_messages(cid, limit=count)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    
    def delete_conversation(self, cid: str) -> bool:
        """Delete conversation and all its messages."""
        session = self._get_session()
        try:
            conversation = self.get_conversation(cid)
            if not conversation:
                return False
            
            session.delete(conversation)
            session.commit()
            logger.info(f"Deleted conversation: {cid}")
            return True
        finally:
            if self._owns_session:
                session.close()
    
    def get_conversation_stats(self, cid: str) -> Optional[Dict]:
        """Get statistics for a conversation."""
        session = self._get_session()
        try:
            conversation = self.get_conversation(cid)
            if not conversation:
                return None
            
            return {
                "cid": conversation.cid,
                "created_at": conversation.created_at.isoformat(),
                "last_updated": conversation.last_updated.isoformat(),
                "message_count": conversation.message_count,
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in conversation.messages
                ]
            }
        finally:
            if self._owns_session:
                session.close()
    
    def get_all_conversations(self, limit: int = 100) -> List[Conversation]:
        """Get all conversations (limited)."""
        session = self._get_session()
        try:
            statement = (
                select(Conversation)
                .order_by(Conversation.last_updated.desc())
                .limit(limit)
            )
            return list(session.exec(statement).all())
        finally:
            if self._owns_session:
                session.close()
    
    def _cleanup_old_messages(self, session: Session, conversation_id: int):
        """Remove messages older than MAX_MESSAGE_AGE_DAYS."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.MAX_MESSAGE_AGE_DAYS)
        
        statement = delete(Message).where(
            Message.conversation_id == conversation_id,
            Message.timestamp < cutoff_date
        )
        
        result = session.exec(statement)
        if result.rowcount > 0:
            session.commit()
            logger.info(f"Cleaned up {result.rowcount} old messages from conversation {conversation_id}")
    
    def _enforce_message_limit(self, session: Session, conversation_id: int):
        """Enforce MAX_MESSAGES limit by deleting oldest messages."""
        # Count current messages
        count_statement = select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id
        )
        count = session.exec(count_statement).one()
        
        if count >= self.MAX_MESSAGES:
            # Get IDs of messages to delete (keep most recent MAX_MESSAGES-1)
            messages_to_keep = (
                select(Message.id)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.timestamp.desc())
                .limit(self.MAX_MESSAGES - 1)
            )
            
            delete_statement = delete(Message).where(
                Message.conversation_id == conversation_id,
                Message.id.not_in(messages_to_keep)
            )
            
            result = session.exec(delete_statement)
            if result.rowcount > 0:
                session.commit()
                logger.info(f"Removed {result.rowcount} old messages to maintain limit")
    
    def _count_messages(self, session: Session, conversation_id: int) -> int:
        """Count messages in a conversation."""
        statement = select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id
        )
        return session.exec(statement).one()
