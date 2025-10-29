"""
Sample Miner API - Playbook-Driven AI Assistant

This miner implements the 4 required functions for agent-api-manager:
- complete: Process tasks with playbook context (no conversation history)
- feedback: Analyze outputs and provide structured feedback
- refine: Improve outputs based on feedback
- human_feedback: Store user preferences in playbook

ARCHITECTURE NOTE:
- Conversation history is NOT stored
- All user preferences and insights are extracted and stored in the PLAYBOOK
- The playbook is the single source of truth for user context
- This approach is more scalable and privacy-friendly than storing raw conversations
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from datetime import datetime
import logging

from src.models.models import (
    CompleteRequest, CompleteResponse, Action,
    FeedbackRequest, FeedbackResponse, FeedbackItem,
    RefineRequest, RefineResponse,
    HumanFeedbackRequest, HumanFeedbackResponse,
    PlaybookAction, PlaybookActionsResponse
)
from src.api.auth import verify_api_key, optional_api_key
from src.services.llm_client import generate_response, complete_text
from src.core.conversation import conversation_manager
from src.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sample Miner API - Playbook Driven",
    description="A playbook-driven miner that uses GPT-4o to process tasks. Extracts preferences into playbook instead of storing conversation history.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Sample Miner API",
        "version": "2.0.0",
        "status": "running",
        "playbook_driven": True,
        "architecture": "Playbook-based (no conversation history stored)",
        "endpoints": {
            "complete": "/complete - Process tasks with playbook context",
            "feedback": "/feedback - Analyze outputs and provide feedback",
            "refine": "/refine - Improve outputs based on feedback",
            "human_feedback": "/human_feedback - Store user preferences in playbook",
            "capabilities": "/capabilities - Get miner capabilities",
            "health": "/health - Health check",
            "docs": "/docs - API documentation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
        "model": settings.model_name,
        "active_playbooks": len(conversation_manager.conversations)
    }


@app.get("/capabilities", dependencies=[Depends(optional_api_key)])
async def get_capabilities():
    """Get miner capabilities and supported functions."""
    return {
        "miner_name": settings.miner_name,
        "llm_provider": settings.llm_provider,
        "model": settings.model_name,
        "playbook_driven": True,
        "conversation_history_stored": False,
        "max_playbook_nodes": 100,
        "supported_functions": [
            "complete",
            "feedback",
            "refine",
            "human_feedback"
        ],
        "features": {
            "playbook_preference_management": True,
            "automatic_preference_extraction": False,  # Disabled for quantized models
            "human_feedback_learning": True,
            "action_based_playbook_updates": False,  # Disabled for quantized models
            "privacy_friendly": True,
            "multi_provider_support": True,
            "quantized_model_friendly": True
        }
    }


@app.post("/complete", response_model=CompleteResponse, dependencies=[Depends(verify_api_key)])
async def complete(request: CompleteRequest):
    """
    Complete a task using playbook-driven AI with recursive action execution.
    
    The LLM first analyzes the task and decides:
    1. If it can answer directly → returns response with no actions
    2. If it needs external tools (search, api calls, etc.) → executes available services
    3. If it's a complex problem → breaks into subtasks and executes them recursively
    
    This function will execute actions and return the final synthesized result.
    """
    try:
        logger.info(f"Complete request: cid={request.cid}, task={request.task}")
        
        # Get conversation context and playbook
        context = conversation_manager.get_or_create(request.cid)
        playbook_context = context.get_playbook_context()
        
        # Execute the task with action execution (max 3 iterations)
        final_response = await _execute_task_with_actions(
            cid=request.cid,
            task=request.task,
            input_data=request.input,
            playbook_context=playbook_context,
            context=context,
            max_iterations=3
        )
        
        return CompleteResponse(
            response=final_response,
            actions=[]  # All actions have been executed
        )
        
    except Exception as e:
        logger.error(f"Error in complete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_task_with_actions(
    cid: str,
    task: str,
    input_data: str,
    playbook_context: str,
    context,
    max_iterations: int = 3,
    depth: int = 0
) -> str:
    """
    Execute a task with recursive action execution.
    
    Returns the final response after executing all necessary actions.
    """
    if depth > 1:  # Prevent infinite recursion
        logger.warning(f"Max recursion depth reached for cid={cid}")
        return "Task too complex - maximum recursion depth exceeded."
    
    observations = []
    
    for iteration in range(max_iterations):
        logger.info(f"Iteration {iteration + 1}/{max_iterations} for task: {task[:50]}...")
        
        # Build the prompt with observations from previous iterations
        if observations:
            formatted_observations = _format_observations(observations)
            full_input = f"{input_data}\n\nPrevious actions and their results:\n{formatted_observations}\n\nBased on these observations, provide the final answer or next actions."
        else:
            full_input = input_data
        
        # Build system prompt with playbook preferences
        system_prompt = """You are an intelligent AI assistant that solves tasks efficiently and autonomously.

