"""
visualization_service.py — AI Agent for Fast Dynamic Visualization
═══════════════════════════════════════════════════════════════════

ARCHITECTURE COMPARISON
────────────────────────────────────────────────────────────────
OLD architecture (Sequential — two separate files):
  Request → Call1(20-40s) → wait → Call2(15-25s) → wait → Response
  Total: 35-65 seconds. Always both Ollama calls. No routing.

NEW architecture (Single file — Smart Agent):
  Request
    │
    ▼
  AgentRouter (instant, Python) — picks fastest strategy:
    │
    ├─ CACHE_HIT    → return instantly   <0.01s
    ├─ PYTHON_ONLY  → no Ollama at all    0.1-0.5s  (table/text/filter)
    ├─ INTENT_ONLY  → 1 Ollama call only  10-20s    (simple charts)
    └─ FULL_AGENT   → 2 Ollama calls      15-25s    (complex charts)
                      with parallel Python fallback always running

HOW TO USE (replace in FastAPI router)
────────────────────────────────────────────────────────────────
  # Just use this one file:
  from visualization_service import generate_react_visualization, cache_clear, cache_stats

  # Cache management:
  from visualization_agent import cache_clear, cache_stats

STRATEGY ROUTING LOGIC
────────────────────────────────────────────────────────────────
  Question keywords detected            → Strategy chosen
  ─────────────────────────────────────────────────────────
  Same question seen before             → CACHE_HIT   (instant)
  "summarize / in text / explain..."    → PYTHON_ONLY (no Ollama)
  "who / which / show me / find / details" → PYTHON_ONLY (no Ollama)
  "count / total / sum / distribution"  → INTENT_ONLY (1 Ollama call)
  Anything else / ambiguous             → FULL_AGENT  (2 Ollama calls)

TOOLS IN THE AGENT
────────────────────────────────────────────────────────────────
  Tool 1: AgentRouter       — decides strategy (instant)
  Tool 2: PythonAnalyzer    — Python-only intent analysis (<10ms)
  Tool 3: OllamaIntentCall  — Call 1, model=qwen2.5:7b-instruct
  Tool 4: PythonHTMLBuilder — Python HTML builders (<50ms)
  Tool 5: OllamaHTMLCall    — Call 2, model=qwen2.5-coder:3b
                              (parallel Python fallback always runs too)
  Tool 6: Validator         — self-heals broken HTML automatically
  Tool 7: CacheStore        — stores result for next request

SELF-HEALING
────────────────────────────────────────────────────────────────
  If Ollama Call 2 returns broken HTML:
    → Auto-fix with _post_process() + _fix_overflow()
    → If still broken → rebuild from Python instantly
    → No extra Ollama call needed
    → result["self_healed"] = True in response

RESPONSE FIELDS
────────────────────────────────────────────────────────────────
  reactCode        — complete HTML to render in iframe
  outputType       — bar|pie|line|area|table|text|card
  strategy         — which strategy was used
  cache_hit        — true if returned from cache
  response_time_s  — total seconds taken
  call1_model      — which model did Call 1 (or "python")
  call2_model      — which model did Call 2 (or "python")
  self_healed      — true if HTML was auto-fixed
═══════════════════════════════════════════════════════════════════
"""

import requests, json, re, hashlib, time, threading
from collections import Counter, OrderedDict
from typing import Any
from pydantic import BaseModel
from fastapi import HTTPException
from app.config import OLLAMA_URL, OLLAMA_MODEL_INTENT, OLLAMA_MODEL_CODE


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

# OLLAMA_URL = "http://localhost:11434/api/generate"

# Call 1 — Intent analysis: best at instructions + JSON output
# OLLAMA_MODEL_INTENT = "qwen2.5:7b-instruct"

# Call 2 — HTML/React code generation: purpose-built for code, 2-3x faster
# Install: ollama pull qwen2.5-coder:3b
# Auto-falls back to OLLAMA_MODEL_INTENT if not installed
# OLLAMA_MODEL_CODE = "qwen2.5-coder:3b"

# ─────────────────────────────────────────────────────────────────────────────
# LRU RESPONSE CACHE
# ─────────────────────────────────────────────────────────────────────────────

_CACHE_MAX = 200          # max entries in memory
_CACHE_TTL = 3600         # 1 hour TTL
_cache: OrderedDict = OrderedDict()

def _cache_key(schema: str, question: str) -> str:
    raw = f"{schema.strip().lower()}|{question.strip().lower()}"
    return hashlib.md5(raw.encode()).hexdigest()

def _cache_get(key: str):
    if key not in _cache:
        return None
    entry = _cache[key]
    if time.time() - entry["ts"] > _CACHE_TTL:
        del _cache[key]
        return None
    _cache.move_to_end(key)
    return entry["value"]

def _cache_set(key: str, value: dict):
    if key in _cache:
        _cache.move_to_end(key)
    _cache[key] = {"value": value, "ts": time.time()}
    while len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)

def cache_clear():
    """Clear all cached results. Call this when underlying data changes."""
    _cache.clear()
    print("[Agent-Cache] Cleared all entries")

def cache_stats() -> dict:
    """Return cache statistics for monitoring."""
    return {
        "entries":     len(_cache),
        "max":         _CACHE_MAX,
        "ttl_seconds": _CACHE_TTL,
        "keys":        [k[:8] for k in list(_cache.keys())[-10:]]  # last 10 keys preview
    }

CDN_SCRIPTS = (
    '<script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>\n'
    '    <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>\n'
    '    <script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>\n'
    '    <script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.js"></script>\n'
    '    <script src="https://unpkg.com/@babel/standalone@7.21.3/babel.min.js"></script>'
)

RECHARTS_INIT = (
    'const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,\n'
    '              ResponsiveContainer, PieChart, Pie, Cell,\n'
    '              LineChart, Line, AreaChart, Area,\n'
    '              ScatterChart, Scatter,\n'
    '              RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } = Recharts;\n'
    '        const COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16","#ec4899","#14b8a6"];'
)

BASE_CSS = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body {
            font-family: 'Segoe UI', sans-serif;
            background: #f1f5f9;
            min-height: 100vh;
            overflow-x: hidden;
            width: 100%;
        }
        body {
            padding: 24px;
        }
        .card {
            background: #fff;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            width: 100%;
            overflow: hidden;
        }
        h2 {
            color: #1e293b;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .subtitle {
            color: #64748b;
            font-size: 13px;
            margin-bottom: 24px;
        }
        #root {
            width: 100%;
            overflow: hidden;
        }
