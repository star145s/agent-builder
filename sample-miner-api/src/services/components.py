"""Component implementations for the unified API interface.

All components follow the same pattern:
- Input: ComponentInput (task, input list, previous_outputs)
- Output: ComponentOutput (task, output, component)
"""

import json
import logging
from typing import List

from src.models.models import (
    ComponentInput, 
    ComponentOutput, 
    ComponentOutputData,
    InputItem, 
    PreviousOutput
)
from src.services.llm_client import generate_response, get_llm_client
from src.core.conversation import ConversationContext
from src.services.playbook_service import PlaybookService

logger = logging.getLogger(__name__)

# Initialize playbook service (will be set up when first used)
_playbook_service = None


def get_playbook_service() -> PlaybookService:
    """Get or create playbook service instance."""
    global _playbook_service
    if _playbook_service is None:
        llm_client = get_llm_client()
        _playbook_service = PlaybookService(llm_client)
    return _playbook_service


async def get_context_additions(
    component_input: ComponentInput,
    context: ConversationContext,
    component_name: str
) -> tuple[list, str]:
    """
    Get conversation history and playbook context based on component input settings.
    
    Args:
        component_input: Component input with settings
        context: Conversation context
        component_name: Name of the component (for logging)
        
    Returns:
        Tuple of (conversation_history, playbook_context_string)
    """
    # Get conversation history if enabled
    conversation_history = []
    if component_input.use_conversation_history:
        conversation_history = context.get_recent_messages(count=5)
        logger.info(f"[{component_name}] Using conversation history: {len(conversation_history)} messages")
    else:
        logger.info(f"[{component_name}] Conversation history disabled")
    
    # Get playbook context if enabled
    playbook_context = ""
    if component_input.use_playbook:
        try:
            playbook_service = get_playbook_service()
            playbook_entries = await playbook_service.get_playbook(component_input.cid)
            if playbook_entries:
                playbook_context = "\n\n" + playbook_service.format_playbook_context(playbook_entries)
                logger.info(f"[{component_name}] Using playbook: {len(playbook_entries)} entries")
        except Exception as e:
            logger.warning(f"[{component_name}] Failed to load playbook: {e}")
            playbook_context = ""  # Ensure empty string on failure
    else:
        logger.info(f"[{component_name}] Playbook disabled")
    
    return conversation_history, playbook_context