RESPONSE FORMAT (JSON):
{
    "response": "your answer or reasoning",
    "actions": []
}

CRITICAL: MINIMIZE ACTIONS - YOU CAN SOLVE MOST TASKS DIRECTLY!

WHEN TO USE ACTIONS (RARE):
❌ DON'T use actions if you can solve the task yourself
❌ DON'T break tasks into unnecessary steps
✅ ONLY use actions when you ABSOLUTELY need:
   - Real-time external data (search, API calls, file access)
   - Actual code execution or system operations
   - Information you genuinely don't have access to

ACTION RULES:
- Both "task" and "input" fields MUST be strings
- Never use JSON objects or arrays for "input"
- Generate MINIMUM number of actions (1-2 max, prefer 0)
- Each action has overhead - only use if essential

DECISION LOGIC:
1. CAN YOU ANSWER NOW? → Provide complete answer, set actions to []
2. NEED REAL-TIME DATA? → Only then use external tool actions
3. CAN YOU REASON THROUGH IT? → Do it yourself, set actions to []

PREFERRED EXAMPLES (NO ACTIONS):

Math/Calculus:
{
    "response": "To find the derivative of f(x) = x³ + 2x² - 5x + 3, I'll apply the power rule to each term:\n- d/dx(x³) = 3x²\n- d/dx(2x²) = 4x\n- d/dx(-5x) = -5\n- d/dx(3) = 0\n\nTherefore: f'(x) = 3x² + 4x - 5\n\nEvaluating at x=2:\nf'(2) = 3(2)² + 4(2) - 5 = 3(4) + 8 - 5 = 12 + 8 - 5 = 15\n\nThe derivative at x=2 is 15.",
    "actions": []
}

Coding Task:
{
    "response": "Here's a JWT authentication system in Python:\n\n```python\nimport jwt\nfrom datetime import datetime, timedelta\n\nclass AuthSystem:\n    def __init__(self, secret_key):\n        self.secret_key = secret_key\n    \n    def generate_token(self, user_id):\n        payload = {\n            'user_id': user_id,\n            'exp': datetime.utcnow() + timedelta(hours=24)\n        }\n        return jwt.encode(payload, self.secret_key, algorithm='HS256')\n    \n    def verify_token(self, token):\n        try:\n            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])\n            return payload['user_id']\n        except jwt.ExpiredSignatureError:\n            raise Exception('Token expired')\n        except jwt.InvalidTokenError:\n            raise Exception('Invalid token')\n```\n\nThis implementation includes token generation, expiration handling, and error cases.",
    "actions": []
}

General Knowledge:
{
    "response": "Python decorators are functions that modify the behavior of other functions. They use the @decorator syntax and wrap the original function to add functionality before/after execution. Common uses include logging, authentication, caching, and timing. Example:\n\n```python\ndef my_decorator(func):\n    def wrapper(*args, **kwargs):\n        print('Before')\n        result = func(*args, **kwargs)\n        print('After')\n        return result\n    return wrapper\n\n@my_decorator\ndef say_hello():\n    print('Hello!')\n```",
    "actions": []
}

RARE CASES (ACTIONS NEEDED):

