# 🚨 SOP Violation Flagger

> Real-time Slack compliance monitoring system that automatically detects and flags Standard Operating Procedure (SOP) violations using AI-powered semantic search and LLM reasoning.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Demo](#demo)
- [Contributing](#contributing)

---

## 🎯 Overview

SOP Violation Flagger is an intelligent compliance monitoring system designed for teams that need to enforce Standard Operating Procedures in real-time. It continuously monitors Slack conversations, uses semantic search to find relevant SOPs from your Notion workspace, and leverages GPT-4o-mini to determine if messages violate any policies.

### **The Problem**

- Manual compliance monitoring is time-consuming and error-prone
- SOPs stored in Notion are often overlooked or forgotten
- Policy violations can go unnoticed until it's too late
- Training new team members on all SOPs is challenging

### **The Solution**

An AI-powered bot that:
- ✅ Monitors all Slack channels in real-time
- ✅ Retrieves relevant SOPs using vector similarity search
- ✅ Analyzes messages against company policies using LLM reasoning
- ✅ Instantly flags violations with specific rule citations
- ✅ Provides educational feedback to prevent future violations

---

## ✨ Features

### **Real-time Monitoring**
- 🔴 **Live Slack Integration** - Monitors all channels the bot is invited to
- ⚡ **Sub-second Response** - Flags violations within 1-3 seconds
- 🎯 **Context-Aware** - Understands nuance and intent, not just keywords

### **Proactive Compliance**
- 📋 **Slash Command** - `/check-sop <message>` to preview before posting
- 📊 **Analytics in Slack** - `/sop-analytics` or `/sop-analytics 2025-01-01` for violation stats
- 📬 **Onboarding DMs** - New users receive key SOP reminders automatically

### **Analytics & Feedback**
- 📊 **Analytics API** - `GET /analytics/stats`, `GET /analytics/violations`, `GET /analytics/export`
- 📈 **CLI Reports** - `python cli.py report` or `report --format csv -o violations.csv`
- 👍 **Feedback Loop** - React :x: (false positive) or :white_check_mark: (correct) on violation messages
- 🧠 **Learns from Feedback** - Uses dynamic few-shot learning: recent feedback examples are injected into the LLM prompt so it improves over time

### **Intelligent Detection**
- 🧠 **RAG-Powered** - Uses Retrieval-Augmented Generation for accurate detection
- 📊 **Semantic Search** - Finds relevant SOPs even with different wording
- 🎓 **LLM Reasoning** - GPT-4o-mini evaluates compliance with human-like understanding

### **Flexible Management**
- 📝 **Notion Sync** - Automatically imports SOPs from Notion workspace
- 🔄 **Smart Upsert** - Updates existing documents, adds new ones without duplicates
- 🗑️ **Easy Cleanup** - Clear and re-sync vector database with one command

### **Developer-Friendly**
- 🚀 **FastAPI Backend** - RESTful API for custom integrations
- 🛠️ **CLI Tools** - Convenient command-line interface
- 📚 **Comprehensive Docs** - Detailed documentation and testing guides

---

## 🛠️ Tech Stack

### **Backend & API**
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework for API
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server for production deployment

### **AI & Machine Learning**
- **[OpenAI GPT-4o-mini](https://openai.com/)** - LLM for compliance reasoning
- **[OpenAI text-embedding-3-small](https://openai.com/)** - Text embeddings (1024 dimensions)
- **[Pinecone](https://www.pinecone.io/)** - Vector database for semantic search

### **Integrations**
- **[Slack SDK](https://slack.dev/python-slack-sdk/)** - Real-time message streaming via Socket Mode
- **[Notion API](https://developers.notion.com/)** - Document retrieval and sync

### **Core Libraries**
- **[Pydantic](https://pydantic.dev/)** - Data validation and settings management
- **[Python-dotenv](https://github.com/theskumar/python-dotenv)** - Environment configuration
- **[Requests](https://requests.readthedocs.io/)** - HTTP client

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Phase 1: Data Ingestion                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Notion SOPs ──► notion_connector.py ──► ingest_notion.py       │
│                           │                      │                │
│                           ▼                      ▼                │
│                   FastAPI /ingest ──► OpenAI Embeddings          │
│                           │                      │                │
│                           ▼                      ▼                │
│                   Pinecone Vector DB (1024-dim vectors)          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                Phase 2: Real-time Monitoring                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Slack Message ──► slack_connector.py ──► slack_bot.py          │
│       │                                           │               │
│       ▼                                           ▼               │
│  Socket Mode                          FastAPI /check-message     │
│  WebSocket                                       │               │
│                                                  ▼               │
│                                      Pinecone Similarity Search  │
│                                      (Top-3 relevant SOPs)       │
│                                                  │               │
│                                                  ▼               │
│                                      GPT-4o-mini Evaluation      │
│                                      (Violation Detection)       │
│                                                  │               │
│                                    ┌─────────────┴────────────┐  │
│                                    │                          │  │
│                                    ▼                          ▼  │
│                              Violated?                  Compliant │
│                                    │                          │  │
│                                    ▼                          ▼  │
│                         Format Warning                   Silent  │
│                                    │                             │
│                                    ▼                             │
│                         Send to Slack Channel                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Notion Connector** - Reads SOP documents from Notion workspace
- **FastAPI Backend** - REST API for ingestion and compliance checks
- **Pinecone Vector DB** - Stores and retrieves document embeddings
- **Slack Connector** - Streams messages and sends responses
- **Compliance Bot** - Orchestrates the detection pipeline

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical documentation.

---

## 🚀 Quick Start

### **1. Setup Environment**

```bash
# Clone and navigate to project
cd SOP-violation-flagger

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Configure API Keys**

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX=sop-index
PINECONE_INDEX_HOST=https://sop-index-xxx.svc.pinecone.io

# Slack (for bot)
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

# Notion (for document ingestion)
NOTION_API_KEY=secret_...
```

**⚠️ Important:** Your Pinecone index must use **1024-dimension vectors** to match OpenAI text-embedding-3-small.

### **3. Verify Setup**

```bash
python cli.py check-setup
```

This validates all API keys and connections.

### **4. Ingest SOPs from Notion**

```bash
# Start the backend server (in terminal 1)
python cli.py start-server

# Ingest Notion pages (in terminal 2)
python cli.py ingest-notion
```

### **5. Start Slack Bot**

```bash
python cli.py start-bot
```

The bot will now monitor all Slack channels it's invited to and automatically flag violations! 🎉

---

## 📚 Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup guide for Slack, Notion, and Pinecone
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and design decisions
- **[API.md](API.md)** - Complete API reference and endpoints
- **[TESTING.md](TESTING.md)** - Testing guide and expected outputs

---

## 🎬 Demo

### **Example Violation Detection**

**Slack Message:**
```
Hey team, use this password for prod: admin123
```

**Bot Response:**
```
🔴 SOP Violation Detected (HIGH)

Rule Violated: Credential sharing in public channels

Why this is a violation:
Production credentials must never be shared in Slack channels. 
Use a secure password manager instead.

Original message:
> Hey team, use this password for prod: admin123

Please review our SOPs and ensure compliance.
```

### **Smart Upsert Demonstration**

First ingestion:
```bash
$ python cli.py ingest-notion
✅ Added new document: 'Data Security Policy'
✅ Added new document: 'Communication Guidelines'

✅ Ingestion complete!
  - Added: 2 documents
  - Updated: 0 documents
```

Re-ingestion after editing one SOP:
```bash
$ python cli.py ingest-notion
🔄 Updated existing document: 'Data Security Policy'
⏭️  Skipped unchanged document: 'Communication Guidelines'

✅ Ingestion complete!
  - Added: 0 documents
  - Updated: 1 document
  - Note: Other documents in Pinecone remain untouched
```

---

## 🛠️ CLI Commands

The project includes a unified CLI for convenience:

```bash
# Check if all API keys and services are configured
python cli.py check-setup

# Start FastAPI backend server
python cli.py start-server

# Start Slack compliance bot
python cli.py start-bot

# Ingest all Notion pages as SOPs
python cli.py ingest-notion

# Ingest a single file
python cli.py ingest-file sop.txt --doc-id sop-001 --title "Company SOPs"

# Clear all vectors from Pinecone (with safety confirmation)
python cli.py clear-pinecone
```

---

## 📂 Project Structure

```
SOP-violation-flagger/
├── app/                          # FastAPI backend
│   ├── main.py                  # Application entry point
│   ├── config.py                # Environment settings
│   ├── services/
│   │   ├── pinecone_svc.py      # Vector database operations
│   │   ├── embeddings.py        # OpenAI embeddings (1024-dim)
│   │   └── llm.py               # GPT-4o-mini violation detection
│   ├── models/                  # Pydantic schemas
│   │   ├── ingest.py            # Ingestion request/response
│   │   └── check.py             # Compliance check schemas
│   └── routers/                 # API endpoints
│       ├── ingest.py            # POST /ingest
│       └── check.py             # POST /check-message
│
├── slack_bot.py                 # Real-time Slack monitor
├── ingest_notion.py             # Notion → Pinecone batch import
├── ingest_file.py               # Single file ingestion
├── clear_pinecone.py            # Database clearing utility
├── cli.py                       # Unified CLI interface
├── slack_connector.py           # Slack Socket Mode client
├── notion_connector.py          # Notion API client
│
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── README.md                    # This file
├── SETUP.md                     # Detailed setup guide
├── ARCHITECTURE.md              # Technical architecture
├── API.md                       # API reference
└── TESTING.md                   # Testing guide
```

---

## 🔧 How It Works

### **Phase 1: Data Ingestion**

1. **Fetch SOPs** - Notion connector retrieves all pages your integration can access
2. **Generate Embeddings** - OpenAI text-embedding-3-small creates 1024-dim vectors
3. **Smart Upsert** - Check if document exists in Pinecone
   - If new → add to database
   - If exists → update vector and metadata
4. **Store** - Vectors saved to Pinecone with rich metadata (title, content, source)

### **Phase 2: Real-Time Monitoring**

1. **Stream Messages** - Slack bot listens via Socket Mode WebSocket
2. **Semantic Search** - Embed message and find top-3 similar SOPs in Pinecone
3. **Fetch Feedback Examples** - Retrieve recent user feedback (false positives + correct flags) from SQLite
4. **LLM Evaluation** - Send message + retrieved SOPs + feedback examples to GPT-4o-mini
   - Prompt includes few-shot examples: "FALSE POSITIVE: don't flag X" / "CORRECT: do flag Y"
   - Response: JSON with {violated, rule, severity, explanation}
5. **Response** - If violation detected, format and post warning to Slack
6. **Feedback** - Users react :x: or :white_check_mark:; stored for future few-shot learning

### **Key Features**

- **Idempotent Ingestion** - Re-running ingestion only updates changed documents
- **Context-Aware** - RAG ensures LLM has relevant SOPs for accurate evaluation
- **Learns from Feedback** - Dynamic few-shot: up to 6 recent feedback examples (3 false positive + 3 correct) are injected into each check; model improves as users correct it
- **Asynchronous** - Backend server and bot run independently
- **Extensible** - REST API allows custom integrations beyond Slack

---

## 🚨 Troubleshooting

### **Server Issues**

**"Port 8000 already in use"**
```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9
python cli.py start-server
```

**"Cannot connect to API"**
- Verify server is running: `curl http://localhost:8000/`
- Check terminal for error messages
- Ensure virtual environment is activated

### **Slack Integration**

**"Slack connection failed"**
- Verify Socket Mode is enabled in Slack App settings
- Check both tokens are correct: `SLACK_BOT_TOKEN` (xoxb-) and `SLACK_APP_TOKEN` (xapp-)
- Ensure bot has required OAuth scopes (see [SETUP.md](SETUP.md))
- Invite bot to channels: `/invite @YourBotName`

**"Bot doesn't respond to messages"**
- Check Event Subscriptions are enabled
- Verify bot is subscribed to message events
- Ensure bot has `chat:write` permission

### **Notion Integration**

**"No pages found"**
- Create integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Share SOP pages with your integration (click Share → Add integration)
- Verify `NOTION_API_KEY` in `.env`

**"Permission denied"**
- Ensure integration has "Read content" capability
- Check pages are in the same workspace as integration

### **Pinecone Issues**

**"Index not found"**
- Verify `PINECONE_INDEX` and `PINECONE_INDEX_HOST` are correct
- Check index exists in Pinecone dashboard
- Ensure API key has access to the index

**"Dimension mismatch"**
- Pinecone index must use **1024 dimensions** to match OpenAI embeddings
- Create new index or update existing one

### **Environment Configuration**

**"Missing API key"**
```bash
# Verify all required keys are set
python cli.py check-setup
```

**"Module not found"**
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🤝 Contributing

Contributions welcome! This project was built for a hackathon but can be extended for production use.

**Potential Enhancements:**
- Add support for Microsoft Teams, Discord, or other platforms
- Implement approval workflows before posting violations
- Add analytics dashboard for compliance metrics
- Support for multi-language SOPs
- Custom severity thresholds per channel

---

## 📄 License

MIT License - feel free to use this project for your own compliance needs!

---

## 👥 Team

Built with ❤️ by the ApexStack team for [Hackathon Name]

---

## 🔗 Links

- **Slack API:** https://api.slack.com/
- **Notion API:** https://developers.notion.com/
- **Pinecone:** https://www.pinecone.io/
- **OpenAI:** https://openai.com/
- **FastAPI:** https://fastapi.tiangolo.com/

---

**Questions?** Check out our detailed documentation files or create an issue!

## Development

Run FastAPI with auto-reload:
```bash
uvicorn app.main:app --reload --log-level debug
```

View API documentation at `http://localhost:8000/docs`

## License

MIT