async def component_complete(
    component_input: ComponentInput,
    context: ConversationContext
) -> ComponentOutput:
    """
    Complete component: Process tasks with optional conversation history and playbook.
    
    Args:
        component_input: Unified component input
        context: Conversation context with history
        
    Returns:
        ComponentOutput with the completed task
    """
    logger.info(f"[complete] Processing task: {component_input.task}")
    
    # Build input text from all input items
    input_text_parts = []
    for idx, item in enumerate(component_input.input, 1):
        input_text_parts.append(f"Query {idx}: {item.user_query}")
    
    input_text = "\n\n".join(input_text_parts)
    
    # Build previous outputs context - LLM will read everything and decide intelligently
    previous_context = ""
    if component_input.previous_outputs:
        previous_context = "\n\nPrevious component outputs:\n"
        for prev in component_input.previous_outputs:
            # Show the complete output with immediate_response and notebook
            previous_context += f"\n[{prev.component}] {prev.task}:\n"
            previous_context += f"  Response: {prev.output.immediate_response}\n"
            if prev.output.notebook and prev.output.notebook != "no update":
                previous_context += f"  Notebook: {prev.output.notebook}\n"
    
    # Get conversation history and playbook context
    conversation_history, playbook_context = await get_context_additions(
        component_input, context, "complete"
    )
    
    # Build system prompt with Canvas-style instructions
    system_prompt = """You are an intelligent AI assistant that helps users complete tasks.

IMPORTANT: Respond in JSON format with two fields:
{
  "immediate_response": "Your natural language explanation of what you did or your answer",
  "notebook": "Updated notebook content OR 'no update'"
}

Guidelines for notebook field:
- If task is conversational only: Return "no update"
- If there's ONE notebook and no changes needed: Return "no update"
- If there's ONE notebook and changes needed: Return the updated version
- If there are MULTIPLE notebooks: You MUST create new content (combine/choose/merge) - NEVER "no update"
- If creating new notebook: Return the full content
- Always provide valid JSON"""
    
    if playbook_context:
        system_prompt += f"\n\nUser preferences and context:\n{playbook_context}"
    
    # Build task prompt
    task_prompt = f"""Task: {component_input.task}

Input:
{input_text}
{previous_context}

Complete this task and respond in JSON format."""
    
    # Generate response with optional conversation history
    response = await generate_response(
        prompt=task_prompt,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        temperature=0.7
    )
    
    # Parse JSON response
    try:
        # Try to extract JSON from response (handle markdown code blocks)
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        immediate_response = result.get("immediate_response", response)
        notebook_output = result.get("notebook", "no update")
        
        # Ensure notebook is a string (convert dict/object to JSON string if needed)
        if isinstance(notebook_output, dict):
            logger.warning(f"[complete] Notebook returned as dict, converting to JSON string")
            notebook_output = json.dumps(notebook_output, indent=2)
        elif not isinstance(notebook_output, str):
            logger.warning(f"[complete] Notebook is not a string (type: {type(notebook_output)}), converting")
            notebook_output = str(notebook_output)
            
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning(f"[complete] Failed to parse JSON response: {e}. Using raw response.")
        immediate_response = response
        notebook_output = "no update"
    
    # Resolve "no update" for notebook - return previous notebook if exists
    if notebook_output == "no update" and component_input.previous_outputs:
        resolved = False
        for prev in component_input.previous_outputs:
            if prev.output.notebook and prev.output.notebook != "no update":
                notebook_output = prev.output.notebook
                logger.info(f"[complete] Resolved 'no update' to previous notebook from [{prev.component}]")
                resolved = True
                break
        
        if not resolved:
            logger.info(f"[complete] No previous notebook found to resolve - keeping 'no update'")
    
    # Store in conversation history
    context.add_user_message(f"Task: {component_input.task}\n{input_text}")
    context.add_assistant_message(immediate_response)
    
    return ComponentOutput(
        cid=component_input.cid,
        task=component_input.task,
        input=component_input.input,
        output=ComponentOutputData(
            immediate_response=immediate_response,
            notebook=notebook_output  # Resolved: new content, previous notebook, or "no update"
        ),
        component="complete"
    )


