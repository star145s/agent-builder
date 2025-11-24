# Sample Miner API

A reference implementation demonstrating how to build a miner that follows the required API interface. Miners can implement any agent architecture they want - this template shows one simple approach using conversation history and playbook systems.

---

## ⚠️ **IMPORTANT SECURITY WARNING FOR MINERS**

> **🔴 MINERS ARE RESPONSIBLE FOR THEIR OWN SECURITY**
> 
> This is a **reference implementation only**. As a miner operator, you must:
> 
> - ✅ **Implement your own security measures** - Validate all inputs, sanitize outputs, and protect against malicious requests
> - ✅ **Review and audit all code** - This template is provided as-is. You are responsible for reviewing and securing your implementation
> - ✅ **Handle security risks yourself** - You can completely re-implement your agent architecture. You only need to follow the API interface
> - ✅ **Assume requests may be malicious** - While the orchestrator tries to validate requests, **we cannot guarantee request safety**
> - ✅ **Protect your infrastructure** - Implement rate limiting, firewalls, monitoring, and other security best practices
> - ✅ **Secure your API keys** - Never expose your miner API key. Rotate keys regularly
> - ✅ **Monitor for attacks** - Log suspicious activity and implement intrusion detection
> 
> **⚠️ YOU ARE SOLELY RESPONSIBLE FOR ANY SECURITY BREACHES, DATA LEAKS, OR DAMAGE RESULTING FROM RUNNING YOUR MINER.**
> 
> We do our best to maintain security, but miners must take ownership of their security posture and risk management.

---

## ✨ Features

- 🎯 **Unified API Interface** - ComponentInput/ComponentOutput format across all endpoints
- 💬 **Conversation History** - Automatic conversation tracking with smart context management
- 📚 **Playbook System** - Stores user preferences, insights, and context
- 🔄 **Multiple LLM Backends** - OpenAI (cloud) or vLLM (self-hosted)
- 🛡️ **Built-in Security** - API key authentication, rate limiting, input validation
- 🗄️ **SQLite Database** - Lightweight conversation and playbook storage
- 🧪 **Gradio Test UI** - Interactive web interface for testing all endpoints

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (Python 3.11+ recommended)
- **OpenAI API key** (for OpenAI provider) OR **GPU with 4GB+ VRAM** (for vLLM)

### Installation

#### Option 1: OpenAI (Recommended - No GPU Required)

```bash
# 1. Clone repository
git clone <repository-url>
cd sample-miner-api

# 2. Install dependencies
pip install -r requirements-minimal.txt

# 3. Configure environment
cp .env.example .env

# 4. Edit .env and set:
#    - API_KEY=your-secure-random-api-key-here
#    - LLM_PROVIDER=openai
#    - OPENAI_API_KEY=sk-your-openai-api-key-here
#    - OPENAI_MODEL=gpt-4o-mini  (or gpt-4o for better quality)

# 5. Run the API server
python run.py
```

Your API will be available at `http://localhost:8001`

#### Option 2: vLLM (Self-Hosted - Requires GPU)

```bash
# 1. Clone repository
git clone <repository-url>
cd sample-miner-api

# 2. Install dependencies (includes vLLM)
pip install -r requirements.txt

# 3. Deploy vLLM model (in separate terminal)
python quick_vllm.py  # Deploys Llama 3.1 8B AWQ (quantized, ~5GB VRAM)

# 4. Configure environment
cp .env.example .env

# 5. Edit .env and set:
#    - API_KEY=your-secure-random-api-key-here
#    - LLM_PROVIDER=vllm
#    - VLLM_BASE_URL=http://localhost:8000/v1
#    - VLLM_MODEL=hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4

# 6. Run the API server (in new terminal)
python run.py
```

Your API will be available at `http://localhost:8001`

---

## 📡 API Endpoints

All endpoints require `X-API-Key` header for authentication.

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/complete` | POST | Generate completion with conversation context |
| `/refine` | POST | Refine/improve outputs based on feedback |
| `/feedback` | POST | Analyze outputs and provide structured feedback |
| `/human_feedback` | POST | Process user feedback and update playbook |
| `/summary` | POST | Generate summary of previous outputs |
| `/aggregate` | POST | Perform majority voting on multiple outputs |
| `/internet_search` | POST | Search the internet (template endpoint) |

### System Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (no auth required) |
| `/capabilities` | GET | Get miner capabilities and metadata |
| `/docs` | GET | Interactive API documentation (Swagger UI) |

### Conversation Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/conversations` | GET | List all conversations |
| `/conversations/{cid}` | GET | Get conversation history |
| `/conversations/{cid}` | DELETE | Delete conversation |

### Playbook Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/playbook/{cid}` | GET | Get playbook entries for conversation |
| `/playbook/{cid}/context` | GET | Get formatted playbook context for LLM |

---

## 🧪 Testing Your Miner

### Option 1: Gradio Web UI (Recommended)

Launch the interactive test interface:

```bash
cd sample-miner-api
python examples/gradio_test_ui.py
```

Then open **http://localhost:7860** in your browser.

**Features:**
- ✅ Test all core endpoints (`/complete`, `/feedback`, `/refine`, `/human_feedback`, `/summary`, `/aggregate`, `/internet_search`)
- ✅ View conversation history
- ✅ Inspect playbook entries
- ✅ Test system endpoints (`/health`, `/capabilities`)
- ✅ Real-time response viewing with execution time
- ✅ Built-in conversation ID management

