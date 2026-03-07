# Testing Guide

This document shows the expected outcomes for testing each component of the SOP Violation Flagger system.

## Setup Verification

### Test 1: Check Environment Setup

**Command:**
```bash
python cli.py check-setup
```

**Expected Output:**
```
🔍 Checking setup...

✅ .env file exists
✅ OPENAI_API_KEY is set
✅ PINECONE_API_KEY is set
✅ PINECONE_INDEX is set
✅ PINECONE_INDEX_HOST is set
✅ Virtual environment active
✅ All dependencies installed

✅ Setup looks good! You're ready to go.
```

**If issues found:**
- Missing .env: `cp .env.example .env` and fill in API keys
- Missing dependencies: `pip install -r requirements.txt`
- Virtual env not active: `source .venv/bin/activate`

---

## Component Testing

### Test 2: Start FastAPI Server

**Terminal 1:**
```bash
source .venv/bin/activate
python cli.py start-server
```

**Expected Output:**
```
🚀 Starting FastAPI server...
INFO:     Will watch for changes in these directories: ['/Users/.../SOP-violation-flagger']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify server is running:**
```bash
curl http://localhost:8000/
```

**Expected Response:**
```json
{"status":"ok"}
```

**Check API docs:**
Open in browser: `http://localhost:8000/docs`

You should see:
- Swagger UI with endpoints
- `/ingest` - POST endpoint
- `/check-message` - POST endpoint

---

### Test 3: Ingest SOP from File (Testing)

**Terminal 2:**
```bash
source .venv/bin/activate
python ingest_file.py sop.txt --doc-id "sop-apexstack-v3.2" --title "ApexStack SOP v3.2"
```

**Expected Output:**
```
📤 Ingesting: sop.txt
   Doc ID: sop-apexstack-v3.2
   Title: ApexStack SOP v3.2
   Content length: 28736 characters

✅ Success: {'status': 'ok', 'doc_id': 'sop-apexstack-v3.2'}
```

**What this means:**
- ✅ API connection working
- ✅ File read successfully
- ✅ Document uploaded to Pinecone
- ✅ Pinecone automatically embedded the content

**If you see errors:**
- `Cannot connect to API`: Make sure server is running (Test 2)
- `Pinecone error`: Check PINECONE_API_KEY and PINECONE_INDEX_HOST in .env
- `OpenAI error`: Check OPENAI_API_KEY in .env

---

### Test 4: Ingest SOPs from Notion

**Terminal 2:**
```bash
python cli.py ingest-notion
```

**Expected Output:**
```
🔄 Starting Notion document ingestion...
📡 API endpoint: http://localhost:8000
📚 Fetching Notion pages...

✅ Connected to API

📄 Found 5 Notion pages

============================================================

[1/5] 
📄 Processing: Engineering SOPs
   ID: a1b2c3d4-e5f6-7890-1234-567890abcdef
   Content length: 15234 characters
   ✅ Ingested successfully

[2/5] 
📄 Processing: Security Policies
   ID: b2c3d4e5-f6g7-8901-2345-678901bcdefg
   Content length: 8456 characters
   ✅ Ingested successfully

[3/5] 
📄 Processing: Communication Guidelines
   ID: c3d4e5f6-g7h8-9012-3456-789012cdefgh
   Content length: 12089 characters
   ✅ Ingested successfully

[4/5] 
📄 Processing: Incident Response
   ID: d4e5f6g7-h8i9-0123-4567-890123defghi
   Content length: 6723 characters
   ✅ Ingested successfully

[5/5] 
📄 Processing: Code Review Standards
   ID: e5f6g7h8-i9j0-1234-5678-901234efghij
   Content length: 9345 characters
   ✅ Ingested successfully

============================================================

✨ Ingestion complete!
   ✅ Success: 5
   ❌ Failed: 0
   📊 Total: 5
```

**What this means:**
- ✅ Notion API connection working
- ✅ Integration has access to pages
- ✅ All pages successfully uploaded to Pinecone
- ✅ Vector database ready for similarity search

**If you see errors:**
- `No pages found`: Share Notion pages with your integration
- `403 Forbidden`: Check NOTION_API_KEY in .env
- `Cannot connect to API`: Make sure FastAPI server is running

---

### Test 5: Manual API Test (Violation Detection)

**Test a violation:**
```bash
curl -X POST http://localhost:8000/check-message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345",
    "user_id": "U67890",
    "message_text": "Here is the prod database password: postgres://admin:secret123@prod-db.company.com",
    "timestamp": "1234567890.123456"
  }'
```

**Expected Response:**
```json
{
  "violated": true,
  "rule": "Confidential Information - Production database credentials",
  "severity": "high",
  "explanation": "Sharing production database credentials in Slack is a critical security violation. Credentials must only be shared through encrypted secret managers like Vault or AWS Secrets Manager.",
}
```

**Test compliance (no violation):**
```bash
curl -X POST http://localhost:8000/check-message \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "C12345",
    "user_id": "U67890",
    "message_text": "I stored the database credentials in AWS Secrets Manager as per our SOP",
    "timestamp": "1234567890.123456"
  }'
```

**Expected Response:**
```json
{
  "violated": false,
  "rule": null,
  "severity": null,
  "explanation": "The message describes proper credential management using AWS Secrets Manager, which complies with the SOP requirement for storing credentials in encrypted secret managers."
}
```