async def component_refine(
    component_input: ComponentInput,
    context: ConversationContext
) -> ComponentOutput:
    """
    Refine component: Improve outputs with optional conversation history and playbook.
    
    Args:
        component_input: Unified component input with previous outputs to refine
        context: Conversation context
        
    Returns:
        ComponentOutput with refined output
    """
    logger.info(f"[refine] Processing task: {component_input.task}")
    
    # Build input text
    input_text_parts = []
    for idx, item in enumerate(component_input.input, 1):
        input_text_parts.append(f"Query {idx}: {item.user_query}")
    
    input_text = "\n\n".join(input_text_parts)
    
    # Build previous outputs context - LLM will read everything and decide intelligently
    previous_outputs_text = ""
    if component_input.previous_outputs:
        previous_outputs_text = "\n\nPrevious outputs to refine:\n"
        for prev in component_input.previous_outputs:
            previous_outputs_text += f"\n[{prev.component}] {prev.task}:\n"
            previous_outputs_text += f"  Response: {prev.output.immediate_response}\n"
            if prev.output.notebook and prev.output.notebook != "no update":
                previous_outputs_text += f"  Notebook: {prev.output.notebook}\n"
    
    # Get conversation history and playbook context
    conversation_history, playbook_context = await get_context_additions(
        component_input, context, "refine"
    )
    
    # Build system prompt with Canvas-style instructions
    system_prompt = """You are an AI assistant that refines and improves outputs.

IMPORTANT: Respond in JSON format:
{
  "immediate_response": "Explanation of what you refined and why",
  "notebook": "The refined/improved content OR 'no update'"
}

Guidelines for notebook field:
- If providing feedback only: Set notebook to "no update"
- If there's ONE notebook and no improvements needed: Set to "no update"
- If there's ONE notebook and improvements needed: Write the improved version
- If there are MULTIPLE notebooks: You MUST create new content (refine one, combine, or merge) - NEVER "no update"
- Always provide valid JSON"""
    
    if playbook_context:
        system_prompt += f"\n\nUser preferences:\n{playbook_context}"
    
    # Build refine prompt
    refine_prompt = f"""Task: {component_input.task}

Original Input:
{input_text}
{previous_outputs_text}

Refine and improve the outputs. Respond in JSON format."""
    
    # Generate response
    response = await generate_response(
        prompt=refine_prompt,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        temperature=0.7
    )
    
    # Parse JSON response
    try:
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        immediate_response = result.get("immediate_response", response)
        notebook_output = result.get("notebook", "no update")
        
        # Ensure notebook is a string (convert dict/object to JSON string if needed)
        if isinstance(notebook_output, dict):
            logger.warning(f"[refine] Notebook returned as dict, converting to JSON string")
            notebook_output = json.dumps(notebook_output, indent=2)
        elif not isinstance(notebook_output, str):
            logger.warning(f"[refine] Notebook is not a string (type: {type(notebook_output)}), converting")
            notebook_output = str(notebook_output)
            
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning(f"[refine] Failed to parse JSON response: {e}. Using raw response.")
        immediate_response = response
        notebook_output = "no update"
    
    # Resolve "no update" for notebook - return previous notebook if exists
    if notebook_output == "no update" and component_input.previous_outputs:
        resolved = False
        for prev in component_input.previous_outputs:
            if prev.output.notebook and prev.output.notebook != "no update":
                notebook_output = prev.output.notebook
                logger.info(f"[refine] Resolved 'no update' to previous notebook from [{prev.component}]")
                resolved = True
                break
        
        if not resolved:
            logger.info(f"[refine] No previous notebook found to resolve - keeping 'no update'")
    
    # Store in conversation history
    context.add_user_message(f"Refine task: {component_input.task}")
    context.add_assistant_message(immediate_response)
    
    return ComponentOutput(
        cid=component_input.cid,
        task=component_input.task,
        input=component_input.input,
        output=ComponentOutputData(
            immediate_response=immediate_response,
            notebook=notebook_output  # Resolved: refined content, previous notebook, or "no update"
        ),
        component="refine"
    )


async def component_feedback(
    component_input: ComponentInput,
    context: ConversationContext
) -> ComponentOutput:
    """
    Feedback component: Analyze outputs and provide structured feedback.
    
    Args:
        component_input: Unified component input with outputs to analyze
        context: Conversation context
        
    Returns:
        ComponentOutput with structured feedback
    """
    logger.info(f"[feedback] Processing task: {component_input.task}")
    
    # Build previous outputs to analyze
    outputs_to_analyze = ""
    if component_input.previous_outputs:
        outputs_to_analyze = "\n\nOutputs to analyze:\n"
        for prev in component_input.previous_outputs:
            # Access Pydantic object attributes
            outputs_to_analyze += f"\n[{prev.component}] {prev.task}:\n"
            outputs_to_analyze += f"  Response: {prev.output.immediate_response}\n"
            if prev.output.notebook and prev.output.notebook != "no update":
                outputs_to_analyze += f"  Notebook: {prev.output.notebook}\n"
    
    # Get conversation history and playbook context
    conversation_history, playbook_context = await get_context_additions(
        component_input, context, "feedback"
    )
    
    # Build system prompt
    system_prompt = "You are an AI assistant that provides constructive feedback."
    if playbook_context:
        system_prompt += f"\n{playbook_context}"
    
    # Build feedback prompt
    feedback_prompt = f"""Task: {component_input.task}
{outputs_to_analyze}

Analyze the outputs and provide structured feedback:

For each output, identify:
1. Strengths (what works well)
2. Weaknesses (what could be improved)
3. Specific suggestions for improvement

Format your feedback clearly with sections."""
    
    # Generate feedback
    response = await generate_response(
        prompt=feedback_prompt,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        temperature=0.7
    )
    
    # Store in conversation history
    context.add_user_message(f"Feedback request: {component_input.task}")
    context.add_assistant_message(response)
    
    # Feedback is conversational - no notebook editing
    return ComponentOutput(
        cid=component_input.cid,
        task=component_input.task,
        input=component_input.input,
        output=ComponentOutputData(
            immediate_response=response,
            notebook="no update"
        ),
        component="feedback"
    )


