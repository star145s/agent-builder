"""Conversation context management using SQLite database.

This module uses SQLite for persistent storage (file-based, zero configuration).
Database file location: ./data/miner_api.db (configured in .env)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from src.repositories.conversation_repository import ConversationRepository

logger = logging.getLogger(__name__)


class ConversationContext:
    """
    Manages conversation context for a single conversation ID.
    Now backed by SQLite database via SQLModel ORM.
    
    Stores up to 10 recent messages and automatically cleans up old messages.
    Messages older than 7 days are automatically deleted.
    """
    
    MAX_MESSAGES = 10  # Store up to 10 recent messages
    MAX_MESSAGE_AGE_DAYS = 7  # Auto-delete messages older than 7 days
    
    def __init__(self, cid: str):
        self.cid = cid
        self.repository = ConversationRepository()
        # Ensure conversation exists in database
        self.repository.get_or_create_conversation(cid)
    
    def add_message(self, role: str, content: str, extra_data: Optional[dict] = None):
        """
        Add a message to conversation history. Stores up to 10 recent messages.
        Automatically cleans up messages older than 7 days.
        """
        # Skip if content is None or empty
        if not content or not content.strip():
            logger.warning(f"Skipping empty message for conversation {self.cid}")
            return
        
        # Add message to database
        self.repository.add_message(
            cid=self.cid,
            role=role,
            content=content,
            extra_data=extra_data
        )
    
    def add_user_message(self, content: str, extra_data: Optional[dict] = None):
        """Add a user message to conversation history."""
        self.add_message("user", content, extra_data)
    
    def add_assistant_message(self, content: str, extra_data: Optional[dict] = None):
        """Add an assistant message to conversation history."""
        self.add_message("assistant", content, extra_data)
    
    def get_messages(self) -> List[Dict]:
        """
        Get conversation history as a list of message dictionaries.
        Returns up to 10 most recent messages, excluding messages older than 7 days.
        """
        messages = self.repository.get_recent_messages(self.cid, count=self.MAX_MESSAGES)
        return messages
    
    def get_context_summary(self) -> str:
        """
        Get a summary of the conversation context from recent messages.
        """
        messages = self.get_messages()
        if not messages:
            return "No conversation context yet."
        
        history_text = "Recent conversation:\n"
        for msg in messages[-5:]:  # Show last 5 messages
            role = msg['role'].capitalize()
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            history_text += f"{role}: {content}\n"
        
        return history_text
    
    def get_context(self) -> str:
        """
        Get full conversation context as formatted string for LLM.
        Alias for get_context_summary.
        """
        return self.get_context_summary()
    
    def get_recent_messages(self, count: int = 5) -> List[Dict]:
        """
        Get the most recent N messages.
        
        Args:
            count: Number of recent messages to return
        
        Returns:
            List of message dictionaries
        """
        return self.repository.get_recent_messages(self.cid, count=count)
    
    def clear(self):
        """Clear conversation messages by deleting the conversation."""
        self.repository.delete_conversation(self.cid)
        logger.info(f"Cleared messages for conversation {self.cid}.")
    
    @property
    def created_at(self) -> Optional[datetime]:
        """Get conversation creation time."""
        conversation = self.repository.get_conversation(self.cid)
        return conversation.created_at if conversation else None
    
    @property
    def last_updated(self) -> Optional[datetime]:
        """Get last update time."""
        conversation = self.repository.get_conversation(self.cid)
        return conversation.last_updated if conversation else None


class ConversationManager:
    """
    Manages all conversation contexts.
    Now uses SQLite database for persistent storage.
    """
    
    def __init__(self):
        self.repository = ConversationRepository()
    
    def get_or_create(self, cid: str) -> ConversationContext:
        """Get an existing conversation or create a new one."""
        return ConversationContext(cid)
    
    def get(self, cid: str) -> Optional[ConversationContext]:
        """Get an existing conversation context."""
        conversation = self.repository.get_conversation(cid)
        if conversation:
            return ConversationContext(cid)
        return None
    
    def delete(self, cid: str):
        """Delete a conversation context."""
        self.repository.delete_conversation(cid)
    
    def get_stats(self) -> Dict:
        """Get statistics about conversations."""
        conversations = self.repository.get_all_conversations(limit=100)
        
        return {
            "total_conversations": len(conversations),
            "max_conversations": 100,  # Database limit for stats display
            "conversations": [
                {
                    "cid": conv.cid,
                    "messages": conv.message_count,
                    "created_at": conv.created_at.isoformat(),
                    "last_updated": conv.last_updated.isoformat()
                }
                for conv in conversations
            ]
        }


# Global conversation manager instance
conversation_manager = ConversationManager()