"""


# ─────────────────────────────────────────────────────────────────────────────
# REQUEST MODEL
# ─────────────────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    schemaName: str
    query:      str
    textQue:    str
    dbJsonData: Any


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY ENUM
# ─────────────────────────────────────────────────────────────────────────────

class Strategy:
    CACHE_HIT   = "cache_hit"    # Same question seen before — return instantly
    PYTHON_ONLY = "python_only"  # Table/text/filter — zero Ollama calls
    INTENT_ONLY = "intent_only"  # Simple chart — only Call 1 Ollama
    FULL_AGENT  = "full_agent"   # Complex — both Ollama calls (with parallel fallback)


# ─────────────────────────────────────────────────────────────────────────────
# AGENT STATE — carries all context through the pipeline
# ─────────────────────────────────────────────────────────────────────────────

class AgentState:
    def __init__(self, question, schema_name, rows, query=""):
        self.question    = question
        self.schema_name = schema_name
        self.rows        = rows
        self.query       = query
        self.t_start     = time.time()

        # Agent decisions
        self.strategy    = Strategy.FULL_AGENT
        self.cache_key   = ""

        # Tool outputs
        self.structured  = {}
        self.html        = ""
        self.issues      = []

        # Tracking
        self.call1_model = ""
        self.call2_model = ""
        self.t_call1     = 0.0
        self.t_call2     = 0.0
        self.self_healed = False

    def elapsed(self) -> float:
        return round(time.time() - self.t_start, 3)

    def log(self, msg: str):
        print(f" [Agent +{self.elapsed():.2f}s] {msg}")



# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD SETS FOR ROUTING
# ─────────────────────────────────────────────────────────────────────────────

# Text/narrative → Python only (no Ollama at all)
_TEXT_KW = {
    "summarize", "summary", "summarized", "in text", "as text", "text format",
    "insight", "insights", "report", "analyze", "analysis", "describe",
    "explain", "tell me", "narrative", "write about", "overview", "give me"
}

# Filter/list → Python only (table, no Ollama)
# NOTE: No hardcoded schema words (employee, project, etc.)
# Detection is purely grammar-based — works for ANY schema.
_FILTER_KW = {
    "who ", "which ", "having ", "that have", "that are",
    "show all", "list all", "show me", "find me",
    "where ", "with status", "with type", "filter by",
}

# Generic question starters that suggest showing specific rows
_FILTER_STARTERS = (
    "who ", "which ", "show me ", "find me ", "list me ",
    "get me ", "give me ", "fetch ", "display ",
)

# Generic question verbs that suggest detail view
_DETAIL_VERBS = (
    "details", "detail", "info", "information", "profile",
    "records", "entries", "data of", "data for",
)

# Simple aggregation → Intent only (1 Ollama call, Python builds HTML)
_SIMPLE_KW = {
    "count", "how many", "distribution", "breakdown", "frequency",
    "total", "sum", "average", "avg", "mean", "by ", "group by",
    "per ", "each "
}


def _is_filter_question(q: str, rows: list) -> bool:
    """
    Dynamically detect if the user wants to filter/show specific rows.
    Works for ANY schema — no hardcoded entity names.

    Detection logic:
    1. Grammar-based starters: "who ", "which ", "show me ", "find "...
    2. Detail request words: "details", "info", "profile"...
    3. Value match: if any actual data value appears in the question
       e.g. "Project Alpha details" — "Project Alpha" is a value in the data
    4. Having/where patterns: "having salary > ...", "where status = ..."
    """
    # 1. Grammar starters
    if any(q.startswith(s) or f" {s}" in q for s in _FILTER_STARTERS):
        return True

    # 2. Detail request words
    if any(d in q for d in _DETAIL_VERBS):
        return True

    # 3. "having", "where", "with" filter patterns
    if any(kw in q for kw in ("having ", "where ", "with status", "with type", "filter by", "that have", "that are")):
        return True

    # 4. Check if any actual DATA VALUE from the rows appears in the question
    #    This handles: "show Project Alpha", "employees in HR", "status Active"
    #    without knowing what schema we're on
    if rows:
        sample = rows[0]
        for col, val in sample.items():
            if val and isinstance(val, str) and len(str(val)) > 2:
                # Check a few rows, not just sample, to get more values
                all_vals = set(str(r.get(col, "")) for r in rows[:50] if r.get(col))
                for v in all_vals:
                    if len(v) > 2 and v.lower() in q:
                        return True
    return False


def     tool_1_route(state: AgentState):
    """
    TOOL 1 — AgentRouter
    Decides which strategy to use. Runs in microseconds. No Ollama.
    """
    q  = state.question.lower()
    ck = _cache_key(state.schema_name, state.question)
    state.cache_key = ck

    # Cache hit? Return instantly
    if _cache_get(ck) is not None:
        state.strategy = Strategy.CACHE_HIT
        state.log(f"Strategy: CACHE_HIT ✅")
        return

    # Text/narrative keywords → Python only
    if any(kw in q for kw in _TEXT_KW):
        state.strategy = Strategy.PYTHON_ONLY
        state.log(f"Strategy: PYTHON_ONLY (text/summary detected)")
        return

    # Filter/list detection — purely grammar-based, no schema-specific words
    # Detects: "who has...", "which project...", "show me...", "find records where..."
    # Also detects: question starts with a data VALUE that exists in the rows
    if _is_filter_question(q, state.rows):
        state.strategy = Strategy.PYTHON_ONLY
        state.log(f"Strategy: PYTHON_ONLY (filter/list detected)")
        return

    # Simple aggregation → Intent only (skip Call 2 Ollama)
    if any(kw in q for kw in _SIMPLE_KW):
        state.strategy = Strategy.INTENT_ONLY
        state.log(f"Strategy: INTENT_ONLY (simple chart detected)")
        return

    # Fallback: full agent (both Ollama calls)
    state.strategy = Strategy.FULL_AGENT
    state.log(f"Strategy: FULL_AGENT (complex/ambiguous question)")



# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2 — PYTHON ANALYZER (no Ollama, <10ms)
# ─────────────────────────────────────────────────────────────────────────────

def tool_2_python_analyze(state: AgentState):
    """
    TOOL 2 — Pure Python intent analysis.
    Runs in <10ms. Used for PYTHON_ONLY strategy.
    """
    t = time.time()
    state.log("Tool-2: Python analyze...")

    sample   = state.rows[0] if state.rows else {}
    columns  = list(sample.keys())
    num_cols = [k for k,v in sample.items() if isinstance(v,(int,float)) and v is not None]
    str_cols = [k for k,v in sample.items() if isinstance(v,str) and v is not None]

    state.structured = _python_analyze(
        state.question, state.rows, columns, num_cols, str_cols
    )
    state.call1_model = "python"
    state.t_call1     = time.time() - t
    state.log(f"Tool-2 done in {state.t_call1:.3f}s — viz={state.structured.get('viz_type')}")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3 — OLLAMA INTENT CALL (Call 1)
# ─────────────────────────────────────────────────────────────────────────────

def tool_3_ollama_intent(state: AgentState):
    """
    TOOL 3 — Ollama Call 1 (model: qwen2.5:7b-instruct).
    Understands intent, transforms data, decides viz type.
    Falls back to Python if Ollama fails or times out.
    """
    t = time.time()
    state.log(f"Tool-3: Ollama intent call ({OLLAMA_MODEL_INTENT})...")

    try:
        state.structured = call1_analyze_and_structure(
            question    = state.question,
            rows        = state.rows,
            schema_name = state.schema_name,
        )
        state.call1_model = OLLAMA_MODEL_INTENT
    except Exception as e:
        state.log(f"Tool-3 error: {e} — Python fallback")
        sample   = state.rows[0] if state.rows else {}
        columns  = list(sample.keys())
        num_cols = [k for k,v in sample.items() if isinstance(v,(int,float)) and v is not None]
        str_cols = [k for k,v in sample.items() if isinstance(v,str) and v is not None]
        state.structured  = _python_analyze(state.question, state.rows, columns, num_cols, str_cols)
        state.call1_model = "python-fallback"

    state.t_call1 = time.time() - t
    state.log(f"Tool-3 done in {state.t_call1:.2f}s — viz={state.structured.get('viz_type')} title={state.structured.get('title')}")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 4 — PYTHON HTML BUILDER (<50ms, guaranteed correct)
# ─────────────────────────────────────────────────────────────────────────────

def tool_4_python_html(state: AgentState):
    """
    TOOL 4 — Python HTML builder.
    Runs in <50ms. 100% reliable — no LLM hallucination.
    Used for: table, text, card, and INTENT_ONLY charts.
    """
    t = time.time()
    state.log("Tool-4: Python HTML builder...")

    s    = state.structured
    viz  = s.get("viz_type", "bar")
    data = s.get("data", [])

    # Sanitize title — never "None"
    title = (s.get("title") or "").strip()
    if not title or title.lower() in ("none", "null", ""):
        # Try to get name from first raw_row
        raw_rows = s.get("raw_rows", [])
        if raw_rows:
            first = raw_rows[0]
            name_keys = ["name","project_name","employee_name","title","label"]
            title = next((str(first.get(k,"")) for k in name_keys if first.get(k)), "")
        title = title or state.schema_name or "Data"

    subtitle = s.get("subtitle", "")
    x_key    = s.get("x_key")
    y_key    = s.get("y_key")

    if not data:
        state.html = _html_empty(title)
    elif viz == "table":
        state.html = _build_table(data, title, subtitle, state.schema_name, state.question)
    elif viz == "text":
        state.html = _call2_text(data, title, subtitle, state.schema_name, state.question, structured=s)
    elif viz == "card":
        state.html = _build_cards(data, title, subtitle, state.schema_name)
    else:
        # Chart built in Python (fast, reliable)
        x  = x_key or "name"
        y  = y_key or "value"
        dj = json.dumps(data, default=str)
        state.html = _build_chart_python(data, title, subtitle, x, y, viz, state.schema_name, len(data), dj)

    state.call2_model = "python"
    state.t_call2     = time.time() - t
    state.log(f"Tool-4 done in {state.t_call2:.3f}s — HTML {len(state.html)} chars")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 5 — OLLAMA HTML CALL (Call 2) + parallel Python fallback
# ─────────────────────────────────────────────────────────────────────────────

def tool_5_ollama_html(state: AgentState):
    """
    TOOL 5 — Ollama Call 2 (model: qwen2.5-coder:3b).
    Generates React HTML for complex charts.

    PARALLEL TRICK: Python fallback builds simultaneously in a background thread.
    → If Ollama succeeds → use Ollama result (better quality)
    → If Ollama fails / returns broken HTML → Python fallback is already ready (0 wait)
    This means worst-case is same as INTENT_ONLY, not a full extra timeout.
    """
    t = time.time()
    state.log(f"Tool-5: Ollama HTML call ({OLLAMA_MODEL_CODE}) + parallel Python fallback...")

    s    = state.structured
    viz  = s.get("viz_type", "bar")
    data = s.get("data", [])
    x    = s.get("x_key") or "name"
    y    = s.get("y_key") or "value"
    dj   = json.dumps(data, default=str)
    n    = len(data)

    # Sanitize title
    title = (s.get("title") or "").strip()
    if not title or title.lower() in ("none","null",""):
        title = state.schema_name or "Data"
    subtitle = s.get("subtitle", "")

    # ── Start Python fallback in background (parallel) ────────────────────────
    _fallback = {}

    def _build_fallback():
        _fallback["html"] = _build_chart_python(
            data, title, subtitle, x, y, viz, state.schema_name, n, dj
        )

    fallback_thread = threading.Thread(target=_build_fallback, daemon=True)
    fallback_thread.start()

    # ── Build prompt ──────────────────────────────────────────────────────────
    spec   = _chart_jsx_spec(viz, x, y)
    prompt = _make_chart_prompt(viz, title, subtitle, state.schema_name, x, y, n, dj, spec)

    # ── Ollama request ────────────────────────────────────────────────────────
    ollama_html = None
    used_model  = "python-parallel-fallback"

    try:
        def _post(model):
            return requests.post(
                OLLAMA_URL,
                json={
                    "model":  model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 3000,
                        "temperature": 0.1,
                        "top_p":       0.9,
                        "num_ctx":     8192,
                    },
                },
                timeout=500,
            )

        resp      = _post(OLLAMA_MODEL_CODE)
        resp_json = resp.json()

        # Auto-fallback if coder model not installed
        if "error" in resp_json and "not found" in resp_json.get("error","").lower():
            state.log(f"{OLLAMA_MODEL_CODE} not found → {OLLAMA_MODEL_INTENT}")
            resp      = _post(OLLAMA_MODEL_INTENT)
            resp_json = resp.json()
            used_model = OLLAMA_MODEL_INTENT
        else:
            used_model = OLLAMA_MODEL_CODE

        raw        = resp_json.get("response","").strip()
        candidate  = _extract_html(raw)
        candidate  = _post_process(candidate, dj, x, y)
        issues     = _validate(candidate)

        if not issues:
            ollama_html = candidate
            state.log(f"Tool-5 Ollama OK — model={used_model}")
        else:
            state.log(f"Tool-5 Ollama HTML broken {issues} — using Python fallback")

    except Exception as e:
        state.log(f"Tool-5 Ollama error: {e} — using Python fallback")

    # ── Wait for Python fallback (usually already done) ───────────────────────
    fallback_thread.join(timeout=5)

    if ollama_html:
        state.html        = ollama_html
        state.call2_model = used_model
    else:
        state.html        = _fallback.get("html", _html_empty(title))
        state.call2_model = "python-parallel-fallback"

    state.t_call2 = time.time() - t
    state.log(f"Tool-5 done in {state.t_call2:.2f}s — model={state.call2_model} HTML={len(state.html)} chars")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 6 — VALIDATOR + SELF-HEALER
# ─────────────────────────────────────────────────────────────────────────────

def tool_6_validate(state: AgentState):
    """
    TOOL 6 — Validate HTML and self-heal if broken.
    No extra Ollama call — uses targeted Python fixes.
    Worst case: rebuilds from Python (guaranteed correct).
    """
    issues = _validate(state.html)
    if not issues:
        state.log("Tool-6: ✅ HTML valid")
        return

    state.log(f"Tool-6: Issues found {issues} — auto-fixing...")
    state.issues = issues

    # Fix 1: Post-processor
    x  = state.structured.get("x_key") or "name"
    y  = state.structured.get("y_key") or "value"
    dj = json.dumps(state.structured.get("data",[]), default=str)
    state.html = _post_process(state.html, dj, x, y)
    state.html = _fix_overflow(state.html)

    # Fix 2: If still broken → Python rebuild (guaranteed correct)
    if _validate(state.html):
        state.log("Tool-6: Still broken → Python rebuild")
        tool_4_python_html(state)
        state.self_healed = True
        state.log("Tool-6: ✅ Self-healed via Python rebuild")
    else:
        state.self_healed = True
        state.log("Tool-6: ✅ Fixed via post-processor")


# ─────────────────────────────────────────────────────────────────────────────
# CHART PROMPT BUILDER (used by Tool 5)
# ─────────────────────────────────────────────────────────────────────────────

def _make_chart_prompt(viz, title, subtitle, schema, x, y, n, dj, spec) -> str:
    return (
        "Generate a COMPLETE React visualization HTML page.\n"
        "Output ONLY the HTML from <!DOCTYPE html> to </html>. NOTHING ELSE.\n\n"
        f"CHART: {viz.upper()}  X-KEY: {x}  Y-KEY: {y}  ROWS: {n}\n"
        f"TITLE: {title}  |  SCHEMA: {schema}\n\n"
        f"DATA (use exactly):\n{dj}\n\n"
        "STRUCTURE TO FOLLOW:\n"
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="UTF-8">\n'
        f"<title>{title}</title>\n"
        f"{CDN_SCRIPTS}\n"
        f"<style>{BASE_CSS}</style></head>\n"
        '<body><div id="root"></div>\n'
        '<script type="text/babel">\n'
        f"{RECHARTS_INIT}\n"
        f"const data = {dj};\n"
        "const App = () => (\n"
        '  <div className="card">\n'
        f"    <h2>{title}</h2>\n"
        f'    <p className="subtitle">{subtitle} &middot; {n} records</p>\n'
        '    <ResponsiveContainer width="100%" height={480}>\n'
        f"      {spec}\n"
        "    </ResponsiveContainer>\n"
        "  </div>\n"
        ");\n"
        'ReactDOM.render(<App />, document.getElementById("root"));\n'
        "</script></body></html>\n\n"
        "RULES (follow exactly):\n"
        f"1. const data = {dj};\n"
        f'2. XAxis/nameKey = "{x}"\n'
        f'3. dataKey value = "{y}"\n'
        "4. Double quotes only in JS strings\n"
        "5. ReactDOM.render(<App />, document.getElementById(\"root\"))\n"
        "6. No import statements\n"
        "7. Output ONLY the complete HTML file"
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN AGENT ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def generate_react_visualization(request: QueryRequest) -> dict:
    """
    AI Agent entry point.
    Drop-in replacement for visualization_service.generate_react_visualization().
    Same input (QueryRequest), same output dict, but much faster.

    Speed benchmarks:
      Cache hit          <0.01s  (instant)
      Table/filter/text   0.1s   (Python only)
      Simple charts      10-20s  (1 Ollama call)
      Complex charts     15-25s  (2 Ollama calls, parallel fallback)
      Old sequential     35-65s  (always both calls, no routing)
    """

    # ── Parse data ────────────────────────────────────────────────────────────
    if isinstance(request.dbJsonData, str):
        try:    db_data = json.loads(request.dbJsonData)
        except: raise HTTPException(400, "Invalid JSON in dbJsonData")
    else:
        db_data = request.dbJsonData

    rows = db_data.get("rows", []) if isinstance(db_data, dict) else db_data
    if not rows:
        raise HTTPException(400, "No data rows provided")

    # ── Create agent state ────────────────────────────────────────────────────
    state = AgentState(
        question    = request.textQue,
        schema_name = request.schemaName,
        rows        = rows,
        query       = request.query,
    )

    sep = "─" * 55
    print(f"\n{sep}")
    print(f" [Agent] Q: {state.question[:80]}")
    print(f" [Agent] rows={len(rows)}  schema={state.schema_name}")

    # ══════════════════════════════════════════════════════════════
    # TOOL 1 — ROUTE  (always first, instant)
    # ══════════════════════════════════════════════════════════════
    tool_1_route(state)

    # ══════════════════════════════════════════════════════════════
    # CACHE HIT — return immediately
    # ══════════════════════════════════════════════════════════════
    if state.strategy == Strategy.CACHE_HIT:
        cached = _cache_get(state.cache_key)
        if cached:
            cached["cache_hit"]       = True
            cached["response_time_s"] = state.elapsed()
            print(f" [Agent] ✅ Cache HIT — returned in {state.elapsed()}s")
            print(sep)
            return cached
        # Cache was cleared between route and get — fall through
        state.strategy = Strategy.FULL_AGENT
        state.log("Cache miss after route — escalating to FULL_AGENT")

    # ══════════════════════════════════════════════════════════════
    # INTENT ANALYSIS (Tool 2 or Tool 3)
    # ══════════════════════════════════════════════════════════════
    if state.strategy == Strategy.PYTHON_ONLY:
        tool_2_python_analyze(state)
    else:
        tool_3_ollama_intent(state)   # INTENT_ONLY or FULL_AGENT

    # ══════════════════════════════════════════════════════════════
    # HTML GENERATION (Tool 4 or Tool 5)
    # ══════════════════════════════════════════════════════════════
    viz = state.structured.get("viz_type", "bar")

    # Non-chart types always use Python builder (fast + guaranteed)
    if viz in ("table", "text", "card"):
        tool_4_python_html(state)

    # PYTHON_ONLY or INTENT_ONLY → Python chart builder (skip Ollama Call 2)
    elif state.strategy in (Strategy.PYTHON_ONLY, Strategy.INTENT_ONLY):
        tool_4_python_html(state)

    # FULL_AGENT → Ollama Call 2 with parallel Python fallback
    else:
        tool_5_ollama_html(state)

    # ══════════════════════════════════════════════════════════════
    # VALIDATE + SELF-HEAL (Tool 6)
    # ══════════════════════════════════════════════════════════════
    tool_6_validate(state)

    # ══════════════════════════════════════════════════════════════
    # BUILD + CACHE RESULT
    # ══════════════════════════════════════════════════════════════
    result = {
        "status":          "success",
        "schemaName":      state.schema_name,
        "query":           state.query,
        "textQuestion":    state.question,
        "outputType":      state.structured.get("viz_type", "bar"),
        "reactCode":       state.html,
        "structured":      state.structured,
        "cache_hit":       False,
        "response_time_s": state.elapsed(),
        "strategy":        state.strategy,
        "call1_model":     state.call1_model,
        "call2_model":     state.call2_model,
        "self_healed":     state.self_healed,
    }

    _cache_set(state.cache_key, result)
    print(f" [Agent] ✅ Done in {state.elapsed()}s  strategy={state.strategy}  "
          f"call1={state.call1_model}  call2={state.call2_model}  "
          f"healed={state.self_healed}")
    print(sep)

    return result

# ─────────────────────────────────────────────────────────────────────────────
# TOOL LIBRARY — all helper functions (from visualization_service)
# ─────────────────────────────────────────────────────────────────────────────

def _build_dynamic_examples(columns: list, str_cols: list, num_cols: list, rows: list) -> str:
    """
    Build Call 1 prompt examples dynamically from the ACTUAL schema columns and data.
    No hardcoded 'employee', 'leave_type', 'department', 'salary' — works for any schema.
    """
    if not rows:
        return ""

    sample     = rows[0]
    # Pick best categorical column (2–15 unique values)
    cat_col    = None
    best_uv    = 9999
    for col in str_cols:
        uv = len(set(str(r.get(col,"")) for r in rows if r.get(col)))
        if 2 <= uv <= 15 and uv < best_uv:
            cat_col = col; best_uv = uv

    # Pick best name/label column (high uniqueness)
    name_col   = None
    for col in str_cols:
        uv = len(set(str(r.get(col,"")) for r in rows if r.get(col)))
        if uv >= len(rows) * 0.5:  # at least 50% unique → probably a name
            name_col = col; break
    if not name_col and str_cols:
        name_col = str_cols[0]

    # Pick best numeric column
    num_col    = num_cols[0] if num_cols else None

    # Get real sample values from the data
    cat_vals   = list(set(str(r.get(cat_col,"")) for r in rows if r.get(cat_col)))[:3] if cat_col else []
    name_vals  = list(set(str(r.get(name_col,"")) for r in rows if r.get(name_col)))[:2] if name_col else []

    ex = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nEXAMPLES (using THIS schema's actual columns):\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    # Example 1: pie chart of categorical column
    if cat_col and cat_vals:
        v1, v2 = (cat_vals + cat_vals)[:2]
        ex += (
            f'"show pie chart of {cat_col}"  →\n'
            f'  viz_type=pie, x_key="{cat_col}", y_key="count"\n'
            f'  data=[{{"{cat_col}":"{v1}","count":4}},{{{chr(34)}{cat_col}{chr(34)}:"{v2}","count":3}},...]\n\n'
        )

    # Example 2: filter/show specific record by name/value
    if name_col and name_vals:
        val = name_vals[0]
        ex += (
            f'"show {name_col} {val}"  →\n'
            f'  viz_type=table, x_key=null, y_key=null\n'
            f'  data=[all raw rows where {name_col}=="{val}"]\n\n'
        )

    # Example 3: bar chart count by categorical column
    if cat_col and cat_vals:
        v1, v2 = (cat_vals + cat_vals)[:2]
        ex += (
            f'"bar chart count by {cat_col}"  →\n'
            f'  viz_type=bar, x_key="{cat_col}", y_key="count"\n'
            f'  data=[{{"{cat_col}":"{v1}","count":4}},{{{chr(34)}{cat_col}{chr(34)}:"{v2}","count":3}},...]\n\n'
        )

    # Example 4: summarize
    ex += (
        '"summarize the data"  →\n'
        '  viz_type=text, x_key=null, y_key=null\n'
        '  data=[{"metric":"Total Records","value":N},{"metric":"...","value":"..."},...]\n\n'
    )

    # Example 5: specific record summarized in text
    if name_col and name_vals:
        val = name_vals[0]
        ex += (
            f'"{val} details summarized in text"  →\n'
            f'  viz_type=text (text keyword detected)\n'
            f'  Filter rows where {name_col}="{val}", compute summary metrics\n'
            f'  data=[{{"metric":"{name_col}","value":"{val}"}},{{"metric":"...","value":"..."}},...]\n\n'
        )

    # Example 6: sum by category (only if numeric + categorical exist)
    if cat_col and num_col:
        ex += (
            f'"total {num_col} by {cat_col}"  →\n'
            f'  viz_type=bar, x_key="{cat_col}", y_key="total_{num_col}"\n'
            f'  data=[{{"{cat_col}":"A","total_{num_col}":50000}},{{"{cat_col}":"B","total_{num_col}":30000}},...]\n\n'
        )

    return ex


def call1_analyze_and_structure(question: str, rows: list, schema_name: str) -> dict:
    """
    Ollama reads the user question + raw data and returns a StructuredResult:
    {
        viz_type : bar | pie | line | area | scatter | radar | table | card | text
        title    : chart title string
        subtitle : short description
        x_key    : key name used for X axis / labels
        y_key    : key name used for Y axis / values
        data     : fully transformed, aggregated, ready-to-render data array
    }
    """
    sample   = rows[0] if rows else {}
    columns  = list(sample.keys())
    num_cols = [k for k, v in sample.items() if isinstance(v, (int, float)) and v is not None]
    str_cols = [k for k, v in sample.items() if isinstance(v, str) and v is not None]

    # Describe each column with its type and real sample values
    col_info = []
    for col in columns:
        dtype = "number" if col in num_cols else "text"
        vals  = [str(r.get(col, "")) for r in rows if r.get(col) is not None]
        uvals = list(dict.fromkeys(vals))[:6]   # preserve order, deduplicate
        col_info.append(f'  · "{col}"  type={dtype}  samples=[{", ".join(uvals)}]')

    prompt = (
        "You are an expert data analyst and visualization engineer.\n"
        "Read the user question carefully and decide the best way to visualize the data.\n"
        "Then return ONLY a valid JSON object — nothing else.\n\n"

        f'USER QUESTION: "{question}"\n'
        f"SCHEMA: {schema_name}   TOTAL ROWS: {len(rows)}\n\n"

        "COLUMNS:\n" + "\n".join(col_info) + "\n\n"

        "ALL DATA (use this to compute the result):\n"
        + json.dumps(rows, default=str) + "\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "RETURN FORMAT (JSON only, no markdown):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "{\n"
        '  "viz_type": "bar|pie|line|area|scatter|radar|table|card|text",\n'
        '  "title":    "descriptive chart title",\n'
        '  "subtitle": "one sentence explaining what is shown",\n'
        '  "x_key":    "exact key name in data objects for X axis / labels (null for table/card/text)",\n'
        '  "y_key":    "exact key name in data objects for Y axis / numeric value (null for table/card/text)",\n'
        '  "data":     [ /* transformed data array — see rules below */ ]\n'
        "}\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "VIZ_TYPE SELECTION GUIDE:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  bar     → comparing values across categories (counts, totals, averages)\n"
        "  pie     → distribution, proportion, percentage breakdown\n"
        "  line    → trends over time, sequential data\n"
        "  area    → cumulative trends over time\n"
        "  scatter → correlation between two numeric columns\n"
        "  radar   → multi-attribute comparison across categories\n"
        "  table   → user wants to SEE individual rows (filter, list, search) — no aggregation\n"
        "  card    → user wants KPI numbers / totals / metrics displayed as number cards\n"
        "  text    → ONLY use when user EXPLICITLY says: 'summarize', 'summarized in text',\n"
        "            'in text', 'as text', 'text format', 'explain', 'give me insights',\n"
        "            'describe', 'write a report', 'analyze', 'tell me about'\n"
        "            IMPORTANT: If the question contains ANY of these text keywords,\n"
        "            use viz_type=text EVEN IF a specific record name is mentioned.\n"
        "            e.g. 'Project Alpha details summarized in text' → viz_type=text (NOT table)\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "DATA TRANSFORMATION RULES:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  COUNT (for distribution charts):\n"
        "    → count occurrences of each unique value in a column\n"
        '    → data shape: [{"<group_col>": "Sick", "count": 4}, ...]\n'
        '    → x_key = "<group_col>", y_key = "count"\n\n'

        "  SUM (for total charts):\n"
        "    → sum a numeric column grouped by a category column\n"
        '    → data shape: [{"<group_col>": "HR", "total_salary": 50000}, ...]\n'
        '    → x_key = "<group_col>", y_key = "total_<numeric_col>"\n\n'

        "  AVERAGE:\n"
        "    → average a numeric column grouped by a category\n"
        '    → data shape: [{"<group_col>": "HR", "avg_salary": 5000}, ...]\n'
        '    → x_key = "<group_col>", y_key = "avg_<numeric_col>"\n\n'

        "  FILTER (for table):\n"
        "    → return only matching rows, as-is from the raw data\n"
        "    → match case-insensitively if needed\n"
        "    → x_key = null, y_key = null\n\n"

        "  SUMMARY (for text/card):\n"
        '    → data shape: [{"metric": "Total Records", "value": 10}, ...]\n'
        "    → compute counts, totals, averages, top values\n"
        "    → x_key = null, y_key = null\n\n"

        "  RAW (for table when no transformation needed):\n"
        "    → return all rows as-is\n\n"

        + _build_dynamic_examples(columns, str_cols, num_cols, rows)
        +


        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "CRITICAL:\n"
        "  · x_key and y_key MUST exactly match keys present in data objects\n"
        "  · data must include ALL records (not just 3 examples)\n"
        "  · Return ONLY the JSON object — no markdown, no backticks, no text\n"
    )

    print("\n▶ CALL 1: Sending to Ollama...")

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":  OLLAMA_MODEL_INTENT,   # intent model: best at JSON + instructions
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 4000,
                    "temperature": 0.1,   # low temp = deterministic JSON
                    "top_p":       0.9,
                    "num_ctx":     8192,
                },
            },
            timeout=800,
        )
        raw = resp.json().get("response", "").strip()
        print(f"  response length: {len(raw)}")
        print(f"  preview: {raw[:200]}")

        result = _extract_json(raw)

        if result and _is_valid_structured(result):
            result = _fix_keys(result)

            # If Ollama chose text and data looks like filter result (all same structure as raw rows),
            # also attach raw_rows so Call 2 can write a proper narrative about specific records
            if result.get("viz_type") == "text":
                # Try to find if user mentioned a specific value to filter
                q = question.lower()
                for col in columns:
                    uvals = set(str(r.get(col, "")) for r in rows if r.get(col))
                    for val in uvals:
                        if val.lower() in q and len(val) > 2:
                            filtered = [r for r in rows if str(r.get(col,"")).lower() == val.lower()]
                            if filtered:
                                result["raw_rows"] = filtered
                                result["user_question"] = question
                            break
                    if result.get("raw_rows"):
                        break

            return result

        print("  ⚠ Invalid response — running Python fallback")
        return _python_analyze(question, rows, columns, num_cols, str_cols)

    except Exception as e:
        print(f"  ✗ Error: {e} — running Python fallback")
        return _python_analyze(question, rows, columns, num_cols, str_cols)


def _extract_json(text: str) -> dict | None:
    """Robustly extract a JSON object from Ollama response text."""
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()

    # Find the outermost { ... }
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _is_valid_structured(obj: dict) -> bool:
    """Check the Call 1 result has the minimum required fields."""
    valid_types = {"bar","pie","line","area","scatter","radar","table","card","text"}
    if not isinstance(obj, dict):                           return False
    if obj.get("viz_type") not in valid_types:             return False
    if not isinstance(obj.get("data"), list):              return False
    if len(obj.get("data", [])) == 0:                      return False
    return True


def _fix_keys(result: dict) -> dict:
    """Ensure x_key / y_key actually exist in the data objects."""
    data   = result.get("data", [])
    x_key  = result.get("x_key")
    y_key  = result.get("y_key")

    if not data:
        return result

    actual_keys = list(data[0].keys()) if data else []

    # If declared keys are missing from data, try to auto-detect
    if x_key and x_key not in actual_keys:
        # Pick first non-numeric key
        x_key = next((k for k in actual_keys if not isinstance(data[0].get(k), (int, float))), actual_keys[0])
        result["x_key"] = x_key

    if y_key and y_key not in actual_keys:
        # Pick first numeric key
        y_key = next((k for k in actual_keys if isinstance(data[0].get(k), (int, float))), actual_keys[-1])
        result["y_key"] = y_key

    return result


# ─────────────────────────────────────────────────────────────────────────────
# PYTHON FALLBACK for Call 1
# ─────────────────────────────────────────────────────────────────────────────

def _python_analyze(question: str, rows: list, columns: list, num_cols: list, str_cols: list) -> dict:
    """
    Pure Python intent analysis — runs when Ollama Call 1 fails.
    Priority order: text/summarize → filter → chart types
    """
    q = question.lower()

    # ── TEXT / SUMMARIZE — check FIRST, highest priority ─────────────────────
    # These keywords override everything else, even if filter values are present
    text_triggers = [
        "summarize", "summary", "summarized", "in text", "as text",
        "text format", "insight", "insights", "statistics", "overview",
        "report", "analyze", "analysis", "tell me about", "describe",
        "explain", "narrative", "write about"
    ]
    wants_text = any(t in q for t in text_triggers)

    if wants_text:
        # Check if user also wants to filter a specific subset
        # e.g. "Project Alpha details summarized in text"
        filtered_rows = rows
        filter_label  = ""
        for col in str_cols:
            unique_vals = set(str(r.get(col, "")) for r in rows if r.get(col))
            for val in unique_vals:
                if val.lower() in q and len(val) > 2:
                    filtered_rows = [r for r in rows if str(r.get(col, "")).lower() == val.lower()]
                    filter_label  = f" — {col}: {val}"
                    break
            if filter_label:
                break

        data, subtitle = _compute_summary(filtered_rows, num_cols, str_cols)
        # Build a meaningful title — never "None"
        if filter_label:
            clean_label = filter_label.replace(" — ", "").replace("_", " ").title()
            computed_title = f"{clean_label} — Summary"
        else:
            computed_title = "Data Summary"
        # Also inject the raw filtered rows so _call2_text has full context
        return {
            "viz_type":      "text",
            "title":         computed_title,
            "subtitle":      subtitle,
            "x_key":         None,
            "y_key":         None,
            "data":          data,
            "raw_rows":      filtered_rows,   # extra context for Call 2
            "user_question": question,
        }

    # ── FILTER — fully dynamic, no hardcoded schema words ───────────────────
    # Use _is_filter_question() which checks grammar + data values
    if _is_filter_question(q, rows):
        # Try to find which column+value the user is filtering on
        # by checking if any actual data value appears in the question
        for col in str_cols:
            unique_vals = set(str(r.get(col, "")) for r in rows if r.get(col))
            for val in sorted(unique_vals, key=len, reverse=True):  # longest match first
                if len(val) > 2 and val.lower() in q:
                    filtered = [r for r in rows if str(r.get(col, "")).lower() == val.lower()]
                    if filtered:
                        # Dynamic title from schema name + col/val — no hardcoded words
                        col_label = col.replace("_", " ").title()
                        return {
                            "viz_type": "table",
                            "title":    f"{val}",
                            "subtitle": f"Filtered by {col_label} = {val}",
                            "x_key": None, "y_key": None,
                            "data": filtered,
                        }
        # No specific value matched — show all rows
        return {
            "viz_type": "table",
            "title":    "Search Results",
            "subtitle": question,
            "x_key": None, "y_key": None, "data": rows,
        }

    # ── SUMMARIZE (explicit, no filter) ──────────────────────────────────────
    if any(t in q for t in ["summarize", "summary", "insight", "statistics", "overview", "report", "analyze"]):
        data, subtitle = _compute_summary(rows, num_cols, str_cols)
        return {
            "viz_type": "text", "title": "Data Summary", "subtitle": subtitle,
            "x_key": None, "y_key": None, "data": data,
        }

    # ── Determine viz type ────────────────────────────────────────────────────
    viz = "bar"
    if any(t in q for t in ["pie", "donut", "distribution", "proportion", "percentage"]): viz = "pie"
    elif any(t in q for t in ["line", "trend", "over time", "monthly", "yearly", "daily"]): viz = "line"
    elif any(t in q for t in ["area", "cumulative", "stacked"]): viz = "area"
    elif any(t in q for t in ["table", "list", "show all", "all records", "rows"]): viz = "table"
    elif any(t in q for t in ["card", "kpi", "metric", "total only"]): viz = "card"
    elif any(t in q for t in ["scatter", "correlation", " vs "]): viz = "scatter"

    if viz == "table":
        return {"viz_type": "table", "title": "Data", "subtitle": "All records",
                "x_key": None, "y_key": None, "data": rows}

    # ── Find group column ─────────────────────────────────────────────────────
    gc = None
    for col in str_cols:
        if col.lower() in q or col.lower().replace("_", " ") in q:
            gc = col; break
    if not gc:
        # Auto-pick: fewest unique values (most categorical)
        best = 9999
        for col in str_cols:
            uv = len(set(str(r.get(col, "")) for r in rows if r.get(col)))
            if 2 <= uv <= 15 and uv < best:
                gc = col; best = uv

    # ── SUM ───────────────────────────────────────────────────────────────────
    if any(t in q for t in ["total", "sum"]) and num_cols and gc:
        nc  = next((c for c in num_cols if c.lower() in q), num_cols[0])
        tot = {}
        for r in rows:
            k = str(r.get(gc, "?")); tot[k] = tot.get(k, 0) + (r.get(nc, 0) or 0)
        vk   = f"total_{nc}"
        data = [{gc: k, vk: round(v, 2)} for k, v in sorted(tot.items(), key=lambda x: -x[1])]
        return {"viz_type": viz, "title": f"Total {nc} by {gc}", "subtitle": f"Sum of {nc} per {gc}",
                "x_key": gc, "y_key": vk, "data": data}

    # ── AVG ───────────────────────────────────────────────────────────────────
    if any(t in q for t in ["average", "avg", "mean"]) and num_cols and gc:
        nc   = next((c for c in num_cols if c.lower() in q), num_cols[0])
        s, c = {}, {}
        for r in rows:
            k = str(r.get(gc, "?")); v = r.get(nc, 0) or 0
            s[k] = s.get(k, 0) + v; c[k] = c.get(k, 0) + 1
        vk   = f"avg_{nc}"
        data = [{gc: k, vk: round(s[k]/c[k], 2)} for k in sorted(s, key=lambda x: -s[x])]
        return {"viz_type": viz, "title": f"Average {nc} by {gc}", "subtitle": f"Avg {nc} per {gc}",
                "x_key": gc, "y_key": vk, "data": data}

    # ── COUNT (default for charts) ────────────────────────────────────────────
    if gc:
        counts = Counter(str(r.get(gc, "?")) for r in rows)
        data   = [{gc: k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]
        return {
            "viz_type": viz,
            "title":    f"{gc.replace('_', ' ').title()} Distribution",
            "subtitle": f"Count of records by {gc}",
            "x_key": gc, "y_key": "count",
            "data": data,
        }

    # ── RAW fallback ──────────────────────────────────────────────────────────
    lc = str_cols[0] if str_cols else columns[0]
    vc = num_cols[0]  if num_cols  else columns[-1]
    return {"viz_type": viz, "title": "Data Overview", "subtitle": "Data visualization",
            "x_key": lc, "y_key": vc, "data": rows[:100]}


def _compute_summary(rows, num_cols, str_cols):
    data  = [{"metric": "Total Records", "value": len(rows)}]
    lines = [f"Total records: {len(rows)}"]
    for col in num_cols:
        vals = [r[col] for r in rows if r.get(col) is not None]
        if vals:
            avg = round(sum(vals) / len(vals), 2)
            data += [
                {"metric": f"{col} — Total",   "value": round(sum(vals), 2)},
                {"metric": f"{col} — Average", "value": avg},
                {"metric": f"{col} — Max",     "value": max(vals)},
                {"metric": f"{col} — Min",     "value": min(vals)},
            ]
            lines.append(f"{col}: total={round(sum(vals),2)}, avg={avg}, max={max(vals)}, min={min(vals)}")
    for col in str_cols[:4]:
        top = Counter(str(r.get(col, "")) for r in rows if r.get(col)).most_common(5)
        for k, v in top:
            data.append({"metric": f"{col}: {k}", "value": v})
        lines.append(f"{col} breakdown — " + ", ".join(f"{k}({v})" for k, v in top))
    return data, " | ".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CALL 2 — GENERATE HTML
# ─────────────────────────────────────────────────────────────────────────────

    def _try_ollama_call(model_name: str):
        return requests.post(
            OLLAMA_URL,
            json={
                "model":  model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 3000,
                    "temperature": 0.1,   # low temp = consistent code
                    "top_p":       0.9,
                    "num_ctx":     8192,
                },
            },
            timeout=800,
        )

    try:
        print(f"  trying model: {OLLAMA_MODEL_CODE}")
        resp = _try_ollama_call(OLLAMA_MODEL_CODE)
        # If model not found, Ollama returns error in response body
        resp_json = resp.json()
        if "error" in resp_json and "not found" in resp_json.get("error","").lower():
            print(f"  {OLLAMA_MODEL_CODE} not found → fallback to {OLLAMA_MODEL_INTENT}")
            resp = _try_ollama_call(OLLAMA_MODEL_INTENT)
        raw  = resp.json().get("response", "").strip()
        print(f"  response length: {len(raw)}")
        print(f"  preview: {raw[:150]}")

        html   = _extract_html(raw)
        html   = _post_process(html, dj, x, y)
        issues = _validate(html)

        if issues:
            print(f"  ⚠ Issues after fix: {issues}")
            print("  → Using Python chart builder as fallback")
            return _build_chart_python(data, title, subtitle, x, y, viz_type, schema_name, n, dj)

        return html

    except Exception as e:
        print(f"  ✗ Error: {e} — Python fallback")
        return _build_chart_python(data, title, subtitle, x, y, viz_type, schema_name, n, dj)


def _chart_jsx_spec(viz_type: str, x: str, y: str) -> str:
    """Return the JSX spec string for the given chart type + keys."""
    specs = {
        "bar": (
            f'<BarChart data={{data}} margin={{{{top:20,right:30,left:20,bottom:data.length>5?80:50}}}}>\n'
            f'          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />\n'
            f'          <XAxis\n'
            f'            dataKey="{x}"\n'
            f'            interval={{0}}\n'
            f'            tick={{{{fontSize:13,fill:"#374151"}}}}\n'
            f'            angle={{data.length>6?-35:0}}\n'
            f'            textAnchor={{data.length>6?"end":"middle"}}\n'
            f'          />\n'
            f'          <YAxis tick={{{{fontSize:12}}}} />\n'
            f'          <Tooltip />\n'
            f'          <Legend />\n'
            f'          <Bar dataKey="{y}" radius={{[6,6,0,0]}} maxBarSize={{80}}>\n'
            f'            {{data.map((_,i) => <Cell key={{i}} fill={{COLORS[i%COLORS.length]}} />)}}\n'
            f'          </Bar>\n'
            f'        </BarChart>'
        ),
        "pie": (
            f'<PieChart>\n'
            f'          <Pie\n'
            f'            data={{data}}\n'
            f'            dataKey="{y}"\n'
            f'            nameKey="{x}"\n'
            f'            cx="50%" cy="50%"\n'
            f'            outerRadius={{180}} innerRadius={{70}}\n'
            f'            label={{({{name,percent}}) => `${{name}} ${{(percent*100).toFixed(1)}}%`}}\n'
            f'          >\n'
            f'            {{data.map((_,i) => <Cell key={{i}} fill={{COLORS[i%COLORS.length]}} />)}}\n'
            f'          </Pie>\n'
            f'          <Tooltip />\n'
            f'          <Legend />\n'
            f'        </PieChart>'
        ),
        "line": (
            f'<LineChart data={{data}} margin={{{{top:20,right:30,left:20,bottom:20}}}}>\n'
            f'          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />\n'
            f'          <XAxis dataKey="{x}" />\n'
            f'          <YAxis />\n'
            f'          <Tooltip />\n'
            f'          <Legend />\n'
            f'          <Line type="monotone" dataKey="{y}" stroke="#3b82f6" strokeWidth={{2}} dot={{{{fill:"#3b82f6",r:5}}}} />\n'
            f'        </LineChart>'
        ),
        "area": (
            f'<AreaChart data={{data}} margin={{{{top:20,right:30,left:20,bottom:20}}}}>\n'
            f'          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />\n'
            f'          <XAxis dataKey="{x}" />\n'
            f'          <YAxis />\n'
            f'          <Tooltip />\n'
            f'          <Legend />\n'
            f'          <Area type="monotone" dataKey="{y}" stroke="#3b82f6" fill="#bfdbfe" />\n'
            f'        </AreaChart>'
        ),
        "scatter": (
            f'<ScatterChart margin={{{{top:20,right:30,left:20,bottom:20}}}}>\n'
            f'          <CartesianGrid stroke="#f0f0f0" />\n'
            f'          <XAxis dataKey="{x}" name="{x}" />\n'
            f'          <YAxis dataKey="{y}" name="{y}" />\n'
            f'          <Tooltip cursor={{{{strokeDasharray:"3 3"}}}} />\n'
            f'          <Scatter data={{data}} fill="#3b82f6" />\n'
            f'        </ScatterChart>'
        ),
        "radar": (
            f'<RadarChart cx="50%" cy="50%" outerRadius={{180}} data={{data}}>\n'
            f'          <PolarGrid />\n'
            f'          <PolarAngleAxis dataKey="{x}" />\n'
            f'          <PolarRadiusAxis />\n'
            f'          <Radar dataKey="{y}" stroke="#3b82f6" fill="#3b82f6" fillOpacity={{0.5}} />\n'
            f'          <Tooltip />\n'
            f'          <Legend />\n'
            f'        </RadarChart>'
        ),
    }
    return specs.get(viz_type, specs["bar"])


# ─────────────────────────────────────────────────────────────────────────────
# HTML HELPERS — extract, fix, validate
# ─────────────────────────────────────────────────────────────────────────────

def _extract_html(text: str) -> str:
    """Pull the complete HTML out of an Ollama response."""
    text = text.strip()
    # Strip markdown fences
    for pat in [r"```html\s*([\s\S]*?)\s*```", r"```\s*([\s\S]*?)\s*```"]:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip()
            if _is_complete_html(candidate):
                return candidate
    # Raw HTML
    for marker in ["<!DOCTYPE html>", "<!doctype html>", "<html"]:
        idx = text.lower().find(marker)
        if idx != -1:
            candidate = text[idx:].strip()
            if _is_complete_html(candidate):
                return candidate
    return text


def _is_complete_html(text: str) -> bool:
    t = text.lower()
    return ("<!doctype html>" in t or "<html" in t) and "</html>" in t and len(text) > 500


def _post_process(html: str, data_json: str, x_key: str, y_key: str) -> str:
    """Fix the most common issues in Ollama-generated HTML."""
    # Find the babel script block
    m = re.search(r'(<script[^>]*text/babel[^>]*>)([\s\S]*?)(</script>)', html, re.IGNORECASE)
    if not m:
        return html

    js = m.group(2)

    # Fix 1: Replace any partial Recharts destructure with the full RECHARTS_INIT
    if re.search(r'const\s*\{[^}]+\}\s*=\s*Recharts', js):
        js = re.sub(r'const\s*\{[^}]+\}\s*=\s*Recharts\s*;?', RECHARTS_INIT.strip(), js, count=1)
    elif "Recharts" in js and "= Recharts" not in js:
        js = RECHARTS_INIT + "\n        " + js

    # Fix 2: Remove duplicate COLORS declarations (keep only first)
    color_matches = list(re.finditer(r'const COLORS\s*=\s*\[[^\]]+\]\s*;?', js))
    for dup in reversed(color_matches[1:]):
        js = js[:dup.start()] + js[dup.end():]

    # Fix 3: Replace wrong data if data_json not in script
    if data_json and "const data" in js and data_json not in js:
        js = re.sub(r'const data\s*=\s*\[[\s\S]*?\]\s*;', f'const data = {data_json};', js, count=1)

    # Fix 4: Single-quoted hex colors
    js = re.sub(r"'(#[0-9a-fA-F]{3,8})'", r'"\1"', js)

    # Fix 5: createRoot → ReactDOM.render
    js = re.sub(
        r'ReactDOM\.createRoot\([^)]+\)\.render\(\s*(<App\s*/>)\s*\)',
        r'ReactDOM.render(\1, document.getElementById("root"))',
        js,
    )

    # Fix 6: Direct JSX render (no App wrapper)
    if "const App" not in js:
        direct = re.search(
            r'(ReactDOM\.render\()\s*\n?\s*'
            r'(<(?:ResponsiveContainer|BarChart|LineChart|PieChart|AreaChart|ScatterChart|RadarChart)'
            r'[\s\S]+?)\s*,\s*\n?\s*(document\.getElementById\(["\']root["\']\))\s*\)',
            js,
        )
        if direct:
            inner = direct.group(2).strip()
            js = (
                js[:direct.start()]
                + 'const App = () => (\n      <div className="card">\n        '
                + inner
                + '\n      </div>\n    );\n    '
                + 'ReactDOM.render(<App />, document.getElementById("root"));'
                + js[direct.end():]
            )

    # Fix 7: Missing ReactDOM.render
    if "ReactDOM.render" not in js and "const App" in js:
        js += '\n    ReactDOM.render(<App />, document.getElementById("root"));\n'

    # Fix 8: Remove import statements
    js = re.sub(r"^import\s+.*?;?\s*$", "", js, flags=re.MULTILINE)

    return html[:m.start(1)] + m.group(1) + js + m.group(3) + html[m.end(3):]


def _validate(html: str) -> list:
    """Return list of issues. Empty list = valid."""
    issues = []
    if not html or len(html) < 400:
        issues.append("HTML too short")
        return issues
    if not _is_complete_html(html):
        issues.append("Incomplete HTML structure")

    m = re.search(r'<script[^>]*text/babel[^>]*>([\s\S]*?)</script>', html, re.IGNORECASE)
    if m:
        js = m.group(1)
        if re.search(r"^import\s", js, re.M): issues.append("import statements in babel block")
        if "createRoot" in js:               issues.append("createRoot (use ReactDOM.render)")
        if "ReactDOM.render" not in js:      issues.append("missing ReactDOM.render")
    return issues


# ─────────────────────────────────────────────────────────────────────────────
# PYTHON HTML BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _call2_text(data, title, subtitle, schema_name, question, structured=None):
    """
    Pure Python text/narrative page builder.
    No Ollama — guaranteed correct title, no scrollbar, always has narrative.
    Handles both:
    - Pure summaries ("summarize the data")
    - Filtered + summarize ("Project Alpha details summarized in text")
    """
    raw_rows = (structured or {}).get("raw_rows", [])

    # Fix title — never show "None"
    if not title or title.strip().lower() in ("none", "null", ""):
        if raw_rows:
            # Try to get a meaningful title from the first record
            first = raw_rows[0]
            name_keys = ["name", "project_name", "employee_name", "title", "label"]
            found_name = next(
                (str(first.get(k, "")) for k in name_keys if first.get(k)),
                None
            )
            if not found_name:
                found_name = str(list(first.values())[0]) if first else ""
            title = f"{found_name} — Details" if found_name else "Data Summary"
        else:
            title = "Data Summary"

    COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
              "#06b6d4", "#f97316", "#84cc16", "#ec4899", "#14b8a6"]

    # ── Build detail cards ─────────────────────────────────────────────────────
    cards_html = ""

    if raw_rows:
        # One card per column of the matching record(s)
        first = raw_rows[0]
        for i, (key, val) in enumerate(first.items()):
            if val is None or str(val).strip() == "":
                continue
            label = key.replace("_", " ").title()
            color = COLORS[i % len(COLORS)]
            # Format dates
            val_str = str(val)
            if re.match(r"\d{4}-\d{2}-\d{2}", val_str):
                val_str = val_str.split("T")[0]
            cards_html += f"""
            <div style="background:#fff;border-radius:12px;padding:20px 24px;
                        border-left:4px solid {color};box-shadow:0 2px 10px rgba(0,0,0,0.06);
                        min-width:0;word-break:break-word;">
              <div style="color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;
                          letter-spacing:.6px;margin-bottom:8px;">{label}</div>
              <div style="color:{color};font-size:18px;font-weight:700;line-height:1.3;">{val_str}</div>
            </div>"""

        # Build narrative from raw row fields
        field_lines = []
        for key, val in first.items():
            if val is not None and str(val).strip():
                val_str = str(val)
                if re.match(r"\d{4}-\d{2}-\d{2}", val_str):
                    val_str = val_str.split("T")[0]
                field_lines.append(f"<strong>{key.replace('_',' ').title()}</strong>: {val_str}")

        narrative_items = "".join(f"<li style='margin-bottom:8px;'>{line}</li>" for line in field_lines)
        narrative_html = f"""
        <div style="background:#fff;border-radius:14px;padding:24px 28px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-top:20px;">
          <h3 style="color:#1e293b;font-size:16px;font-weight:700;margin-bottom:16px;
                     padding-bottom:10px;border-bottom:2px solid #f1f5f9;">📋 Full Details</h3>
          <ul style="list-style:none;padding:0;margin:0;">
            {narrative_items}
          </ul>
        </div>"""

        # Multi-record note
        if len(raw_rows) > 1:
            narrative_html += f"""
        <div style="background:#fefce8;border-left:4px solid #f59e0b;border-radius:0 10px 10px 0;
                    padding:12px 16px;margin-top:16px;color:#92400e;font-size:13px;">
          ℹ️ {len(raw_rows)} matching records found. Showing details for the first record above.
        </div>"""

    else:
        # Metric/value cards from summary data
        for i, row in enumerate(data[:20]):
            metric = str(row.get("metric", row.get("name", "")))
            val    = row.get("value", "")
            if not metric:
                continue
            color = COLORS[i % len(COLORS)]
            cards_html += f"""
            <div style="background:#fff;border-radius:12px;padding:20px 24px;
                        border-left:4px solid {color};box-shadow:0 2px 10px rgba(0,0,0,0.06);">
              <div style="color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;
                          letter-spacing:.6px;margin-bottom:8px;">{metric}</div>
              <div style="color:{color};font-size:22px;font-weight:800;">{val}</div>
            </div>"""

        # Narrative from subtitle stats
        narrative_text = subtitle or "This summary provides an overview of the available data."
        stat_parts     = narrative_text.split(" | ")
        stat_items     = "".join(
            f"<li style='padding:8px 12px;background:#f8fafc;border-radius:8px;"
            f"font-size:14px;color:#374151;'>{p}</li>"
            for p in stat_parts if p.strip()
        )
        narrative_html = f"""
        <div style="background:#fff;border-radius:14px;padding:24px 28px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.06);margin-top:20px;">
          <h3 style="color:#1e293b;font-size:16px;font-weight:700;margin-bottom:14px;
                     padding-bottom:10px;border-bottom:2px solid #f1f5f9;">📊 Statistical Breakdown</h3>
          <ul style="list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;">
            {stat_items}
          </ul>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html, body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #f1f5f9;
      overflow-x: hidden;
      overflow-y: auto;
      width: 100%;
      min-height: 100vh;
    }}
    body {{ padding: 24px; }}
    .wrap {{ max-width: 900px; margin: 0 auto; }}
  </style>
