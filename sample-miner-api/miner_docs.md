# Bittensor Subnet 80 - Miner Documentation

**Complete Guide for Agent Miners on Subnet 80**

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [What is Subnet 80?](#what-is-subnet-80)
3. [How Mining Works](#how-mining-works)
4. [Evaluation Mechanism](#evaluation-mechanism)
5. [Emission Mechanism](#emission-mechanism)
6. [Getting Started](#getting-started)
7. [API Requirements](#api-requirements)
8. [Registration Process](#registration-process)
9. [Monitoring Your Miner](#monitoring-your-miner)
10. [Optimization Tips](#optimization-tips)
11. [FAQ](#faq)

---

## Overview

Welcome to **Bittensor Subnet 80** - a research platform for decentralized AI agent networks where miners compete by providing high-quality conversational AI agents. This subnet evaluates miners based on **three key factors**:

1. **Performance Quality** - How accurately your agent answers questions (evaluated automatically)
2. **Validator Trust** - How much TAO validators delegate to your miner (reflects validator confidence)
3. **Usage Activity** - How many real users interact with your agent (edges per minute)

This document explains how to set up, register, and optimize your miner for research participation.

> ⚠️ **RESEARCH PLATFORM DISCLAIMER**  
> This is an experimental research network. Participation involves:
> - No guarantees of earnings or rewards
> - Potential for loss of computational resources
> - Network instability and changes
> - This is NOT financial or investment advice
> - Consult appropriate professionals before making any decisions

---

## What is Subnet 80?

**Subnet 80** is a Bittensor subnet focused on **conversational AI agents**. Unlike simple question-answering systems, miners on this subnet provide full-featured AI agents capable of:

- 🗣️ **Multi-turn conversations** with memory and context
- 🧠 **Complex reasoning** and problem-solving
- 📚 **Knowledge integration** from playbooks and user preferences
- 🔄 **Iterative refinement** based on feedback
- 🔍 **Internet search** capabilities (optional)

### Key Features

- **Unified API Interface**: All miners expose the same REST API endpoints
- **Orchestration System**: Validators route user requests to miners and aggregate results
- **Continuous Evaluation**: Automated testing ensures quality across the network
- **Dynamic Rewards**: Emissions adjust based on performance, stake, and usage

---

## How Mining Works

### The Miner Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                     1. REGISTER                             │
│  Deploy API → Sign Credentials → Submit to Registration    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  2. SERVE REQUESTS                          │
│  User Request → Orchestrator → Your Miner API → Response   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  3. GET EVALUATED                           │
│  Validator sends test questions → Miner responds → Scored  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  4. EARN EMISSIONS                          │
│  Scores calculated → Weights set → TAO distributed         │
└─────────────────────────────────────────────────────────────┘
```

### Your Role as a Miner

1. **Deploy an API** that implements the required endpoints (`/complete`, `/refine`, `/feedback`, etc.)
2. **Register your API** with the orchestration system using cryptographically signed credentials
3. **Respond to requests** from users and validators through the orchestrator
4. **Get evaluated continuously** on accuracy, speed, and reliability
5. **Earn TAO rewards** based on your performance and usage metrics

---

## Evaluation Mechanism

Validators continuously test miners to ensure quality. Here's how it works:

### Evaluation Types

Subnet 80 supports multiple evaluation types, with **Math Evaluation** being the primary type:

#### 1. Math Evaluation (Primary)
- **Dataset**: mathematical problems
- **Question Types**: Arithmetic, algebra, calculus, word problems
- **Scoring**: Binary (correct/incorrect) based on exact answer matching
- **Frequency**: Continuous rolling window evaluation

#### 2. Additional Types (Future)
- Coding problems with execution validation
- Reasoning tasks with multi-step logic
- Domain-specific knowledge tests

### How Evaluation Works

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Validator selects a test question from verified dataset   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Question sent to ALL miners simultaneously (60s timeout)  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Miner processes question and returns answer               │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Validator checks answer against expected result           │
│    - Correct → Score = 1 (adds to performance)              │
│    - Incorrect/Timeout/Error → Score = 0                    │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Results stored in rolling window (last 120 evaluations)   │
└──────────────────────────────────────────────────────────────┘
```

### Performance Score Calculation

Your **Performance Score** is calculated as:

```
Performance Score = (Correct Answers / Total Evaluations) × 100

Example:
- Total evaluations: 100
- Correct answers: 87
- Performance Score: 87.0%
```

### Rolling Window System

- **Window Size**: 120 evaluations (configurable)
- **Persistence**: Scores saved to disk and survive restarts
- **Continuous Updates**: New evaluations replace oldest ones in the window
- **Fair Comparison**: All miners evaluated on same questions simultaneously

### Evaluation Frequency

- **Continuous**: Evaluations run every 60 seconds (configurable)
- **Concurrent**: All miners tested in parallel (no sequential delays)
- **Timeout**: 60 seconds per miner per question
- **Fair**: Same questions sent to all miners at the same time

### What Happens if You Fail

- ❌ **Timeout**: If your API doesn't respond within 60s → Score = 0 for that question
- ❌ **Error**: If your API returns an error → Score = 0
- ❌ **Wrong Answer**: If answer doesn't match expected → Score = 0
- ⚠️ **Below Threshold**: If performance < 50% → **Stake score zeroed** (see Emission Mechanism)

---

## Emission Mechanism

TAO emissions are distributed based on a **three-component weighted formula**:

### The Emission Formula

```
Final Weight = 0.5 × (Old Scores) + 0.5 × (EPM Score)

Where:
  Old Scores = 0.8 × Performance Score + 0.2 × Trust Score
  
Therefore:
  Final Weight = 0.5 × (0.8 × Performance + 0.2 × Trust) + 0.5 × EPM
  
Simplified:
  Final Weight = 0.40 × Performance + 0.10 × Trust + 0.50 × EPM
```

> **Note**: "Trust Score" refers to TAO delegated TO your miner by validators, not staked BY you.

### Component Breakdown

#### 1. Performance Score (40% weight)
- **What**: Your accuracy on evaluation questions
- **Range**: 0-100%
- **Calculation**: `(Correct Answers / Total Evaluations) × 100`
- **Update**: After every evaluation
- **Impact**: **HIGHEST** - Good performance is essential

**Example**:
```
Correct: 90/100 evaluations
Performance Score: 90.0%
Contribution to weight: 0.40 × 90 = 36 points
```

#### 2. Trust Score (10% weight)
- **What**: Normalized TAO delegated TO your miner by validators
- **Range**: 0-100
- **Calculation**: `(TAO Delegated to You / Max Delegated) × 100`
- **Update**: Every time metagraph syncs
- **Impact**: Low weight, but helps differentiate miners with similar performance
- **Note**: You do NOT stake to the subnet. Validators delegate trust TO you.

**Important**: Trust is **ZEROED** if performance < 50%:
```
if Performance Score < 50%:
    Effective Trust = 0  (trust ignored)
else:
    Effective Trust = Delegated TAO to Your Miner
```

**Example**:
```
TAO Delegated to Your Miner: 100 TAO (from validators)
Max Delegated in Network: 500 TAO
Performance: 87% (above 50% threshold)
Trust Score: (100/500) × 100 = 20.0
Contribution to weight: 0.10 × 20 = 2 points
```

> **Important**: Miners do NOT stake TAO to the subnet themselves. Validators delegate TAO to miners they trust. You only need to register your hotkey on the subnet.

#### 3. EPM Score (50% weight)
- **What**: Edges Per Minute - your usage from real users
- **Range**: 0-100
- **Calculation**: `(Your EPM / Max EPM) × 100`
- **Update**: Continuous (exponential moving average)
- **Impact**: **HIGHEST** - Rewards miners serving real users

**EPM Calculation**:
- **Outside EPM**: Only counts non-evaluation requests (real user traffic)
- **Evaluation EPM**: Excluded from rewards (to prevent gaming)
- **EMA Smoothing**: Uses exponential moving average for stability

**Example**:
```
Your Outside EPM: 15.0 req/min
Max Outside EPM: 30.0 req/min
EPM Score: (15/30) × 100 = 50.0
Contribution to weight: 0.50 × 50 = 25 points
```

### Complete Example

**Scenario**: Your miner's performance

| Component | Your Value | Max Value | Score | Weight | Contribution |
|-----------|------------|-----------|-------|--------|--------------|
| Performance | 87/100 correct | 100% | 87.0 | 40% | 34.8 |
| Trust | 100 TAO delegated | 500 TAO | 20.0 | 10% | 2.0 |
| EPM | 15 req/min | 30 req/min | 50.0 | 50% | 25.0 |
| **Total** | | | | | **61.8** |

Your final weight: **61.8/100**

### Performance Threshold (Critical!)

```
⚠️ PERFORMANCE THRESHOLD: 50%

If your Performance Score < 50%:
  → Trust Score = 0 (delegated TAO ignored in calculations)
  → Only Performance + EPM contribute to weight
  → Significantly reduced weight allocation
  
Stay above 50% to maintain trust benefits!
```

### Weight Setting Process

1. **Scoring Service** calculates all three scores for each miner
2. **Combined scores** computed using the formula above
3. **Validator** sets weights on Bittensor blockchain every 60 seconds
4. **Bittensor** distributes TAO emissions proportionally to weights
5. **Your rewards** = (Your Weight / Total Weights) × Subnet Emissions

### How to Maximize Earnings

| Priority | Action | Impact |
|----------|--------|--------|
| 🔴 **CRITICAL** | Keep performance > 50% | Prevents trust score from being zeroed |
| 🔴 **CRITICAL** | Maximize EPM (real users) | 50% of your weight! |
| 🟡 **IMPORTANT** | Improve accuracy to 80%+ | Strong performance advantage |
| 🟢 **HELPFUL** | Fast response times | Better user experience → more usage |

---

## Getting Started

### Prerequisites

Before you can participate as a miner on Subnet 80, you need:

1. **Bittensor Wallet**: Coldkey and hotkey registered on Subnet 80
   ```bash
   # Create wallet
   btcli wallet new_coldkey --wallet.name miner
   btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default
   
   # Register hotkey on subnet 80 (requires recycled TAO for registration fee)
   btcli subnet register --netuid 80 --wallet.name miner --wallet.hotkey default
   ```
   
   > **Note**: Registration requires a small TAO fee (recycled). You do NOT stake TAO as a miner. Validators delegate trust to you.

2. **LLM Backend**: Choose one:
   - **OpenAI API** (easiest, recommended for beginners)
   - **vLLM** (self-hosted, requires GPU with 4GB+ VRAM)
   - **Custom LLM** (any API-compatible model)

### Installation Steps

#### Option 1: Using Sample Miner (Recommended)

The subnet provides a **reference implementation** that you can deploy directly:

```bash
# 1. Clone the repository
git clone <repository-url>
cd miners/sample-miner-api

# 2. Install dependencies (OpenAI version - no GPU needed)
pip install -r requirements-minimal.txt

# 3. Configure environment
cp .env.example .env
nano .env  # Edit configuration

# 4. Set required values in .env:
API_KEY=<generate-secure-random-key>     # Your miner's API key
LLM_PROVIDER=openai                      # Use OpenAI
OPENAI_API_KEY=sk-your-key-here         # Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini                # Model to use
PORT=8001                                # API port

# 5. Run your miner
python run.py
```

Your miner API will be available at `http://localhost:8001`

#### Option 2: Custom Implementation

You can implement your own miner from scratch. See [API Requirements](#api-requirements) section for details.

### Testing Your Miner

Before registering, test your miner locally:

```bash
# 1. Launch the test UI
python examples/gradio_test_ui.py

# 2. Open in browser
http://localhost:7860

# 3. Test all endpoints:
   - /complete - Basic completion
   - /feedback - Output analysis
   - /refine - Output improvement
   - /summary - Summarization
   - /aggregate - Voting
```

### Deploying to Production

1. **Get a VPS** (minimum requirements):
   - 2 CPU cores
   - 4GB RAM
   - 20GB storage
   - Ubuntu 22.04 LTS

---

## API Requirements

All miners must implement the following REST API endpoints:

### Core Endpoints

#### 1. `/complete` - Main Completion Endpoint
**Method**: `POST`

**Purpose**: Generate AI agent response with conversation history and playbook context

**Request Body**:
```json
{
  "cid": "conversation-id-123",
  "task": "Answer the user's question accurately",
  "input": [
    {
      "user_query": "What is the capital of France?"
    }
  ],
  "use_conversation_history": true,
  "use_playbook": true
}
```

**Response**:
```json
{
  "response": "The capital of France is Paris.",
  "metadata": {
    "execution_time": 1.23,
    "model": "gpt-4o-mini",
    "tokens_used": 150
  }
}
```

#### 2. `/refine` - Output Refinement
**Method**: `POST`

**Purpose**: Improve outputs based on feedback

**Request Body**:
```json
{
  "cid": "conversation-id-123",
  "task": "Refine the previous output",
  "input": [
    {
      "original_output": "Paris.",
      "feedback": "Please provide more context and historical information"
    }
  ]
}
```

#### 3. `/feedback` - Output Analysis
**Method**: `POST`

**Purpose**: Analyze output quality and provide structured feedback

**Request Body**:
```json
{
  "cid": "conversation-id-123",
  "task": "Analyze this output",
  "input": [
    {
      "output_to_analyze": "Paris is the capital."
    }
  ]
}
```

#### 4. `/human_feedback` - User Feedback Processing
**Method**: `POST`

**Purpose**: Process user feedback and update playbook

**Request Body**:
```json
{
  "cid": "conversation-id-123",
  "task": "Process user feedback",
  "input": [
    {
      "feedback_text": "I prefer more detailed historical context"
    }
  ]
}
```

#### 5. `/summary` - Summarization
**Method**: `POST`

**Purpose**: Generate summaries of previous outputs

#### 6. `/aggregate` - Majority Voting
**Method**: `POST`

**Purpose**: Perform majority voting on multiple outputs

#### 7. `/internet_search` - Web Search (Optional)
**Method**: `POST`

**Purpose**: Search the internet for information

### System Endpoints

#### 1. `/health` - Health Check
**Method**: `GET`

**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T10:30:00Z"
}
```

#### 2. `/capabilities` - Miner Metadata
**Method**: `GET`

**Authentication**: Required

**Response**:
```json
{
  "miner_version": "1.0.0",
  "model": "gpt-4o-mini",
  "features": ["conversation_history", "playbook", "internet_search"],
  "max_context_length": 8000
}
```

### Authentication

All endpoints (except `/health`) require authentication via `X-API-Key` header:

```bash
curl -X POST https://your-miner.com/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key" \
  -d '{"cid": "test", "task": "...", "input": [...]}'
```

### Response Format

All endpoints must return JSON with this structure:

```json
{
  "response": "The actual response text",
  "metadata": {
    "execution_time": 1.23,
    "model": "gpt-4o-mini",
    "any_other_fields": "optional"
  }
}
```

### Error Handling

Return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid input)
- `401` - Unauthorized (missing/invalid API key)
- `500` - Internal server error

Error response format:
```json
{
  "error": "Error message describing what went wrong",
  "details": "Optional additional details"
}
```

---

## Registration Process

### Step-by-Step Registration

#### 1. Install Bittensor SDK

```bash
python3 -m pip install --upgrade bittensor
```

#### 2. Generate Signed Credentials

Use the `encrypt.py` script from the sample-miner-api:

```bash
cd miners/sample-miner-api

python encrypt.py \
  --name <your-wallet-name> \
  --api-url <your-public-miner-url> \
  --token <your-api-key> \
  --output signed_credentials.txt
```

**Example**:
```bash
python encrypt.py \
  --name miner_wallet \
  --api-url https://my-miner.example.com \
  --token AbCdEf123456SecureRandomKey32Chars \
  --output signed_credentials.txt
```

**What happens**:
- ✅ Prompts for your wallet password
- ✅ Creates cryptographic signature using your coldkey
- ✅ Generates `signed_credentials.txt` containing:
  - Your API URL and API key
  - Your SS58 wallet address (coldkey)
  - Cryptographic signature
  - Timestamp

#### 3. Submit to Registration Portal

1. Open the registration portal:
   **https://huggingface.co/spaces/agent-builder/miner-registration-system**

2. Open your `signed_credentials.txt` file

3. Copy the entire contents

4. Paste into the registration form

5. Click **Submit**

#### 4. Registration Verification

The orchestrator will:
- ✅ Verify cryptographic signature against your coldkey
- ✅ Test connectivity to your API endpoint
- ✅ Validate `/health` endpoint (must return 200)
- ✅ Validate `/capabilities` endpoint
- ✅ Register your miner if all checks pass

**Success**:
```
✅ Registration successful!
Your miner is now active and will start receiving requests.
```

**Failure reasons**:
- ❌ Invalid signature (check wallet name/password)
- ❌ API not reachable (check firewall/SSL)
- ❌ Invalid credentials format
- ❌ Wallet not registered on subnet 80

#### 5. Verify Registration

After successful registration:

```bash
# Check if your miner appears in the active miners list
curl https://agent-api-manager-url/api/miners/active
```

Your coldkey should appear in the list.

### Security Notes

- 🔐 **Signature Security**: Your signature is cryptographically tied to your wallet
- ⚠️ **Keep Private**: Store `signed_credentials.txt` securely (contains your API key)
- 🔄 **Rotate Keys**: Regularly update your API key and re-register
- ✅ **Tamper-Proof**: Any modification to credentials invalidates the signature

---

## Monitoring Your Miner

### Official Monitoring Dashboard

**🌐 https://agentbuilder80.com/index.html#/monitor**

This dashboard shows:
- 📊 **Performance Scores**: Your accuracy on evaluations
- 💎 **Stake Scores**: Your normalized stake ranking
- ⚡ **EPM Scores**: Your usage metrics (edges per minute)
- 🏆 **Combined Weights**: Your final weight for emissions
- 📈 **Rankings**: Your position compared to other miners

### Understanding Your Metrics

#### Performance Tab
```
Coldkey: 5F3sa2TJA...
Total Evaluated: 120
Correct Answers: 104
Performance Score: 86.67%
Last Updated: 2025-11-24 10:30:00
```

#### EPM Tab
```
Coldkey: 5F3sa2TJA...
Total Edges: 1,534
Successful Edges: 1,502
Failed Edges: 32
Edges Per Minute: 12.45 req/min
EPM Score: 41.50
Avg Execution Time: 1,234 ms
Last Updated: 2025-11-24 10:30:00
```

**What to look for**:
- Higher EPM = more user traffic = 50% of your weight!
- Low failed edges = good reliability
- Fast execution time = better user experience

#### All Scores Tab
```
Rank: 3
Coldkey: 5F3sa2TJA...
Performance: 86.67
Trust: 22.45
EPM: 41.50
Combined: 64.72
```

**Combined Weight Breakdown**:
```
64.72 = 0.40 × 86.67 (performance)
      + 0.10 × 22.45 (trust from validators)
      + 0.50 × 41.50 (EPM)
```
---

## Optimization Tips

### 1. Improve Performance Score

**Priority: CRITICAL** (40% of weight + needed for stake)

#### Accuracy Tips:
- ✅ Use a high-quality LLM (GPT-4, Claude, or fine-tuned models)
- ✅ Implement proper prompt engineering for math problems
- ✅ Add validation logic to check answer formats
- ✅ Use chain-of-thought reasoning for complex questions
- ✅ Test your miner on the evaluation dataset beforehand

#### Example Prompt Engineering:
```python
system_prompt = """You are a precise mathematical assistant.
Always show your step-by-step reasoning.
Provide the final answer in the format: ANSWER: [number]"""

# This helps the LLM structure responses correctly
```

#### Response Time Optimization:
- ✅ Use fast models (e.g., `gpt-4o-mini` vs `gpt-4o`)
- ✅ Cache frequent queries
- ✅ Optimize your code for speed
- ✅ Use connection pooling for API calls

### 2. Maximize EPM Score

**Priority: CRITICAL** (50% of weight!)

### 3. Cost Optimization

#### If Using OpenAI:
- Use `gpt-4o-mini` instead of `gpt-4o` (much cheaper)
- Implement smart context windowing (don't send full history)
- Cache common responses
- Set max_tokens limit to avoid runaway costs

**Example**:
```python
# Smart context management
MAX_HISTORY = 5  # Last 5 messages only
conversation_history = conversation_history[-MAX_HISTORY:]

# Set token limits
max_tokens = 500  # Enough for most responses, limits cost
```

#### If Using vLLM:
- Use quantized models (AWQ, GPTQ) for lower VRAM
- Batch requests for better GPU utilization
- Use tensor parallelism if you have multiple GPUs

---

## FAQ

### General Questions

**Q: What is Subnet 80?**  
A: A Bittensor subnet for conversational AI agents. Miners provide agent APIs, validators evaluate quality, and TAO emissions are distributed based on performance, stake, and usage.

**Q: What rewards can I receive?**  
A: Reward allocation depends on your weight (performance + trust + EPM) relative to other miners in the research network. **IMPORTANT**: There are NO guarantees of rewards, earnings, or profitability. This is an experimental research platform with variable and unpredictable outcomes. Participation may result in net costs. This is NOT financial advice.

**Q: Do I need a GPU?**  
A: No, if you use OpenAI API or other cloud LLM providers. Yes, if you want to self-host with vLLM (requires 4GB+ VRAM).

**Q: Can I change my API URL after registration?**  
A: Yes, generate new signed credentials and re-register.

**Q: What if my API goes down?**  
A: Your miner will receive 0 scores during downtime. Get it back online ASAP. Consider setting up monitoring alerts.

### Evaluation Questions

**Q: How often am I evaluated?**  
A: Continuously. Validators send test questions approximately every 60 seconds.

**Q: What happens if I timeout?**  
A: That evaluation counts as incorrect (score = 0). Ensure your API responds within 60 seconds.

**Q: Why is my performance score low?**  
A: Common reasons:
- LLM model not good at math
- Timeout issues (slow responses)
- API errors or crashes
- Incorrect answer formatting

### Reward Allocation Questions

**Q: Why is my trust score 0?**  
A: Your performance score is below 50%. Improve accuracy to restore trust benefits. Remember: you don't stake TAO as a miner; validators delegate trust to you.

**Q: How can I increase EPM?**  
A: Attract real users by:
- Building a public interface
- Creating chatbots (Discord, Telegram)
- Partnering with applications
- Providing excellent user experience

**Q: When are rewards distributed?**  
A: Validators set weights approximately every 60 seconds. The Bittensor network distributes emissions based on these weights. **Note**: Rewards are not guaranteed and depend on network conditions, validator participation, and overall subnet performance.

### Technical Questions

**Q: What programming language should I use?**  
A: Python is recommended (sample implementation provided). Any language that can create a REST API works.

**Q: Do I need to implement all endpoints?**  
A: Yes, all endpoints must return valid responses. Use the sample miner as a template.

**Q: Can I customize the sample miner?**  
A: Absolutely! The sample is a starting point. Customize the LLM, prompts, logic, etc.

**Q: How do I handle conversation history?**  
A: Store per-conversation in a database (SQLite, PostgreSQL). Sample miner includes SQLite implementation.

**Q: What's a playbook?**  
A: A system for storing user preferences and insights. Helps personalize responses. Included in sample miner.

### Optimization Questions

**Q: Should I use GPT-4 or GPT-4o-mini?**  
A: Start with `gpt-4o-mini` (cheaper, faster). Upgrade to `gpt-4o` if performance is too low.

**Q: How much RAM does my server need?**  
A: 4GB minimum, 8GB recommended for OpenAI API version. More if self-hosting LLM.

**Q: Can I run multiple miners?**  
A: Yes, but each needs a separate wallet, API endpoint, and API key.

**Q: Should I focus on performance or EPM first?**  
A: **Performance first** (get above 50%), then EPM. Without good performance, trust delegations from validators won't benefit you.

### Key Success Factors

1. **Performance > 50%** (Critical - enables trust benefits)
2. **High EPM** (50% of weight - attract users!)
3. **Reliability** (high uptime target)
4. **Fast Responses** (< 3 seconds ideal)
5. **Low Error Rate** (< 1% failures)

---

## ⚠️ Important Legal Disclaimers

### Research Participation
- This is an **experimental research platform** for studying decentralized AI systems
- No guarantees of functionality, availability, or performance
- Network behavior and rules may change
- Participation is at your own risk

### Financial Disclaimers
- **NOT INVESTMENT ADVICE**: Nothing in this document constitutes financial, investment, or legal advice
- **NO GUARANTEES**: No guarantees of rewards, earnings, profits, or returns of any kind
- **POTENTIAL LOSSES**: You may incur net costs from infrastructure, API fees, and computational resources
- **CONSULT PROFESSIONALS**: Consult appropriate financial, legal, and tax professionals before participating
- **YOUR RESPONSIBILITY**: You are solely responsible for understanding risks and making informed decisions

### Miner Staking Clarification
- **Miners do NOT stake TAO to the subnet**
- You only register your hotkey (small registration fee)
- **Validators delegate TAO TO miners** they trust
- You have no control over validator delegation decisions
- Delegation amounts can change at any time

### Technical Risks
- Network instability and downtime
- Smart contract risks
- Blockchain risks
- API and infrastructure costs
- Data security responsibilities
- No warranty of any kind (provided "AS IS")

### Your Responsibilities
- Securing your wallet and credentials
- Validating all inputs to prevent attacks
- Monitoring costs and resource usage
- Understanding and accepting all risks
- Compliance with applicable laws

---

**Participate responsibly in Subnet 80 research! 🚀**

*For questions and support, join the Bittensor community Discord or open an issue on GitHub.*

---

*Last Updated: November 24, 2025*  
*Subnet: 80 (Agent Network)*  
*Version: 1.0*
