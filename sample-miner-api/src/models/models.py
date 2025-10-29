"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class Action(BaseModel):
    """Represents an action to be taken."""
    task: str = Field(..., description="The task description")
    input: str = Field(..., description="The input for the task")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task": "Search for information",
                "input": "machine learning basics"
            }
        }
    }


class CompleteRequest(BaseModel):
    """Request model for task completion."""
    
    cid: str = Field(..., description="Conversation ID - unique for each conversation/user")
    task: str = Field(..., description="Task description")
    input: str = Field(..., description="User query/input")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cid": "user_123_conv_456",
                "task": "Answer a question about Python",
                "input": "What is a decorator in Python?"
            }
        }
    }


class CompleteResponse(BaseModel):
    """Response model for task completion."""
    
    response: str = Field(..., description="The response to the task")
    actions: List[Action] = Field(default_factory=list, description="Suggested follow-up actions")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "A decorator is a design pattern in Python...",
                "actions": [
                    {
                        "task": "Show example", 
                        "input": "decorator example code"
                    }
                ]
            }
        }
    }


class FeedbackItem(BaseModel):
    """A single feedback item."""
    problem: str = Field(..., description="The identified problem")
    suggestion: str = Field(..., description="Suggestion for improvement")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "problem": "Response is too technical",
                "suggestion": "Use simpler language for beginners"
            }
        }
    }


class FeedbackRequest(BaseModel):
    """Request model for providing feedback on output."""
    
    cid: str = Field(..., description="Conversation ID")
    task: str = Field(..., description="The task that was performed")
    input: str = Field(..., description="The input that was given")
    output: str = Field(..., description="The output to evaluate")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cid": "user_123_conv_456",
                "task": "Explain Python decorators",
                "input": "What is a decorator?",
                "output": "A decorator is a function that modifies another function..."
            }
        }
    }


class FeedbackResponse(BaseModel):
    """Response model for feedback."""
    
    feedbacks: List[FeedbackItem] = Field(..., description="List of feedback items")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "feedbacks": [
                    {
                        "problem": "Missing practical examples",
                        "suggestion": "Add code examples to illustrate the concept"
                    },
                    {
                        "problem": "Too brief",
                        "suggestion": "Expand explanation with more details"
                    }
                ]
            }
        }
    }


class RefineRequest(BaseModel):
    """Request model for refining output based on feedback."""
    
    cid: str = Field(..., description="Conversation ID")
    task: str = Field(..., description="The task to perform")
    input: str = Field(..., description="The original input")
    output: str = Field(..., description="The previous output to refine")
    feedbacks: List[FeedbackItem] = Field(..., description="List of feedback to incorporate")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cid": "user_123_conv_456",
                "task": "Explain Python decorators",
                "input": "What is a decorator?",
                "output": "A decorator is a function that modifies another function.",
                "feedbacks": [
                    {
                        "problem": "Missing examples",
                        "suggestion": "Add code examples"
                    }
                ]
            }
        }
    }


class RefineResponse(BaseModel):
    """Response model for refined output."""
    
    output: str = Field(..., description="The refined output")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "output": "A decorator is a design pattern in Python that allows you to modify the behavior of a function. Here's an example: @log_time\\ndef my_function():..."
            }
        }
    }


class HumanFeedbackRequest(BaseModel):
    """Request model for human feedback."""
    
    cid: str = Field(..., description="Conversation ID")
    human_feedback: str = Field(..., description="Human feedback to incorporate into knowledge")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cid": "user_123_conv_456",
                "human_feedback": "The user prefers simple explanations with practical examples"
            }
        }
    }


class HumanFeedbackResponse(BaseModel):
    """Response model for human feedback."""
    
    status: str = Field(..., description="Status of the feedback incorporation")
    message: str = Field(..., description="Confirmation message")
    actions_applied: List[Dict[str, Any]] = Field(default_factory=list, description="Playbook actions that were applied")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Feedback incorporated into conversation context",
                "actions_applied": [
                    {
                        "action": "insert",
                        "node_id": "pref_001",
                        "content": "User prefers concise explanations"
                    }
                ]
            }
        }
    }


class PlaybookNode(BaseModel):
    """A single node in the user's preference playbook."""
    
    node_id: str = Field(..., description="Unique identifier for this preference node")
    content: str = Field(..., description="The preference or knowledge content")
    category: Optional[str] = Field(None, description="Category of preference (e.g., 'style', 'domain', 'format')")
    created_at: str = Field(..., description="When this node was created")
    updated_at: str = Field(..., description="When this node was last updated")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "node_id": "pref_001",
                "content": "User prefers concise explanations with code examples",
                "category": "style",
                "created_at": "2025-10-26T10:00:00Z",
                "updated_at": "2025-10-26T10:00:00Z"
            }
        }
    }


class PlaybookAction(BaseModel):
    """An action to modify the playbook."""
    
    action: str = Field(..., description="Action type: 'insert', 'update', or 'delete'")
    node_id: str = Field(..., description="Node ID to insert/update/delete")
    content: Optional[str] = Field(None, description="Content for insert/update actions")
    category: Optional[str] = Field(None, description="Category for the node")
    reason: Optional[str] = Field(None, description="Reason for this action")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "action": "insert",
                "node_id": "pref_001",
                "content": "User prefers technical depth over simplicity",
                "category": "style",
                "reason": "User explicitly requested more detailed technical explanations"
            }
        }
    }


class PlaybookActionsResponse(BaseModel):
    """Response from LLM with playbook actions to apply."""
    
    actions: List[PlaybookAction] = Field(..., description="List of playbook actions to perform")
    reasoning: Optional[str] = Field(None, description="Overall reasoning for these actions")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "actions": [
                    {
                        "action": "update",
                        "node_id": "pref_001",
                        "content": "User prefers highly technical explanations with mathematical proofs",
                        "category": "style",
                        "reason": "User's feedback suggests they want more rigor"
                    }
                ],
                "reasoning": "Updated preference node to reflect user's desire for more technical depth"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Invalid request",
                "detail": "Missing required field: prompt"
            }
        }
    }


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    miner_name: str = Field(..., description="Miner identifier")
    model: str = Field(..., description="AI model in use")
    openai_status: str = Field(..., description="OpenAI API connectivity status")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "miner_name": "sample-miner-gpt4o",
                "model": "gpt-4o",
                "openai_status": "connected"
            }
        }
    }


class CapabilitiesResponse(BaseModel):
    """Capabilities response model."""
    
    miner_name: str
    model: str
    supported_functions: List[str]
    conversation_aware: bool
    max_context_length: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "miner_name": "sample-miner-gpt4o",
                "model": "gpt-4o",
                "supported_functions": ["complete", "feedback", "refine", "human_feedback"],
                "conversation_aware": True,
                "max_context_length": 10
            }
        }
    }