async def component_human_feedback(
    component_input: ComponentInput,
    context: ConversationContext
) -> ComponentOutput:
    """
    Human feedback component: Process and extract structured insights to playbook.
    
    Uses LLM to extract actionable insights from human feedback and stores them
    in a structured playbook (knowledge base) with operations (insert/update/delete).
    
    Inspired by: https://github.com/kayba-ai/agentic-context-engine
    
    Args:
        component_input: Unified component input with human feedback
        context: Conversation context
        
    Returns:
        ComponentOutput with summary of extracted insights
    """
    logger.info(f"[human_feedback] Processing task: {component_input.task}")
    
    # Extract human feedback from input
    feedback_text_parts = []
    for item in component_input.input:
        if item.user_query:
            feedback_text_parts.append(item.user_query)
    
    feedback_text = "\n".join(feedback_text_parts)
    

    
    if not feedback_text.strip():
        return ComponentOutput(
            cid=component_input.cid,
            task=component_input.task,
            input=component_input.input,
            output=ComponentOutputData(
                immediate_response="No feedback text provided.",
                notebook="no update"
            ),
            component="human_feedback"
        )
    
    logger.info(f"[human_feedback] Received feedback: {feedback_text[:100]}...")
    
    try:
        # Get playbook service
        playbook_service = get_playbook_service()
        
        # Get conversation context for better extraction
        conversation_context = "\n".join([
            f"{msg['role']}: {msg['content'][:100]}..."
            for msg in context.get_messages()[-5:]  # Last 5 messages
        ])
        
        # Extract insights using LLM
        insights = await playbook_service.extract_insights(
            feedback=feedback_text,
            cid=component_input.cid,
            context=conversation_context
        )
        
        # Apply operations to playbook
        entries = await playbook_service.apply_operations(
            insights=insights,
            cid=component_input.cid,
            source_feedback=feedback_text
        )
        
        # Format response
        if insights:
            response_parts = [
                "✅ Thank you for your feedback! I've analyzed it and extracted the following insights:\n"
            ]
            
            for idx, insight in enumerate(insights, 1):
                operation_emoji = {
                    "insert": "➕",
                    "update": "🔄",
                    "delete": "❌"
                }.get(insight["operation"], "•")
                
                response_parts.append(
                    f"{operation_emoji} **{insight['insight_type'].title()}** ({insight['operation']})\n"
                    f"   Key: `{insight['key']}`\n"
                    f"   Value: {insight['value']}\n"
                    f"   Confidence: {insight.get('confidence_score', 0.8):.0%}"
                )
                if insight.get('tags'):
                    response_parts.append(f"   Tags: {', '.join(insight['tags'])}")
                response_parts.append("")
            
            response_parts.append(
                f"\n📚 Your playbook now has {len(entries)} active entries. "
                "I'll use this knowledge in our future conversations!"
            )
            
            message = "\n".join(response_parts)
        else:
            message = (
                "Thank you for your feedback. However, I couldn't extract any "
                "actionable insights to add to your playbook. Your feedback has "
                "been stored in the conversation history for context."
            )
        
        logger.info(f"[human_feedback] Extracted {len(insights)} insights, created/updated {len(entries)} entries")
        
        # Store in conversation history
        context.add_user_message(f"User feedback: {feedback_text}")
        context.add_assistant_message(message)
        
        # Create JSON summary of insights for notebook
        notebook_data = {
            "feedback": feedback_text,
            "insights_extracted": len(insights),
            "entries_modified": len(entries),
            "insights": insights
        }
        
        notebook_json = json.dumps(notebook_data, indent=2)
        
        return ComponentOutput(
            cid=component_input.cid,
            task=component_input.task,
            input=component_input.input,
            output=ComponentOutputData(
                immediate_response=message,
                notebook=notebook_json  # Structured insights data
            ),
            component="human_feedback"
        )
        
    except Exception as e:
        logger.error(f"[human_feedback] Error processing feedback: {e}", exc_info=True)
        
        # Fallback to simple storage
        message = (
            f"Thank you for your feedback. I've noted it for future reference:\n\n"
            f"{feedback_text}\n\n"
            f"(Note: Advanced insight extraction encountered an error, but your "
            f"feedback is stored in conversation history)"
        )
        
        context.add_user_message(f"User feedback: {feedback_text}")
        context.add_assistant_message(message)
        
        return ComponentOutput(
            cid=component_input.cid,
            task=component_input.task,
            input=component_input.input,
            output=ComponentOutputData(
                immediate_response=message,
                notebook="no update"  # Error case
            ),
            component="human_feedback"
        )


