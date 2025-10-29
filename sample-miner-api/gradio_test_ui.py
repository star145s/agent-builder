#!/usr/bin/env python3
"""
Simple Gradio Test UI for Sample Miner API
Test your miner endpoints directly with a web interface
"""

import gradio as gr
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_KEY = os.getenv("MINER_API_KEY", "your-secure-miner-key")

def test_complete(task: str, user_input: str, cid: str = "test-conversation"):
    """Test the /complete endpoint"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/complete",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": task,
                "input": user_input
            },
            timeout=180  # 3 minutes for LLM processing
        )
        
        if response.status_code == 200:
            result = response.json()
            return (
                result.get("response", ""),
                json.dumps(result.get("actions", []), indent=2),
                json.dumps(result.get("playbook", {}), indent=2),
                "✅ Success"
            )
        else:
            return "", "", "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", "", "", f"❌ Exception: {str(e)}"

def test_feedback(cid: str, task: str, user_input: str, output: str):
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
                "input": user_input,
                "output": output
            },
            timeout=120  # 2 minutes for feedback analysis
        )
        
        if response.status_code == 200:
            result = response.json()
            return json.dumps(result, indent=2), "✅ Success"
        else:
            return "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", f"❌ Exception: {str(e)}"

def test_refine(cid: str, task: str, user_input: str, output: str, feedback: str):
    """Test the /refine endpoint"""
    try:
        # Parse feedback as a list of feedback items
        feedback_items = [
            {"problem": "User feedback", "suggestion": feedback}
        ]
        
        response = requests.post(
            f"{API_BASE_URL}/refine",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            },
            json={
                "cid": cid,
                "task": task,
                "input": user_input,
                "output": output,
                "feedbacks": feedback_items
            },
            timeout=180  # 3 minutes for refining output
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("output", ""), "✅ Success"
        else:
            return "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", f"❌ Exception: {str(e)}"

def test_human_feedback(cid: str, human_feedback: str):
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
                "human_feedback": human_feedback
            },
            timeout=120  # 2 minutes for processing feedback
        )
        
        if response.status_code == 200:
            result = response.json()
            return json.dumps(result, indent=2), "✅ Success"
        else:
            return "", f"❌ Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return "", f"❌ Exception: {str(e)}"

def test_health():
    """Test the /health endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return json.dumps(response.json(), indent=2), "✅ Healthy"
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
with gr.Blocks(title="Sample Miner API Tester", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🧪 Sample Miner API Test Interface")
    gr.Markdown(f"**API URL:** `{API_BASE_URL}` | **API Key:** Loaded from `.env`")
    
    with gr.Tabs():
        # Tab 1: Complete Endpoint
        with gr.Tab("💬 Complete"):
            gr.Markdown("### Test the main /complete endpoint")
            with gr.Row():
                with gr.Column():
                    complete_cid = gr.Textbox(label="Conversation ID", value="test-conversation")
                    complete_task = gr.Textbox(
                        label="Task", 
                        value="Help me learn about machine learning",
                        lines=2
                    )
                    complete_input = gr.Textbox(
                        label="User Input", 
                        value="What is machine learning in simple terms?",
                        lines=3
                    )
                    complete_btn = gr.Button("Send Request", variant="primary")
                
                with gr.Column():
                    complete_response = gr.Textbox(label="Response", lines=8)
                    complete_actions = gr.Textbox(label="Actions (JSON)", lines=5)
                    complete_playbook = gr.Textbox(label="Playbook (JSON)", lines=5)
                    complete_status = gr.Textbox(label="Status")
            
            complete_btn.click(
                test_complete,
                inputs=[complete_task, complete_input, complete_cid],
                outputs=[complete_response, complete_actions, complete_playbook, complete_status]
            )
        
        # Tab 2: Feedback Endpoint
        with gr.Tab("📊 Feedback"):
            gr.Markdown("### Test the /feedback endpoint")
            with gr.Row():
                with gr.Column():
                    feedback_cid = gr.Textbox(label="Conversation ID", value="test-conversation")
                    feedback_task = gr.Textbox(
                        label="Task",
                        value="Explain quantum computing",
                        lines=2
                    )
                    feedback_input = gr.Textbox(
                        label="User Input",
                        value="What is quantum computing?",
                        lines=2
                    )
                    feedback_output = gr.Textbox(
                        label="Output to Analyze",
                        value="Quantum computing uses qubits that can be 0 and 1 at the same time.",
                        lines=5
                    )
                    feedback_btn = gr.Button("Get Feedback", variant="primary")
                
                with gr.Column():
                    feedback_result = gr.Textbox(label="Feedback Result (JSON)", lines=12)
                    feedback_status = gr.Textbox(label="Status")
            
            feedback_btn.click(
                test_feedback,
                inputs=[feedback_cid, feedback_task, feedback_input, feedback_output],
                outputs=[feedback_result, feedback_status]
            )
        
        # Tab 3: Refine Endpoint
        with gr.Tab("✨ Refine"):
            gr.Markdown("### Test the /refine endpoint")
            with gr.Row():
                with gr.Column():
                    refine_cid = gr.Textbox(label="Conversation ID", value="test-conversation")
                    refine_task = gr.Textbox(
                        label="Task",
                        value="Write a technical explanation",
                        lines=2
                    )
                    refine_input = gr.Textbox(
                        label="User Input",
                        value="Explain APIs",
                        lines=2
                    )
                    refine_output = gr.Textbox(
                        label="Original Output",
                        value="APIs are interfaces for programs to talk.",
                        lines=4
                    )
                    refine_feedback = gr.Textbox(
                        label="Feedback",
                        value="Too brief, add more technical details and examples",
                        lines=3
                    )
                    refine_btn = gr.Button("Refine Output", variant="primary")
                
                with gr.Column():
                    refine_result = gr.Textbox(label="Refined Output", lines=12)
                    refine_status = gr.Textbox(label="Status")
            
            refine_btn.click(
                test_refine,
                inputs=[refine_cid, refine_task, refine_input, refine_output, refine_feedback],
                outputs=[refine_result, refine_status]
            )
        
        # Tab 4: Human Feedback Endpoint
        with gr.Tab("💬 Human Feedback"):
            gr.Markdown("### Test the /human_feedback endpoint")
            gr.Markdown("Store user preferences directly into the playbook")
            with gr.Row():
                with gr.Column():
                    hf_cid = gr.Textbox(label="Conversation ID", value="test-conversation")
                    hf_feedback = gr.Textbox(
                        label="Human Feedback",
                        value="I prefer concise explanations with code examples",
                        lines=4
                    )
                    hf_btn = gr.Button("Submit Feedback", variant="primary")
                
                with gr.Column():
                    hf_result = gr.Textbox(label="Response (JSON)", lines=12)
                    hf_status = gr.Textbox(label="Status")
            
            hf_btn.click(
                test_human_feedback,
                inputs=[hf_cid, hf_feedback],
                outputs=[hf_result, hf_status]
            )
        
        # Tab 5: System Endpoints
        with gr.Tab("🔧 System"):
            gr.Markdown("### Test system endpoints")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### Health Check")
                    health_btn = gr.Button("Check Health", variant="primary")
                    health_result = gr.Textbox(label="Health Status", lines=3)
                    health_status = gr.Textbox(label="Status")
                
                with gr.Column():
                    gr.Markdown("#### Capabilities")
                    capabilities_btn = gr.Button("Get Capabilities", variant="primary")
                    capabilities_result = gr.Textbox(label="Capabilities (JSON)", lines=10)
                    capabilities_status = gr.Textbox(label="Status")
            
            health_btn.click(test_health, outputs=[health_result, health_status])
            capabilities_btn.click(test_capabilities, outputs=[capabilities_result, capabilities_status])
    
    gr.Markdown("---")

if __name__ == "__main__":
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\n� Shutting down Gradio UI...")
        sys.exit(0)
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("�🚀 Starting Gradio Test UI...")
    print(f"📡 Testing API at: {API_BASE_URL}")
    print(f"🔑 Using API Key from .env file")
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
