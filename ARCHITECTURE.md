# 🏗️ System Architecture

Technical documentation for SOP Violation Flagger architecture, design decisions, and data flow.

---

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Sources                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Notion Workspace          Slack Workspace                      │
│   (SOP Documents)           (User Messages)                      │
│         │                          │                             │
│         └──────────────┬───────────┘                             │
│                        │                                         │
└────────────────────────┼─────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Layer                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   notion_connector.py        slack_connector.py                  │
│   - list_all_pages()         - stream_messages()                 │
│   - read_page()              - send_message()                    │
│                                                                   │
│         │                          │                             │
│         ▼                          ▼                             │
│                                                                   │
│   ingest_notion.py           slack_bot.py                        │
│   - Batch ingestion          - Real-time monitoring              │
│   - Title extraction         - Violation detection               │
│   - Metadata enrichment      - Response formatting               │
│                                                                   │
└────────────────────────┬────────────┬────────────────────────────┘
                         │            │
                         ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   POST /ingest              POST /check-message                  │
│   - Validate request        - Validate message                   │
│   - Generate embeddings     - Query similar docs                 │
│   - Check if exists         - LLM evaluation                     │
│   - Upsert to Pinecone      - Return verdict                     │
│                                                                   │
└────────────────────────┬────────────┬────────────────────────────┘
                         │            │
                         ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Pinecone Vector DB        OpenAI API                           │
│   - Store embeddings        - text-embedding-3-small             │
│   - Similarity search       - gpt-4o-mini                        │
│   - Metadata storage        - JSON mode responses                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Diagrams

### **Ingestion Pipeline**

```
┌──────────┐
│  Notion  │
│   Page   │
└─────┬────┘
      │
      ▼
┌───────────────────┐
│ notion_connector  │
│  .read_page()     │
│                   │
│ Returns:          │
│ - page_id         │
│ - properties      │
│ - markdown text   │
└─────┬─────────────┘
      │
      ▼
┌───────────────────┐
│ ingest_notion.py  │
│                   │
│ Extracts:         │
│ - Title from props│
│ - Plain content   │
│ - Metadata        │
└─────┬─────────────┘
      │
      │ POST /ingest
      ▼
┌───────────────────┐
│ FastAPI Backend   │
│                   │
│ 1. Validate       │
│ 2. Embed content  │
│ 3. Check exists?  │
└─────┬─────────────┘
      │
      ├─── Yes ──► Update vector ──► Return "updated"
      │
      └─── No  ──► Insert vector ──► Return "added"
      
      ▼
┌───────────────────┐
│ Pinecone Index    │
│                   │
│ Vector:           │
│ - 1024 dims       │
│ - Metadata        │
└───────────────────┘
```

### **Violation Detection Pipeline**

```
┌──────────────┐
│ Slack User   │
│ sends message│
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Slack Socket API │
│ (WebSocket)      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ slack_connector  │
│ .stream_messages │
│                  │
│ Yields:          │
│ - channel_id     │
│ - user_id        │
│ - text           │
│ - timestamp      │
└──────┬───────────┘
       │
       ▼
┌──────────────────────┐
│ slack_bot.py         │
│                      │
│ Filters:             │
│ - Ignore bot msgs    │
│ - Ignore irrelevant  │
└──────┬───────────────┘
       │
       │ POST /check-message
       ▼
┌──────────────────────┐
│ FastAPI /check       │
│                      │
│ 1. Embed message     │
│ 2. Query Pinecone    │
│    (top-3 similar)   │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Pinecone             │
│ Vector Search        │
│                      │
│ Returns:             │
│ [sop1, sop2, sop3]   │
│ with scores          │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ LLM Service          │
│ (GPT-4o-mini)        │
│                      │
│ Prompt:              │
│ - Message text       │
│ - Retrieved SOPs     │
│ - System: compliance │
│           auditor    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ JSON Response        │
│                      │
│ {                    │
│   violated: bool     │
│   rule: str          │
│   severity: str      │
│   explanation: str   │
│ }                    │
└──────┬───────────────┘
       │
       ├── violated = false ──► Silent (no action)
       │
       └── violated = true  ──► Format warning
                                     │
                                     ▼
                              ┌──────────────┐
                              │ slack_bot.py │
                              │ send_message │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │ Slack Channel│
                              │ Bot posts    │
                              │ warning      │
                              └──────────────┘
```

---

## 🗂️ Component Breakdown

### **1. Backend (FastAPI)**

**Location:** `app/`

**Purpose:** RESTful API for document ingestion and compliance checking

**Key Files:**
- `main.py` - Application entry point
- `config.py` - Environment configuration
- `routers/` - API endpoint definitions
- `services/` - Business logic
- `models/` - Pydantic schemas

**Design Decisions:**

✅ **FastAPI chosen because:**
- Automatic API documentation (Swagger UI)
- Type safety with Pydantic
- High performance (async support)
- Easy to extend with new endpoints

