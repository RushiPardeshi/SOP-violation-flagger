# 📡 API Documentation

Complete REST API reference for SOP Violation Flagger backend.

---

## 🌐 Base URL

```
http://localhost:8000
```

For production deployment, replace with your actual domain.

---

## 🔍 Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These interfaces allow you to:
- Browse all endpoints
- View request/response schemas
- Try API calls directly from browser
- Download OpenAPI specification

---

## 🚀 Endpoints

### **1. Health Check**

Check if the API server is running.

**Request:**

```http
GET /
```

**Response:**

```json
{
  "status": "ok",
  "message": "SOP Violation Flagger API"
}
```

**Status Codes:**
- `200 OK` - Server is running

**Example:**

```bash
curl http://localhost:8000/
```

---

### **2. Ingest Document**

Add or update a document in the vector database.

**Request:**

```http
POST /ingest
Content-Type: application/json
```

**Body:**

```json
{
  "doc_id": "string",
  "title": "string",
  "content": "string"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `doc_id` | string | Yes | Unique identifier for the document |
| `title` | string | Yes | Document title (used for context) |
| `content` | string | Yes | Full document text content |

**Response:**

```json
{
  "status": "ok",
  "doc_id": "string",
  "action": "added" | "updated"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always "ok" on success |
| `doc_id` | string | Echoed doc_id from request |
| `action` | string | "added" if new, "updated" if existing doc |

**Status Codes:**
- `200 OK` - Document successfully ingested
- `400 Bad Request` - Invalid request body
- `500 Internal Server Error` - Server-side error

**Example:**

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "sop-001",
    "title": "Data Security Policy",
    "content": "All sensitive data must be encrypted at rest and in transit..."
  }'