async def component_internet_search(
    component_input: ComponentInput,
    context: ConversationContext
) -> ComponentOutput:
    """
    Internet search component: Search the internet for information.
    
    NOTE: This is a template implementation. Miners should implement actual
    internet search functionality using services like:
    - Google Custom Search API
    - Bing Search API
    - DuckDuckGo API
    - SerpAPI
    - Or any other search service
    
    Args:
        component_input: Unified component input with search queries
        context: Conversation context
        
    Returns:
        ComponentOutput with search results (currently returns "unavailable service")
    """
    logger.info(f"[internet_search] Processing task: {component_input.task}")
    
    # Extract search queries
    search_queries = []
    for item in component_input.input:
        search_queries.append(item.user_query)
    
    # Template response - miners should replace this with actual implementation
    response = f"""Internet Search Service: UNAVAILABLE (Template)

This is a template implementation. Miners should implement actual internet search.

Queries received:
{chr(10).join(f"- {q}" for q in search_queries)}

IMPLEMENTATION NOTES FOR MINERS:
==================================
To implement internet search, you can use:

1. Google Custom Search API:
   - Create API key at: https://console.cloud.google.com/
   - Use googleapis Python library
   - Example: google.search(query, num_results=10)

2. Bing Search API:
   - Get API key from Azure Cognitive Services
   - Use requests library to call Bing API

3. DuckDuckGo API:
   - Free and no API key required
   - Use duckduckgo-search Python library
   - Example: from duckduckgo_search import DDGS

4. SerpAPI:
   - Multi-engine search API
   - Supports Google, Bing, Yahoo, etc.
   - Example: serpapi.search(query)

Implementation should:
- Parse search queries from component_input.input
- Execute searches using your chosen service
- Format results as structured text
- Return ComponentOutput with results
- Handle rate limiting and errors gracefully

Replace this function body with your actual search implementation."""
    
    # Store in conversation history
    context.add_user_message(f"Search: {', '.join(search_queries)}")
    context.add_assistant_message(response)
    

    
    # Internet search is conversational - no notebook editing
    return ComponentOutput(
        cid=component_input.cid,
        task=component_input.task,
        input=component_input.input,
        output=ComponentOutputData(
            immediate_response=response,
            notebook="no update"
        ),
        component="internet_search"
    )


