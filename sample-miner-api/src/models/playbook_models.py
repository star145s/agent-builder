"""Playbook models for storing structured insights from human feedback."""

from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import JSON, Index


class PlaybookEntry(SQLModel, table=True):
    """Playbook entries - structured knowledge extracted from human feedback."""
    __tablename__ = "playbook_entries"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    cid: str = Field(index=True, max_length=100, description="Conversation ID this belongs to")
    
    # Insight information
    insight_type: str = Field(
        max_length=50,
        description="Type of insight: preference, instruction, fact, correction, context"
    )
    key: str = Field(max_length=200, description="Searchable key/topic for this insight")
    value: str = Field(description="The actual insight/knowledge content")
    
    # Operation tracking
    operation: str = Field(
        default="insert",
        max_length=20,
        description="Last operation performed (insert/update/delete)"
    )
    
    # Metadata
    source_feedback: str = Field(description="Original human feedback text")
    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="LLM confidence in this extraction (0-1)"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When insight was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last updated")
    
    # Versioning
    version: int = Field(default=1, description="Version number for updates")
    is_active: bool = Field(default=True, index=True, description="Whether this entry is currently active")
    
    # Additional context
    tags: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Tags for categorization"
    )
    extra_data: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "cid": "user_123_conv_456",
                "insight_type": "preference",
                "key": "response_style",
                "value": "User prefers concise, bullet-point responses with code examples",
                "operation": "insert",
                "source_feedback": "Please keep responses short and always include code examples",
                "confidence_score": 0.9,
                "tags": ["communication", "style"],
                "is_active": True
            }
        }


class PlaybookOperation(SQLModel, table=True):
    """History of operations performed on playbook entries."""
    __tablename__ = "playbook_operations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    playbook_entry_id: Optional[int] = Field(
        default=None,
        foreign_key="playbook_entries.id",
        description="Related playbook entry (null for failed operations)"
    )
    
    cid: str = Field(index=True, max_length=100, description="Conversation ID")
    operation: str = Field(max_length=20, description="Operation type (insert/update/delete)")
    
    # What was extracted
    extracted_data: dict = Field(sa_column=Column(JSON), description="Full extracted insight data")
    
    # Result
    success: bool = Field(default=True, description="Whether operation succeeded")
    error_message: Optional[str] = Field(default=None, description="Error if operation failed")
    
    # Context
    source_feedback: str = Field(description="Original human feedback")
    llm_response: Optional[str] = Field(default=None, description="Full LLM extraction response")
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True, description="When operation occurred")
    
    class Config:
        json_schema_extra = {
            "example": {
                "playbook_entry_id": 1,
                "cid": "user_123_conv_456",
                "operation": "insert",
                "extracted_data": {
                    "insight_type": "preference",
                    "key": "response_style",
                    "value": "User prefers concise responses"
                },
                "success": True,
                "source_feedback": "Please keep responses short"
            }
        }


# Create indexes for efficient querying
__table_args__ = (
    Index('idx_playbook_cid_active', 'cid', 'is_active'),
    Index('idx_playbook_cid_key', 'cid', 'key'),
    Index('idx_playbook_type_active', 'insight_type', 'is_active'),
)
