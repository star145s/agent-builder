"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any


# ============================================================================
# Unified Component Models (New Interface)
# ============================================================================

class InputItem(BaseModel):
    """Represents a single input item with user query.
    
    The notebook/document is NOT part of input - it's part of the OUTPUT
    from the previous component execution. This creates cleaner separation:
    - Input = what the user asks
    - Output = what the component produces (response + notebook)
    """
    user_query: str = Field(..., min_length=1, max_length=10000, description="User's query or question (required, max 10k chars)")
    
    @field_validator('user_query')
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Validate content length to prevent token abuse."""
        if len(v) > 10000:
            raise ValueError(f"user_query too long ({len(v)} chars, max 10000)")
        if not v.strip():
            raise ValueError("user_query cannot be empty or whitespace only")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"user_query": "How do I implement JWT authentication?"},
                {"user_query": "Write a short story about a detective"},
                {"user_query": "Review and improve this code"}
            ]
        }
    }


class ComponentOutputData(BaseModel):
    """The actual output data containing immediate response and notebook.
    
    This is what gets returned in ComponentOutput.output field.
    Components produce TWO things:
    1. immediate_response: Direct answer/explanation the agent gives immediately
       - If NO notebook editing: This is the FULL answer
       - If notebook editing: Agent can say "I've updated the code..." or similar
    2. notebook: The actual code/document/content (or "no update" if no editing)
    """
    immediate_response: str = Field(..., max_length=50000, description="Direct answer or explanation from the agent (max 50k chars)")
    notebook: str = Field(..., max_length=100000, description="Updated notebook/code/document content, or 'no update' if no editing occurred (max 100k chars)")
    
    @field_validator('immediate_response')
    @classmethod
    def validate_immediate_response(cls, v: str) -> str:
        """Validate immediate response length."""
        if len(v) > 50000:
            raise ValueError(f"immediate_response too long ({len(v)} chars, max 50000)")
        return v
    
    @field_validator('notebook')
    @classmethod
    def validate_notebook(cls, v: str) -> str:
        """Validate notebook length."""
        if len(v) > 100000:
            raise ValueError(f"notebook too long ({len(v)} chars, max 100000)")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "immediate_response": "I've added JWT authentication with login and protected routes.",
                    "notebook": "from flask import Flask\nfrom flask_jwt_extended import JWTManager, create_access_token, jwt_required\n\napp = Flask(__name__)\napp.config['JWT_SECRET_KEY'] = 'secret'\njwt = JWTManager(app)\n\n@app.route('/login', methods=['POST'])\ndef login():\n    token = create_access_token(identity='user')\n    return {'token': token}\n\n@app.route('/protected')\n@jwt_required()\ndef protected():\n    return {'msg': 'Access granted'}"
                },
                {
                    "immediate_response": "JWT (JSON Web Token) is a compact, URL-safe means of representing claims between two parties. It consists of three parts: header, payload, and signature...",
                    "notebook": "no update"
                }
            ]
        }
    }


class PreviousOutput(BaseModel):
    """Represents output from a previous component execution for chaining.
    
    This matches the new ComponentOutput structure for workflow chaining.
    When chaining components, use this format to pass results forward.
    
    Fields:
    - task: What task was performed
    - input: Input items (user queries only)
    - output: ComponentOutputData with {immediate_response, notebook}
    - component: Which component generated this
    """
    task: str = Field(..., max_length=1000, description="The task that was executed (max 1000 chars)")
    input: List[InputItem] = Field(..., max_length=50, description="Input items (user queries, max 50 items)")
    output: ComponentOutputData = Field(..., description="Output data with immediate_response and notebook")
    component: str = Field(..., max_length=50, description="Component name (complete, refine, feedback, etc., max 50 chars)")
    
    @field_validator('input')
    @classmethod
    def validate_input_items(cls, v: List[InputItem]) -> List[InputItem]:
        """Validate input items count."""
        if len(v) > 50:
            raise ValueError(f"Too many input items in previous output ({len(v)}, max 50)")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task": "Add authentication",
                "input": [
                    {
                        "user_query": "Add JWT to my Flask app"
                    }
                ],
                "output": {
                    "immediate_response": "I've added JWT authentication with login and protected routes.",
                    "notebook": "from flask import Flask\nfrom flask_jwt_extended import JWTManager\n..."
                },
                "component": "complete"
            }
        }
    }


class ComponentInput(BaseModel):
    """Unified input format for all component functions."""
    cid: str = Field(..., max_length=100, description="Conversation ID (max 100 chars)")
    task: str = Field(..., max_length=1000, description="Task description (max 1000 chars)")
    input: List[InputItem] = Field(..., max_length=50, description="List of user queries (max 50 items)")
    previous_outputs: List[PreviousOutput] = Field(
        default_factory=list,
        max_length=20,
        description="Outputs from previous component executions (max 20 items)"
    )
    use_conversation_history: bool = Field(
        default=True,
        description="Whether to include conversation history in the LLM context"
    )
    use_playbook: bool = Field(
        default=True,
        description="Whether to include playbook insights in the LLM context"
    )
    
    @field_validator('input')
    @classmethod
    def validate_input_count(cls, v: List[InputItem]) -> List[InputItem]:
        """Validate input count to prevent abuse."""
        if len(v) > 50:
            raise ValueError(f"Too many input items ({len(v)}, max 50)")
        if len(v) == 0:
            raise ValueError("At least one input item is required")
        return v
    
    @field_validator('previous_outputs')
    @classmethod
    def validate_previous_outputs_count(cls, v: List[PreviousOutput]) -> List[PreviousOutput]:
        """Validate previous outputs count."""
        if len(v) > 20:
            raise ValueError(f"Too many previous outputs ({len(v)}, max 20)")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "cid": "user_123_conv_456",
                "task": "Implement authentication system",
                "input": [
                    {
                        "user_query": "Create JWT authentication for my Flask app"
                    }
                ],
                "previous_outputs": [
                    {
                        "task": "Research JWT",
                        "input": [{"user_query": "What is JWT?"}],
                        "output": {
                            "immediate_response": "JWT is a standard for secure authentication...",
                            "notebook": "no update"
                        },
                        "component": "internet_search"
                    }
                ]
            }
        }
    }


class ComponentOutput(BaseModel):
    """Unified output format for all component functions.
    
    IMPORTANT - Canvas-style behavior (like ChatGPT Canvas):
    
    NEW CLEANER DESIGN:
    - input: Contains only user queries (what user asks)
    - output: Contains BOTH immediate_response AND notebook (what component produces)
    
    This creates perfect separation:
    - Input = what you ask for
    - Output = what you get back (immediate answer + content)
    
    Format:
    - cid: Conversation ID for traceability
    - task: The task that was executed
    - input: List of InputItem (user queries only)
    - output: ComponentOutputData with:
        * immediate_response: Direct answer from agent
          - If NO editing: Full answer here
          - If editing: Agent can say "I've updated..." or similar
        * notebook: Updated code/document OR "no update"
    - component: Which component generated this output
    
    Response Strategy:
    1. **For tasks requiring notebook/code editing** (write code, edit story, modify report):
       - output.immediate_response: "I've updated the code to include authentication..."
       - output.notebook: The ACTUAL updated code/story/document
    
    2. **For conversational tasks** (explain, answer, discuss):
       - output.immediate_response: The FULL answer/explanation
       - output.notebook: "no update"
    
    Example Flow (like Canvas):
    User: "Write a short story"
    → output.immediate_response: "Here's a short story about a detective..."
    → output.notebook: "Detective Jake walked into the dark alley..."
    
    User: "Make it longer"
    → output.immediate_response: "I've expanded the story with more details..."
    → output.notebook: "Detective Jake walked into the dark alley. He had been following..."
    """
    cid: str = Field(..., max_length=100, description="Conversation ID this output belongs to (max 100 chars)")
    task: str = Field(..., max_length=1000, description="The task that was executed (max 1000 chars)")
    input: List[InputItem] = Field(..., max_length=50, description="Input items (user queries, max 50 items)")
    output: ComponentOutputData = Field(..., description="Output data with immediate_response and notebook")
    component: str = Field(..., max_length=50, description="Component name that generated this output (max 50 chars)")
    
    @field_validator('input')
    @classmethod
    def validate_input_items(cls, v: List[InputItem]) -> List[InputItem]:
        """Validate input items count."""
        if len(v) > 50:
            raise ValueError(f"Too many input items ({len(v)}, max 50)")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cid": "user_123_conv_456",
                    "task": "Write authentication code",
                    "input": [
                        {
                            "user_query": "Add JWT authentication to my Flask app"
                        }
                    ],
                    "output": {
                        "immediate_response": "I've added JWT authentication to your Flask app. The code now includes a /login endpoint that generates tokens and a /protected endpoint that requires authentication.",
                        "notebook": "from flask import Flask\nfrom flask_jwt_extended import JWTManager, create_access_token, jwt_required\n\napp = Flask(__name__)\napp.config['JWT_SECRET_KEY'] = 'secret'\njwt = JWTManager(app)\n\n@app.route('/login', methods=['POST'])\ndef login():\n    token = create_access_token(identity='user')\n    return {'token': token}\n\n@app.route('/protected')\n@jwt_required()\ndef protected():\n    return {'msg': 'Access granted'}"
                    },
                    "component": "complete"
                },
                {
                    "cid": "user_123_conv_456",
                    "task": "Make story longer",
                    "input": [
                        {
                            "user_query": "Write it longer with more details"
                        }
                    ],
                    "output": {
                        "immediate_response": "I've expanded the story with more atmospheric details about the investigation and added tension to the confrontation scene.",
                        "notebook": "Detective Jake walked into the dark alley. He had been following the suspect for three days now, through rain-soaked streets and abandoned warehouses. Tonight would be different. He could feel it in his bones.\n\nThe footsteps ahead quickened. Jake's hand moved instinctively to his holster as he rounded the corner. There, standing under the flickering streetlight, was the figure he'd been chasing. But something was wrong. The suspect was smiling."
                    },
                    "component": "refine"
                },
                {
                    "cid": "user_123_conv_456",
                    "task": "Explain concept",
                    "input": [
                        {
                            "user_query": "What are Python decorators?"
                        }
                    ],
                    "output": {
                        "immediate_response": "Decorators in Python are functions that modify the behavior of other functions. They use the @decorator syntax and are commonly used for logging, authentication, and caching. For example, @login_required can be placed above a function to ensure only authenticated users can access it.",
                        "notebook": "no update"
                    },
                    "component": "complete"
                }
            ]
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
