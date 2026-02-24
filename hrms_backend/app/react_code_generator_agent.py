"""
visualization_service.py
═══════════════════════════════════════════════════════════════

ARCHITECTURE — Two Ollama Calls:

  QueryRequest (schemaName, query, textQue, dbJsonData)
       │
       ▼
  ┌─────────────────────────────────────────────────────┐
  │  CALL 1 — analyze_and_structure()                   │
  │                                                     │
  │  INPUT : textQue + raw dbJsonData rows              │
  │  TASK  : Understand intent, transform data,         │
  │          decide viz type, identify x/y keys         │
  │  OUTPUT: StructuredResult JSON                      │
  │    {                                                │
  │      viz_type : bar|pie|line|area|table|text|card   │
  │      title    : string                              │
  │      subtitle : string                              │
  │      x_key    : column name for X axis              │
  │      y_key    : column name for Y axis / value      │
  │      data     : [transformed, aggregated rows]      │
  │    }                                                │
  └─────────────────────────────────────────────────────┘
       │
       ▼  StructuredResult
  ┌─────────────────────────────────────────────────────┐
  │  CALL 2 — generate_html()                           │
  │                                                     │
  │  INPUT : StructuredResult                           │
  │  TASK  : Generate complete React HTML UI            │
  │          matching the viz_type and data             │
  │  OUTPUT: Complete HTML string                       │
  └─────────────────────────────────────────────────────┘
       │
       ▼
  { status, reactCode, outputType, analysisType, ... }

NOTE:
  - Table / text / card pages are built in Python (no Ollama needed)
  - Charts (bar/pie/line/area) go through Ollama Call 2
  - All fixes are applied post Call 2 to guarantee correct render
═══════════════════════════════════════════════════════════════
"""

import requests, json, re
from collections import Counter
from typing import Any
from pydantic import BaseModel
from fastapi import HTTPException
from app.config import OLLAMA_URL, OLLAMA_MODEL
# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

