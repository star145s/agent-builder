#!/usr/bin/env python3
"""
Gradio Test UI for Sample Miner API
Test the unified component interface with conversation history
"""

import gradio as gr
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_KEY = os.getenv("API_KEY")

# Require API_KEY to be set
if not API_KEY:
    raise ValueError(
        "❌ API_KEY environment variable must be set!\n"
        "Set it in your .env file or export API_KEY=your-key\n"
        "Generate secure key: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )

def format_output_data(output_data):
    """Format output data (dict with 'immediate_response' and 'notebook') into readable text.
    
    Format:
    - output: {immediate_response: str, notebook: str}
    - Input only contains user_query (no notebook in input)
    - Output contains both natural response and notebook
    """
    if not output_data:
        return ""
    
    parts = []
    
    # Natural response
    immediate_response = output_data.get('immediate_response', '')
    if immediate_response:
        parts.append(f"**Response:**\n{immediate_response}")
    
    # Notebook (if provided and not "no update")
    notebook = output_data.get('notebook', '')
    if notebook and notebook.lower() != "no update":
        parts.append(f"\n**Notebook/Code:**\n```\n{notebook}\n```")
    
    return "\n\n".join(parts)

def test_complete(task: str, user_query: str, notebook: str, use_history: bool, use_playbook: bool, cid: str = "test-conversation"):
    """Test the /complete endpoint (unified interface)
    
    Format:
    - Input: Only contains user_query (notebook removed from input)
    - Output: Contains {immediate_response, notebook}
    - Previous outputs also use new format
    """
    try:
        # Build request - note: notebook param is now passed via previous_outputs if needed
        request_data = {
            "cid": cid,
            "task": task,
            "input": [
                {
                    "user_query": user_query
                }
            ],
            "previous_outputs": [],
            "use_conversation_history": use_history,
            "use_playbook": use_playbook
        }
        
        # If notebook content is provided, add it as a previous output (simulating a previous step)
        if notebook and notebook.strip():
            request_data["previous_outputs"].append({
                "task": "Previous code/document",
                "input": [{"user_query": "Context"}],
                "output": {
                    "immediate_response": "Here's the current code/document",
                    "notebook": notebook
                },
                "component": "complete"
            })
        
        response = requests.post(
            f"{API_BASE_URL}/complete",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json=request_data,
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            output_text = format_output_data(result.get("output", {}))
            return (
                output_text,
                result.get("component", ""),
                json.dumps(result, indent=2),
                "✅ Success"
            )
        elif response.status_code == 429:
            return "", "", "", "⚠️ Rate limit exceeded. Wait a moment and try again."
        else:
            return "", "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", "", f"❌ Exception: {str(e)}"

def test_refine(task: str, user_query: str, prev_output: str, use_history: bool, use_playbook: bool, cid: str = "test-conversation"):
    """Test the /refine endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/refine",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": task,
                "input": [{"user_query": user_query}],  # No notebook in input
                "previous_outputs": [
                    {
                        "task": "Previous task",
                        "input": [{"user_query": "Generate content"}],
                        "output": {  # NEW: output is dict with immediate_response and notebook
                            "immediate_response": "Previous response",
                            "notebook": prev_output
                        },
                        "component": "complete"
                    }
                ],
                "use_conversation_history": use_history,
                "use_playbook": use_playbook
            },
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            output_text = format_output_data(result.get("output", {}))
            return (
                output_text,
                json.dumps(result, indent=2),
                "✅ Success"
            )
        elif response.status_code == 429:
            return "", "", "⚠️ Rate limit exceeded. Wait a moment and try again."
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_feedback(task: str, prev_output: str, use_history: bool, use_playbook: bool, cid: str = "test-conversation"):
    """Test the /feedback endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/feedback",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": task,
                "input": [{"user_query": "Analyze this output"}],
                "previous_outputs": [
                    {
                        "task": task,
                        "input": [{"user_query": "Previous request"}],
                        "output": {
                            "immediate_response": "Previous response",
                            "notebook": prev_output
                        },
                        "component": "complete"
                    }
                ],
                "use_conversation_history": use_history,
                "use_playbook": use_playbook
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            output_text = format_output_data(result.get("output", {}))
            return (
                output_text,
                json.dumps(result, indent=2),
                "✅ Success"
            )
        elif response.status_code == 429:
            return "", "", "⚠️ Rate limit exceeded. Wait a moment and try again."
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_human_feedback(human_feedback: str, cid: str = "test-conversation"):
    """Test the /human_feedback endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/human_feedback",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": "Store user preference",
                "input": [{"user_query": human_feedback}],
                "previous_outputs": []
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            output_text = format_output_data(result.get("output", {}))
            return (
                output_text,
                json.dumps(result, indent=2),
                "✅ Success"
            )
        elif response.status_code == 429:
            return "", "", "⚠️ Rate limit exceeded. Wait a moment and try again."
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_summary(outputs_text: str, use_history: bool, use_playbook: bool, cid: str = "test-conversation"):
    """Test the /summary endpoint"""
    try:
        # Parse outputs (one per line)
        outputs = [line.strip() for line in outputs_text.split('\n') if line.strip()]
        previous_outputs = [
            {
                "task": f"Output {i+1}",
                "input": [{"user_query": f"Query {i+1}"}],
                "output": {
                    "immediate_response": output,
                    "notebook": "no update"
                },
                "component": "complete"
            }
            for i, output in enumerate(outputs)
        ]
        
        response = requests.post(
            f"{API_BASE_URL}/summary",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": "Summarize these outputs",
                "input": [{"user_query": "Create a comprehensive summary"}],
                "previous_outputs": previous_outputs,
                "use_conversation_history": use_history,
                "use_playbook": use_playbook
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            output_text = format_output_data(result.get("output", {}))
            return (
                output_text,
                json.dumps(result, indent=2),
                "✅ Success"
            )
        elif response.status_code == 429:
            return "", "", "⚠️ Rate limit exceeded. Wait a moment and try again."
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_aggregate(outputs_text: str, use_history: bool, use_playbook: bool, cid: str = "test-conversation"):
    """Test the /aggregate endpoint"""
    try:
        # Parse outputs (one per line)
        outputs = [line.strip() for line in outputs_text.split('\n') if line.strip()]
        previous_outputs = [
            {
                "task": f"Output {i+1}",
                "input": [{"user_query": f"Query {i+1}"}],
                "output": {
                    "immediate_response": output,
                    "notebook": "no update"
                },
                "component": "complete"
            }
            for i, output in enumerate(outputs)
        ]
        
        response = requests.post(
            f"{API_BASE_URL}/aggregate",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": "Find consensus answer",
                "input": [{"user_query": "Determine majority voting result"}],
                "previous_outputs": previous_outputs,
                "use_conversation_history": use_history,
                "use_playbook": use_playbook
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            output_text = format_output_data(result.get("output", {}))
            return (
                output_text,
                json.dumps(result, indent=2),
                "✅ Success"
            )
        elif response.status_code == 429:
            return "", "", "⚠️ Rate limit exceeded. Wait a moment and try again."
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_internet_search(query: str, cid: str = "test-conversation"):
    """Test the /internet_search endpoint (template)"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/internet_search",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": "Search the internet",
                "input": [{"user_query": query}],
                "previous_outputs": []
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            output_text = format_output_data(result.get("output", {}))
            return (
                output_text,
                json.dumps(result, indent=2),
                "✅ Success (Note: Template implementation)"
            )
        elif response.status_code == 429:
            return "", "", "⚠️ Rate limit exceeded. Wait a moment and try again."
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_get_conversation(cid: str):
    """Get conversation details"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/conversations/{cid}",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            messages = result.get("messages", [])
            msg_count = len(messages)
            return (
                json.dumps(result, indent=2),
                f"✅ Found {msg_count} messages"
            )
        elif response.status_code == 404:
            return "", "⚠️ Conversation not found"
        else:
            return "", f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        return "", f"❌ Exception: {str(e)}"

def test_delete_conversation(cid: str):
    """Delete conversation"""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/conversations/{cid}",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            return "✅ Conversation deleted successfully"
        elif response.status_code == 404:
            return "⚠️ Conversation not found"
        else:
            return f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Exception: {str(e)}"

def test_get_playbook(cid: str, insight_type: str = None):
    """Get playbook entries for a conversation"""
    try:
        url = f"{API_BASE_URL}/playbook/{cid}"
        if insight_type and insight_type != "all":
            url += f"?insight_type={insight_type}"
        
        response = requests.get(
            url,
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            entries = result.get("entries", [])
            
            if not entries:
                return (
                    "No playbook entries found for this conversation.",
                    "",
                    "⚠️ No entries"
                )
            
            # Format entries in a readable way
            formatted = []
            formatted.append(f"📚 **Playbook for {cid}** ({len(entries)} entries)\n")
            
            # Group by insight type
            by_type = {}
            for entry in entries:
                itype = entry['insight_type']
                if itype not in by_type:
                    by_type[itype] = []
                by_type[itype].append(entry)
            
            for itype, type_entries in by_type.items():
                formatted.append(f"\n## {itype.upper()} ({len(type_entries)} entries)")
                for entry in type_entries:
                    operation_emoji = {
                        "insert": "➕",
                        "update": "🔄",
                        "delete": "❌"
                    }.get(entry['operation'], "•")
                    
                    formatted.append(f"\n{operation_emoji} **{entry['key']}** (v{entry['version']})")
                    formatted.append(f"   {entry['value']}")
                    formatted.append(f"   Confidence: {entry['confidence_score']:.0%}")
                    if entry.get('tags'):
                        formatted.append(f"   Tags: {', '.join(entry['tags'])}")
                    formatted.append(f"   Created: {entry['created_at']}")
                    if entry['updated_at'] != entry['created_at']:
                        formatted.append(f"   Updated: {entry['updated_at']}")
            
            return (
                "\n".join(formatted),
                json.dumps(result, indent=2),
                f"✅ Found {len(entries)} entries"
            )
        elif response.status_code == 404:
            return "", "", "⚠️ Conversation not found"
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_get_playbook_context(cid: str):
    """Get formatted playbook context for a conversation"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/playbook/{cid}/context",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return (
                result.get("context", ""),
                json.dumps(result, indent=2),
                f"✅ Found {result.get('total_entries', 0)} entries"
            )
        elif response.status_code == 404:
            return "", "", "⚠️ Conversation not found"
        else:
            return "", "", f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        return "", "", f"❌ Exception: {str(e)}"

def test_health():
    """Test the /health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            result = response.json()
            return (
                json.dumps(result, indent=2),
                f"✅ Healthy - {result.get('active_conversations', 0)} active conversations"
            )
        else:
            return "", f"❌ Unhealthy: {response.status_code}"
    except Exception as e:
        return "", f"❌ Cannot connect: {str(e)}"

def test_capabilities():
    """Test the /capabilities endpoint"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/capabilities",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            return json.dumps(response.json(), indent=2), "✅ Success"
        else:
            return "", f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        return "", f"❌ Exception: {str(e)}"

# Build Gradio Interface
with gr.Blocks(title="Sample Miner API v3.0 Tester", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧪 Sample Miner API v3.0 Test Interface")
    gr.Markdown(f"""
    **API URL:** `{API_BASE_URL}` | **Version:** 3.0.0 (Unified Interface)
    
    **Features:**
    - ✅ Unified ComponentInput/ComponentOutput interface
    - ✅ Conversation history (max 10 messages, 7-day retention)
    - ✅ Smart history (5 recent messages per request)
    - ✅ Rate limiting (10-30 req/min depending on endpoint)
    - ✅ Input validation (prevents token abuse)
    - ✅ Connection pooling (20-30% faster)
    """)
    
    with gr.Tabs():
        # Tab 1: Complete Endpoint
        with gr.Tab("💬 Complete"):
            gr.Markdown("### Test the unified /complete endpoint")
            gr.Markdown("Rate limit: **20 requests/minute**")
            with gr.Row():
                with gr.Column():
                    v2_complete_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    v2_complete_task = gr.Textbox(
                        label="Task",
                        value="Help me understand machine learning",
                        lines=2
                    )
                    v2_complete_query = gr.Textbox(
                        label="User Query (max 10k chars)",
                        value="What is machine learning in simple terms?",
                        lines=4
                    )
                    v2_complete_notebook = gr.Textbox(
                        label="Notebook Context (optional, max 50k chars)",
                        value="",
                        lines=4,
                        placeholder="# Code context here..."
                    )
                    with gr.Row():
                        v2_complete_use_history = gr.Checkbox(label="Use Conversation History", value=True)
                        v2_complete_use_playbook = gr.Checkbox(label="Use Playbook", value=True)
                    v2_complete_btn = gr.Button("Send Request", variant="primary")
                
                with gr.Column():
                    v2_complete_output = gr.Textbox(label="Output", lines=10)
                    v2_complete_component = gr.Textbox(label="Component")
                    v2_complete_json = gr.Textbox(label="Full Response (JSON)", lines=6)
                    v2_complete_status = gr.Textbox(label="Status")
            
            v2_complete_btn.click(
                test_complete,
                inputs=[v2_complete_task, v2_complete_query, v2_complete_notebook, v2_complete_use_history, v2_complete_use_playbook, v2_complete_cid],
                outputs=[v2_complete_output, v2_complete_component, v2_complete_json, v2_complete_status]
            )
        
        # Tab 2: Refine Endpoint
        with gr.Tab("✨ Refine"):
            gr.Markdown("### Test the unified /refine endpoint")
            gr.Markdown("Rate limit: **20 requests/minute**")
            with gr.Row():
                with gr.Column():
                    v2_refine_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    v2_refine_task = gr.Textbox(
                        label="Task",
                        value="Improve the explanation",
                        lines=2
                    )
                    v2_refine_query = gr.Textbox(
                        label="User Query",
                        value="Make this more detailed and add examples",
                        lines=3
                    )
                    v2_refine_prev = gr.Textbox(
                        label="Previous Output to Refine",
                        value="Machine learning is when computers learn from data.",
                        lines=5
                    )
                    with gr.Row():
                        v2_refine_use_history = gr.Checkbox(label="Use Conversation History", value=True)
                        v2_refine_use_playbook = gr.Checkbox(label="Use Playbook", value=True)
                    v2_refine_btn = gr.Button("Refine Output", variant="primary")
                
                with gr.Column():
                    v2_refine_output = gr.Textbox(label="Refined Output", lines=12)
                    v2_refine_json = gr.Textbox(label="Full Response (JSON)", lines=6)
                    v2_refine_status = gr.Textbox(label="Status")
            
            v2_refine_btn.click(
                test_refine,
                inputs=[v2_refine_task, v2_refine_query, v2_refine_prev, v2_refine_use_history, v2_refine_use_playbook, v2_refine_cid],
                outputs=[v2_refine_output, v2_refine_json, v2_refine_status]
            )
        
        # Tab 3: Feedback Endpoint
        with gr.Tab("📊 Feedback"):
            gr.Markdown("### Test the unified /feedback endpoint")
            gr.Markdown("Rate limit: **20 requests/minute**")
            with gr.Row():
                with gr.Column():
                    v2_feedback_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    v2_feedback_task = gr.Textbox(
                        label="Task",
                        value="Analyze this output",
                        lines=2
                    )
                    v2_feedback_output = gr.Textbox(
                        label="Output to Analyze",
                        value="Quantum computing uses quantum bits called qubits. They can be 0 and 1 simultaneously.",
                        lines=6
                    )
                    with gr.Row():
                        v2_feedback_use_history = gr.Checkbox(label="Use Conversation History", value=True)
                        v2_feedback_use_playbook = gr.Checkbox(label="Use Playbook", value=True)
                    v2_feedback_btn = gr.Button("Get Feedback", variant="primary")
                
                with gr.Column():
                    v2_feedback_output_result = gr.Textbox(label="Feedback", lines=12)
                    v2_feedback_json = gr.Textbox(label="Full Response (JSON)", lines=6)
                    v2_feedback_status = gr.Textbox(label="Status")
            
            v2_feedback_btn.click(
                test_feedback,
                inputs=[v2_feedback_task, v2_feedback_output, v2_feedback_use_history, v2_feedback_use_playbook, v2_feedback_cid],
                outputs=[v2_feedback_output_result, v2_feedback_json, v2_feedback_status]
            )
        
        # Tab 4: Human Feedback
        with gr.Tab("💬 Human Feedback"):
            gr.Markdown("### Test the unified /human_feedback endpoint")
            gr.Markdown("Rate limit: **30 requests/minute** (higher for feedback)")
            with gr.Row():
                with gr.Column():
                    v2_hf_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    v2_hf_feedback = gr.Textbox(
                        label="Human Feedback (max 5k chars)",
                        value="I prefer concise explanations with code examples and visual diagrams when possible.",
                        lines=6
                    )
                    v2_hf_btn = gr.Button("Submit Feedback", variant="primary")
                
                with gr.Column():
                    v2_hf_output = gr.Textbox(label="Acknowledgment", lines=8)
                    v2_hf_json = gr.Textbox(label="Full Response (JSON)", lines=8)
                    v2_hf_status = gr.Textbox(label="Status")
            
            v2_hf_btn.click(
                test_human_feedback,
                inputs=[v2_hf_feedback, v2_hf_cid],
                outputs=[v2_hf_output, v2_hf_json, v2_hf_status]
            )
        
        # Tab 5: Summary
        with gr.Tab("📝 Summary"):
            gr.Markdown("### Test the unified /summary endpoint")
            gr.Markdown("Rate limit: **15 requests/minute**")
            with gr.Row():
                with gr.Column():
                    v2_summary_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    v2_summary_outputs = gr.Textbox(
                        label="Multiple Outputs (one per line)",
                        value="""Machine learning helps computers learn from data.
Deep learning uses neural networks with many layers.
AI can recognize patterns and make predictions.
Training requires large datasets and computing power.""",
                        lines=10
                    )
                    with gr.Row():
                        v2_summary_use_history = gr.Checkbox(label="Use Conversation History", value=True)
                        v2_summary_use_playbook = gr.Checkbox(label="Use Playbook", value=True)
                    v2_summary_btn = gr.Button("Generate Summary", variant="primary")
                
                with gr.Column():
                    v2_summary_output = gr.Textbox(label="Summary", lines=12)
                    v2_summary_json = gr.Textbox(label="Full Response (JSON)", lines=6)
                    v2_summary_status = gr.Textbox(label="Status")
            
            v2_summary_btn.click(
                test_summary,
                inputs=[v2_summary_outputs, v2_summary_use_history, v2_summary_use_playbook, v2_summary_cid],
                outputs=[v2_summary_output, v2_summary_json, v2_summary_status]
            )
        
        # Tab 6: Aggregate
        with gr.Tab("🎯 Aggregate"):
            gr.Markdown("### Test the unified /aggregate endpoint")
            gr.Markdown("Rate limit: **15 requests/minute**")
            with gr.Row():
                with gr.Column():
                    v2_agg_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    v2_agg_outputs = gr.Textbox(
                        label="Multiple Outputs (one per line)",
                        value="""The answer is 42.
I think the answer is 42.
Calculation shows 42 as the result.
The correct answer is 41.
Based on my analysis, it's 42.""",
                        lines=10
                    )
                    with gr.Row():
                        v2_agg_use_history = gr.Checkbox(label="Use Conversation History", value=True)
                        v2_agg_use_playbook = gr.Checkbox(label="Use Playbook", value=True)
                    v2_agg_btn = gr.Button("Find Consensus", variant="primary")
                
                with gr.Column():
                    v2_agg_output = gr.Textbox(label="Consensus Result", lines=12)
                    v2_agg_json = gr.Textbox(label="Full Response (JSON)", lines=6)
                    v2_agg_status = gr.Textbox(label="Status")
            
            v2_agg_btn.click(
                test_aggregate,
                inputs=[v2_agg_outputs, v2_agg_use_history, v2_agg_use_playbook, v2_agg_cid],
                outputs=[v2_agg_output, v2_agg_json, v2_agg_status]
            )
        
        # Tab 7: Internet Search
        with gr.Tab("🔍 Internet Search"):
            gr.Markdown("### Test the unified /internet_search endpoint")
            gr.Markdown("⚠️ **Note:** This is a template implementation. Returns 'unavailable service' message.")
            gr.Markdown("Rate limit: **10 requests/minute** (lower for expensive operations)")
            with gr.Row():
                with gr.Column():
                    v2_search_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    v2_search_query = gr.Textbox(
                        label="Search Query",
                        value="What is the latest Python version?",
                        lines=3
                    )
                    v2_search_btn = gr.Button("Search", variant="primary")
                
                with gr.Column():
                    v2_search_output = gr.Textbox(label="Search Result", lines=10)
                    v2_search_json = gr.Textbox(label="Full Response (JSON)", lines=6)
                    v2_search_status = gr.Textbox(label="Status")
            
            v2_search_btn.click(
                test_internet_search,
                inputs=[v2_search_query, v2_search_cid],
                outputs=[v2_search_output, v2_search_json, v2_search_status]
            )
        
        # Tab 8: Playbook Management (NEW)
        with gr.Tab("📚 Playbook"):
            gr.Markdown("### View and manage playbook entries")
            gr.Markdown("""
            The **Playbook** is a knowledge base that stores structured insights extracted from human feedback.
            Each entry contains preferences, instructions, facts, corrections, context, or constraints.
            """)
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### View Playbook Entries")
                    playbook_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    playbook_filter = gr.Dropdown(
                        label="Filter by Insight Type",
                        choices=["all", "preference", "instruction", "fact", "correction", "context", "constraint"],
                        value="all"
                    )
                    playbook_get_btn = gr.Button("Get Playbook", variant="primary")
                    playbook_formatted = gr.Textbox(label="Playbook Entries (Formatted)", lines=15)
                    playbook_status = gr.Textbox(label="Status")
                
                with gr.Column():
                    gr.Markdown("#### Playbook Context (for LLM)")
                    playbook_context_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    playbook_context_btn = gr.Button("Get Context Format", variant="secondary")
                    playbook_context_output = gr.Textbox(label="Formatted Context", lines=15)
                    playbook_context_status = gr.Textbox(label="Status")
            
            with gr.Row():
                with gr.Column():
                    playbook_json = gr.Textbox(label="Full Playbook Data (JSON)", lines=10)
            
            playbook_get_btn.click(
                test_get_playbook,
                inputs=[playbook_cid, playbook_filter],
                outputs=[playbook_formatted, playbook_json, playbook_status]
            )
            
            playbook_context_btn.click(
                test_get_playbook_context,
                inputs=[playbook_context_cid],
                outputs=[playbook_context_output, playbook_json, playbook_context_status]
            )
        
        # Tab 9: Conversation Management
        with gr.Tab("💾 Conversations"):
            gr.Markdown("### Manage conversation history")
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Get Conversation")
                    conv_get_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    conv_get_btn = gr.Button("Get Conversation", variant="primary")
                    conv_get_result = gr.Textbox(label="Conversation Data (JSON)", lines=12)
                    conv_get_status = gr.Textbox(label="Status")
                
                with gr.Column():
                    gr.Markdown("#### Delete Conversation")
                    conv_del_cid = gr.Textbox(label="Conversation ID", value="test-conv-001")
                    conv_del_btn = gr.Button("Delete Conversation", variant="stop")
                    conv_del_status = gr.Textbox(label="Status", lines=3)
            
            conv_get_btn.click(
                test_get_conversation,
                inputs=[conv_get_cid],
                outputs=[conv_get_result, conv_get_status]
            )
            
            conv_del_btn.click(
                test_delete_conversation,
                inputs=[conv_del_cid],
                outputs=[conv_del_status]
            )
        
        # Tab 10: System
        with gr.Tab("🔧 System"):
            gr.Markdown("### Test system endpoints")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Health Check")
                    health_btn = gr.Button("Check Health", variant="primary")
                    health_result = gr.Textbox(label="Health Status (JSON)", lines=6)
                    health_status = gr.Textbox(label="Status")
                
                with gr.Column():
                    gr.Markdown("#### Capabilities")
                    capabilities_btn = gr.Button("Get Capabilities", variant="primary")
                    capabilities_result = gr.Textbox(label="Capabilities (JSON)", lines=15)
                    capabilities_status = gr.Textbox(label="Status")
            
            health_btn.click(test_health, outputs=[health_result, health_status])
            capabilities_btn.click(test_capabilities, outputs=[capabilities_result, capabilities_status])
    
    gr.Markdown("---")
    gr.Markdown("""
    ### 📚 API Information
    
    **What's New in v3.0:**
    - Unified component interface (all endpoints use same input/output)
    - **Agentic Context Engine (Playbook)** - LLM-powered insight extraction from human feedback
    - Conversation history with smart context (5 recent messages)
    - Rate limiting for security
    - Input validation (prevents token abuse)
    - Connection pooling for better performance
    - 40-50% token savings with smart history
    
    **Playbook System:**
    - Automatically extracts structured insights from human feedback
    - Determines operations (insert/update/delete) using LLM
    - Stores persistent knowledge per conversation
    - Insight types: preference, instruction, fact, correction, context, constraint
    - Confidence scoring and versioning
    - Full audit trail of all operations
    
    **Rate Limits:**
    - Complete/Refine/Feedback: 20 req/min
    - Human Feedback: 30 req/min (higher for feedback)
    - Summary/Aggregate: 15 req/min
    - Internet Search: 10 req/min
    
    **Input Limits:**
    - User query: max 10,000 characters
    - Notebook: max 50,000 characters
    - Input items: max 50 per request
    - Previous outputs: max 20 per request
    
    **Documentation:**
    - 📖 PLAYBOOK_SYSTEM.md - Complete playbook documentation
    - 📖 README.md - API reference
    - 📖 GRADIO_UI.md - UI guide
    """)

if __name__ == "__main__":
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down Gradio UI...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting Gradio Test UI for Sample Miner API...")
    print(f"📡 Testing API at: {API_BASE_URL}")
    print(f"🔑 Using API Key: {API_KEY[:20]}...")
    print(f"📖 Unified Component Interface")
    print("⏸️  Press Ctrl+C to stop\n")
    
    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=True,
            show_error=True,
            quiet=False
        )
    except KeyboardInterrupt:
        print("\n✅ Gradio UI stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
