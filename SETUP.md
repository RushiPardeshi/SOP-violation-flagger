# 🔧 Setup Guide

Complete setup instructions for SOP Violation Flagger, including all required API configurations.

---

## 📋 Prerequisites

Before setting up the project, ensure you have:

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/downloads)
- **Terminal/Command Line** access
- **Text Editor** (VS Code, Sublime, etc.)

---

## 🚀 Installation

### **1. Clone the Repository**

```bash
git clone <your-repo-url>
cd SOP-violation-flagger
```

### **2. Create Virtual Environment**

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

You should see `(.venv)` prefix in your terminal prompt.

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi>=0.110.0` - Web framework
- `uvicorn[standard]` - ASGI server
- `openai>=1.12.0` - OpenAI API client
- `pinecone>=3.2.0` - Pinecone vector database
- `slack-sdk>=3.27.0` - Slack integration
- `requests>=2.31.0` - HTTP client
- `python-dotenv>=1.0.0` - Environment management
- `pydantic>=2.0.0` - Data validation
- `pydantic-settings>=2.0.0` - Settings management

---

## 🔑 API Configuration

### **1. OpenAI Setup**

**Get API Key:**
1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Navigate to **API keys** section
4. Click **"Create new secret key"**
5. Copy the key (starts with `sk-`)

**Add to `.env`:**
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Models Used:**
- `text-embedding-3-small` (1024 dimensions) - For embeddings
- `gpt-4o-mini` - For violation detection

**Pricing (as of 2024):**
- Embeddings: ~$0.02 per 1M tokens
- GPT-4o-mini: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

---

### **2. Pinecone Setup**

**Create Account:**
1. Go to [pinecone.io](https://www.pinecone.io)
2. Sign up for free account
3. Verify email

**Create Index:**
1. Go to **Indexes** in dashboard
2. Click **"Create Index"**
3. Configure:
   - **Name:** `sop-index` (or your preferred name)
   - **Dimensions:** `1024` ⚠️ *Must be 1024 to match OpenAI embeddings*
   - **Metric:** `cosine` (recommended)
   - **Cloud:** Choose your region
   - **Plan:** Starter (free) is sufficient for testing
4. Click **"Create Index"**

**Get API Credentials:**
1. Go to **API Keys** section
2. Copy your API key
3. Go to your index → **Connect** tab
4. Copy the **Host** URL (e.g., `https://sop-index-abc123.svc.pinecone.io`)

**Add to `.env`:**
```env
PINECONE_API_KEY=abcd1234-5678-90ef-ghij-klmnopqrstuv
PINECONE_INDEX=sop-index
PINECONE_INDEX_HOST=https://sop-index-abc123.svc.pinecone.io
PINECONE_NAMESPACE=default
```

**Important Notes:**
- Index must use **1024 dimensions**
- `cosine` metric is recommended for text similarity
- Free tier includes 100K vectors (sufficient for most use cases)

---

### **3. Slack App Setup**

**Create Slack App:**
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Enter app name: `SOP Compliance Bot`
5. Select your workspace

**Enable Socket Mode:**
1. Go to **Settings → Socket Mode**
2. Toggle **"Enable Socket Mode"** → ON
3. Create App-Level Token:
   - Name: `socket-token`
   - Scope: `connections:write`
   - Click **"Generate"**
   - **Copy token** (starts with `xapp-`)

**Configure OAuth Scopes:**
1. Go to **Features → OAuth & Permissions**
2. Scroll to **Bot Token Scopes**
3. Add these scopes:
   - `chat:write` - Send messages
   - `channels:history` - Read public channels
   - `groups:history` - Read private channels
   - `im:history` - Read direct messages
   - `im:write` - Send onboarding DMs to new users
   - `mpim:history` - Read multi-person DMs
   - `channels:read` - View channel info
   - `users:read` - View user info
   - `reactions:write` - Add reactions (for feedback prompts)

