# AI Agent Builder - Public API Developer Guide

**Last Updated:** November 23, 2025  
**API Base URL:** `https://agent-builder-agent-builder-dev-api.hf.space`

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Stake-Based Rate Limiting](#stake-based-rate-limiting)
5. [API Endpoints](#api-endpoints)
6. [Workflow Export & Execution](#workflow-export--execution)
7. [Code Examples](#code-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Agent Builder Public API allows developers to programmatically execute AI agent workflows designed in the Builder interface. This API uses **Bittensor wallet-based authentication** and **stake-based rate limiting** to ensure fair access to computational resources.

### Key Features

- 🔐 **Secure Authentication**: Bittensor coldkey signature-based authentication
- ⚖️ **Fair Access**: Proportional rate limiting based on alpha stake
- 🚀 **High Performance**: Distributed miner network for scalable AI execution
- 📊 **Graph Execution**: Execute complex multi-agent workflows
- 🔄 **Async Processing**: Non-blocking async API design

---

## Getting Started

### Prerequisites

1. **Bittensor Wallet**: You need a Bittensor wallet with a coldkey
2. **Alpha Stake** (Optional): Stake alpha tokens in Subnet 80 for higher rate limits
3. **Workflow JSON**: Export your workflow from the Builder interface

### Installation

Install required Python packages:

```bash
pip install bittensor requests
```

---

## Authentication

### How It Works

Authentication uses **Bittensor coldkey signatures** to verify wallet ownership. This prevents unauthorized access and enables stake-based rate limiting.

### Step 1: Sign a Message

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
print(f"Signed Message: {auth_data['signed_message'][:100]}...")
```

### Step 2: Include in API Requests

Add the signed message to your HTTP request headers:

```python
import requests

headers = {
    "X-Signed-Message": auth_data["signed_message"],
    "Content-Type": "application/json"
}

response = requests.get(
    "https://agent-builder-agent-builder-dev-api.hf.space/health",
    headers=headers
)
```

---

## Stake-Based Rate Limiting

### Overview

The API uses a **proportional stake-based rate limiting system** to fairly allocate computational resources among users.

### How It Works

1. **Total System Capacity**: 90 requests per minute (RPM)
2. **Your Share**: Calculated proportionally based on your alpha stake
3. **Formula**: `Your RPM = (Your Stake / Total Active Stake) × 90 RPM`
4. **Minimum Guarantee**: 1 RPM even with 0 stake

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
        Dictionary with RPM allocation and stake info
    """
    headers = {"X-Signed-Message": signed_message}
    
    response = requests.get(
        f"https://agent-builder-agent-builder-dev-api.hf.space/stake/check-rpm",
        params={"coldkey": coldkey},
        headers=headers
    )
    
    return response.json()

# Usage
rate_info = check_rate_limit(auth_data["signed_message"], auth_data["coldkey"])
print(f"Your RPM: {rate_info['rpm']}")
print(f"Your Stake: {rate_info['stake']} alpha")
print(f"Stake Ratio: {rate_info['stake_ratio']:.2%}")
```

### Rate Limit Response Example

```json
{
  "rpm": 15,
  "stake": 1000.5,
  "total_active_stake": 5000.0,
  "stake_ratio": 0.20,
  "max_system_rpm": 90,
  "description": "Your RPM is calculated based on your proportional stake"
}
```

### Increasing Your Rate Limit

To increase your rate limit:

1. **Stake More Alpha**: Increase your stake in Subnet 80
2. **Wait for Refresh**: Stake info is cached for 5 minutes
3. **Verify**: Check your new RPM allocation

**Note**: Staking is done through the Bittensor network, not through this API.

---

## API Endpoints

### Public Endpoints (No Authentication Required)

#### Health Check

```
GET /health
```

Check if the API service is operational.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-23T17:00:00Z",
  "version": "1.0.0"
}
```

### Protected Endpoints (Authentication Required)

All endpoints below require the `X-Signed-Message` header.

#### Execute Workflow

```
POST /execute
```

Execute an AI agent workflow from exported JSON.

**Request Body:**
```json
{
  "workflow": {
    "name": "My Workflow",
    "version": "1.0",
    "nodes": [...],
    "edges": [...],
    "config": {...}
  },
  "input": {
    "user_message": "Hello, AI agents!"
  }
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "status": "completed",
  "output": {
    "response": "AI agent response...",
    "execution_time": 2.5,
    "tokens_used": 150
  },
  "metadata": {
    "miner_hotkey": "5Abc...",
    "execution_path": ["agent1", "agent2"]
  }
}
```

#### List Available Miners

```
GET /miners
```

Get list of available AI miners in the network.

**Response:**
```json
{
  "miners": [
    {
      "hotkey": "5Abc...",
      "coldkey": "5Def...",
      "stake": 1000.0,
      "trust": 0.95,
      "incentive": 0.05,
      "status": "active"
    }
  ],
  "total": 25,
  "active": 23
}
```

---

## Workflow Export & Execution

### Step 1: Design Your Workflow

1. Open the **Builder** page in the UI
2. Drag and drop agents to create your workflow
3. Connect agents with edges to define execution flow
4. Configure each agent's parameters

### Step 2: Export Workflow

Click the **"Export"** button to download your workflow as JSON:

```json
{
  "name": "Customer Support Agent",
  "version": "1.0",
  "nodes": [
    {
      "id": "node_1",
      "type": "llm",
      "data": {
        "label": "Greeting Agent",
        "system_prompt": "You are a friendly customer support agent...",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
      },
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "node_2",
      "type": "llm",
      "data": {
        "label": "Technical Support",
        "system_prompt": "You are a technical support specialist...",
        "model": "gpt-4",
        "temperature": 0.3
      },
      "position": {"x": 300, "y": 100}
    }
  ],
  "edges": [
    {
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "type": "default"
    }
  ],
  "config": {
    "max_iterations": 5,
    "timeout": 30
  }
}
```

### Step 3: Execute via API

```python
import requests
import json

def execute_workflow(signed_message: str, workflow_json: dict, user_input: str) -> dict:
    """
    Execute an exported workflow via API.
    
    Args:
        signed_message: Your signed authentication message
        workflow_json: Exported workflow JSON from Builder
        user_input: User's input message
    
    Returns:
        Execution result with AI response
    """
    headers = {
        "X-Signed-Message": signed_message,
        "Content-Type": "application/json"
    }
    
    payload = {
        "workflow": workflow_json,
        "input": {
            "user_message": user_input
        }
    }
    
    response = requests.post(
        "https://agent-builder-agent-builder-dev-api.hf.space/execute",
        headers=headers,
        json=payload,
        timeout=60
    )
    
    return response.json()

# Load exported workflow
with open("my_workflow.json", "r") as f:
    workflow = json.load(f)

# Execute
result = execute_workflow(
    auth_data["signed_message"],
    workflow,
    "I need help with my account"
)

print(f"Response: {result['output']['response']}")
```

---

## Code Examples

### Complete Example: End-to-End Workflow Execution

```python
#!/usr/bin/env python3
"""
Complete example: Authenticate, check rate limit, and execute workflow.
"""

import bittensor as bt
import requests
import json
from binascii import hexlify
import time

class AgentBuilderClient:
    """Client for AI Agent Builder Public API."""
    
    def __init__(self, wallet_name: str, password: str):
        """
        Initialize client with Bittensor wallet.
        
        Args:
            wallet_name: Your Bittensor wallet name
            password: Wallet password
        """
        self.base_url = "https://agent-builder-agent-builder-dev-api.hf.space"
        self.wallet_name = wallet_name
        self.password = password
        self.signed_message = None
        self.coldkey = None
        
        # Authenticate
        self._authenticate()
    
    def _authenticate(self):
        """Generate signed authentication message."""
        wallet = bt.wallet(name=self.wallet_name)
        wallet.coldkey_file.save_password_to_env(self.password)
        wallet.unlock_coldkey()
        
        message = "agent-builder-proxy-auth"
        signature = wallet.coldkey.sign(message.encode())
        signature_hex = hexlify(signature).decode()
        
        self.coldkey = wallet.coldkey.ss58_address
        self.signed_message = f"{message}<separate>Signed by: {self.coldkey}<separate>Signature: {signature_hex}"
        
        print(f"✅ Authenticated with coldkey: {self.coldkey[:20]}...{self.coldkey[-10:]}")
    
    def _get_headers(self):
        """Get request headers with authentication."""
        return {
            "X-Signed-Message": self.signed_message,
            "Content-Type": "application/json"
        }
    
    def check_rate_limit(self):
        """Check current rate limit allocation."""
        response = requests.get(
            f"{self.base_url}/stake/check-rpm",
            params={"coldkey": self.coldkey},
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def execute_workflow(self, workflow: dict, user_input: str):
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow JSON exported from Builder
            user_input: User's input message
        
        Returns:
            Execution result
        """
        payload = {
            "workflow": workflow,
            "input": {
                "user_message": user_input
            }
        }
        
        response = requests.post(
            f"{self.base_url}/execute",
            headers=self._get_headers(),
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    
    def list_miners(self):
        """Get list of available miners."""
        response = requests.get(
            f"{self.base_url}/miners",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()


# Usage Example
if __name__ == "__main__":
    # Initialize client
    client = AgentBuilderClient("my_wallet", "my_password")
    
    # Check rate limit
    rate_info = client.check_rate_limit()
    print(f"Your RPM: {rate_info['rpm']}")
    print(f"Your Stake: {rate_info['stake']} alpha")
    
    # Load workflow
    with open("my_workflow.json", "r") as f:
        workflow = json.load(f)
    
    # Execute workflow
    result = client.execute_workflow(workflow, "Hello, I need assistance!")
    print(f"Response: {result['output']['response']}")
    print(f"Execution Time: {result['output']['execution_time']}s")
```

### Error Handling Example

```python
import requests
from requests.exceptions import HTTPError, Timeout

def execute_with_retry(client, workflow, user_input, max_retries=3):
    """
    Execute workflow with retry logic.
    
    Args:
        client: AgentBuilderClient instance
        workflow: Workflow JSON
        user_input: User input
        max_retries: Maximum retry attempts
    
    Returns:
        Execution result or None
    """
    for attempt in range(max_retries):
        try:
            result = client.execute_workflow(workflow, user_input)
            return result
        
        except HTTPError as e:
            if e.response.status_code == 429:
                # Rate limit exceeded
                print(f"⚠️ Rate limit exceeded. Waiting 60s...")
                time.sleep(60)
            elif e.response.status_code == 401:
                # Authentication failed
                print(f"❌ Authentication failed. Check your wallet signature.")
                return None
            else:
                print(f"❌ HTTP Error: {e}")
                return None
        
        except Timeout:
            print(f"⏱️ Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))  # Exponential backoff
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    print(f"❌ Failed after {max_retries} attempts")
    return None
```

---

## Best Practices

### Security

1. **Never Share Your Wallet**: Keep your wallet password and private keys secure
2. **Rotate Signatures**: Generate new signatures periodically (they don't expire but can be revoked)
3. **Use HTTPS**: Always use the HTTPS endpoint
4. **Validate Responses**: Always check response status codes and validate JSON

### Performance

1. **Cache Workflows**: Don't reload workflow JSON on every request
2. **Reuse Signatures**: Generate signature once, reuse for multiple requests
3. **Handle Rate Limits**: Implement exponential backoff when rate limited
4. **Set Timeouts**: Always set request timeouts (recommended: 60s)

### Rate Limiting

1. **Monitor Usage**: Track your RPM usage to avoid hitting limits
2. **Batch Requests**: Group related requests when possible
3. **Implement Queuing**: Queue requests locally if you exceed your RPM
4. **Consider Staking**: Increase your alpha stake for higher limits

### Error Handling

1. **Handle All HTTP Errors**: 401 (auth), 429 (rate limit), 500 (server error)
2. **Implement Retries**: Use exponential backoff for transient errors
3. **Log Failures**: Log all errors for debugging
4. **Graceful Degradation**: Have fallback behavior when API is unavailable

---

## Troubleshooting

### Common Issues

#### 401 Unauthorized

**Problem**: Authentication failed

**Solutions**:
- Verify your wallet name and password are correct
- Ensure wallet is unlocked: `wallet.unlock_coldkey()`
- Check signature format: Must be `message<separate>Signed by: coldkey<separate>Signature: hex`
- Regenerate signature if old

#### 429 Too Many Requests

**Problem**: Rate limit exceeded

**Solutions**:
- Check your RPM allocation: `GET /stake/check-rpm`
- Wait 60 seconds before retrying
- Increase your alpha stake for higher limits
- Implement request queuing

#### 500 Internal Server Error

**Problem**: Server-side error

**Solutions**:
- Check API status: `GET /health`
- Retry with exponential backoff
- Verify workflow JSON is valid
- Report persistent errors to support

#### Workflow Execution Timeout

**Problem**: Workflow takes too long to execute

**Solutions**:
- Simplify workflow (reduce number of agents)
- Reduce `max_iterations` in workflow config
- Break complex workflows into smaller parts

### Getting Help

**⚠️ SECURITY NOTICE:**
- Do NOT share your wallet private keys
- Do NOT share your signed messages publicly
- Do NOT include sensitive data in workflow prompts

For support:
1. Check the [API Documentation](https://agent-builder-agent-builder-dev-api.hf.space/docs)
2. Review workflow JSON for errors
3. Check API health endpoint
4. Contact support with:
   - Error message (sanitized)
   - Timestamp
   - Your coldkey (public address only)
   - Workflow structure (without sensitive data)

---

## API Limits & Fair Use

### Rate Limits

- **Base Rate**: 1 RPM (no stake)
- **Maximum Rate**: 90 RPM (proportional to stake)
- **Refresh Interval**: 1 minute rolling window
- **Burst Allowance**: 2x RPM for 10 seconds

### Request Limits

- **Max Request Size**: 10 MB
- **Max Workflow Nodes**: 20 agents per workflow
- **Max Execution Time**: 60 seconds
- **Max Tokens per Request**: 4000 tokens

### Fair Use Policy

This API is for **research and development purposes only**:

✅ **Allowed**:
- Testing AI agent workflows
- Building proof-of-concept applications
- Educational and research projects
- Personal development tools

❌ **Not Allowed**:
- High-volume production applications
- Reselling API access
- Automated scraping or data mining
- Malicious or abusive behavior

Violations may result in access revocation.

---

## Appendix

### Workflow JSON Schema

```json
{
  "name": "string (required)",
  "version": "string (required)",
  "nodes": [
    {
      "id": "string (required)",
      "type": "llm | tool | condition (required)",
      "data": {
        "label": "string",
        "system_prompt": "string",
        "model": "string",
        "temperature": "number (0-2)",
        "max_tokens": "number"
      },
      "position": {
        "x": "number",
        "y": "number"
      }
    }
  ],
  "edges": [
    {
      "id": "string (required)",
      "source": "string (node id, required)",
      "target": "string (node id, required)",
      "type": "default | conditional"
    }
  ],
  "config": {
    "max_iterations": "number (default: 5)",
    "timeout": "number (seconds, default: 30)"
  }
}
```

### Response Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 401 | Unauthorized | Check authentication |
| 429 | Rate Limited | Wait and retry |
| 500 | Server Error | Retry with backoff |
| 503 | Service Unavailable | Check /health endpoint |

### Supported Models

- `gpt-4` - Best quality, slower
- `gpt-3.5-turbo` - Balanced performance
- `claude-2` - Anthropic Claude (when available)
- Model availability depends on miner network

---

## Legal & Disclaimers

### Terms of Use

By using this API, you agree to:

1. Use the API for research and development only
2. Not abuse or circumvent rate limits
3. Not use for illegal or harmful purposes
4. Comply with all applicable laws and regulations

### Staking Disclaimers

**IMPORTANT - READ CAREFULLY:**

- Staking alpha tokens is **NOT** a financial investment or purchase transaction
- You **retain full ownership** of your staked tokens at all times
- Token values **can fluctuate** - prices may go up or down
- We make **NO GUARANTEES** about profits, returns, or asset values
- This is a **computational resource allocation mechanism**, not an investment product
- You are **solely responsible** for your staking decisions and their consequences
- Staking involves blockchain risks including smart contract risks, network risks, and market volatility
- **Consult a financial advisor** before making any staking decisions
- This documentation is **NOT financial or investment advice**

### Liability Limitations

- API provided "AS IS" without warranties
- No guarantee of availability, accuracy, or performance
- Not liable for data loss, damages, or losses from API use
- AI outputs may be inaccurate - always verify critical information
- Users responsible for compliance with applicable laws

### Data & Privacy

- We do NOT store your workflow prompts or AI responses
- Authentication uses cryptographic signatures (no passwords stored)
- Requests are routed to third-party miners who may log data
- Do NOT send sensitive or confidential information through the API

---

**Version:** 1.0.0  
**Last Updated:** November 23, 2025  
**API Status:** https://agent-builder-agent-builder-dev-api.hf.space/health
