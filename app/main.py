from fastapi import FastAPI
from app.routers import ingest, check, analytics, feedback, violations

app = FastAPI(
    title="SOP Violation Flagger",
    version="0.1.0",
    description="Checks Slack messages against SOP documents stored in Pinecone and flags violations using LLM reasoning.",
)

app.include_router(ingest.router)
app.include_router(check.router)
app.include_router(analytics.router)
app.include_router(feedback.router)
app.include_router(violations.router)


@app.get("/")
async def health_check():
    return {"status": "ok"}
