import json
from openai import OpenAI
from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

_SYSTEM_PROMPT = """You are an SOP compliance auditor. You will be given a Slack message and a list of relevant SOP (Standard Operating Procedure) documents retrieved from a vector database.

Your task is to determine whether the message violates any SOP rule.

Respond ONLY with a valid JSON object in exactly this format:
{
  "violated": true | false,
  "rule": "<name or short description of the violated SOP rule, or null if no violation>",
  "severity": "<low | medium | high | null if no violation>",
  "explanation": "<brief explanation of why this is or is not a violation>"
}

Severity guidelines:
- low: minor deviation, unlikely to cause immediate harm
- medium: moderate deviation, could cause operational issues
- high: serious deviation, could cause significant harm or non-compliance

If no violation is found, set violated to false, and rule and severity to null."""


def check_violation(message_text: str, sop_docs: list[dict]) -> dict:
    docs_text = "\n\n".join(
        f"[SOP: {doc['metadata'].get('title', doc['id'])} (relevance: {doc['score']:.2f})]\n{doc['metadata'].get('content', '')}"
        for doc in sop_docs
    )

    user_content = f"Slack message:\n{message_text}\n\nRelevant SOP documents:\n{docs_text}"

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )

    return json.loads(response.choices[0].message.content)