async def component_summary(
    component_input: ComponentInput,
    context: ConversationContext
) -> ComponentOutput:
    """
    Summary component: Use LLM to summarize previous outputs.
    
    Args:
        component_input: Unified component input with outputs to summarize
        context: Conversation context
        
    Returns:
        ComponentOutput with summarized content
    """
    logger.info(f"[summary] Processing task: {component_input.task}")
    
    # Build content to summarize from previous outputs
    content_to_summarize = []
    if component_input.previous_outputs:
        for prev in component_input.previous_outputs:
            # Access Pydantic object attributes
            output_text = f"[{prev.component}] {prev.task}:\n"
            output_text += f"Response: {prev.output.immediate_response}\n"
            if prev.output.notebook and prev.output.notebook != "no update":
                output_text += f"Notebook: {prev.output.notebook}\n"
            content_to_summarize.append(output_text)
    

    
    if not content_to_summarize:
        return ComponentOutput(
            cid=component_input.cid,
            task=component_input.task,
            input=component_input.input,
            output=ComponentOutputData(
                immediate_response="No previous outputs to summarize.",
                notebook="no update"
            ),
            component="summary"
        )
    
    combined_content = "\n\n---\n\n".join(content_to_summarize)
    
    # Get conversation history and playbook context
    conversation_history, playbook_context = await get_context_additions(
        component_input, context, "summary"
    )
    
    # Build system prompt with Canvas-style instructions
    system_prompt = """You are an AI assistant that creates concise, comprehensive summaries.

IMPORTANT: Respond in JSON format with two fields:
{
  "immediate_response": "Your summary explanation",
  "notebook": "Summarized notebook content OR 'no update'"
}

Guidelines for notebook field:
- If there's NO notebook content in inputs: Return "no update"
- If there's ONE notebook to summarize: Return the summarized version
- If there are MULTIPLE notebooks: Create a combined summary
- Always provide valid JSON"""
    
    if playbook_context:
        system_prompt += f"\n\nUser preferences:\n{playbook_context}"
    
    # Build summary prompt
    summary_prompt = f"""Task: {component_input.task}

Content to summarize:
{combined_content}

Create a comprehensive summary that:
1. Captures the main points and key insights
2. Maintains important details
3. Removes redundancy
4. Organizes information logically

Respond in JSON format."""
    
    # Generate summary
    response = await generate_response(
        prompt=summary_prompt,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        temperature=0.5
    )
    
    # Parse JSON response
    try:
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        immediate_response = result.get("immediate_response", response)
        notebook_output = result.get("notebook", "no update")
        
        # Ensure notebook is a string
        if isinstance(notebook_output, dict):
            logger.warning(f"[summary] Notebook returned as dict, converting to JSON string")
            notebook_output = json.dumps(notebook_output, indent=2)
        elif not isinstance(notebook_output, str):
            logger.warning(f"[summary] Notebook is not a string (type: {type(notebook_output)}), converting")
            notebook_output = str(notebook_output)
            
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning(f"[summary] Failed to parse JSON response: {e}. Using raw response.")
        immediate_response = response
        notebook_output = "no update"
    
    # Resolve "no update" for notebook - return previous notebook if exists
    if notebook_output == "no update" and component_input.previous_outputs:
        resolved = False
        for prev in component_input.previous_outputs:
            if prev.output.notebook and prev.output.notebook != "no update":
                notebook_output = prev.output.notebook
                logger.info(f"[summary] Resolved 'no update' to previous notebook from [{prev.component}]")
                resolved = True
                break
        
        if not resolved:
            logger.info(f"[summary] No previous notebook found to resolve - keeping 'no update'")
    
    # Store in conversation history
    context.add_user_message(f"Summarize: {component_input.task}")
    context.add_assistant_message(immediate_response)
    
    return ComponentOutput(
        cid=component_input.cid,
        task=component_input.task,
        input=component_input.input,
        output=ComponentOutputData(
            immediate_response=immediate_response,
            notebook=notebook_output  # Resolved: summarized content, previous notebook, or "no update"
        ),
        component="summary"
    )