**Enable Event Subscriptions:**
1. Go to **Features → Event Subscriptions**
2. Toggle **"Enable Events"** → ON
3. Expand **Subscribe to bot events**
4. Add these events:
   - `message.channels` - Public channel messages
   - `message.groups` - Private channel messages
   - `message.im` - Direct messages
   - `message.mpim` - Multi-person DMs
   - `reaction_added` - User feedback on violation messages
5. Click **"Save Changes"**

**Create Slash Commands (important order):**

⚠️ **Slash commands must be created AFTER Socket Mode is enabled.** If you created them before, delete and recreate them—otherwise Slack may show "invalid_url" and never deliver the command.

1. Go to **Features → Slash Commands**
2. Create `/check-sop`:
   - **Command:** `/check-sop`
   - **Request URL:** (leave blank – Socket Mode handles it)
   - **Short Description:** `Check a message for SOP violations before posting`
   - **Usage Hint:** `your message here`
3. Create `/sop-analytics`:
   - **Command:** `/sop-analytics`
   - **Request URL:** (leave blank)
   - **Short Description:** `View SOP violation analytics and feedback stats`
   - **Usage Hint:** `[optional: 2025-01-01 for date filter]`
4. **Leave Request URL blank** for both commands (Socket Mode delivers via WebSocket)
5. Click **"Save"** for each

**Slash commands troubleshooting:**
- **"invalid_url" or nothing happens:** Delete the slash command, ensure Socket Mode is ON, then recreate it with Request URL blank
- **Bot must be running:** `python slack_bot.py` (or `python cli.py start-bot`) must be running for the WebSocket connection
- **API must be running:** `uvicorn app.main:app --reload` for `/check-sop` and `/sop-analytics` to work

**Install App to Workspace:**
1. Go to **Settings → Install App**
2. Click **"Install to Workspace"**
3. Review permissions
4. Click **"Allow"**
5. **Copy Bot User OAuth Token** (starts with `xoxb-`)

**Add to `.env`:**
```env
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_APP_TOKEN=xapp-x-xxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Invite Bot to Channels:**

In Slack, type in any channel:
```
/invite @SOP Compliance Bot
```

The bot will now monitor messages in that channel.

---

### **4. Notion Integration Setup**

**Create Integration:**
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Configure:
   - **Name:** `SOP Ingestion Bot`
   - **Logo:** (optional)
   - **Associated workspace:** Select your workspace
   - **Capabilities:**
     - ✅ Read content
     - ✅ Read comments (optional)
     - ❌ Update content (not needed)
     - ❌ Insert content (not needed)
4. Click **"Submit"**
5. **Copy Internal Integration Token** (starts with `secret_`)

**Share Pages with Integration:**
1. Open your SOP page in Notion
2. Click **"Share"** (top right)
3. Click **"Invite"**
4. Search for your integration name: `SOP Ingestion Bot`
5. Click to add
6. Repeat for all SOP pages/databases you want to ingest

**Add to `.env`:**
```env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Note:** You can share:
- Individual pages
- Entire databases
- Parent pages (integration inherits access to child pages)

---

## 📝 Environment File

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Your `.env` should look like:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Pinecone Configuration
PINECONE_API_KEY=abcd1234-5678-90ef-ghij-klmnopqrstuv
PINECONE_INDEX=sop-index
PINECONE_INDEX_HOST=https://sop-index-abc123.svc.pinecone.io
PINECONE_NAMESPACE=default

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_APP_TOKEN=xapp-x-xxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Notion Configuration
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional Configuration
TOP_K=3
```

**Security Warning:** Never commit `.env` to version control! It's listed in `.gitignore`.

---

## ✅ Verify Setup

Run the setup verification script:

```bash
source .venv/bin/activate
python cli.py check-setup
```

Expected output:
```
🔍 Checking setup...

✅ OpenAI API key configured
✅ Pinecone API key configured
✅ Pinecone index configured
✅ Slack bot token configured
✅ Slack app token configured
✅ Notion API key configured

✅ All required environment variables are set!
```

If any checks fail, review the relevant section above.

---

## 🧪 Test Individual Components

### **Test OpenAI Connection:**

```bash
python -c "
from app.config import get_settings
from app.services.embeddings import embed_text

