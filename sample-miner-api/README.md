# Sample Miner API

A reference implementation demonstrating how to build a miner that follows the required API interface. Miners can implement any agent architecture they want - this template shows one simple approach.

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
> 
> 📖 **Read the full [SECURITY.md](SECURITY.md) guide for detailed security best practices and implementation guidelines.**

---

## 🎯 LLM Backend Options

This template supports **OpenAI API** (cloud) or **vLLM** (self-hosted):
- **OpenAI**: Quick setup, no GPU needed
- **vLLM**: Self-hosted, privacy-focused, requires GPU 

---

## 🚀 Quick Start

### Option 1: OpenAI 

```bash
# 1. Clone and navigate
git clone <repository-url>
cd sample-miner-api

# 2. Configure environment
cp .env.example .env
# Edit .env: Set LLM_PROVIDER=openai and add your OPENAI_API_KEY

# 3. Install and run
pip install -r requirements.txt
python run.py
```

### Option 2: vLLM (Self-Hosted)

```bash
# 1. Clone and navigate
git clone <repository-url>
cd sample-miner-api

# 2. Install dependencies (includes vLLM)
pip install -r requirements.txt

# 3. Deploy vLLM model
python quick_vllm.py  # Deploys Llama 3.1 8B AWQ (quantized)

# 4. In a new terminal, configure miner
cp .env.example .env
# Edit .env: Set LLM_PROVIDER=vllm

# 5. Run the miner API
python run.py
```

---

## 📡 API Endpoints

All endpoints require `X-API-Key` header for authentication.

**Core Endpoints:**
- `POST /complete` - Process tasks with playbook context
- `POST /feedback` - Analyze outputs and provide feedback
- `POST /refine` - Improve outputs based on feedback
- `POST /human_feedback` - Store user preferences

**Utility Endpoints:**
- `GET /health` - Health check
- `GET /capabilities` - Get miner capabilities
- `GET /docs` - Interactive API documentation

---

## 🧪 Testing

### Option 1: Web UI (Recommended)

Launch the Gradio test interface:

```bash
python gradio_test_ui.py
```

Then open http://localhost:7860 in your browser. The UI lets you test:
- `/complete` endpoint with conversation history
- `/feedback` endpoint for output analysis
- `/refine` endpoint for improving outputs
- System endpoints (`/health`, `/capabilities`)

### Option 2: Command Line (cURL)

```bash
curl -X POST http://localhost:8001/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-miner-key" \
  -d '{
    "cid": "test-123",
    "task": "What is machine learning?",
    "input": "Explain in simple terms"
  }'
```

---

### 🔧 Playbook Updates

To support smaller quantized models that struggle with complex JSON generation:
- **`/complete`**, **`/feedback`**, **`/refine`**: No automatic playbook updates (simple text responses only)
- **`/human_feedback`**: Only endpoint that updates playbook (uses simpler, more reliable prompts)

This ensures the miner works reliably with 3B-8B quantized models.

---

## 🔧 Configuration

Edit `.env` to configure the miner:

```env
# LLM Provider
LLM_PROVIDER=openai  # or "vllm"

# OpenAI Settings (if using OpenAI)
OPENAI_API_KEY=sk-your-key-here
MODEL_NAME=gpt-4o

# vLLM Settings (if using vLLM)
VLLM_API_BASE=http://localhost:8000/v1
MODEL_NAME=hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4

# Miner Settings
MINER_API_KEY=your-secure-miner-key
API_PORT=8001
MAX_TOKENS=4000
TEMPERATURE=0.7
```

**Switching providers:** Just change `LLM_PROVIDER` and restart the API.

---

## � Registering Your Miner

Once your miner API is running and tested, register it with the orchestration system using the **encrypt.py** tool to securely sign your API credentials.

Registration Link: https://huggingface.co/spaces/star145s/miner-registration
### Step 1: Prepare Your API Information

Make sure your miner API is running and accessible:
- **API URL**: The publicly accessible URL of your miner (e.g., `https://your-miner.example.com`)
- **API Token**: Your miner's API key (from `MINER_API_KEY` in `.env`)

### Step 2: Install Bittensor

```bash
python3 -m pip install --upgrade bittensor
```

### Step 3: Encrypt Your Credentials

Use the `encrypt.py` script to cryptographically sign your API information with your Bittensor wallet:

```bash
python encrypt.py \
  --name <your-wallet-name> \
  --api-url <your-miner-api-url> \
  --token <your-miner-api-key> \
  --output signed_credentials.txt
```

**Example:**
```bash
python encrypt.py \
  --name my_miner_wallet \
  --api-url https://miner.example.com \
  --token your-secure-miner-key \
  --output signed_credentials.txt
```

You'll be prompted for your wallet password. The script will generate a signed file containing:
- Your API URL and token
- Your wallet's SS58 address (signer)
- Cryptographic signature
- Timestamp

### Step 4: Submit to Miner Registration System

Submit the contents of `signed_credentials.txt` to the miner registration system. The orchestrator will:
1. Verify the signature matches your wallet address
2. Test connectivity to your API endpoint
3. Register your miner if validation passes

### Security Notes

- ✅ **Secure**: Your credentials are cryptographically signed with your coldkey
- ✅ **Verifiable**: The orchestrator can verify the signature against your wallet address
- ✅ **Tamper-proof**: Any modification to the signed data will invalidate the signature
- ⚠️ **Keep Safe**: Store your `signed_credentials.txt` securely - it contains your API token