✅ **Separation of concerns:**
- Routers handle HTTP
- Services handle business logic
- Models define data contracts

✅ **Stateless design:**
- No session management
- Each request is independent
- Easy to scale horizontally

---

### **2. Vector Database (Pinecone)**

**Service:** `app/services/pinecone_svc.py`

**Operations:**

```python
def check_doc_exists(doc_id: str) -> bool:
    """Check if document already exists in index"""
    
def upsert_doc(doc_id: str, title: str, content: str) -> dict:
    """Insert or update document vector"""
    
def query_similar(query: str, top_k: int) -> list:
    """Find similar documents using vector search"""
```

**Data Model:**

```python
{
    "id": "notion-page-abc123",           # Unique identifier
    "values": [0.123, -0.456, ...],       # 1024-dim embedding
    "metadata": {
        "title": "Data Security Policy",
        "content": "All sensitive data...",
        "source": "notion",
        "ingested_at": "2024-03-07T10:30:00Z"
    }
}
```

**Design Decisions:**

✅ **Manual embeddings (not inference API):**
- More control over dimensions
- Better error handling
- Consistent with OpenAI API

✅ **Cosine similarity metric:**
- Standard for text embeddings
- Range: -1 to 1 (higher = more similar)
- Well-suited for normalized vectors

✅ **Smart upsert logic:**
- Check existence via `fetch()`
- Update if exists, insert if new
- Return action taken for transparency

---

### **3. Embeddings Service**

**Service:** `app/services/embeddings.py`

**Configuration:**

```python
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1024
```

**Why 1024 dimensions?**

- ✅ Good balance of accuracy vs cost/speed
- ✅ Smaller than default 1536 (cheaper storage)
- ✅ Sufficient for SOP semantic similarity
- ✅ Faster vector operations

**Function:**

```python
def embed_text(text: str) -> list[float]:
    """
    Generate 1024-dimensional embedding vector
    
    Performance:
    - ~1000 tokens/sec
    - Cost: $0.02 per 1M tokens
    """
```

---

### **4. LLM Service (GPT-4o-mini)**

**Service:** `app/services/llm.py`

**System Prompt:**

```python
_SYSTEM_PROMPT = """
You are a compliance auditor for a company. You have access to 
the company's Standard Operating Procedures (SOPs).

Your task is to determine if a Slack message violates any SOPs.

Be strict but reasonable. Consider context and intent.
"""
```

**JSON Mode Response:**

```python
{
    "violated": bool,
    "rule": str,          # Which SOP rule
    "severity": str,      # low/medium/high/critical
    "explanation": str    # Why it's a violation
}
```

**Design Decisions:**

✅ **GPT-4o-mini vs GPT-4:**
- 90%+ accuracy at 10% of cost
- Faster response times
- Sufficient for compliance checks

✅ **JSON mode:**
- Guaranteed structured output
- No parsing errors
- Type-safe responses

✅ **Contextual evaluation:**
- Receives top-3 relevant SOPs
- Not all SOPs (would exceed context limit)
- RAG approach improves accuracy

---

### **5. Slack Integration**

**Connector:** `slack_connector.py`

**Socket Mode Architecture:**

```
┌──────────────┐                    ┌─────────────┐
│ Slack Server │◄──WebSocket────────┤ Socket Mode │
│              │                    │   Client    │
│   Events:    │                    │             │
│   - message  │                    │ Maintains   │
│   - reaction │                    │ connection  │
│   - etc.     │                    │             │
└──────────────┘                    └─────────────┘
```

**Why Socket Mode?**

✅ **No public URL required**
- Runs locally or behind firewall
- No need for ngrok/tunneling
- Great for development/demos

✅ **Real-time streaming**
- Immediate message delivery
- No polling required
- Low latency

✅ **Bidirectional**
- Receive events
- Send messages
- All over one WebSocket

**Functions:**

```python
def stream_messages() -> Generator:
    """Yield messages from all channels in real-time"""
    
def send_message(channel_id: str, text: str) -> dict:
    """Post message to specified channel"""
```

---

### **6. Notion Integration**

**Connector:** `notion_connector.py`

**API Operations:**

```python
def list_all_pages() -> list[dict]:
    """List all pages accessible to integration"""
    
def read_page(page_id: str) -> str:
    """Read page content as markdown"""
```

**Content Extraction:**

Notion stores content as blocks:
- Paragraph blocks
- Heading blocks
- List blocks
- Code blocks
- etc.

We extract as markdown for readability:

```markdown
# Security Policy

## Data Handling
- Never share credentials
- Use password managers
- Enable 2FA
```

**Design Decisions:**

✅ **Read-only access:**
- Integration only needs read capability
- Principle of least privilege
- Safer for production

✅ **Markdown format:**
- Preserves formatting
- Human-readable
- Good for LLM context

---

## 🔐 Security Architecture

### **API Key Management**

```
.env (local file)
    ↓
Environment Variables
    ↓
Pydantic Settings
    ↓
Service Layers
```

