# SOP Violation Flagger

FastAPI backend that monitors Slack messages and flags SOP (Standard Operating Procedure) violations using Pinecone vector search and OpenAI LLM reasoning.

## Architecture

- **Ingestion**: Upload SOP documents → intelligently chunk into sections/paragraphs → Pinecone auto-embeds each chunk → store in vector index
- **Detection**: Receive Slack message → Pinecone auto-embeds query → retrieve top-K most similar SOP chunks → LLM judges violation → return structured response

**Chunking Strategy:**
- Splits documents by numbered sections (e.g., "1.1 Rules", "2.3 Policy")
- Falls back to paragraph boundaries if no clear sections
- Large paragraphs are split with overlap to preserve context
- Each chunk ~800 characters with 100-character overlap
- Metadata preserved: title, section, parent doc_id

## Prerequisites

- Python 3.11+
- OpenAI API key (for LLM reasoning only)
- Pinecone account with an **inference-enabled index** (Pinecone handles embeddings automatically)

## Setup

### 1. Clone and create virtual environment

```bash
cd SOP-violation-flagger
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_INDEX=sop-index
PINECONE_INDEX_HOST=https://sop-index-xxx.svc.pinecone.io
PINECONE_NAMESPACE=default
TOP_K=3
```

**Important**: Your Pinecone index must be **inference-enabled** (Pinecone handles embedding automatically).

### 4. Start the server

```bash
uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

## API Endpoints

### Health Check
```bash
GET /
```

### Ingest SOP Document
```bash
POST /ingest
Content-Type: application/json

{
  "doc_id": "sop-001",
  "title": "Data Handling Policy",
  "content": "..."
}
```

Response:
```json
{
  "status": "ok",
  "doc_id": "sop-001",
  "chunks_created": 12
}
```
_Documents are automatically chunked by section/paragraph before embedding._

### Check Message for Violations
```bash
POST /check-message
Content-Type: application/json

{
  "channel_id": "C12345",
  "user_id": "U67890",
  "message_text": "Here is the production password: admin123",
  "timestamp": "1234567890.123456"
}
```

Response:
```json
{
  "violated": true,
  "rule": "Credential sharing in public channels",
  "severity": "critical",
  "explanation": "Production credentials must never be shared in Slack"
}
```

## Usage

### Ingest the sample SOP

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d "$(jq -n --rawfile content sop.txt \
       '{doc_id: "sop-apexstack-v3.2", title: "ApexStack Technologies Internal SOP v3.2", content: $content}')"
```

### Test violation detection

```bash
curl -X POST http://localhost:8000/check-message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345",
    "user_id": "U67890",
    "message_text": "Use this password: prod_db_admin_123",
    "timestamp": "1234567890.123456"
  }'
```

## Project Structure

```
app/
  main.py              # FastAPI app + router registration
  config.py            # Environment configuration
  services/
    chunking.py        # Intelligent SOP document chunking (sections/paragraphs)
    embeddings.py      # OpenAI embedding wrapper (legacy, not used)
    pinecone_svc.py    # Pinecone inference API (auto-embedding + similarity search)
    llm.py             # OpenAI LLM violation reasoning (JSON mode)
  models/
    ingest.py          # IngestRequest/Response schemas
    check.py           # CheckRequest/Response schemas
  routers/
    ingest.py          # POST /ingest endpoint
    check.py           # POST /check-message endpoint
```

## Integration with Slack Bot

Your Slack bot should:

1. Listen to message events
2. Call `POST /check-message` with the message details
3. If `violated: true`, post a warning to Slack with the `rule`, `severity`, and `explanation`

This service only returns JSON — it does not call the Slack API directly.

## Severity Levels

- **low**: Minor deviation, unlikely to cause immediate harm
- **medium**: Moderate deviation, could cause operational issues  
- **high**: Serious deviation, significant risk
- **critical**: Security breach or production compromise
# SOP-violation-flagger

## Notion polling

Polls Notion every 1 day and reads all documents the integration has access to.

```bash
pip install -r requirements.txt
# Set NOTION_API_KEY in .env
python main.py
```

**Setup:** Create an integration at [notion.so/my-integrations](https://www.notion.so/my-integrations), enable "Read content", and share your pages with the integration.
Slack connector for streaming messages and sending replies.

## Quick start

```bash
pip install -r requirements.txt
# Set SLACK_APP_TOKEN and SLACK_BOT_TOKEN in .env
python main.py
```

Streams messages from all channels the bot is in. To send: `channel_id message` or `channel_id1,channel_id2 message`

## Library usage

```python
from notion_connector import list_all_pages, read_page

# List all accessible pages
pages = list_all_pages()

# Read a specific page
content = read_page("page-id-or-url")
```
from slack_connector import stream_messages, send_message

# Stream from all channels (real-time, chronological)
for channel_id, user_id, message, timestamp in stream_messages():
    print(f"[{channel_id}] {user_id}: {message}")

# Send to one or more channels
send_message("C0ABC123", "Hello")
send_message(["C0ABC123", "C0XYZ789"], "Hello everyone")
```