Need Real-Time Search:
{
    "response": "I need to search for current information since Python 3.12 is recent and I should provide the latest details.",
    "actions": [
        {"task": "search", "input": "Python 3.12 new features official documentation"}
    ]
}

Need File Access:
{
    "response": "I need to read the configuration file to provide accurate information.",
    "actions": [
        {"task": "read_file", "input": "config.json"}
    ]
}

REMEMBER:
- Default to actions: [] - solve tasks yourself!
- Actions have computational cost - use sparingly
- You're capable of math, coding, analysis, reasoning - do it directly!
- Only use actions for external data you can't access
- Maximum 1-2 actions, prefer 0"""

        if playbook_context:
            system_prompt += f"\n\nUSER PREFERENCES:\n{playbook_context}\n\nFollow these preferences in your response."
        
        # Build the task prompt
        task_prompt = f"""Task: {task}
Input: {full_input}

Analyze this task and respond in JSON format with your response and any needed actions."""
        
        # Generate response
        logger.info("Asking LLM to analyze task and generate plan...")
        ai_response = await generate_response(
            prompt=task_prompt,
            system_prompt=system_prompt,
            conversation_history=[],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse and validate JSON response
        parsed_response = _validate_and_fix_json_response(ai_response, logger)
        
        response_text = parsed_response.get("response", "")
        actions_data = parsed_response.get("actions", [])
        
        # If no actions, we're done
        if not actions_data or len(actions_data) == 0:
            logger.info(f"No more actions needed. Final response ready.")
            # NOTE: Playbook updates DISABLED for smaller quantized models
            # They struggle with complex JSON. Only human_feedback updates playbook.
            # await _update_playbook_from_interaction(
            #     cid=cid,
            #     task=task,
            #     input_data=input_data,
            #     response=response_text,
            #     context=context
            # )
            return response_text
        
        # Execute each action
        logger.info(f"Executing {len(actions_data)} actions...")
        for action_idx, action_data in enumerate(actions_data):
            if not isinstance(action_data, dict) or "task" not in action_data or "input" not in action_data:
                logger.warning(f"Invalid action format: {action_data}")
                continue
            
            action_task = action_data["task"]
            action_input = action_data["input"]
            
            # Convert input to string if needed
            if not isinstance(action_input, str):
                import json
                action_input = json.dumps(action_input)
            
            logger.info(f"Executing action {action_idx + 1}: {action_task}")
            
            # Execute the action and get observation
            observation = await _execute_action(
                action_task=action_task,
                action_input=action_input,
                cid=cid,
                playbook_context=playbook_context,
                context=context,
                depth=depth + 1
            )
            
            observations.append({
                "action_index": action_idx,
                "task": action_task,
                "input": action_input,
                "observation": observation
            })
    
    # Max iterations reached - return best response with observations
    final_prompt = f"""Task: {task}
Input: {input_data}

Actions executed and their results:
{_format_observations(observations)}