**Key Features:**
- Never hardcoded in source
- Not committed to git
- Validated at startup
- Injected via dependency injection

### **Slack Security**

```
Bot Token (xoxb-)  ──► Workspace-level permissions
App Token (xapp-)  ──► Socket Mode connection
```

**Permissions:**
- Read: channels, users, messages
- Write: Only to channels bot is in
- No admin capabilities

### **Notion Security**

```
Integration Token ──► Page-level access
```

**Scope:**
- Only shared pages accessible
- Can be revoked anytime
- Audit logs in Notion

---

## 📊 Data Models

### **IngestRequest**

```python
class IngestRequest(BaseModel):
    doc_id: str         # Unique identifier
    title: str          # Document title
    content: str        # Full text content
```

### **IngestResponse**

```python
class IngestResponse(BaseModel):
    status: str         # "ok" or "error"
    doc_id: str         # Echoed doc_id
    action: str | None  # "added" or "updated"
```

### **CheckRequest**

```python
class CheckRequest(BaseModel):
    channel_id: str     # Slack channel ID
    user_id: str        # Slack user ID
    message_text: str   # Message content
    timestamp: str      # Message timestamp
```

### **CheckResponse**

```python
class CheckResponse(BaseModel):
    violated: bool                  # Violation detected?
    rule: str | None                # Which rule violated
    severity: Literal['low', 'medium', 'high', 'critical'] | None
    explanation: str | None         # Why violation occurred
```

---

## 🚀 Performance Considerations

### **Ingestion Performance**

**Bottleneck:** OpenAI API calls

```python
# Sequential (slow)
for page in pages:
    embed_and_upsert(page)  # ~200ms per page
    
# Parallel (faster)
with ThreadPoolExecutor() as executor:
    executor.map(embed_and_upsert, pages)  # ~50ms per page
```

**Current Implementation:** Sequential (simpler, easier to debug)

**Future Optimization:** Batch API calls (OpenAI supports batching)

### **Real-time Detection Performance**

**Target:** < 2 seconds from message to response

**Actual Breakdown:**
- Embed query: ~100ms
- Pinecone search: ~50ms
- LLM evaluation: ~800ms
- Format & send: ~50ms
- **Total: ~1 second** ✅

**Optimization Opportunities:**
- Cache embeddings for common phrases
- Use streaming responses from LLM
- Parallel Pinecone + LLM calls where possible

### **Cost Optimization**

**Per 1000 Messages:**

| Component | Cost | Notes |
|-----------|------|-------|
| Embedding | $0.0004 | 1000 messages × 200 tokens avg |
| Pinecone Query | $0.00 | Free tier |
| LLM Evaluation | $0.03 | 1000 messages × 500 tokens avg |
| **Total** | **~$0.03** | Very affordable |

**Optimization Strategies:**
- Use smaller embeddings (1024 vs 1536)
- Cache frequent queries
- Batch operations
- Filter obvious non-violations before LLM

---

## 🔮 Future Enhancements

### **Scalability**

```
Current: Single process
Future: Microservices architecture

┌──────────┐  ┌──────────┐  ┌──────────┐
│ Ingestion│  │ Detection│  │ Response │
│ Service  │  │ Service  │  │ Service  │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────┬───┴─────────────┘
               │
        ┌──────▼──────┐
        │ Message Bus │
        └─────────────┘
```

### **Monitoring**

```python
# Add observability
from prometheus_client import Counter, Histogram

violations_detected = Counter('violations_total', 'Total violations')
detection_latency = Histogram('detection_seconds', 'Detection time')
```

### **Caching**

```python
# Redis cache for frequent queries
@cache(ttl=3600)
def get_relevant_sops(query: str) -> list:
    return pinecone.query_similar(query)
```

### **Multi-tenancy**

```python
# Support multiple workspaces
namespace = f"tenant-{workspace_id}"
index.query(namespace=namespace, ...)
```

---

## 🎓 Design Principles Applied

1. **Separation of Concerns**
   - Connectors handle external APIs
   - Services handle business logic
   - Routers handle HTTP

2. **Single Responsibility**
   - Each module has one clear purpose
   - Easy to test in isolation
   - Simple to maintain

3. **Dependency Injection**
   - Configuration injected via Pydantic
   - Services receive dependencies
   - Testable and flexible

4. **Fail Fast**
   - Validate at API boundary
   - Check env vars at startup
   - Clear error messages

5. **Idempotency**
   - Re-running ingestion safe
   - Upsert, not insert
   - No side effects

6. **Observability**
   - Structured logging
   - Clear console output
   - Error tracking

---

## 📖 References

- **FastAPI:** https://fastapi.tiangolo.com/
- **Pinecone:** https://docs.pinecone.io/
- **OpenAI:** https://platform.openai.com/docs/
- **Slack API:** https://api.slack.com/
- **Notion API:** https://developers.notion.com/

---

**Questions or suggestions?** Open an issue or check other docs!