```

**Response:**

```json
{
  "status": "ok",
  "doc_id": "sop-001",
  "action": "added"
}
```

**Notes:**

- Documents are automatically embedded using OpenAI text-embedding-3-small
- If `doc_id` already exists, the document vector is updated
- Content should be plain text (markdown is fine)
- Maximum content length: ~8000 tokens (~32,000 characters)

---

### **3. Check Message for Violations**

Evaluate a message against stored SOPs to detect policy violations.

**Request:**

```http
POST /check-message
Content-Type: application/json
```

**Body:**

```json
{
  "channel_id": "string",
  "user_id": "string",
  "message_text": "string",
  "timestamp": "string"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel_id` | string | Yes | Slack channel ID where message was sent |
| `user_id` | string | Yes | Slack user ID who sent the message |
| `message_text` | string | Yes | The message content to check |
| `timestamp` | string | Yes | Message timestamp (for threading) |

**Response:**

```json
{
  "violated": boolean,
  "rule": "string" | null,
  "severity": "low" | "medium" | "high" | "critical" | null,
  "explanation": "string" | null
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `violated` | boolean | `true` if violation detected, `false` otherwise |
| `rule` | string \| null | Which SOP rule was violated (null if no violation) |
| `severity` | string \| null | Severity level: "low", "medium", "high", "critical" |
| `explanation` | string \| null | Detailed explanation of why it's a violation |

**Status Codes:**
- `200 OK` - Check completed successfully
- `400 Bad Request` - Invalid request body
- `404 Not Found` - No SOPs in database to check against
- `500 Internal Server Error` - Server-side error

**Example - Violation Detected:**

```bash
curl -X POST http://localhost:8000/check-message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345ABC",
    "user_id": "U67890DEF",
    "message_text": "Hey team, the prod password is admin123",
    "timestamp": "1234567890.123456"
  }'
```

**Response:**

```json
{
  "violated": true,
  "rule": "Credential sharing in public channels",
  "severity": "high",
  "explanation": "Production credentials must never be shared in Slack channels. This poses a significant security risk. Use a secure password manager or secrets management system instead."
}
```

**Example - No Violation:**

```bash
curl -X POST http://localhost:8000/check-message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345ABC",
    "user_id": "U67890DEF",
    "message_text": "The quarterly report is ready for review",
    "timestamp": "1234567890.123456"
  }'
```

**Response:**

```json
{
  "violated": false,
  "rule": null,
  "severity": null,
  "explanation": null
}
```

**Notes:**

- Detection uses RAG (Retrieval-Augmented Generation):
  1. Message is embedded using OpenAI
  2. Top-3 similar SOPs are retrieved from Pinecone
  3. GPT-4o-mini evaluates message against retrieved SOPs
- Detection typically completes in 1-2 seconds
- Context from channel/user IDs may be used for better detection

---

## 🔐 Authentication

**Current Version:** No authentication required (local development)

**Production Recommendations:**

```python
# Add API key authentication
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Protect endpoints
@router.post("/ingest", dependencies=[Depends(verify_api_key)])
async def ingest(...):
    ...
```

**Alternative Authentication Methods:**
- OAuth 2.0 with JWT tokens
- Basic Auth for simple use cases
- mTLS for service-to-service communication

---

## 📊 Rate Limiting

**Current Version:** No rate limiting (local development)

**Production Recommendations:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/check-message")
@limiter.limit("100/minute")
async def check_message(...):
    ...
```

**Suggested Limits:**
- `/ingest`: 10 requests/minute (slow operation)
- `/check-message`: 100 requests/minute (typical Slack traffic)
- `/`: Unlimited (health check)

---

## 🔍 Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### **Common Errors**

**400 Bad Request**

```json
{
  "detail": "Field 'content' is required"
}
```

Causes:
- Missing required fields
- Invalid field types
- Malformed JSON

**404 Not Found**

```json
{
  "detail": "No documents found in database. Please ingest SOPs first."
}
```

Causes:
- No documents in Pinecone
- Invalid endpoint

**500 Internal Server Error**

```json
{
  "detail": "Failed to connect to Pinecone"
}
```

Causes:
- External service unavailable (OpenAI, Pinecone)
- Configuration error
- Server-side bug

---

## 🧪 Testing Examples

### **Python (requests library)**

```python
import requests

BASE_URL = "http://localhost:8000"

# Ingest document
response = requests.post(
    f"{BASE_URL}/ingest",
    json={
        "doc_id": "security-policy-v2",
        "title": "Security Policy v2.0",
        "content": "All production access must use 2FA..."
    }
)
print(response.json())
# {'status': 'ok', 'doc_id': 'security-policy-v2', 'action': 'added'}

# Check message
response = requests.post(
    f"{BASE_URL}/check-message",
    json={
        "channel_id": "C123",
        "user_id": "U456",
        "message_text": "I'll disable 2FA for now to speed things up",
        "timestamp": "1234567890.123"
    }
)
print(response.json())
# {'violated': True, 'rule': '2FA requirement', ...}
```

### **JavaScript (fetch)**

```javascript
const BASE_URL = "http://localhost:8000";

// Ingest document
const ingestResponse = await fetch(`${BASE_URL}/ingest`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    doc_id: "comm-guidelines",
    title: "Communication Guidelines",
    content: "Always be respectful and professional..."
  })
});
const ingestData = await ingestResponse.json();
console.log(ingestData);
// {status: 'ok', doc_id: 'comm-guidelines', action: 'added'}

// Check message
const checkResponse = await fetch(`${BASE_URL}/check-message`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    channel_id: "C123",
    user_id: "U456",
    message_text: "This idea is stupid and you're an idiot",
    timestamp: "1234567890.123"
  })
});
const checkData = await checkResponse.json();
console.log(checkData);
// {violated: true, rule: 'Professional communication', ...}
```

### **cURL**

```bash
# Health check
curl http://localhost:8000/

# Ingest document
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "doc_id": "deployment-sop",
  "title": "Deployment Standard Operating Procedure",
  "content": "All deployments must go through staging first..."
}
EOF