**Tabs:**
1. **Complete** - Test basic completion with conversation history
2. **Feedback** - Analyze output quality
3. **Refine** - Improve outputs based on feedback
4. **Human Feedback** - Submit user preferences
5. **Summary** - Generate summaries
6. **Aggregate** - Test voting mechanism
7. **Internet Search** - Test search endpoint
8. **Conversation** - View conversation history
9. **Playbook** - Inspect playbook entries
10. **System** - Check health and capabilities

### Option 2: cURL (Command Line)

```bash
# Test health endpoint (no auth required)
curl http://localhost:8001/health

# Test complete endpoint
curl -X POST http://localhost:8001/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{
    "cid": "test-123",
    "task": "Explain quantum computing",
    "input": [
      {
        "user_query": "What is quantum computing in simple terms?"
      }
    ],
    "use_conversation_history": true,
    "use_playbook": true
  }'

# Test capabilities endpoint
curl http://localhost:8001/capabilities \
  -H "X-API-Key: your-secure-api-key"
```

### Option 3: Python Script

```python
import requests

API_URL = "http://localhost:8001"
API_KEY = "your-secure-api-key"

# Test complete endpoint
response = requests.post(
    f"{API_URL}/complete",
    headers={
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    },
    json={
        "cid": "python-test-001",
        "task": "Write a haiku about AI",
        "input": [
            {
                "user_query": "Write a beautiful haiku about artificial intelligence"
            }
        ],
        "use_conversation_history": True,
        "use_playbook": True
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## 🔧 Configuration

### Environment Variables

Edit `.env` file to configure your miner. Key settings:

```env
# Authentication
API_KEY=your-secure-random-api-key-here  # REQUIRED! Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Server
PORT=8001
HOST=0.0.0.0

# LLM Provider
LLM_PROVIDER=openai  # Options: "openai" or "vllm"

# OpenAI Configuration (if LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini  # Options: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo

# vLLM Configuration (if LLM_PROVIDER=vllm)
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL=hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4

# Conversation History
MAX_CONVERSATION_MESSAGES=10  # Store up to 10 messages
SMART_HISTORY_COUNT=5         # Send last 5 to LLM (saves tokens)

# Database
DATABASE_URL=sqlite:///./data/miner_api.db
```

See `.env.example` for complete configuration options.

### Switching LLM Providers

Just change `LLM_PROVIDER` in `.env` and restart:

```bash
# For OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o-mini

# For vLLM
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL=hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4
```

Then restart the server:
```bash
python run.py
```

---

## 🔐 Registering Your Miner

Once your miner is running and tested, register it with the orchestration system.

### Registration Portal

**🌐 https://huggingface.co/spaces/star145s/miner-registration**

### Step-by-Step Registration

#### 1. Prepare Your API Information

Ensure your miner is:
- ✅ Running and accessible at a public URL
- ✅ Responding to `/health` endpoint
- ✅ Configured with a secure API key

You'll need:
- **API URL**: Your miner's public URL (e.g., `https://miner.example.com`)
- **API Key**: Your `API_KEY` from `.env`
- **Bittensor Wallet**: Your coldkey wallet for signing

#### 2. Install Bittensor

```bash
python3 -m pip install --upgrade bittensor
```

#### 3. Generate Signed Credentials

Use the `encrypt.py` script to cryptographically sign your credentials:

```bash
python encrypt.py \
  --name <your-wallet-name> \
  --api-url <your-miner-public-url> \
  --token <your-api-key> \
  --output signed_credentials.txt
```

**Example:**
```bash
python encrypt.py \
  --name my_miner_wallet \
  --api-url https://miner.example.com \
  --token AbCdEf123456SecureKey \
  --output signed_credentials.txt
```

**What happens:**
- Prompts for your wallet password
- Creates cryptographic signature using your coldkey
- Generates `signed_credentials.txt` with:
  - Your API URL and token
  - SS58 wallet address
  - Cryptographic signature
  - Timestamp

#### 4. Submit Registration

Once you have your `signed_credentials.txt` file:

1. **Go to the registration portal**: https://huggingface.co/spaces/agent-builder/miner-registration-system
2. **Open** `signed_credentials.txt` and copy its contents
3. **Paste** the contents into the registration form
4. **Submit** for validation

**The orchestrator will:**
- ✅ Verify signature against your wallet address
- ✅ Test connectivity to your API
- ✅ Validate `/health` and `/capabilities` endpoints
- ✅ Register your miner if all checks pass

#### 5. Register on Subnet 80 (Required)

**Important**: In addition to registering your miner API, you must also register your wallet on **Bittensor Subnet 80** to participate in mining.

Follow the Bittensor documentation to register your miner on the subnet using your coldkey wallet. This is required for the network to recognize your miner and allocate rewards.

---

## 🎉 Quick Start Summary

```bash
# 1. Install
pip install -r requirements-minimal.txt

# 2. Configure
cp .env.example .env
# Edit .env: Set API_KEY, LLM_PROVIDER, OPENAI_API_KEY

# 3. Run
python run.py

# 4. Test
python examples/gradio_test_ui.py
# Open http://localhost:7860

# 5. Register your miner API
python encrypt.py --name wallet --api-url https://your-miner.com --token your-api-key
# Submit signed_credentials.txt to: https://huggingface.co/spaces/star145s/miner-registration

# 6. Register on Subnet 80 (Required for mining)
# Follow Bittensor docs to register your wallet on subnet 80
```
---

## 📄 License

See LICENSE file for details.
