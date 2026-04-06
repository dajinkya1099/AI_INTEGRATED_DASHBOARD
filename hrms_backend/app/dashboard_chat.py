"""
dashboard_chat.py  — Dashboard chatbot endpoint (simplified, no activeModule)

Flow:
  1. Frontend sends { schemaName, textQue }
  2. Calls build_prompt_for_query_genrate() → SQL prompt
  3. Ollama → SQL query
  4. Execute SQL → raw rows (tuples or dicts, both handled)
  5. Ollama → plain English answer
  6. Return { answer, sql }

Register in main.py:
  from app.dashboard_chat import router as chat_router
  app.include_router(chat_router)
"""

import json, re, requests
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import OLLAMA_URL, OLLAMA_MODEL_INTENT

# ── Import your existing prompt builder ──────────────────────────────────────
# Adjust import path to wherever build_prompt_for_query_genrate lives
# from app.visualization_service import build_prompt_for_query_genrate
from app.query_generator import build_prompt_for_query_genrate

# ── Import your existing DB executor ─────────────────────────────────────────
# We import get_db_connection directly so we can control cursor + column names
# from app.database import get_db_connection   # ← adjust to your actual function name
from app.db import get_connection
from app.schema_generator import clean_sql_query_and_append_schemaName

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST MODEL
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    schemaName: str = ""
    textQue:    str = ""


# ─────────────────────────────────────────────────────────────────────────────
# OLLAMA HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _ollama(prompt: str, max_tokens: int = 300, temperature: float = 0.1) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":  OLLAMA_MODEL_INTENT,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "num_ctx":     8192
                }
            },
            timeout=200
        )
        return resp.json().get("response", "").strip()
    except Exception as e:
        print(f"[dashboard_chat] Ollama error: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Generate SQL using existing build_prompt_for_query_genrate()
# ─────────────────────────────────────────────────────────────────────────────

def generate_sql(request: ChatRequest) -> str:
    prompt = build_prompt_for_query_genrate(request)

    print(f"[dashboard_chat] prompt..: {prompt}")
    print("[dashboard_chat] Calling Ollama for SQL...")
    raw = _ollama(prompt, max_tokens=400, temperature=0.05)
    print(f"[dashboard_chat] Raw SQL response: {raw[:150]}")

    # Strip markdown fences
    sql = re.sub(r"```(?:sql)?\s*", "", raw).strip().rstrip("`").strip()

    # Extract just the SELECT statement
    m = re.search(r"(SELECT\b[\s\S]+?)(?:;|\Z)", sql, re.IGNORECASE)
    if m:
        sql = m.group(1).strip() + ";"

    return sql if sql.upper().startswith("SELECT") else ""


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Execute SQL, return list of dicts (handles tuples + dicts)
# ─────────────────────────────────────────────────────────────────────────────

def run_query(schema_name: str, sql: str) -> list:
    """
    Executes SQL and always returns a list of dicts regardless of what
    the DB driver returns (tuples, RealDictRow, named tuples, etc.)
    """
    try:
        print(f"[dashboard_chat] clean_sql_query_and_append_schemaName..: {sql}")
        updatedQuery =clean_sql_query_and_append_schemaName(schema_name,sql)
        print(f"[dashboard_chat] clean_sql_query_and_append_schemaName..: {updatedQuery}")
        conn = get_connection()
        # conn = get_db_connection(schema_name)
        cur  = conn.cursor()
        cur.execute(updatedQuery)

        # Get column names from cursor description
        col_names = [desc[0] for desc in cur.description]
        raw_rows  = cur.fetchall()

        cur.close()
        conn.close()

        # Convert every row to a plain dict
        result = []
        for row in raw_rows:
            if isinstance(row, dict):
                result.append(row)
            else:
                # tuple, RealDictRow, NamedTuple etc.
                result.append(dict(zip(col_names, row)))

        print(f"[dashboard_chat] Rows fetched: {len(result)}")
        return result

    except Exception as e:
        print(f"[dashboard_chat] DB error: {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Convert rows → plain English (text only, no table)
# ─────────────────────────────────────────────────────────────────────────────

def rows_to_answer(question: str, rows: list) -> str:
    if not rows:
        return "No results found for your question."

    # rows is now guaranteed list of dicts
    sample = rows[:15]

    prompt = (
        "You are a friendly HR data assistant.\n"
        "The user asked a question and a database query returned results.\n"
        "Write a SHORT plain-English answer — 1 to 3 sentences only.\n"
        "Use specific numbers from the data. Be direct and conversational.\n"
        "Do NOT mention SQL, tables, columns, or technical terms.\n"
        "Do NOT list all rows — give the key insight only.\n\n"
        f"Question: {question}\n\n"
        f"Query result ({len(rows)} total rows):\n"
        f"{json.dumps(sample, default=str)}\n\n"
        "Answer (1-3 sentences):"
    )

    answer = _ollama(prompt, max_tokens=180, temperature=0.3)

    # Clean any accidental wrapping
    answer = re.sub(r'^["\'\s]+|["\'\s]+$', '', answer).strip()
    answer = re.sub(r'^Answer:\s*', '', answer, flags=re.IGNORECASE).strip()

    return answer or f"Found {len(rows)} result(s) for your question."


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/dashboard-chat")
async def dashboard_chat(request: ChatRequest):
    """
    POST /dashboard-chat
    Body:   { schemaName: str, textQue: str }
    Returns: { answer: str, sql: str }
    """
    print(f"\n{'─'*50}")
    print(f"[DashboardChat] Q      : {request.textQue}")
    print(f"[DashboardChat] Schema : {request.schemaName}")

    # ── Validation ────────────────────────────────────────────────────────────
    if not request.schemaName:
        return {"answer": "Please select a schema first.", "sql": ""}

    if not request.textQue.strip():
        return {"answer": "Please type a question.", "sql": ""}

    # ── Safety — block write operations ──────────────────────────────────────
    blocked = {"drop","delete","insert","update","truncate","alter","create","grant","revoke"}
    if set(request.textQue.lower().split()) & blocked:
        return {"answer": "⚠️ I can only read data, not modify it.", "sql": ""}

    # ── Step 1: Generate SQL ──────────────────────────────────────────────────
    try:
        sql = generate_sql(request)
        print(f"[DashboardChat] SQL    : {sql[:150]}")
    except Exception as e:
        print(f"[DashboardChat] SQL gen error: {e}")
        return {"answer": "I couldn't generate a query. Try rephrasing your question.", "sql": ""}

    if not sql:
        return {
            "answer": "I couldn't turn your question into a query. Try something like: 'How many employees are there?'",
            "sql": ""
        }

    # ── Step 2: Execute SQL ───────────────────────────────────────────────────
    try:
        rows = run_query(request.schemaName, sql)
    except Exception as e:
        print(f"[DashboardChat] DB error: {e}")
        return {
            "answer": "The query ran but the database returned an error. Try a simpler question.",
            "sql": sql
        }

    # ── Step 3: Rows → answer ────────────────────────────────────────────────
    answer = rows_to_answer(request.textQue, rows)
    print(f"[DashboardChat] Answer : {answer}")
    print(f"{'─'*50}\n")

    return {"answer": answer, "sql": sql}