async def component_aggregate(
    component_input: ComponentInput,
    context: ConversationContext
) -> ComponentOutput:
    """
    Aggregate component: Perform majority voting on previous outputs.
    
    This component analyzes multiple previous outputs and identifies the most
    common or agreed-upon answer through majority voting logic.
    
    Args:
        component_input: Unified component input with outputs to aggregate
        context: Conversation context
        
    Returns:
        ComponentOutput with aggregated result
    """
    logger.info(f"[aggregate] Processing task: {component_input.task}")
    

    
    if not component_input.previous_outputs:
        return ComponentOutput(
            cid=component_input.cid,
            task=component_input.task,
            input=component_input.input,
            output=ComponentOutputData(
                immediate_response="No previous outputs to aggregate.",
                notebook="no update"
            ),
            component="aggregate"
        )
    
    # Build outputs for analysis
    outputs_text = []
    for idx, prev in enumerate(component_input.previous_outputs, 1):
        # Access Pydantic object attributes
        output_text = f"Output {idx} [{prev.component}]:\n"
        output_text += f"Response: {prev.output.immediate_response}\n"
        if prev.output.notebook and prev.output.notebook != "no update":
            output_text += f"Notebook: {prev.output.notebook}\n"
        outputs_text.append(output_text)
    
    combined_outputs = "\n\n---\n\n".join(outputs_text)
    
    # Get conversation history and playbook context
    conversation_history, playbook_context = await get_context_additions(
        component_input, context, "aggregate"
    )
    
    # Build system prompt with Canvas-style instructions
    system_prompt = """You are an AI assistant that aggregates multiple outputs using majority voting.

IMPORTANT: Respond in JSON format with two fields:
{
  "immediate_response": "Your explanation of the consensus and voting results",
  "notebook": "The aggregated/consensus notebook content OR 'no update'"
}

Guidelines for notebook field:
- If there's NO notebook content in inputs: Return "no update"
- If there's ONE notebook: Return it as-is (or "no update" if no changes)
- If there are MULTIPLE notebooks: Create aggregated version using majority voting
- Use majority voting: Choose the most common content or merge agreements
- Always provide valid JSON"""
    
    if playbook_context:
        system_prompt += f"\n\nUser preferences:\n{playbook_context}"
    
    # Build aggregate prompt
    aggregate_prompt = f"""Task: {component_input.task}

Multiple outputs to aggregate:
{combined_outputs}

Analyze these outputs and determine the consensus answer by:
1. Identifying common themes and agreements
2. Noting where outputs differ
3. Using majority voting logic to determine the most supported answer
4. Highlighting any important minority opinions

Respond in JSON format."""
    
    # Generate aggregate result
    response = await generate_response(
        prompt=aggregate_prompt,
        system_prompt=system_prompt,
        conversation_history=conversation_history,
        temperature=0.3
    )
    
    # Parse JSON response
    try:
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        immediate_response = result.get("immediate_response", response)
        notebook_output = result.get("notebook", "no update")
        
        # Ensure notebook is a string
        if isinstance(notebook_output, dict):
            logger.warning(f"[aggregate] Notebook returned as dict, converting to JSON string")
            notebook_output = json.dumps(notebook_output, indent=2)
        elif not isinstance(notebook_output, str):
            logger.warning(f"[aggregate] Notebook is not a string (type: {type(notebook_output)}), converting")
            notebook_output = str(notebook_output)
            
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning(f"[aggregate] Failed to parse JSON response: {e}. Using raw response.")
        immediate_response = response
        notebook_output = "no update"
    
    # Resolve "no update" for notebook - return previous notebook if exists
    if notebook_output == "no update" and component_input.previous_outputs:
        resolved = False
        for prev in component_input.previous_outputs:
            if prev.output.notebook and prev.output.notebook != "no update":
                notebook_output = prev.output.notebook
                logger.info(f"[aggregate] Resolved 'no update' to previous notebook from [{prev.component}]")
                resolved = True
                break
        
        if not resolved:
            logger.info(f"[aggregate] No previous notebook found to resolve - keeping 'no update'")
    
    # Store in conversation history
    context.add_user_message(f"Aggregate: {component_input.task}")
    context.add_assistant_message(immediate_response)
    
    return ComponentOutput(
        cid=component_input.cid,
        task=component_input.task,
        input=component_input.input,
        output=ComponentOutputData(
            immediate_response=immediate_response,
            notebook=notebook_output  # Resolved: aggregated content, previous notebook, or "no update"
        ),
        component="aggregate"
    )
