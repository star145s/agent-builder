**Welcome to AI Agent Builder - Subnet 80 Research Platform! 🚀**

---

*This is experimental research infrastructure. By using this platform, you acknowledge that it is provided for research and educational purposes without warranties or guarantees of any kind.*ittensor wallet, optional alpha stake for higher rate limits |
| **Participant** | Test and use experimental features | None (handled by applications) |ized AI agent networks powered by Bittensor**

> ⚠️ **RESEARCH PROJECT** - This is an experimental research tool for exploring decentralized AI agent architectures. Use for research, development, and educational purposes only.

[![Bittensor](https://img.shields.io/badge/Bittensor-Subnet%2080-blue)](https://bittensor.com)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Research](https://img.shields.io/badge/status-research-orange.svg)](https://github.com/star145s/agent-builder)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [What is Subnet 80?](#what-is-subnet-80)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
  - [🛠️ For Miners](#-for-miners)
  - [✅ For Validators](#-for-validators)
  - [👨‍💻 For Developers](#-for-developers)
- [Repository Structure](#repository-structure)
- [Quick Links](#quick-links)

---

## 🎯 Overview

**AI Agent Builder** is a research platform on Bittensor Subnet 80 for exploring decentralized AI agent architectures. This experimental network enables researchers and developers to:

- Study distributed AI systems at scale
- Test novel agent coordination mechanisms  
- Explore cryptographic authentication patterns
- Research fair resource allocation models

### Network Participants

- **Miners**: AI service providers implementing standardized APIs
- **Validators**: Weight setters that evaluate miner performance
- **Developers**: Researchers building experimental applications
- **End Users**: Participants testing AI-powered workflows

### Research Focus Areas

- 🔌 **Unified API Interface**: Standardized component API for interoperability research
- 💬 **Conversation History**: Context management for multi-turn interaction studies
- 📚 **Playbook System**: Learning user preferences and insights over time
- ⚖️ **Stake-Based Access**: Fair resource allocation based on alpha token stakes
- 🏗️ **Graph Execution**: Complex multi-agent workflow orchestration
- 🔐 **Wallet-Based Auth**: Bittensor cryptographic authentication patterns

### ⚠️ Research & Development Only

**This platform is for research purposes:**
- ✅ Academic research and experimentation
- ✅ Educational and learning projects
- ✅ Proof-of-concept development
- ✅ Testing decentralized AI architectures
- ❌ NOT for production applications
- ❌ NOT for high-volume commercial use
- ❌ NO guarantees of availability or performance

---

## 🌐 What is Subnet 80?

**Subnet 80** is a Bittensor subnet that provides:

1. **Decentralized AI Infrastructure**: Miners compete to provide high-quality AI responses
2. **Fair Reward Distribution**: Validators score miners based on performance
3. **Open Competition**: Anyone can join as a miner or validator
4. **Cryptographic Security**: Bittensor wallet-based authentication and signing

### Network Roles

| Role | Description | Requirements |
|------|-------------|--------------|
| **Miner** | Run AI services and earn rewards | Bittensor wallet, API implementation, registration on subnet 80 |
| **Validator** | Set weights and earn rewards | Bittensor wallet, TAO stake, registration on subnet 80 |
| **Developer** | Build applications | Bittensor wallet, optional alpha stake for higher rate limits |
| **User** | Use applications | None (applications handle authentication) |

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     BITTENSOR SUBNET 80                        │
│                   AI Agent Builder Network                      │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐       ┌──────────────────┐                  │
│  │  End Users   │──────▶│  Applications    │                  │
│  │ (Consumers)  │       │  (Developers)    │                  │
│  └──────────────┘       └────────┬─────────┘                  │
│                                   │                            │
│                    ┌──────────────▼────────────┐               │
│                    │   Agent API Manager      │               │
│                    │    (Orchestrator)         │               │
│                    │  - Routes requests        │               │
│                    │  - Tracks performance     │               │
│                    │  - Provides scoring API   │               │
│                    └──────────┬────────────────┘               │
│                               │                                │
│           ┌───────────────────┼────────────────────┐           │
│           │                   │                    │           │
│      ┌────▼─────┐       ┌────▼─────┐       ┌─────▼────┐      │
│      │ Miner 1  │       │ Miner 2  │  ...  │ Miner N  │      │
│      │ UID: 0   │       │ UID: 1   │       │ UID: N   │      │
│      │          │       │          │       │          │      │
│      │ GPT-4o   │       │ Claude   │       │ Custom   │      │
│      │ + Tools  │       │ + RAG    │       │  Model   │      │
│      └────┬─────┘       └────┬─────┘       └────┬─────┘      │
│           │                  │                   │            │
│           └──────────────────┼───────────────────┘            │
│                              │                                │
│                    ┌─────────▼──────────┐                     │
│                    │  Validators        │                     │
│                    │  - Fetch weights   │                     │
│                    │  - Set on-chain    │                     │
│                    └────────────────────┘                     │
│                              │                                │
│                    ┌─────────▼──────────┐                     │
│                    │ Bittensor Blockchain│                     │
│                    │ - Weight consensus  │                     │
│                    │ - TAO distribution  │                     │
│                    └─────────────────────┘                     │
└────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Agent API Manager (Orchestrator)**: 
   - Routes user requests to miners
   - Tracks miner performance and quality
   - Provides scoring API for validators
   - Manages stake-based rate limiting

2. **Miners**: 
   - Independent AI service providers
   - Implement standardized component API
   - Compete for rewards based on quality
   - Must register on Subnet 80

3. **Validators**: 
   - Fetch performance scores from orchestrator
   - Submit weights to Bittensor blockchain
   - Earn rewards proportional to stake
   - Must have TAO stake

4. **Researchers/Developers**: 
   - Build experimental applications using the API
   - Authenticate with Bittensor wallets
   - Rate limited based on alpha stake
   - Access distributed miner network for research

---

## 🚀 Getting Started

### 🛠️ For Miners

**Want to run an AI service and earn rewards?**

👉 **Go to: [`sample-miner-api/`](./sample-miner-api/)**

The `sample-miner-api/` folder contains a complete reference implementation showing how to:

- ✅ Implement the required unified component API
- ✅ Set up conversation history management
- ✅ Configure OpenAI or vLLM backends
- ✅ Register your miner on the network
- ✅ Sign credentials with Bittensor wallet
- ✅ Test your API with Gradio UI

**Quick Start:**
```bash
cd sample-miner-api
pip install -r requirements-minimal.txt
cp .env.example .env
# Edit .env with your API keys
python run.py
```

**📖 Full Documentation:** [`sample-miner-api/README.md`](./sample-miner-api/README.md)

**Key Topics:**
- API endpoint implementation
- Registration process
- Security best practices
- Testing your miner
- Deployment guide

---

### ✅ For Validators

**Want to earn rewards by validating miners?**

👉 **Go to: [`validator/`](./validator/)**

The `validator/` folder contains a simple auto weight setter that:

- ✅ Fetches miner performance scores from the orchestrator
- ✅ Submits weights to Bittensor blockchain
- ✅ Runs continuously with configurable intervals
- ✅ Requires TAO stake for weight setting

**Quick Start:**
```bash
cd validator
pip install bittensor requests
python validator.py --wallet my_wallet --hotkey default
```

**📖 Full Documentation:** [`validator/README.md`](./validator/README.md)

**Key Topics:**
- Validator setup
- TAO staking requirements
- Weight submission process
- Monitoring and maintenance

---

### 👨‍💻 For Developers/Researchers

**Want to experiment with the miner network for research?**

👉 **Go to: [`developer/`](./developer/)**

The `developer/` folder contains the Public API documentation showing how to:

- ✅ Authenticate with Bittensor wallet signatures
- ✅ Execute AI agent workflows
- ✅ Export workflows from the Builder UI
- ✅ Handle stake-based rate limiting
- ✅ Build experimental applications and research tools

> **Note**: This API is for research and development only. See fair use policy in the documentation.

**📖 Full Documentation:** [`developer/document.md`](./developer/document.md)

---

## 📁 Repository Structure

```
agent-builder/
├── README.md                    # ← You are here! Main guide
│
├── sample-miner-api/            # 🛠️ FOR MINERS
│   ├── README.md               # Complete miner implementation guide
│   ├── src/                    # Source code for reference miner
│   │   ├── api/               # FastAPI endpoints
│   │   ├── core/              # Core logic (conversation, playbook)
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # Business logic (LLM, components)
│   │   └── utils/             # Utilities
│   ├── examples/              # Test tools
│   │   ├── gradio_test_ui.py # Interactive test interface
│   │   └── quick_vllm.py     # vLLM deployment helper
│   ├── encrypt.py             # Wallet signing tool for registration
│   ├── run.py                 # Server launcher
│   ├── requirements.txt       # Full dependencies (with vLLM)
│   └── requirements-minimal.txt # Minimal dependencies (OpenAI only)
│
├── validator/                   # ✅ FOR VALIDATORS
│   ├── README.md               # Validator setup and operation guide
│   └── validator.py            # Auto weight setter script
│
└── developer/                   # 👨‍💻 FOR DEVELOPERS
    └── document.md              # Public API developer documentation
```

---

## 🔗 Quick Links

### 🌐 Web Interfaces

| Resource | URL | Description |
|----------|-----|-------------|
| **Builder UI** | Released | Design agent workflows visually |
| **Miner Registration** | https://huggingface.co/spaces/agent-builder/miner-registration-system | Register your miner API |
| **Scoring API** | https://agentbuilder80.com/index.html#/monitor | View miner performance scores |
| **Public API** | https://agent-builder-agent-builder-dev-api.hf.space | Execute workflows programmatically |

### 📚 Documentation

| Role | Documentation | Quick Start |
|------|---------------|-------------|
| **Miners** | [`sample-miner-api/README.md`](./sample-miner-api/README.md) | [Miner Quick Start](#-for-miners) |
| **Validators** | [`validator/README.md`](./validator/README.md) | [Validator Quick Start](#-for-validators) |
| **Researchers/Developers** | [`developer/document.md`](./developer/document.md) | [Developer Quick Start](#-for-developersresearchers) |

### 🔧 Prerequisites

| Role | Requirements |
|------|-------------|
| **Miners** | • Python 3.10+<br>• Bittensor wallet<br>• OpenAI API key OR GPU (4GB+ VRAM)<br>• Registration on Subnet 80 |
| **Validators** | • Python 3.10+<br>• Bittensor wallet<br>• TAO stake<br>• Registration on Subnet 80 |
| **Researchers/Developers** | • Python 3.10+<br>• Bittensor wallet<br>• Optional: Alpha stake for higher rate limits<br>• Research/educational use only |

---

## 🤝 Getting Help

### Support Channels

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check role-specific README files
- **Security Issues**: Report privately (do not share wallet keys publicly)

### Common Questions

**Q: How do I register on Subnet 80?**
- Miners: See [`sample-miner-api/README.md`](./sample-miner-api/README.md) → "Registering Your Miner"
- Validators: See [`validator/README.md`](./validator/README.md) → "Prerequisites"

**Q: Do I need alpha stake to use the API?**
- No, but it increases your rate limit proportionally

**Q: Can I customize the miner implementation?**
- Yes! You can completely re-implement the architecture. You only need to follow the API interface.

**Q: Can I use this for production applications?**
- No. This is a research platform for experimentation and learning only. Not suitable for production use.

**Q: Are there any guarantees of service availability?**
- No. This is experimental research infrastructure with no SLA or availability guarantees.

---

## ⚖️ Important Disclaimers

### Research Use Only

This platform is provided for **research and educational purposes only**:

- ❌ **NOT** for production applications
- ❌ **NOT** for commercial use at scale
- ❌ **NO** guarantees of availability, accuracy, or performance
- ❌ **NO** warranty of any kind (provided "AS IS")

### Financial Disclaimers

- Token staking is **NOT** an investment or financial transaction
- No guarantees of profit or returns
- Token values may fluctuate
- You retain ownership of staked tokens
- Blockchain risks apply (smart contract risks, network risks, etc.)
- **This is NOT financial advice** - consult professionals before staking

### Liability

- Users are responsible for their own implementations and security
- Miners responsible for validating inputs and protecting infrastructure
- No liability for data loss, damages, or losses from platform use
- AI outputs may be inaccurate - always verify critical information

### Data & Privacy

- Requests are routed to third-party miners who may log data
- Do NOT send sensitive or confidential information
- We do not store workflow prompts or AI responses
- Authentication uses cryptographic signatures (no passwords stored)

---

## 📄 License

See [LICENSE](./LICENSE) file for details.

---
