# Miner Introduction Guide

---

## ⚠️ **SECURITY WARNING FOR MINER OPERATORS**

> **🔴 CRITICAL: MINERS ARE RESPONSIBLE FOR THEIR OWN SECURITY**
> 
> By operating a miner, you acknowledge and accept full responsibility for:
> 
> - **Security Implementation**: You must implement your own security measures, input validation, output sanitization, and protection against malicious requests
> - **Code Review**: This is a reference implementation only. You are responsible for reviewing, auditing, and securing your own code
> - **Custom Implementation**: You can completely re-implement your agent from scratch. You only need to follow the API interface specification
> - **Request Safety**: While the orchestrator attempts to validate requests, **WE CANNOT GUARANTEE REQUEST SAFETY**. Assume all requests may be malicious
> - **Infrastructure Protection**: Implement rate limiting, firewalls, DDoS protection, monitoring, logging, and intrusion detection
> - **API Key Security**: Protect your miner API keys. Never expose them publicly. Rotate regularly
> - **Risk Management**: Monitor for suspicious activity, implement circuit breakers, and have incident response plans
> 
> **⚠️ YOU ARE SOLELY RESPONSIBLE FOR ANY SECURITY BREACHES, DATA LEAKS, FINANCIAL LOSSES, OR DAMAGE RESULTING FROM OPERATING YOUR MINER.**
> 
> We provide best-effort security guidance, but miners must take full ownership of their security posture and operational risks.

---

## 🎯 What is a Miner?

In this system, a **miner** is an AI service provider that implements a standardized API interface to offer AI capabilities (language models, specialized tools, or custom algorithms) to the network. Miners compete to provide high-quality responses and earn rewards based on their performance.

Think of miners as **independent AI service providers** that:
- Process natural language requests
- Generate intelligent responses
- Provide feedback and refinement capabilities
- Support iterative agent workflows with action-observation loops
- Operate autonomously with their own infrastructure

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Participants                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐       ┌─────────────────┐                │
│  │   End Users  │──────▶│  Applications   │                │
│  │ (Consumers)  │       │   (Builders)    │                │
│  └──────────────┘       └────────┬────────┘                │
│                                   │                         │
│                         ┌─────────▼─────────┐               │
│                         │ Agent API Manager │               │
│                         │  (Orchestrator)   │               │
│                         └─────────┬─────────┘               │
│                                   │                         │
│              ┌────────────────────┼────────────────────┐    │
│              │                    │                    │    │
│         ┌────▼────┐         ┌────▼────┐         ┌────▼────┐│
│         │ Miner 1 │         │ Miner 2 │   ...   │ Miner N ││
│         │ (You!)  │         │ (Other) │         │ (Other) ││
│         │         │         │         │         │         ││
│         │ GPT-4o  │         │ Claude  │         │ Custom  ││
│         │ + Tools │         │ + RAG   │         │  Model  ││
│         └─────────┘         └─────────┘         └─────────┘│
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Agent API Manager**: Central orchestration system that routes requests to miners
2. **Miners (You)**: Independent AI service providers implementing the standardized API
3. **Applications**: Developers building on top of the miner network
4. **End Users**: Consumers using applications powered by miners

## 🔧 What Does a Miner Do?

As a miner, you provide four core capabilities:
(Sample miner code will be released next week)
### 1. **Complete** - Generate Responses
Process a task and generate an intelligent response. This is your primary capability.

**Use Cases:**
- Answer questions
- Write content (articles, code, summaries)
- Perform analysis
- Execute multi-step reasoning
- **Return actions** for iterative agent workflows (optional but powerful)

**Example:**
```
Task: "Explain quantum computing"
Input: "What is quantum computing and how does it differ from classical computing?"

Response:
"Quantum computing is a revolutionary approach to computation that leverages quantum mechanical phenomena..."

Actions (Optional): [
  {"task": "provide_example", "input": "Give a practical example of quantum computing"},
  {"task": "compare_performance", "input": "Compare quantum vs classical performance"}
]
```

### 2. **Feedback** - Analyze and Critique
Review an output and provide structured, constructive feedback identifying problems and suggesting improvements.

**Use Cases:**
- Quality assurance
- Content review
- Code review
- Fact-checking

**Example:**
```
Task: "Review code quality"
Input: "Check this Python function"
Output: "def add(a,b): return a+b"

Feedback:
[
  {
    "problem": "Missing type hints",
    "suggestion": "Add type annotations: def add(a: int, b: int) -> int"
  },
  {
    "problem": "No docstring",
    "suggestion": "Add a docstring explaining the function's purpose"
  }
]
```

### 3. **Refine** - Improve Outputs
Take an output and feedback, then generate an improved version.

**Use Cases:**
- Iterative improvement
- Quality enhancement
- Error correction
- Style refinement

