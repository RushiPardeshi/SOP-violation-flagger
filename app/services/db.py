"""
SQLite persistence for violations and feedback.
Used for analytics, reporting, and feedback loop.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sop_violations.db"


def _ensure_db_dir():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_conn():
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                message_text TEXT NOT NULL,
                message_ts TEXT NOT NULL,
                rule TEXT NOT NULL,
                severity TEXT NOT NULL,
                explanation TEXT,
                bot_message_ts TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                violation_id INTEGER NOT NULL,
                feedback_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (violation_id) REFERENCES violations(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_violations_bot_msg 
            ON violations(channel_id, bot_message_ts)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_violations_created 
            ON violations(created_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_violation 
            ON feedback(violation_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS onboarded_users (
                user_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            )
        """)


@contextmanager
def get_db():
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def record_violation(
    channel_id: str,
    user_id: str,
    message_text: str,
    message_ts: str,
    rule: str,
    severity: str,
    explanation: str,
    bot_message_ts: str | None = None,
) -> int:
    """Record a violation. Returns violation id."""
    init_db()
    created_at = datetime.utcnow().isoformat()
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO violations 
            (channel_id, user_id, message_text, message_ts, rule, severity, explanation, bot_message_ts, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (channel_id, user_id, message_text, message_ts, rule, severity, explanation, bot_message_ts, created_at),
        )
        return cur.lastrowid


def update_violation_bot_message(violation_id: int, bot_message_ts: str) -> None:
    """Update violation with bot message ts (for reaction lookup)."""
    with get_db() as conn:
        conn.execute(
            "UPDATE violations SET bot_message_ts = ? WHERE id = ?",
            (bot_message_ts, violation_id),
        )


def get_violation_by_bot_message(channel_id: str, bot_message_ts: str) -> dict | None:
    """Look up violation by our bot's message location (for reaction feedback)."""
    init_db()
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM violations WHERE channel_id = ? AND bot_message_ts = ?",
            (channel_id, bot_message_ts),
        ).fetchone()
        return dict(row) if row else None


def record_feedback(violation_id: int, feedback_type: str, user_id: str) -> None:
    """Record user feedback: 'false_positive' or 'correct'."""
    init_db()
    if feedback_type not in ("false_positive", "correct"):
        raise ValueError("feedback_type must be 'false_positive' or 'correct'")
    created_at = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO feedback (violation_id, feedback_type, user_id, created_at) VALUES (?, ?, ?, ?)",
            (violation_id, feedback_type, user_id, created_at),
        )


def get_violations(
    limit: int = 100,
    offset: int = 0,
    channel_id: str | None = None,
    user_id: str | None = None,
    since: str | None = None,
) -> list[dict]:
    """Fetch violations with optional filters."""
    init_db()
    query = "SELECT * FROM violations WHERE 1=1"
    params: list = []
    if channel_id:
        query += " AND channel_id = ?"
        params.append(channel_id)
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    if since:
        query += " AND created_at >= ?"
        params.append(since)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with _get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def is_onboarded(user_id: str) -> bool:
    """Check if user has received onboarding DM."""
    init_db()
    with _get_conn() as conn:
        row = conn.execute("SELECT 1 FROM onboarded_users WHERE user_id = ?", (user_id,)).fetchone()
        return row is not None


def record_onboarded(user_id: str) -> None:
    """Record that user received onboarding DM."""
    init_db()
    created_at = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO onboarded_users (user_id, created_at) VALUES (?, ?)",
            (user_id, created_at),
        )


def get_feedback_examples(
    max_false_positives: int = 3,
    max_correct: int = 3,
) -> list[dict]:
    """
    Fetch recent feedback examples for few-shot learning.
    Returns list of {message_text, rule, feedback_type} ordered by recency.
    """
    init_db()
    examples: list[dict] = []

    with _get_conn() as conn:
        # Get false positives (user said it was NOT a violation)
        fp_rows = conn.execute(
            """
            SELECT v.message_text, v.rule, f.feedback_type
            FROM feedback f
            JOIN violations v ON f.violation_id = v.id
            WHERE f.feedback_type = 'false_positive'
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (max_false_positives,),
        ).fetchall()

        # Get correct flags (user confirmed it WAS a violation)
        correct_rows = conn.execute(
            """
            SELECT v.message_text, v.rule, f.feedback_type
            FROM feedback f
            JOIN violations v ON f.violation_id = v.id
            WHERE f.feedback_type = 'correct'
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (max_correct,),
        ).fetchall()

    for row in fp_rows:
        r = dict(row)
        examples.append({"message_text": r.get("message_text", ""), "rule": r.get("rule", ""), "feedback_type": "false_positive"})
    for row in correct_rows:
        r = dict(row)
        examples.append({"message_text": r.get("message_text", ""), "rule": r.get("rule", ""), "feedback_type": "correct"})

    return examples


def get_analytics(
    since: str | None = None,
) -> dict:
    """Aggregate analytics: counts, by channel, by user, by rule, feedback stats."""
    init_db()
    params: list = []
    where = ""
    if since:
        where = " AND v.created_at >= ?"
        params.append(since)

    with _get_conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM violations v WHERE 1=1{where}",
            params,
        ).fetchone()[0]

        by_severity = dict(
            conn.execute(
                f"SELECT severity, COUNT(*) as cnt FROM violations WHERE 1=1{where} GROUP BY severity",
                params,
            ).fetchall()
        )

        by_channel = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT channel_id, COUNT(*) as count 
                FROM violations WHERE 1=1{where}
                GROUP BY channel_id ORDER BY count DESC
                """,
                params,
            ).fetchall()
        ]

        by_user = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT user_id, COUNT(*) as count 
                FROM violations WHERE 1=1{where}
                GROUP BY user_id ORDER BY count DESC
                """,
                params,
            ).fetchall()
        ]

        by_rule = [
            dict(row)
            for row in conn.execute(
                f"""
                SELECT rule, COUNT(*) as count 
                FROM violations WHERE 1=1{where}
                GROUP BY rule ORDER BY count DESC
                """,
                params,
            ).fetchall()
        ]

        feedback_where = "v.created_at >= ?" if since else "1=1"
        feedback_params = [since] if since else []

        false_positives = conn.execute(
            f"""
            SELECT COUNT(*) FROM feedback f
            JOIN violations v ON f.violation_id = v.id
            WHERE f.feedback_type = 'false_positive' AND {feedback_where}
            """,
            feedback_params,
        ).fetchone()[0]

        correct_flags = conn.execute(
            f"""
            SELECT COUNT(*) FROM feedback f
            JOIN violations v ON f.violation_id = v.id
            WHERE f.feedback_type = 'correct' AND {feedback_where}
            """,
            feedback_params,
        ).fetchone()[0]

    return {
        "total_violations": total,
        "by_severity": by_severity,
        "by_channel": by_channel,
        "by_user": by_user,
        "by_rule": by_rule,
        "feedback": {
            "false_positives": false_positives,
            "correct": correct_flags,
        },
    }