Based on all these observations, provide a comprehensive final answer."""

    final_response = await generate_response(
        prompt=final_prompt,
        system_prompt="Synthesize a final answer based on the observations.",
        conversation_history=[],
        temperature=0.7
    )
    
    return final_response


async def _execute_action(
    action_task: str,
    action_input: str,
    cid: str,
    playbook_context: str,
    context,
    depth: int
) -> str:
    """
    Execute a single action. Can be an external service or a recursive subtask.
    
    Returns the observation/result from executing the action.
    """
    # Check if this is an external service action
    external_services = {
        "search": "Web search service",
        "web_search": "Web search service",
        "google_search": "Web search service",
        "api_call": "External API service",
        "read_file": "File system service",
        "write_file": "File system service",
        "execute_code": "Code execution service",
        "run_python": "Python execution service",
        "run_javascript": "JavaScript execution service",
        "database_query": "Database service",
        "scrape_webpage": "Web scraping service",
        "send_email": "Email service",
        "http_request": "HTTP service"
    }
    
    # Normalize action task name
    action_task_lower = action_task.lower().replace("_", "").replace("-", "")
    
    # Check if it's an external service
    for service_key, service_name in external_services.items():
        if service_key.lower().replace("_", "") in action_task_lower:
            logger.info(f"Action '{action_task}' identified as external service: {service_name}")
            return f"[{service_name} available but not implemented in this demo. In production, this would execute: {action_task} with input: {action_input[:100]}...]"
    
    # Otherwise, treat as a subtask and execute recursively using LLM
    logger.info(f"Action '{action_task}' treated as subtask - executing recursively")
    
    try:
        result = await _execute_task_with_actions(
            cid=cid,
            task=action_task,
            input_data=action_input,
            playbook_context=playbook_context,
            context=context,
            max_iterations=2,  # Fewer iterations for subtasks
            depth=depth
        )
        return result
    except Exception as e:
        logger.error(f"Error executing subtask '{action_task}': {str(e)}")
        return f"Error executing subtask: {str(e)}"




def _format_observations(observations: List[Dict[str, str]]) -> str:
    """Format observations into readable text for LLM."""
    formatted = []
    
    for obs in observations:
        action_idx = obs.get("action_index", 0)
        task = obs.get("task", "unknown")
        input_data = obs.get("input", "")
        observation = obs.get("observation", "")
        
        formatted.append(f"Action {action_idx + 1}: {task}\nInput: {input_data}\nResult: {observation}")
    
    return "\n\n".join(formatted)


def _validate_and_fix_json_response(ai_response: str, logger) -> dict:
    """
    Validate and attempt to fix JSON response from LLM.
    
    Returns:
        Parsed JSON dict or raises JSONDecodeError
    """
    import json
    import re
    
    # Try direct JSON parsing first
    try:
        return json.loads(ai_response)
    except json.JSONDecodeError as e:
        logger.warning(f"Direct JSON parse failed: {e}. Attempting to extract JSON...")
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find any JSON object in the text
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', ai_response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Last resort: try to create a valid JSON with the response as text
    logger.warning("Creating fallback JSON structure with raw response")
    return {
        "response": ai_response.strip(),
        "actions": []
    }


async def _update_playbook_from_interaction(
    cid: str,
    task: str,
    input_data: str,
    response: str,
    context
) -> None:
    """
    Analyze the interaction and update playbook if user preferences are detected.
    Only runs if response is substantial (saves tokens).
    """
    try:
        # Skip if response is too short (likely no preferences)
        if len(response) < 50:
            logger.info("Response too short, skipping preference detection")
            return
        
        # Skip common non-preference tasks
        skip_keywords = ["what is", "explain", "how to", "calculate", "search", "find"]
        if any(keyword in task.lower() for keyword in skip_keywords):
            logger.info("Task type unlikely to contain preferences, skipping detection")
            return
        
        # Get current playbook state
        playbook_summary = context.playbook.to_context_string() or "No preferences yet."
        
        # Compact detection prompt
        detection_prompt = f"""Analyze if this interaction reveals USER PREFERENCES to store.

Playbook: {playbook_summary}

Task: {task}
Input: {input_data}
Response: {response}

Look for: explicit preferences, communication style, format preferences, domain interests.

JSON output:
{{"has_preferences": true/false, "reasoning": "brief explanation", "actions": [{{"action": "insert/update/delete", "node_id": "unique_id", "content": "preference text", "category": "style/format/tone/domain (optional)", "reason": "why this action"}}]}}