# Check message
curl -X POST http://localhost:8000/check-message \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "channel_id": "C789",
  "user_id": "U012",
  "message_text": "Let's push directly to prod, testing takes too long",
  "timestamp": "1234567890.123456"
}
EOF
```

---

## 📈 Performance Metrics

### **Endpoint Latencies (Typical)**

| Endpoint | Avg Latency | P95 Latency | Notes |
|----------|-------------|-------------|-------|
| `GET /` | <10ms | <20ms | No external calls |
| `POST /ingest` | ~150ms | ~300ms | OpenAI embedding call |
| `POST /check-message` | ~1000ms | ~2000ms | Pinecone + OpenAI LLM |

### **Throughput**

| Endpoint | Max RPS | Bottleneck |
|----------|---------|------------|
| `GET /` | 1000+ | CPU |
| `POST /ingest` | ~10 | OpenAI API |
| `POST /check-message` | ~20 | OpenAI API |

**RPS** = Requests Per Second

### **Token Usage (per request)**

| Endpoint | Input Tokens | Output Tokens | Cost |
|----------|--------------|---------------|------|
| `POST /ingest` | ~200 (avg) | 0 | ~$0.004 |
| `POST /check-message` | ~500 (avg) | ~100 (avg) | ~$0.0009 |

---

## 🔄 Webhooks (Future Feature)

**Coming Soon:** Webhook support for asynchronous violation notifications

**Proposed Endpoint:**

```http
POST /webhooks/register
Content-Type: application/json

{
  "url": "https://your-server.com/violations",
  "events": ["violation.detected"],
  "secret": "your-webhook-secret"
}
```

When violation detected, POST to your URL:

```json
{
  "event": "violation.detected",
  "timestamp": "2024-03-07T15:30:00Z",
  "data": {
    "channel_id": "C123",
    "user_id": "U456",
    "message_text": "...",
    "violation": {
      "rule": "...",
      "severity": "high",
      "explanation": "..."
    }
  }
}
```

---

## 📚 SDKs & Client Libraries

### **Python Client Example**

```python
# sop_client.py
import requests
from typing import Optional

class SOPClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def ingest(self, doc_id: str, title: str, content: str) -> dict:
        """Ingest a document"""
        response = requests.post(
            f"{self.base_url}/ingest",
            json={
                "doc_id": doc_id,
                "title": title,
                "content": content
            }
        )
        response.raise_for_status()
        return response.json()
    
    def check_message(
        self,
        channel_id: str,
        user_id: str,
        message_text: str,
        timestamp: str
    ) -> dict:
        """Check message for violations"""
        response = requests.post(
            f"{self.base_url}/check-message",
            json={
                "channel_id": channel_id,
                "user_id": user_id,
                "message_text": message_text,
                "timestamp": timestamp
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = SOPClient()
result = client.check_message(
    channel_id="C123",
    user_id="U456",
    message_text="Test message",
    timestamp="1234567890.123"
)
print(f"Violation: {result['violated']}")
```

---

## 🐛 Debugging

### **Enable Debug Mode**

Set in FastAPI:

```python
# app/main.py
app = FastAPI(debug=True)
```

Start with reload:

```bash
uvicorn app.main:app --reload --log-level debug
```

### **View Logs**

Server logs show:
- Incoming requests
- Pinecone operations
- OpenAI API calls
- Response times

Example log output:

```
INFO:     127.0.0.1:52843 - "POST /check-message HTTP/1.1" 200 OK
DEBUG:    Embedded message in 123ms
DEBUG:    Found 3 similar documents
DEBUG:    LLM check completed in 876ms
```

### **Common Issues**

**"No documents found" on check**

Solution: Ingest SOPs first
```bash
python cli.py ingest-notion
```

**"Connection timeout" errors**

Causes:
- OpenAI API slow/down
- Pinecone unreachable
- Network issues

Solutions:
- Check API status pages
- Verify API keys
- Retry with backoff

**"Dimension mismatch" errors**

Cause: Pinecone index not 1024 dimensions

Solution: Recreate index with correct dimensions

---

## 🔗 Related Documentation

- **[README.md](README.md)** - Project overview
- **[SETUP.md](SETUP.md)** - Setup instructions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[TESTING.md](TESTING.md)** - Testing guide

---

## 📞 Support

**Issues:** Create an issue on GitHub
**Questions:** Check documentation or ask in discussions

---

**API Version:** 1.0.0  
**Last Updated:** March 2024