</head>
<body>
<div class="wrap">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#1e293b,#334155);color:#fff;
              border-radius:16px;padding:32px 36px;margin-bottom:20px;">
    <div style="font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;
                margin-bottom:8px;">📁 {schema_name}</div>
    <h1 style="font-size:26px;font-weight:700;line-height:1.3;">{title}</h1>
  </div>

  <!-- Question -->
  <div style="background:#eff6ff;border-left:4px solid #3b82f6;padding:14px 20px;
              border-radius:0 12px 12px 0;color:#1e40af;font-size:14px;
              font-style:italic;margin-bottom:24px;line-height:1.5;">
    💬 {question}
  </div>

  <!-- Cards grid -->
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));
              gap:14px;margin-bottom:4px;">
    {cards_html}
  </div>

  <!-- Narrative / breakdown -->
  {narrative_html}

</div>
</body>
</html>"""


def _fix_overflow(html: str) -> str:
    """Inject overflow-x:hidden into any HTML page to prevent horizontal scrollbar."""
    if "overflow-x:hidden" in html or "overflow-x: hidden" in html:
        return html
    fix = "<style>html,body{overflow-x:hidden!important;width:100%;}</style>"
    if "</head>" in html:
        return html.replace("</head>", fix + "\n</head>", 1)
    return html


def _build_chart_python(data, title, subtitle, x, y, viz_type, schema_name, n, dj):
    """Fallback chart builder — pure Python, no Ollama."""
    spec = _chart_jsx_spec(viz_type, x, y)
    return (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "  <meta charset='UTF-8'>\n"
        f"  <title>{title}</title>\n"
        f"  {CDN_SCRIPTS}\n"
        f"  <style>{BASE_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "  <div id='root'></div>\n"
        "  <script type='text/babel'>\n"
        f"    {RECHARTS_INIT}\n\n"
        f"    const data = {dj};\n\n"
        "    const App = () => (\n"
        "      <div className='card'>\n"
        f"        <h2>{title}</h2>\n"
        f"        <p className='subtitle'>{subtitle} &nbsp;&middot;&nbsp; {n} records</p>\n"
        "        <ResponsiveContainer width='100%' height={480}>\n"
        f"          {spec}\n"
        "        </ResponsiveContainer>\n"
        "      </div>\n"
        "    );\n\n"
        "    ReactDOM.render(<App />, document.getElementById('root'));\n"
        "  </script>\n"
        "</body>\n"
        "</html>"
    )


def _build_table(data, title, subtitle, schema_name, question):
    if not data:
        return _html_empty(title)
    cols = list(data[0].keys())
    dj   = json.dumps(data, default=str)
    cj   = json.dumps(cols)
    hdrs = "".join(
        f"<th onclick='st({i})'>{c.replace('_',' ').title()} <span id='a{i}'></span></th>"
        for i, c in enumerate(cols)
    )
    return (
        f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>{title}</title>\n"
        "<style>\n"
        "* { margin:0; padding:0; box-sizing:border-box; }\n"
        "html, body { font-family:'Segoe UI',sans-serif; background:#f1f5f9; overflow-x:hidden; width:100%; }\n"
        "body { padding:24px; }\n"
        ".w { background:#fff; border-radius:16px; padding:24px; box-shadow:0 4px 24px rgba(0,0,0,.08); }\n"
        ".top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; flex-wrap:wrap; gap:8px; }\n"
        ".top-left h2 { color:#1e293b; font-size:20px; font-weight:700; }\n"
        ".top-left p { color:#64748b; font-size:13px; margin-top:3px; }\n"
        ".badge { background:#3b82f6; color:#fff; padding:5px 16px; border-radius:20px; font-size:13px; font-weight:600; white-space:nowrap; align-self:center; }\n"
        "input { width:100%; padding:10px 16px; border:1px solid #e2e8f0; border-radius:10px; font-size:14px; margin-bottom:16px; outline:none; transition:.2s; }\n"
        "input:focus { border-color:#3b82f6; box-shadow:0 0 0 3px rgba(59,130,246,.1); }\n"
        ".sc { overflow-x:auto; border-radius:10px; border:1px solid #f1f5f9; }\n"
        "table { width:100%; border-collapse:collapse; font-size:14px; }\n"
        "thead th { background:#1e293b; color:#fff; padding:12px 16px; text-align:left; cursor:pointer; white-space:nowrap; user-select:none; }\n"
        "thead th:hover { background:#334155; }\n"
        "tbody tr:nth-child(even) { background:#f8fafc; }\n"
        "tbody tr:hover { background:#eff6ff; }\n"
        "td { padding:11px 16px; border-bottom:1px solid #f1f5f9; color:#374151; white-space:nowrap; }\n"
        ".nil { color:#94a3b8; font-style:italic; }\n"
        ".pg { display:flex; justify-content:space-between; align-items:center; margin-top:16px; }\n"
        ".pg button { padding:8px 20px; border:1px solid #e2e8f0; border-radius:8px; background:#fff; cursor:pointer; font-size:13px; font-weight:600; }\n"
        ".pg button:hover:not(:disabled) { background:#3b82f6; color:#fff; border-color:#3b82f6; }\n"
        ".pg button:disabled { opacity:.35; cursor:not-allowed; }\n"
        ".pi { color:#64748b; font-size:13px; }\n"
        ".empty-row { text-align:center; padding:40px; color:#94a3b8; display:none; }\n"
        "</style></head>\n"
        f"<body><div class='w'>\n"
        f"<div class='top'><div class='top-left'><h2>{title}</h2><p>{subtitle or schema_name}</p></div>"
        f"<span class='badge' id='badge'>0 rows</span></div>\n"
        f"<input id='s' placeholder='Search all columns...' oninput='fil()'>\n"
        f"<div class='sc'><table><thead><tr>{hdrs}</tr></thead><tbody id='tb'></tbody></table>"
        f"<div class='empty-row' id='empty'>No results found</div></div>\n"
        f"<div class='pg'><button id='p' onclick='pg(-1)'>← Prev</button>"
        f"<span class='pi' id='pi'></span>"
        f"<button id='n' onclick='pg(1)'>Next →</button></div>\n"
        f"</div>\n"
        f"<script>\n"
        f"const D={dj}, C={cj}, PS=20;\n"
        "let f=[...D], sc=-1, sa=true, cp=1;\n"
        "function fmt(v){\n"
        "  if(v==null) return '<span class=\"nil\">—</span>';\n"
        "  if(typeof v==='number') return v.toLocaleString();\n"
        "  const s=String(v);\n"
        "  return s.match(/^\\d{4}-\\d{2}-\\d{2}/) ? s.split('T')[0] : s;\n"
        "}\n"
        "function render(){\n"
        "  const rows=f.slice((cp-1)*PS,cp*PS), tp=Math.ceil(f.length/PS)||1;\n"
        "  document.getElementById('tb').innerHTML=rows.map(r=>'<tr>'+C.map(c=>'<td>'+fmt(r[c])+'</td>').join('')+'</tr>').join('');\n"
        "  document.getElementById('empty').style.display=f.length?'none':'block';\n"
        "  document.getElementById('badge').textContent=f.length+' rows';\n"
        "  document.getElementById('pi').textContent='Page '+cp+' of '+tp;\n"
        "  document.getElementById('p').disabled=cp===1;\n"
        "  document.getElementById('n').disabled=cp>=tp;\n"
        "}\n"
        "function fil(){\n"
        "  const q=document.getElementById('s').value.toLowerCase();\n"
        "  f=D.filter(r=>C.some(c=>String(r[c]??'').toLowerCase().includes(q)));\n"
        "  cp=1; render();\n"
        "}\n"
        "function st(i){\n"
        "  const c=C[i]; if(sc===i) sa=!sa; else { sc=i; sa=true; }\n"
        "  f.sort((a,b)=>{ const av=a[c]??'',bv=b[c]??''; return sa?(av<bv?-1:av>bv?1:0):(av<bv?1:av>bv?-1:0); });\n"
        "  document.querySelectorAll('[id^=\"a\"]').forEach((el,j)=>el.textContent=j===i?(sa?' ↑':' ↓'):'');\n"
        "  cp=1; render();\n"
        "}\n"
        "function pg(d){ cp=Math.max(1,Math.min(cp+d,Math.ceil(f.length/PS)||1)); render(); }\n"
        "render();\n"
        "</script></body></html>"
    )


def _build_summary(data, title, subtitle, schema_name, question):
    COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16"]
    pills  = ""
    for i, row in enumerate(data[:20]):
        metric = str(row.get("metric", ""))
        value  = row.get("value", "")
        clr    = COLORS[i % len(COLORS)]
        if metric:
            pills += (
                f"<div style='background:#fff;border-radius:12px;padding:16px 20px;"
                f"border-left:4px solid {clr};box-shadow:0 2px 8px rgba(0,0,0,.06);'>"
                f"<div style='color:#64748b;font-size:11px;font-weight:700;text-transform:uppercase;"
                f"letter-spacing:.5px;margin-bottom:6px;'>{metric}</div>"
                f"<div style='font-size:22px;font-weight:800;color:{clr};'>{value}</div>"
                f"</div>"
            )
    return (
        f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>{title}</title>\n"
        "<style>* {margin:0;padding:0;box-sizing:border-box;} "
        "html,body {font-family:'Segoe UI',sans-serif;background:#f1f5f9;overflow-x:hidden;width:100%;} "
        "body {padding:24px;}</style>\n"
        "</head><body>\n"
        "<div style='max-width:960px;margin:0 auto;'>\n"
        f"<div style='background:linear-gradient(135deg,#1e293b,#334155);color:#fff;"
        f"border-radius:16px;padding:32px;margin-bottom:20px;'>\n"
        f"  <h1 style='font-size:24px;font-weight:700;margin-bottom:8px;'>{title}</h1>\n"
        f"  <p style='color:#94a3b8;font-size:13px;'>{schema_name}</p>\n"
        f"</div>\n"
        f"<div style='background:#eff6ff;border-left:4px solid #3b82f6;padding:12px 18px;"
        f"border-radius:0 10px 10px 0;color:#1e40af;font-size:14px;font-style:italic;margin-bottom:20px;'>"
        f"{question}</div>\n"
        f"<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;'>"
        f"{pills}</div>\n"
        f"</div></body></html>"
    )


def _build_cards(data, title, subtitle, schema_name):
    COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16"]
    cards  = ""
    for i, row in enumerate(data):
        label = str(row.get("metric", row.get("name", f"Item {i+1}")))
        value = row.get("value", row.get("count", 0))
        clr   = COLORS[i % len(COLORS)]
        fv    = (f"{value:,.2f}" if isinstance(value, float)
                 else f"{value:,}" if isinstance(value, int)
                 else str(value))
        cards += (
            f"<div style='background:#fff;border-radius:14px;padding:24px;"
            f"border-top:4px solid {clr};box-shadow:0 2px 12px rgba(0,0,0,.06);'>"
            f"<div style='color:#64748b;font-size:12px;font-weight:700;text-transform:uppercase;"
            f"letter-spacing:.5px;margin-bottom:10px;'>{label}</div>"
            f"<div style='font-size:30px;font-weight:800;color:{clr};'>{fv}</div>"
            f"</div>"
        )
    return (
        f"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>{title}</title>\n"
        "<style>* {margin:0;padding:0;box-sizing:border-box;} "
        "html,body {font-family:'Segoe UI',sans-serif;background:#f1f5f9;overflow-x:hidden;width:100%;} "
        "body {padding:24px;}</style>\n"
        "</head><body>\n"
        f"<div style='background:#fff;border-radius:16px;padding:28px;"
        f"box-shadow:0 4px 24px rgba(0,0,0,.08);'>\n"
        f"<h2 style='color:#1e293b;font-size:22px;font-weight:700;margin-bottom:6px;'>{title}</h2>\n"
        f"<p style='color:#64748b;font-size:13px;margin-bottom:24px;'>{subtitle or schema_name}</p>\n"
        f"<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px;'>"
        f"{cards}</div>\n"
        f"</div></body></html>"
    )


def _html_empty(title):
    return (
        f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{title}</title>"
        "<style>body{font-family:'Segoe UI',sans-serif;background:#f1f5f9;display:flex;"
        "align-items:center;justify-content:center;height:100vh;margin:0;}"
        ".box{background:#fff;border-radius:16px;padding:48px;text-align:center;"
        "box-shadow:0 4px 24px rgba(0,0,0,.08);}"
        f"h2{{color:#1e293b;margin-bottom:8px;}}p{{color:#64748b;}}</style></head>"
        f"<body><div class='box'><h2>No Data</h2><p>{title}</p></div></body></html>"
    )