**Example:**
```
Task: "Improve the code"
Input: Original task
Feedbacks: [Problems and suggestions from feedback step]

Refined Output:
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b
```

### 4. **Human Feedback** - Learn from Users
Accept and store human preferences to personalize future responses.

**Use Cases:**
- Preference learning
- Style adaptation
- User personalization
- Quality improvement

**Example:**
```
Human Feedback: "I prefer concise explanations with practical examples. Avoid jargon."

Action: Store preferences for this conversation and apply to future responses
```

## 🔄 Iterative Agent Workflows

One of the most powerful features miners can support is **returning actions** from the `complete` function. This enables:

### Action-Observation Loop Pattern

```
1. User Request → Miner Complete
   └─> Response: "I'll research this topic..."
   └─> Actions: [
         {"task": "search_web", "input": "latest AI trends"},
         {"task": "analyze_data", "input": "compile statistics"}
       ]

2. Orchestrator executes Action 1 → Another Miner
   └─> Response: "Found 10 recent articles..."
   └─> Observation stored

3. Orchestrator executes Action 2 → Another Miner  
   └─> Response: "Statistics show 300% growth..."
   └─> Observation stored

4. Observations sent to Feedback/Refine
   └─> Uses all observations as context
   └─> Generates final refined output
```

### Why This Matters

- **Multi-step reasoning**: Break complex tasks into subtasks
- **Tool use**: Call specialized functions/APIs
- **Research workflows**: Gather information before generating final response
- **Collaborative execution**: Different miners handle different subtasks
- **Higher quality**: More context = better outputs

### Implementing Actions in Your Miner

```python
# In your complete endpoint
response = {
    "response": "I'll analyze this by first gathering data...",
    "actions": [  # Optional but powerful!
        {
            "miner_name": "your_miner_coldkey",  # Or another miner
            "function": "complete",
            "parameters": {
                "task": "Gather market data",
                "input": "Get Bitcoin price trends"
            }
        },
        {
            "miner_name": "another_miner_coldkey",
            "function": "complete", 
            "parameters": {
                "task": "Analyze sentiment",
                "input": "Analyze social media sentiment about Bitcoin"
            }
        }
    ]
}
```

**Note:** Currently, actions are executed **independently** (no collaboration between miners during execution). Each action is a separate request to a miner. Future versions may support inter-miner collaboration.

## 📋 Required API Interface

All miners must implement these four endpoints with **Bearer token authentication**:

### Authentication
```
Authorization: Bearer {your_api_key}
```

### Endpoints

#### POST /complete
```json
Request:
{
  "cid": "conversation_id",
  "task": "Task description",
  "input": "User input",
  "at_max_depth": false,        // Optional: orchestrator sets this
  "observations": "..."          // Optional: previous action results
}

Response:
{
  "response": "Generated text",
  "actions": [                   // Optional: for iterative workflows
    {
      "miner_name": "coldkey",
      "function": "complete",
      "parameters": {
        "task": "Subtask",
        "input": "Subtask input"
      }
    }
  ]
}
```

#### POST /feedback
```json
Request:
{
  "cid": "conversation_id",
  "task": "Task description",
  "input": "Original input",
  "output": "Output to analyze",
  "observations": "..."          // Optional: context from previous steps
}

Response:
{
  "feedbacks": [                 // Note: plural
    {
      "problem": "Issue found",
      "suggestion": "How to fix"
    }
  ]
}
```

#### POST /refine
```json
Request:
{
  "cid": "conversation_id",
  "task": "Task description",
  "input": "Original input",
  "output": "Output to improve",  // Optional
  "feedbacks": [...],
  "observations": "..."           // Optional: context from previous steps
}

Response:
{
  "output": "Improved text"      // Note: "output" not "response"
}
```

#### POST /human_feedback
```json
Request:
{
  "cid": "conversation_id",
  "human_feedback": "User preferences/corrections"
}

Response:
{
  "status": "success",
  "message": "Feedback stored"
}
```

### GET /capabilities
```json
Response:
{
  "name": "My Miner",
  "version": "1.0.0",
  "model": "gpt-4o",
  "supported_functions": ["complete", "feedback", "refine", "human_feedback"],
  "max_tokens": 4096,
  "description": "High-quality responses with web search"
}
```

## 🔑 Conversation Management

### What is `cid`?

The `cid` (conversation ID) is a unique identifier for each user conversation. **You are responsible for managing conversation state.**

### Your Responsibilities

1. **Store conversation history** keyed by `cid`
2. **Maintain context** across multiple requests
3. **Apply human feedback** to future responses in that conversation
4. **Limit storage** (e.g., last 10 messages, LRU eviction)
5. **Handle cleanup** (remove old conversations after inactivity)

**Important:** The Agent API Manager is **stateless**—it does not store conversation history. All context management happens in your miner.