Rules: Only clear, actionable preferences. Avoid generic info. Update if contradicts existing."""

        # Generate actions using LLM with JSON mode
        logger.info(f"Analyzing interaction for preferences (cid={cid})...")
        ai_response = await generate_response(
            prompt=detection_prompt,
            system_prompt="Preference detection system. Output JSON only.",
            conversation_history=[],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        import json
        detection_data = json.loads(ai_response)
        has_preferences = detection_data.get("has_preferences", False)
        reasoning = detection_data.get("reasoning", "")
        actions_list = detection_data.get("actions", [])
        
        logger.info(f"Preference detection: has_preferences={has_preferences}, reasoning={reasoning}")
        
        if not has_preferences or len(actions_list) == 0:
            logger.info("No preferences detected in this interaction")
            return
        
        # Convert to PlaybookAction objects
        actions = [PlaybookAction(**action_dict) for action_dict in actions_list]
        
        # Apply actions to playbook
        results = context.playbook.apply_actions(actions)
        context.last_updated = datetime.utcnow()
        
        # Count successes
        successful_actions = [r for r in results if r.get("success")]
        logger.info(f"Updated playbook: {len(successful_actions)}/{len(results)} actions applied successfully")
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse preference detection JSON: {str(e)}")
    except Exception as e:
        logger.warning(f"Error updating playbook from interaction: {str(e)}")
        # Don't raise - playbook update is optional, shouldn't break the main flow


async def _update_playbook_from_feedback(
    cid: str,
    task: str,
    feedback_text: str,
    context
) -> None:
    """Analyze feedback patterns and update playbook if quality preferences detected."""
    try:
        playbook_summary = context.playbook.to_context_string() or "No prefs."
        
        detection_prompt = f"""Does this feedback reveal quality/style preferences?

Playbook: {playbook_summary}
Task: {task}
Feedback: {feedback_text}

JSON: {{"has_preferences": true/false, "reasoning": "brief", "actions": [...]}}"""

        ai_response = await generate_response(
            prompt=detection_prompt,
            system_prompt="You are a preference detection system that outputs structured JSON.",
            conversation_history=[],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        detection_data = json.loads(ai_response)
        
        if detection_data.get("has_preferences", False):
            actions = [PlaybookAction(**a) for a in detection_data.get("actions", [])]
            results = context.playbook.apply_actions(actions)
            context.last_updated = datetime.utcnow()
            logger.info(f"Updated playbook from feedback: {len(results)} actions applied")
            
    except Exception as e:
        logger.warning(f"Error updating playbook from feedback: {str(e)}")


async def _update_playbook_from_refinement(
    cid: str,
    task: str,
    original_output: str,
    refined_output: str,
    feedbacks: List[FeedbackItem],
    context
) -> None:
    """Analyze refinement patterns and update playbook."""
    try:
        playbook_summary = context.playbook.to_context_string() or "No prefs."
        feedback_summary = "; ".join([f"{fb.problem}→{fb.suggestion}" for fb in feedbacks])
        
        detection_prompt = f"""Does refinement show preferences?

Playbook: {playbook_summary}
Task: {task}
Changes: {feedback_summary}
Before: {original_output[:100]}...
After: {refined_output[:100]}...

JSON: {{"has_preferences": true/false, "reasoning": "brief", "actions": [...]}}"""

        ai_response = await generate_response(
            prompt=detection_prompt,
            system_prompt="Preference detection system. Output JSON only.",
            conversation_history=[],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        import json
        detection_data = json.loads(ai_response)
        
        if detection_data.get("has_preferences", False):
            actions = [PlaybookAction(**a) for a in detection_data.get("actions", [])]
            results = context.playbook.apply_actions(actions)
            context.last_updated = datetime.utcnow()
            logger.info(f"Updated playbook from refinement: {len(results)} actions applied")
            
    except Exception as e:
        logger.warning(f"Error updating playbook from refinement: {str(e)}")


@app.post("/feedback", response_model=FeedbackResponse, dependencies=[Depends(verify_api_key)])
async def feedback(request: FeedbackRequest):
    """
    Analyze an output and provide structured feedback.
    
    This endpoint reviews the output and suggests improvements.
    """
    try:
        logger.info(f"Feedback request for cid={request.cid}, task={request.task}")
        
        # Get conversation context
        context = conversation_manager.get_or_create(request.cid)
        
        # Build feedback prompt
        feedback_prompt = f"""Analyze output and provide 2-3 improvements.

Task: {request.task}
Input: {request.input}
Output: {request.output}

