"""Database models for conversation storage using SQLModel + SQLite."""

from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import JSON


class Conversation(SQLModel, table=True):
    """Conversation table - stores conversation metadata."""
    __tablename__ = "conversations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cid: str = Field(index=True, unique=True, max_length=100, description="Conversation ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When conversation was created")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last message timestamp")
    message_count: int = Field(default=0, description="Total number of messages")
    
    # Relationship to messages
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cid": "user_123_conv_456",
                "created_at": "2024-01-01T12:00:00",
                "last_updated": "2024-01-01T12:05:00",
                "message_count": 5
            }
        }


class Message(SQLModel, table=True):
    """Message table - stores individual messages in conversations."""
    __tablename__ = "messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversations.id", index=True, description="FK to conversation")
    role: str = Field(max_length=20, description="Message role: 'user' or 'assistant'")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True, description="Message timestamp")
    extra_data: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional metadata (component, task, etc.)"
    )
    
    # Relationship back to conversation
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": 1,
                "role": "user",
                "content": "What is machine learning?",
                "timestamp": "2024-01-01T12:00:00",
                "extra_data": {
                    "component": "complete",
                    "task": "Answer question"
                }
            }
        }