**What this tests:**
- ✅ Vector search retrieves relevant SOPs
- ✅ LLM correctly identifies violations
- ✅ LLM identifies compliant messages
- ✅ Structured JSON response format

---

### Test 6: Start Slack Bot

**Terminal 2:**
```bash
python cli.py start-bot
```

**Expected Output:**
```
🤖 SOP Compliance Bot starting...
📡 API endpoint: http://localhost:8000
👂 Listening to all Slack channels...

✅ Connected to API

[14:23:45] #general <U12345ABC>: Hey team, working on the new feature
   ✓ Compliant

[14:24:12] #engineering <U67890DEF>: Can someone share the staging db password?
   🚨 VIOLATION DETECTED!
      Severity: MEDIUM
      Rule: Credential sharing in public channels
   ✅ Warning sent to channel

[14:25:03] #general <U11111ZZZ>: Let's meet at 3pm
   ✓ Compliant
```

**In Slack, you should see:**

When a violation occurs, the bot posts:

```
⚠️ SOP Violation Detected (MEDIUM)

Rule Violated: Credential sharing in public channels

Why this is a violation:
Production and staging credentials must never be shared in Slack channels, 
even in private channels. Use a secure password manager or secret management 
system instead.

Original message:
> Can someone share the staging db password?

Please review our SOPs and ensure compliance. If you believe this is a false 
positive, contact your manager.
```

**What to test in Slack:**

1. **Test violation messages:**
   - "Here's the API key: sk-abc123..."
   - "Database password is admin123"
   - "This code is terrible, fire the dev"
   
2. **Test compliant messages:**
   - "I shared the credentials via Vault"
   - "Meeting at 2pm?"
   - "Great work on the feature!"

3. **Test edge cases:**
   - Code snippets with dummy passwords (should ideally flag)
   - Questions about policies (should not flag)
   - General conversation (should not flag)

**Expected bot behavior:**
- ✅ Responds only to violations (no spam on compliant messages)
- ✅ Shows severity level with emoji
- ✅ Cites specific SOP rule violated
- ✅ Provides clear explanation
- ✅ Quotes original message

**If bot doesn't respond:**
- Check bot is invited to the channel: `/invite @YourBotName`
- Verify SLACK_BOT_TOKEN and SLACK_APP_TOKEN in .env
- Check Socket Mode is enabled in Slack App settings
- Ensure required OAuth scopes are granted

---

## Performance Expectations

### Typical Response Times

- **Ingestion:** 1-3 seconds per document
- **Message check:** 500ms - 2 seconds
- **Bot response:** 1-3 seconds from message to warning

### Accuracy Expectations

- **True Positives:** Should catch 90%+ of real violations
- **False Positives:** <10% (may flag borderline cases)
- **False Negatives:** <15% (may miss subtle violations)

### Cost Estimates (per 100 messages)

- **OpenAI API:** ~$0.02-0.05 (GPT-4o-mini)
- **Pinecone:** Free tier covers ~1M queries/month
- **Total:** ~$0.02-0.05 per 100 messages checked

---

## Troubleshooting Common Issues

### Issue: "ModuleNotFoundError"
**Solution:** Activate venv and install deps
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Address already in use"
**Solution:** Kill process on port 8000
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue: "Field required" validation error
**Solution:** Check .env file has all required keys
```bash
python cli.py check-setup
```

### Issue: Bot doesn't respond in Slack
**Solution:** 
1. Invite bot: `/invite @YourBotName`
2. Check bot token permissions
3. Verify Socket Mode is enabled

### Issue: No relevant SOPs retrieved
**Solution:**
1. Check documents were ingested successfully
2. Verify Pinecone index is inference-enabled
3. Try increasing TOP_K in .env

---

## Success Criteria

Your system is working correctly when:

✅ **Setup**
- All environment variables configured
- FastAPI server starts without errors
- API health check returns `{"status":"ok"}`

✅ **Ingestion**
- Notion documents successfully uploaded
- Manual test file ingests without errors
- Pinecone shows documents in index

✅ **Detection**
- Manual API call detects obvious violations
- Manual API call passes compliant messages
- Retrieved SOPs are relevant to query

✅ **Bot**
- Bot connects to Slack successfully
- Violation messages trigger warnings
- Compliant messages don't trigger spam
- Warning format is clear and actionable

✅ **Demo Ready**
- Can send violation message and get instant response
- Response includes specific rule and explanation
- System handles multiple channels simultaneously
- Performance is acceptable (<3s per message)

---

## Demo Script

For hackathon presentation:

1. **Show ingestion** (1 min):
   ```bash
   python cli.py ingest-notion
   ```
   "Here we're importing all our company SOPs from Notion..."

2. **Start bot** (30 sec):
   ```bash
   python cli.py start-bot
   ```
   "Now the bot is monitoring all Slack channels in real-time..."

3. **Send violation** (2 min):
   - Open Slack
   - Type: "Quick fix: use password admin123 for the staging server"
   - Wait 2-3 seconds
   - **Bot responds with warning!**
   - "Notice it identified the specific SOP rule violated and severity level"

4. **Show compliant message** (1 min):
   - Type: "I've stored the staging credentials in AWS Secrets Manager"
   - **Bot stays silent** (no false positive)
   - "And it correctly recognizes compliant behavior"

5. **Show API** (30 sec):
   - Open `http://localhost:8000/docs`
   - "The backend provides REST APIs for custom integrations"

**Total demo time:** 5 minutes
