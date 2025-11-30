# AI Agent Builder - Public API Developer Guide

**Last Updated:** November 29, 2025  
**API Base URL:** `https://agent-builder-agent-builder-dev-api.hf.space`

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Rate Limiting](#rate-limiting)
5. [API Endpoints](#api-endpoints)
6. [Workflow Export & Execution](#workflow-export-execution)
7. [Code Examples](#code-examples)

---

## Overview

The AI Agent Builder Public API allows developers to programmatically execute AI agent workflows designed in the Builder interface. This API uses **optional Bittensor wallet-based authentication** to ensure fair access to computational resources.

### Key Features

- 🔐 **Secure Authentication**: Bittensor coldkey signature-based authentication
- ⚖️ **Fair Access**: Proportional rate limiting based on alpha stake
- 🚀 **High Performance**: Distributed miner network for scalable AI execution
- 📊 **Graph Execution**: Execute complex multi-agent DAG workflows
---

## Getting Started

### Prerequisites

**Minimum Requirements:**
1. **Workflow JSON**: Export your workflow from the Builder interface (see "Export for API" button)
2. **HTTP Client**: Any tool that can make POST requests (curl, Python requests, JavaScript fetch, etc.)

**Optional (for higher rate limits):**
1. **Bittensor Wallet**: A Bittensor wallet with a coldkey for authentication
2. **Stake in Subnet 80**: Higher stake = higher rate limits 

### Installation

Install required Python packages:

```bash
pip install bittensor requests
```

---

## Authentication

### How It Works

Authentication uses **Bittensor coldkey signatures** to verify wallet ownership. This prevents unauthorized access and enables stake-based rate limiting.

Use your Bittensor wallet to sign an authentication message:

```python
import bittensor as bt
from binascii import hexlify

def generate_signed_message(wallet_name: str, password: str) -> dict:
    """
    Generate signed authentication message.
    
    Args:
        wallet_name: Your Bittensor wallet name
        password: Wallet password
    
    Returns:
        Dictionary with signed_message, coldkey, and signature
    """
    # Load wallet
    wallet = bt.wallet(name=wallet_name)
    wallet.coldkey_file.save_password_to_env(password)
    wallet.unlock_coldkey()
    
    # Create message (can be any content)
    message = "agent-builder-proxy-auth"
    
    # Sign message
    signature = wallet.coldkey.sign(message.encode())
    signature_hex = hexlify(signature).decode()
    
    # Get coldkey address
    coldkey = wallet.coldkey.ss58_address
    
    # Create standard format (tab-separated)
    signed_message = f"{message}<separate>Signed by: {coldkey}<separate>Signature: {signature_hex}"
    
    return {
        "signed_message": signed_message,
        "coldkey": coldkey,
        "signature": signature_hex
    }

# Usage
auth_data = generate_signed_message("my_wallet", "my_password")
print(f"Coldkey: {auth_data['coldkey']}")
print(f"Signed Message: {auth_data['signed_message']}")
```

---

## Rate Limiting

### Overview

The API uses a **proportional stake-based rate limiting system** to fairly allocate computational resources among users.

### Rate Limit Types

1. **RPM (Requests Per Minute)**: Maximum requests allowed in a 60-second window
2. **Concurrent Limit**: Maximum simultaneous requests

### Dynamic Concurrent Limit

The concurrent limit is **dynamic** and adjusts based on your remaining RPM:

```python
dynamic_concurrent = min(remaining_rpm, max(1, max_rpm / 2))
```

**Example Scenarios:**

| Max RPM | Used RPM | Remaining RPM | Static Concurrent | Dynamic Concurrent | Result |
|---------|----------|---------------|-------------------|--------------------|--------|
| 48 | 0 | 48 | 24 | min(48, 24) | **24** |
| 48 | 20 | 28 | 24 | min(28, 24) | **24** |
| 48 | 40 | 8 | 24 | min(8, 24) | **8** |
| 48 | 46 | 2 | 24 | min(2, 24) | **2** |

This prevents users from consuming all their RPM in concurrent bursts.

### Important Disclaimers

⚠️ **CRITICAL - PLEASE READ:**

- **NOT A PURCHASE OR SALE**: Staking alpha tokens is NOT a financial transaction or investment
- **YOU RETAIN OWNERSHIP**: You still own your alpha tokens while staked
- **VALUE FLUCTUATION**: The value of alpha tokens can increase or decrease
- **NO GUARANTEES**: We make NO guarantees about profit, returns, or asset value
- **YOUR RESPONSIBILITY**: You are solely responsible for your staking decisions
- **NOT INVESTMENT ADVICE**: This is a computational resource allocation mechanism, not financial advice
- **RISK AWARENESS**: Understand blockchain risks before staking any tokens

### Checking Your Rate Limit

```python
import requests

def check_rate_limit(signed_message: str, coldkey: str) -> dict:
    """
    Check your current rate limit allocation.
    
    Args:
        signed_message: Your signed authentication message
        coldkey: Your Bittensor coldkey address
    
    Returns:
        Dictionary with RPM/concurrent allocation and stake info
    """
    headers = {
        "X-Signed-Message": signed_message,
        "X-Coldkey": coldkey
    }
    
    response = requests.get(
        f"https://agent-builder-agent-builder-dev-api.hf.space/stake/check-rpm",
        params={"coldkey": coldkey},
        headers=headers
    )
    
    return response.json()

# Usage
rate_info = check_rate_limit(auth_data["signed_message"], auth_data["coldkey"])
print(f"Your RPM Limit: {rate_info['rate_limit']['rpm']['limit']}")
print(f"RPM Remaining: {rate_info['rate_limit']['rpm']['remaining']}")
print(f"Concurrent Limit: {rate_info['rate_limit']['concurrent']['limit']}")
print(f"Dynamic Concurrent: {rate_info['rate_limit']['concurrent']['dynamic_limit']}")
print(f"Your Stake: {rate_info['stake_amount_tao']} Alpha")
```

### Increasing Your Rate Limit

To get higher rate limits:

1. **Authenticate**: Add `X-Signed-Message` and `X-Coldkey` headers
2. **Increase Stake**: Stake more tokens in Subnet 80 (via Bittensor network)
3. **Wait for Cache**: Stake info refreshes every 5 minutes
4. **Verify**: Check your new allocation with `/stake/check-rpm`

**Note**: Staking happens on Bittensor network, not through this API.

---

## API Endpoints

### Base URL

```
https://agent-builder-agent-builder-dev-api.hf.space
```

### Public Endpoints (No Authentication Required)

#### Health Check

```http
GET /health
```

Check if the API gateway is operational.

**Response:**
```json
{
  "status": "healthy",
  "service": "agent-builder-proxy-gateway"
}
```

### Workflow Endpoints

#### Execute Workflow (Main Endpoint)

```http
POST /orchestrate/execute
```

Execute an AI agent workflow using the DAG orchestration system.

**Authentication:** Optional (adds `X-Signed-Message` and `X-Coldkey` headers for higher rate limits)

**Request Body:**
```json
{
  "workflow": {
    "workflow_id": "workflow_1732468800000",
    "nodes": [
      {
        "id": "node_1",
        "type": "user",
        "user_query": "Write a blog post about AI",
        "dependencies": []
      },
      {
        "id": "node_2",
        "type": "component",
        "component": "complete",
        "coldkey": "5GrwvaEF...",
        "task": "Write a blog post",
        "use_conversation_history": true,
        "use_playbook": true,
        "dependencies": ["node_1"]
      }
    ]
  },
  "cid": "conv_1732468800000"
}
```

**Request Headers (Optional):**
```http
Content-Type: application/json
X-Signed-Message: message<separate>Signed by: 5GrwvaEF...<separate>Signature: 0x1234...
X-Coldkey: 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "workflow_1764001649914",
  "cid": "conv_1764001649913_test",
  "node_results": {
    "node_1764001643979": {
      "node_id": "node_1764001643979",
      "success": true,
      "result": {
        "type": "user",
        "user_query": "Hello"
      },
      "error": null,
      "execution_time_ms": 0
    },
    "node_1764001645577": {
      "node_id": "node_1764001645577",
      "success": true,
      "result": {
        "cid": "conv_1764001649913_test",
        "task": "Generate a comprehensive and helpful response",
        "input": [{"user_query": "Hello"}],
        "output": {
          "immediate_response": "Hello! How can I help you today?",
          "notebook": "no update"
        },
        "component": "complete"
      },
      "error": null,
      "execution_time_ms": 2487
    }
  },
  "end_node_outputs": [
    {
      "node_id": "node_1764001645577",
      "node_type": "component",
      "result": {
        "cid": "conv_1764001649913_test",
        "task": "Generate a comprehensive and helpful response",
        "input": [{"user_query": "Hello"}],
        "output": {
          "immediate_response": "Hello! How can I help you today?",
          "notebook": "no update"
        },
        "component": "complete"
      },
      "output": {
        "immediate_response": "Hello! How can I help you today?",
        "notebook": "no update"
      },
      "task": "Generate a comprehensive and helpful response",
      "component": "complete"
    }
  ],
  "total_execution_time_ms": 2488,
  "levels_executed": 2,
  "nodes_executed": 2,
  "error": null
}
```

**Response Structure Explained:**

- `success` (boolean) - Whether the workflow executed successfully
- `workflow_id` (string) - The workflow identifier that was executed
- `cid` (string) - Conversation ID used for this execution
- `node_results` (object) - Detailed results for each node by node ID
  - Contains `success`, `result`, `error`, and `execution_time_ms` for each node
- `end_node_outputs` (array) - **Primary output** - Array of final node results
  - Each end node contains:
    - `node_id` - The node identifier
    - `output` - **The AI response** with `immediate_response` and `notebook`
    - `result` - Full execution details including `task`, `input`, `component`
- `total_execution_time_ms` (number) - Total workflow execution time in milliseconds
- `levels_executed` (number) - Number of DAG levels executed
- `nodes_executed` (number) - Total number of nodes executed
- `error` (string|null) - Error message if workflow failed

**Getting the AI Response:**

The actual AI-generated response is in: `end_node_outputs[i].output.immediate_response`

```python
result = response.json()
for end_node in result["end_node_outputs"]:
    ai_response = end_node["output"]["immediate_response"]
    print(ai_response)
```

### Rate Limit Endpoints

#### Check RPM for Coldkey

```http
GET /stake/check-rpm?coldkey=5GrwvaEF...
```

Check the rate limit allocation for a specific coldkey based on stake.

**Query Parameters:**
- `coldkey` (required): Bittensor coldkey SS58 address

**Authentication Headers (Optional):**
```http
X-Signed-Message: message<separate>Signed by: 5GrwvaEF...<separate>Signature: 0x1234...
X-Coldkey: 5GrwvaEF...
```

**Response:**
```json
{
  "coldkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
  "is_miner": false,
  "status": "active",
  "stake_amount_tao": 300,
  "rate_limit": {
    "rpm": {
      "limit": 90,
      "used": 10,
      "remaining": 80,
      "window_seconds": 60
    },
    "concurrent": {
      "limit": 45,
      "dynamic_limit": 45,
      "current": 2,
      "remaining": 43,
      "formula": "min(remaining_rpm, max(1, max_rpm/2))"
    }
  },
  "inference_power": {
    "rpm_percentage": 15.0,
    "concurrent_percentage": 15.0,
    "average_percentage": 15.0,
    "description": "You have 15.0% of RPM capacity and 15.0% of concurrent capacity"
  },
  "rate_limiting_info": {
    "type": "pure_proportional",
    "description": "Your limits are calculated every 10s based on your stake proportion",
    "formula": "user_rpm = 600 × (user_stake / total_active_stake)",
    "concurrent_formula": "dynamic_concurrent = min(remaining_rpm, max(1, max_rpm/2))"
  }
}
```

**Response Fields Explained:**

- `rate_limit.rpm.limit` - Your maximum requests per minute
- `rate_limit.rpm.used` - Requests used in current minute window
- `rate_limit.rpm.remaining` - Requests still available this minute
- `rate_limit.concurrent.limit` - Static max concurrent (max_rpm / 2)
- `rate_limit.concurrent.dynamic_limit` - **Actual limit** based on remaining RPM
- `rate_limit.concurrent.current` - Currently active concurrent requests
- `rate_limit.concurrent.remaining` - Concurrent slots available
  "inference_power" - Your percentage of total system capacity

## Workflow Export & Execution

### Quick Start

1. **Design** your workflow in the Builder UI (drag nodes, connect edges)
2. Click **"Export for API"** button (generates ready-to-use JSON)
3. **Customize** the exported file (update `user_query`)
4. **POST** the file directly to `/orchestrate/execute`

### Export Format

The "Export for API" button generates a clean, minimal JSON payload ready to POST:

```json
{
  "workflow": {
    "workflow_id": "workflow_1732468800000",
    "nodes": [
      {
        "id": "node_1",
        "type": "user",
        "user_query": "Replace with your actual question",
        "dependencies": []
      },
      {
        "id": "node_2",
        "type": "component",
        "component": "complete",
        "coldkey": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
        "task": "Your task instructions here",
        "use_conversation_history": true,
        "use_playbook": true,
        "dependencies": ["node_1"]
      }
    ]
  },
  "cid": "conv_1732468800000"
}
```

**Required Fields:**
- `workflow.workflow_id` (string) - Unique workflow identifier
- `workflow.nodes` (array) - List of nodes to execute
- `cid` (string) - Conversation ID for tracking

**Optional Fields in nodes:**
- `edges` (array) - Optional edge definitions (can use `dependencies` in nodes instead)
- `timeout` (number) - Per-node timeout in seconds (default: 30)
- `notebook` (string) - For `type: "notebook"` nodes
- `user_query` (string) - For `type: "user"` nodes
- `component` (string) - For `type: "component"` nodes: `complete`, `refine`, `feedback`, `internet_search`, `summary`, `aggregate`
- `coldkey` (string) - Required for component nodes
- `task` (string) - Required for component nodes
- `use_conversation_history` (boolean) - Include chat history (default: true)
- `use_playbook` (boolean) - Use miner's learned patterns (default: true)

### Complete Payload Structure Reference

```json
{
  "workflow": {
    "workflow_id": "string",
    "nodes": [
      {
        "id": "string",
        "type": "user | notebook | component",
        "dependencies": ["node_id_array"],
        
        "user_query": "string (for type: user)",
        "notebook": "string (for type: notebook)",
        
        "component": "complete | refine | feedback | internet_search | summary | aggregate",
        "coldkey": "string (required for component)",
        "task": "string (required for component)",
        "use_conversation_history": true,
        "use_playbook": true,
        "timeout": 30
      }
    ],
    "edges": [
      {
        "source": "node_id",
        "target": "node_id"
      }
    ]
  },
  "cid": "string"
}
```

**Node Type Reference:**

| Type | Required Fields | Optional Fields | Description |
|------|----------------|-----------------|-------------|
| `user` | `id`, `type`, `user_query`, `dependencies` | `timeout` | User input node |
| `notebook` | `id`, `type`, `notebook`, `dependencies` | `timeout` | Code/document context |
| `component` | `id`, `type`, `component`, `coldkey`, `task`, `dependencies` | `use_conversation_history`, `use_playbook`, `timeout` | AI processing node |

**Component Types:**
- `complete` - Generate AI completions
- `refine` - Improve/polish existing content
- `feedback` - Provide critiques and suggestions
- `internet_search` - Perform web searches
- `summary` - Summarize content
- `aggregate` - Combine multiple inputs

## Code Examples

### Example 1: Simple Execution

```python
import requests
import json

payload = {
  "workflow": {
    "workflow_id": "workflow_1764001649914",
    "nodes": [
      {
        "id": "node_1764001643979",
        "type": "user",
        "dependencies": [],
        "user_query": "Hello"
      },
      {
        "id": "node_1764001645577",
        "type": "component",
        "dependencies": [
          "node_1764001643979"
        ],
        "component": "complete",
        "coldkey": "5Hata2bXMw44DtDxRcL6wTY44AZcsezh2UeAZiEm6yBkGHc9",
        "task": "Generate a comprehensive and helpful response based on the user input",
        "use_conversation_history": True,
        "use_playbook": True
      }
    ]
  },
  "cid": "conv_1764001649913_test"
}

# POST the workflow payload
response = requests.post(
    "https://agent-builder-agent-builder-dev-api.hf.space/orchestrate/execute",
    headers={"Content-Type": "application/json"},
    json=payload,
    timeout=180
)

result = response.json()

# Access the final output from end nodes
for end_node in result["end_node_outputs"]:
    if "output" in end_node and "immediate_response" in end_node["output"]:
        print("AI Response:", end_node["output"]["immediate_response"])
```

### Example 2: With Authentication

```python
import requests
import json

# Get signed_message from generate_signed_message() function (see Authentication section)
# Format: "message<separate>Signed by: coldkey<separate>Signature: signature_hex"
SIGNED_MESSAGE = "agent-builder-proxy-auth<separate>Signed by: 5GrwvaEF...<separate>Signature: 0x1234..."
COLDKEY = "5GrwvaEF..."

payload = {
  "workflow": {
    "workflow_id": "workflow_1764001649914",
    "nodes": [
      {
        "id": "node_1764001643979",
        "type": "user",
        "dependencies": [],
        "user_query": "Hello"
      },
      {
        "id": "node_1764001645577",
        "type": "component",
        "dependencies": [
          "node_1764001643979"
        ],
        "component": "complete",
        "coldkey": "5Hata2bXMw44DtDxRcL6wTY44AZcsezh2UeAZiEm6yBkGHc9",
        "task": "Generate a comprehensive and helpful response based on the user input",
        "use_conversation_history": True,
        "use_playbook": True
      }
    ]
  },
  "cid": "conv_1764001649913_test"
}

response = requests.post(
    "https://agent-builder-agent-builder-dev-api.hf.space/orchestrate/execute",
    headers={
        "Content-Type": "application/json",
        "X-Signed-Message": SIGNED_MESSAGE,  # Full signed message, not just signature
        "X-Coldkey": COLDKEY
    },
    json=payload,
    timeout=180
)

result = response.json()
# Get the AI response from the end node
for end_node in result["end_node_outputs"]:
    if "output" in end_node:
        print("AI Response:", end_node["output"]["immediate_response"])
```

**Version:** 2.1.0  
**Last Updated:** November 29, 2025