settings = get_settings()
result = embed_text('test')
print(f'✅ OpenAI working - embedding dimensions: {len(result)}')
"
```

Expected: `✅ OpenAI working - embedding dimensions: 1024`

### **Test Pinecone Connection:**

```bash
python -c "
from pinecone import Pinecone
from app.config import get_settings

settings = get_settings()
pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(host=settings.pinecone_index_host)
stats = index.describe_index_stats()
print(f'✅ Pinecone connected - vectors: {stats.total_vector_count}')
"
```

Expected: `✅ Pinecone connected - vectors: 0` (or current count)

### **Test Slack Connection:**

```bash
python -c "
import os
from slack_sdk import WebClient

client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
response = client.auth_test()
print(f'✅ Slack connected - bot: {response[\"user\"]}, team: {response[\"team\"]}')
"
```

Expected: `✅ Slack connected - bot: sop_compliance_bot, team: YourTeam`

### **Test Notion Connection:**

```bash
python -c "
from notion_connector import list_all_pages

pages = list_all_pages()
print(f'✅ Notion connected - accessible pages: {len(pages)}')
"
```

Expected: `✅ Notion connected - accessible pages: X`

---

## 🐛 Troubleshooting

### **Python Version Issues**

```bash
# Check Python version
python3 --version

# If < 3.11, install newer version:
# macOS (Homebrew):
brew install python@3.11

# Ubuntu/Debian:
sudo apt update
sudo apt install python3.11

# Windows: Download from python.org
```

### **Virtual Environment Not Activating**

```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### **Module Import Errors**

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Verify installation
pip list | grep fastapi
pip list | grep openai
pip list | grep pinecone

# Reinstall if missing
pip install -r requirements.txt
```

### **API Key Not Recognized**

- Check for extra spaces in `.env`
- Ensure no quotes around values: `OPENAI_API_KEY=sk-xxx` not `"sk-xxx"`
- Verify `.env` is in project root directory
- Restart terminal after editing `.env`

### **Pinecone Dimension Mismatch**

If you see errors about vector dimensions:

1. **Check your index dimensions:**
   - Go to Pinecone dashboard
   - View index details
   - Confirm: Dimensions = 1024

2. **If wrong, create new index:**
   - Cannot change dimensions on existing index
   - Create new index with 1024 dimensions
   - Update `PINECONE_INDEX` and `PINECONE_INDEX_HOST` in `.env`

### **Slack Socket Mode Connection Fails**

1. Verify Socket Mode is **enabled**
2. Check App-Level Token has `connections:write` scope
3. Ensure bot is **installed** to workspace
4. Try regenerating tokens if still failing

---

## 📚 Next Steps

Once setup is complete:

1. **Start the backend server:**
   ```bash
   python cli.py start-server
   ```

2. **Ingest SOPs from Notion:**
   ```bash
   python cli.py ingest-notion
   ```

3. **Start Slack bot:**
   ```bash
   python cli.py start-bot
   ```

4. **Test in Slack:**
   - Send a test message in a channel where the bot is present
   - Verify bot responds to violations

See [TESTING.md](TESTING.md) for detailed testing procedures.

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Rotate API keys regularly** - Especially after hackathons/demos
3. **Use separate keys for dev/prod** - Don't reuse production keys
4. **Limit Slack bot permissions** - Only add required OAuth scopes
5. **Restrict Notion integration access** - Only share necessary pages
6. **Monitor API usage** - Set up billing alerts on OpenAI/Pinecone

---

## 💡 Tips

- **Free Tier Limits:**
  - OpenAI: Pay-as-you-go (set usage limits)
  - Pinecone: 100K vectors free
  - Slack: Unlimited messages
  - Notion: Unlimited API calls

- **Cost Optimization:**
  - Use `gpt-4o-mini` instead of GPT-4 (much cheaper)
  - 1024 dimensions vs 1536 (smaller = cheaper storage)
  - Cache embeddings when possible

- **Development Workflow:**
  - Keep backend server running in one terminal
  - Run bot in another terminal
  - Use `--reload` flag for auto-restart during development

---

**Setup complete! 🎉** Head to [README.md](README.md) for usage instructions.