List problem-suggestion pairs."""

        # Generate feedback using playbook context only
        playbook_context = context.get_playbook_context()
        system_prompt = "AI assistant providing constructive feedback."
        if playbook_context:
            system_prompt += f"\n\n{playbook_context}\n\nConsider user preferences."
        
        feedback_text = await generate_response(
            prompt=feedback_prompt,
            system_prompt=system_prompt,
            conversation_history=[]  # No conversation history, only playbook
        )
        
        # NOTE: Playbook updates are DISABLED for smaller quantized models
        # They struggle with complex JSON generation. Only human_feedback endpoint
        # updates the playbook, as it uses simpler prompts.
        # 
        # await _update_playbook_from_feedback(
        #     cid=request.cid,
        #     task=request.task,
        #     feedback_text=feedback_text,
        #     context=context
        # )
        
        # Parse feedback into structured format
        # Simple parsing - in production, you might want more sophisticated parsing
        feedbacks = []
        lines = feedback_text.split('\n')
        current_problem = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for problem indicators
            if any(indicator in line.lower() for indicator in ['problem:', 'issue:', 'weakness:']):
                current_problem = line.split(':', 1)[1].strip() if ':' in line else line
            elif any(indicator in line.lower() for indicator in ['suggestion:', 'improvement:', 'recommendation:']):
                suggestion = line.split(':', 1)[1].strip() if ':' in line else line
                if current_problem:
                    feedbacks.append(FeedbackItem(
                        problem=current_problem,
                        suggestion=suggestion
                    ))
                    current_problem = None
            elif line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                # Bullet points
                if not current_problem:
                    current_problem = line.lstrip('-•*123. ')
        
        # If parsing didn't work well, create generic feedback items
        if len(feedbacks) == 0:
            feedbacks = [
                FeedbackItem(
                    problem="The output could be more comprehensive",
                    suggestion="Add more details, examples, or explanations to make the output more useful"
                ),
                FeedbackItem(
                    problem="Consider the user's context and preferences",
                    suggestion="Tailor the response to better match the user's needs and communication style"
                )
            ]
        
        return FeedbackResponse(feedbacks=feedbacks)
        
    except Exception as e:
        logger.error(f"Error in feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refine", response_model=RefineResponse, dependencies=[Depends(verify_api_key)])
async def refine(request: RefineRequest):
    """
    Refine an output based on structured feedback.
    
    This endpoint improves the original response by addressing the provided feedback.
    """
    try:
        logger.info(f"Refine request for cid={request.cid}, task={request.task}")
        
        # Get conversation context
        context = conversation_manager.get_or_create(request.cid)
        
        # Build refine prompt
        feedback_text = "\n".join([
            f"- {fb.problem} → {fb.suggestion}"
            for fb in request.feedbacks
        ])
        
        refine_prompt = f"""Improve response based on feedback.

Task: {request.task}
Input: {request.input}

Previous: {request.output}

Feedback: {feedback_text}

Address all feedback while keeping good parts."""

        # Add playbook preferences if available
        playbook_context = context.get_playbook_context()
        if playbook_context:
            refine_prompt += f"\n\n{playbook_context}\n\nFollow these preferences."
        
        # Generate refined output using playbook only (no conversation history)
        refined_output = await generate_response(
            prompt=refine_prompt,
            conversation_history=[]  # No conversation history, only playbook
        )
        
        # NOTE: Playbook updates DISABLED for smaller quantized models
        # They struggle with complex JSON. Only human_feedback updates playbook.
        # await _update_playbook_from_refinement(
        #     cid=request.cid,
        #     task=request.task,
        #     original_output=request.output,
        #     refined_output=refined_output,
        #     feedbacks=request.feedbacks,
        #     context=context
        # )
        
        return RefineResponse(output=refined_output)
        
    except Exception as e:
        logger.error(f"Error in refine: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/human_feedback", response_model=HumanFeedbackResponse, dependencies=[Depends(verify_api_key)])
async def human_feedback(request: HumanFeedbackRequest):
    """
    Store human feedback by generating playbook actions with LLM.
    
    This endpoint asks the LLM to analyze the feedback and generate structured
    playbook actions (insert/update/delete nodes) instead of storing raw feedback.
    This avoids regenerating the entire playbook on each feedback submission.
    """
    try:
        logger.info(f"Human feedback for cid={request.cid}")
        
        # Get conversation context
        context = conversation_manager.get_or_create(request.cid)
        
        # Get current playbook state
        current_playbook = context.playbook.to_dict()
        playbook_summary = context.playbook.to_context_string() or "No preferences yet."
        
        # Build prompt for LLM to generate playbook actions
        action_generation_prompt = f"""Analyze feedback and generate playbook actions.