# OLLAMA_URL   = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "qwen2.5:7b-instruct"

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
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #f1f5f9;
            padding: 24px;
            min-height: 100vh;
        }
        .card {
            background: #fff;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
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
"""


class QueryRequest(BaseModel):
    schemaName: str
    query:      str
    textQue:    str
    dbJsonData: Any


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def generate_react_visualization(request: QueryRequest) -> dict:

    # Parse incoming data
    if isinstance(request.dbJsonData, str):
        try:    db_data = json.loads(request.dbJsonData)
        except: raise HTTPException(400, "Invalid JSON in dbJsonData")
    else:
        db_data = request.dbJsonData

    rows = db_data.get("rows", []) if isinstance(db_data, dict) else db_data
    if not rows:
        raise HTTPException(400, "No data rows provided")

    print(f"\n{'═'*60}")
    print(f" Q: {request.textQue}")
    print(f" rows={len(rows)}  schema={request.schemaName}")
    print(f"{'═'*60}")

    # ══════════════════════════════════════════════════════════
    # CALL 1  — Analyze + Structure
    # ══════════════════════════════════════════════════════════
    structured = call1_analyze_and_structure(
        question    = request.textQue,
        rows        = rows,
        schema_name = request.schemaName,
    )


    print(f"\n▶ CALL 1 RESULT:")
    print(f"  viz_type : {structured.get('viz_type')}")
    print(f"  title    : {structured.get('title')}")
    print(f"  x_key    : {structured.get('x_key')}")
    print(f"  y_key    : {structured.get('y_key')}")
    print(f"  rows     : {len(structured.get('data', []))}")
    print(f"  sample   : {structured.get('data', [])[:2]}")

    # ══════════════════════════════════════════════════════════
    # CALL 2  — Generate HTML
    # ══════════════════════════════════════════════════════════
    html = call2_generate_html(
        structured  = structured,
        schema_name = request.schemaName,
        question    = request.textQue,
    )

    print(f"\n▶ CALL 2 RESULT: HTML length={len(html)}")

    return {
        "status":       "success",
        "schemaName":   request.schemaName,
        "query":        request.query,
        "textQuestion": request.textQue,
        "outputType":   structured.get("viz_type", "bar"),
        "reactCode":    html,
        "structured":   structured,   # useful for debugging
    }


# ─────────────────────────────────────────────────────────────────────────────
# CALL 1 — ANALYZE & STRUCTURE DATA
# ─────────────────────────────────────────────────────────────────────────────

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
        "  table   → user wants to SEE rows (filter, list, search) — no aggregation\n"
        "  card    → user wants KPI numbers / totals / metrics\n"
        "  text    → user wants a written summary, insight, report, explanation\n\n"

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

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "EXAMPLES:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        '"show pie chart of leave_type"  →\n'
        '  viz_type=pie, x_key="leave_type", y_key="count"\n'
        '  data=[{"leave_type":"Sick","count":4},{"leave_type":"Casual","count":3},...]\n\n'

        '"show employees who have sick leave"  →\n'
        '  viz_type=table, x_key=null, y_key=null\n'
        "  data=[all raw rows where leave_type==\"Sick\"]\n\n"

        '"bar chart count from leave_type"  →\n'
        '  viz_type=bar, x_key="leave_type", y_key="count"\n'
        '  data=[{"leave_type":"Sick","count":4},{"leave_type":"Casual","count":3},...]\n\n'

        '"summarize the data"  →\n'
        '  viz_type=text, x_key=null, y_key=null\n'
        '  data=[{"metric":"Total Records","value":10},{"metric":"Sick Leaves","value":4},...]\n\n'

        '"total salary by department"  →\n'
        '  viz_type=bar, x_key="department", y_key="total_salary"\n'
        '  data=[{"department":"HR","total_salary":150000},...]\n\n'

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
                "model":  OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 4000,
                    "temperature": 0.1,
                    "top_p":       0.9,
                    "num_ctx":     8192,
                },
            },
            timeout=300,
        )
        raw = resp.json().get("response", "").strip()
        print(f"  response length: {len(raw)}")
        print(f"  preview: {raw[:200]}")

        result = _extract_json(raw)

        if result and _is_valid_structured(result):
            # Ensure x_key/y_key match actual data keys
            result = _fix_keys(result)
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
    Covers: filter, summarize, count, sum, avg, raw.
    """
    q = question.lower()

    # ── FILTER ────────────────────────────────────────────────────────────────
    filter_triggers = ["who ", "which employee", "employees who", "employees with",
                       "show employee", "list employee", "having ", "that have", "that are"]
    if any(t in q for t in filter_triggers):
        for col in str_cols:
            unique_vals = set(str(r.get(col, "")) for r in rows if r.get(col))
            for val in unique_vals:
                if val.lower() in q:
                    filtered = [r for r in rows if str(r.get(col, "")).lower() == val.lower()]
                    return {
                        "viz_type": "table",
                        "title":    f"Employees — {col}: {val}",
                        "subtitle": f"Showing rows where {col} = {val}",
                        "x_key": None, "y_key": None,
                        "data": filtered,
                    }
        return {
            "viz_type": "table", "title": "Filtered Results", "subtitle": question,
            "x_key": None, "y_key": None, "data": rows,
        }

    # ── SUMMARIZE ─────────────────────────────────────────────────────────────
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

def call2_generate_html(structured: dict, schema_name: str, question: str) -> str:
    """
    Takes the StructuredResult from Call 1 and generates a complete React HTML page.

    - table / text / card  → built in Python (fast, 100% reliable, no Ollama)
    - bar / pie / line / area / scatter / radar  → Ollama Call 2 generates the React UI
      with a Python-built fallback if Ollama fails or produces invalid HTML
    """
    viz_type = structured.get("viz_type", "bar")
    data     = structured.get("data", [])
    title    = structured.get("title", "Visualization")
    subtitle = structured.get("subtitle", "")
    x_key    = structured.get("x_key")
    y_key    = structured.get("y_key")

    if not data:
        return _html_empty(title)

    # ── Non-chart types → pure Python builders ────────────────────────────────
    if viz_type == "table":
        print("▶ CALL 2: table → Python builder")
        return _build_table(data, title, subtitle, schema_name, question)

    if viz_type == "text":
        print("▶ CALL 2: text/summary → Python builder")
        return _build_summary(data, title, subtitle, schema_name, question)

    if viz_type == "card":
        print("▶ CALL 2: card → Python builder")
        return _build_cards(data, title, subtitle, schema_name)

    # ── Chart types → Ollama Call 2 ───────────────────────────────────────────
    print(f"▶ CALL 2: {viz_type} chart → Ollama")

    x     = x_key or "name"
    y     = y_key or "value"
    dj    = json.dumps(data, default=str)
    n     = len(data)
    spec  = _chart_jsx_spec(viz_type, x, y)

    prompt = (
        "Generate a COMPLETE React visualization HTML page.\n"
        "Output ONLY the raw HTML from <!DOCTYPE html> to </html>. Nothing else.\n\n"

        f"VIZ TYPE  : {viz_type.upper()}\n"
        f"TITLE     : {title}\n"
        f"SUBTITLE  : {subtitle}\n"
        f"SCHEMA    : {schema_name}\n"
        f"X KEY     : {x}\n"
        f"Y KEY     : {y}\n"
        f"DATA ROWS : {n}\n\n"

        "DATA (use exactly as given, do not modify):\n"
        f"{dj}\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "OUTPUT THIS EXACT STRUCTURE:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="UTF-8">\n'
        f"  <title>{title}</title>\n"
        f"  {CDN_SCRIPTS}\n"
        "  <style>\n"
        f"  {BASE_CSS}\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        '  <div id="root"></div>\n'
        '  <script type="text/babel">\n'
        f"    {RECHARTS_INIT}\n\n"
        f"    const data = {dj};\n\n"
        "    const App = () => (\n"
        '      <div className="card">\n'
        f"        <h2>{title}</h2>\n"
        f'        <p className="subtitle">{subtitle} &nbsp;·&nbsp; {n} records</p>\n'
        "        <ResponsiveContainer width=\"100%\" height={480}>\n"
        f"          {spec}\n"
        "        </ResponsiveContainer>\n"
        "      </div>\n"
        "    );\n\n"
        '    ReactDOM.render(<App />, document.getElementById("root"));\n'
        "  </script>\n"
        "</body>\n"
        "</html>\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "MANDATORY RULES:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"1. const data = {dj};  ← use THIS EXACT data, do not change it\n"
        f"2. XAxis / nameKey must use:  {x}\n"
        f"3. dataKey for values must use: {y}\n"
        "4. ALL JS strings → double quotes only\n"
        '5. Use: ReactDOM.render(<App />, document.getElementById("root"))\n'
        "6. Wrap JSX in:  const App = () => (...)\n"
        "7. Do NOT add import statements\n"
        "8. Do NOT duplicate const COLORS or Recharts destructure\n"
        "9. Output ONLY the HTML — no explanation, no markdown\n"
    )

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":  OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 3000,
                    "temperature": 0.1,
                    "top_p":       0.9,
                    "num_ctx":     8192,
                },
            },
            timeout=800,
        )
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
            f'<BarChart data={{data}} margin={{{{top:20,right:30,left:20,bottom:70}}}}>\n'
            f'          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />\n'
            f'          <XAxis dataKey="{x}" angle={{-35}} textAnchor="end" interval={{0}} tick={{{{fontSize:12}}}} />\n'
            f'          <YAxis />\n'
            f'          <Tooltip />\n'
            f'          <Legend />\n'
            f'          <Bar dataKey="{y}" radius={{[6,6,0,0]}}>\n'
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
        f"        <p className='subtitle'>{subtitle} &nbsp;·&nbsp; {n} records</p>\n"
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
        "body { font-family:'Segoe UI',sans-serif; background:#f1f5f9; padding:24px; }\n"
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
        "body {font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:24px;}</style>\n"
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
        "body {font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:24px;}</style>\n"
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