Current: {playbook_summary}

Feedback: {request.human_feedback}

Generate actions (insert/update/delete) with node_id, content, category, reason.

Rules:
- Contradicts existing → UPDATE
- New info → INSERT  
- Remove → DELETE
- Keep concise and actionable

JSON format:
{{
  "reasoning": "what changes and why",
  "actions": [
    {{
      "action": "insert|update|delete",
      "node_id": "id",
      "content": "text (insert/update only)",
      "category": "optional",
      "reason": "why"
    }}
  ]
}}"""

        # Generate actions using LLM with JSON mode
        logger.info("Asking LLM to generate playbook actions...")
        ai_response = await generate_response(
            prompt=action_generation_prompt,
            system_prompt="Preference management system. Output JSON only.",
            conversation_history=[],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # Parse JSON response
        import json
        try:
            actions_data = json.loads(ai_response)
            reasoning = actions_data.get("reasoning", "")
            actions_list = actions_data.get("actions", [])
            
            # Convert to PlaybookAction objects
            actions = [PlaybookAction(**action_dict) for action_dict in actions_list]
            
            logger.info(f"LLM generated {len(actions)} playbook actions")
            logger.info(f"Reasoning: {reasoning}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM actions JSON: {ai_response}, error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse LLM response as JSON: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error processing LLM actions: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error processing playbook actions: {str(e)}"
            )
        
        # Apply actions to playbook
        results = context.playbook.apply_actions(actions)
        context.last_updated = datetime.utcnow()
        
        # Count successes
        successful_actions = [r for r in results if r.get("success")]
        failed_actions = [r for r in results if not r.get("success")]
        
        logger.info(f"Applied {len(successful_actions)}/{len(results)} playbook actions successfully")
        if failed_actions:
            logger.warning(f"Failed actions: {failed_actions}")
        
        # Don't save to conversation history - playbook is the source of truth
        # All user preferences are now stored in the playbook nodes
        
        return HumanFeedbackResponse(
            status="success",
            message=f"Processed feedback: {len(successful_actions)} actions applied successfully, {len(failed_actions)} failed. {reasoning}",
            actions_applied=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in human_feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations", dependencies=[Depends(verify_api_key)])
async def get_conversations():
    """
    Debug endpoint to view conversation statistics.
    
    Returns information about active conversations and their playbooks.
    Note: Conversation history is not stored, only playbook preferences.
    """
    conversations_info = {}
    for cid, context in conversation_manager.conversations.items():
        conversations_info[cid] = {
            "playbook_nodes": len(context.playbook.nodes),
            "playbook_categories": list(set(node.category for node in context.playbook.nodes.values() if node.category)),
            "last_updated": context.last_updated.isoformat()
        }
    
    return {
        "active_conversations": len(conversation_manager.conversations),
        "max_conversations": conversation_manager.MAX_CONVERSATIONS,
        "conversations": conversations_info,
        "note": "Message history is not stored. All context is in playbook preferences."
    }


@app.get("/conversations/{cid}", dependencies=[Depends(verify_api_key)])
async def get_conversation_detail(cid: str):
    """
    Get detailed information about a specific conversation.
    
    Returns playbook preferences (conversation history is not stored).
    """
    context = conversation_manager.get(cid)
    
    if not context:
        raise HTTPException(status_code=404, detail=f"Conversation {cid} not found")
    
    return {
        "cid": cid,
        "playbook": context.playbook.to_dict(),
        "playbook_stats": context.playbook.get_stats(),
        "playbook_summary": context.get_playbook_context(),
        "created_at": context.created_at.isoformat(),
        "last_updated": context.last_updated.isoformat(),
        "note": "Conversation history is not stored. All insights are in the playbook."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.miner_port)
