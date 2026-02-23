import requests
import json
import re
from fastapi import HTTPException
from app.config import OLLAMA_URL, OLLAMA_MODEL
# OLLAMA_URL   = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "llama3"


# ─────────────────────────────────────────────────────────────────────────────
# DETECT OUTPUT TYPE
# ─────────────────────────────────────────────────────────────────────────────
def detect_output_type(text_question: str) -> str:
    """
    Returns one of:
    'bar' | 'pie' | 'line' | 'area' | 'scatter' | 'radar' |
    'funnel' | 'heatmap' | 'card' | 'table' | 'text' | 'auto'
    """
    q = text_question.lower()

    if any(k in q for k in [
        "table", "tabular", "list", "rows", "grid",
        "show data", "display data", "in table", "as table", "spreadsheet"
    ]):
        return "table"

    if any(k in q for k in [
        "pie", "donut", "doughnut", "proportion", "percentage",
        "share", "breakdown", "distribution", "split"
    ]):
        return "pie"

    if any(k in q for k in [
        "line", "trend", "over time", "timeline", "growth",
        "progress", "history", "monthly", "yearly", "daily", "time series"
    ]):
        return "line"

    if any(k in q for k in ["area", "cumulative", "filled", "stacked area"]):
        return "area"

    if any(k in q for k in [
        "scatter", "correlation", "relationship", "versus", " vs ",
        "plot", "bubble"
    ]):
        return "scatter"

    if any(k in q for k in [
        "radar", "spider", "web chart", "radial", "skill", "performance radar"
    ]):
        return "radar"

    if any(k in q for k in [
        "funnel", "pipeline", "stages", "conversion", "drop off", "dropoff"
    ]):
        return "funnel"

    if any(k in q for k in [
        "heatmap", "heat map", "intensity", "matrix", "calendar"
    ]):
        return "heatmap"

    if any(k in q for k in [
        "card", "kpi", "summary", "metric", "count", "total",
        "stats", "statistics", "overview", "highlight"
    ]):
        return "card"

    if any(k in q for k in [
        "bar", "column", "compare", "comparison", "rank", "ranking",
        "salary", "amount", "highest", "lowest", "graph", "chart"
    ]):
        return "bar"

    if any(k in q for k in [
        "text", "explain", "describe", "summarize", "tell me",
        "what is", "analyze", "analysis", "insight", "report",
        "narrative", "write", "paragraph"
    ]):
        return "text"

    # Nothing matched — let Ollama decide
    return "auto"



# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────────────────────────────────────
def generate_react_visualization(request) -> dict:
    if isinstance(request.dbJsonData, str):
        try:
            db_data = json.loads(request.dbJsonData)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in dbJsonData")
    else:
        db_data = request.dbJsonData

    rows = db_data.get("rows", []) if isinstance(db_data, dict) else db_data
    if not rows:
        raise HTTPException(status_code=400, detail="No data rows found in dbJsonData")

    prompt, output_type = build_visualization_prompt(
        request.schemaName, request.query, request.textQue, rows
    )
    print(f"[Visualization] Detected type: {output_type}")

    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=800
    )

    print("STATUS:", response.status_code)
    data = response.json()

    if "response" not in data:
        raise HTTPException(status_code=500, detail=f"Unexpected Ollama response: {data}")

    react_code = extract_html(data["response"])

    return {
        "status":       "success",
        "schemaName":   request.schemaName,
        "query":        request.query,
        "textQuestion": request.textQue,
        "outputType":   output_type,
        "reactCode":    react_code
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT ROUTER
# ─────────────────────────────────────────────────────────────────────────────
def build_visualization_prompt(schema_name, query, text_question, rows):
    output_type = detect_output_type(text_question)

    builders = {
        "table":   build_table_prompt,
        "bar":     build_bar_prompt,
        "pie":     build_pie_prompt,
        "line":    build_line_prompt,
        "area":    build_area_prompt,
        "scatter": build_scatter_prompt,
        "radar":   build_radar_prompt,
        "funnel":  build_funnel_prompt,
        "heatmap": build_heatmap_prompt,
        "card":    build_card_prompt,
        "text":    build_text_prompt,
        "auto":    build_auto_prompt,
    }

    builder = builders.get(output_type, build_auto_prompt)
    return builder(schema_name, query, text_question, rows), output_type


# ─────────────────────────────────────────────────────────────────────────────
# SHARED CONTEXT
# ─────────────────────────────────────────────────────────────────────────────
def _ctx(schema_name, query, text_question, rows):
    sample_row   = rows[0] if rows else {}
    columns      = list(sample_row.keys())
    numeric_cols = [k for k, v in sample_row.items()
                    if isinstance(v, (int, float)) and v is not None]
    text_cols    = [k for k, v in sample_row.items()
                    if isinstance(v, str) and v is not None]
    data_sample  = json.dumps(rows[:50], indent=2, default=str)

    return {
        "columns":      columns,
        "numeric_cols": numeric_cols,
        "text_cols":    text_cols,
        "data_sample":  data_sample,
        "hint_label":   text_cols[0]    if text_cols    else columns[0],
        "hint_value":   numeric_cols[0] if numeric_cols else columns[-1],
        "row_count":    len(rows),
        "base": (
            "SCHEMA: "   + schema_name    + "\n"
            "SQL: "      + query          + "\n"
            "REQUEST: "  + text_question  + "\n"
            "ROWS: "     + str(len(rows)) + "\n"
            "COLUMNS: "  + ", ".join(columns) + "\n\n"
            "DATA:\n"    + data_sample    + "\n\n"
        ),
        "cdns": (
            '<script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>\n'
            '<script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>\n'
            '<script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>\n'
            '<script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.js"></script>\n'
            '<script src="https://unpkg.com/@babel/standalone@7.21.3/babel.min.js"></script>\n'
        ),
        "recharts_destruct": (
            'const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,\n'
            '        ResponsiveContainer, PieChart, Pie, Cell,\n'
            '        LineChart, Line, AreaChart, Area,\n'
            '        ScatterChart, Scatter, ZAxis,\n'
            '        RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,\n'
            '        FunnelChart, Funnel, LabelList } = Recharts;\n'
        ),
        "colors": (
            'const COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444",'
            '"#8b5cf6","#06b6d4","#f97316","#84cc16","#ec4899","#14b8a6"];\n'
        ),
        "base_style": (
            "<style>\n"
            "  * { margin:0; padding:0; box-sizing:border-box; }\n"
            "  body { font-family:'Segoe UI',sans-serif; background:#f8fafc; padding:24px; }\n"
            "  .card { background:#fff; border-radius:16px; padding:28px;"
            " box-shadow:0 4px 24px rgba(0,0,0,0.08); }\n"
            "  h2 { color:#1e293b; font-size:22px; margin-bottom:6px; }\n"
            "  .sub { color:#64748b; font-size:13px; margin-bottom:24px; }\n"
            "</style>\n"
        ),
        "chart_rules": (
            "MANDATORY RULES:\n"
            "1. ALL JavaScript strings MUST use DOUBLE QUOTES only. Never single quotes.\n"
            "2. Hardcode ALL data rows from DATA above into const data = [...].\n"
            "3. dataKey on Bar/Line/Area/Scatter MUST exactly match actual object keys.\n"
            "4. Use ReactDOM.render() NOT ReactDOM.createRoot().\n"
            "5. No import statements inside <script type=\"text/babel\">.\n"
            "6. Wrap chart in <ResponsiveContainer width=\"100%\" height={450}>.\n"
            "7. Return ONLY raw HTML. No markdown. No backticks. Start with <!DOCTYPE html>\n"
        ),
        "vanilla_rules": (
            "MANDATORY RULES:\n"
            "1. Pure HTML + CSS + vanilla JS only (no React, no libraries).\n"
            "2. Hardcode ALL data rows.\n"
            "3. Return ONLY raw HTML. No markdown. No backticks. Start with <!DOCTYPE html>\n"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_bar_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a Bar Chart HTML page using React + Recharts.\n\n"
        + c["base"]
        + "CHART SPEC:\n"
          "- Use <BarChart>\n"
          "- XAxis dataKey=\"" + c["hint_label"] + "\"\n"
          "- <Bar dataKey=\"" + c["hint_value"] + "\" fill=\"#3b82f6\" radius={[6,6,0,0]}>\n"
          "- Add <CartesianGrid strokeDasharray=\"3 3\">, <Tooltip>, <Legend>, <YAxis>\n"
          "- Use COLORS array if multiple bars\n\n"
        + c["chart_rules"]
        + "\nCDNs:\n" + c["cdns"]
    )


def build_pie_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a Donut/Pie Chart HTML page using React + Recharts.\n\n"
        + c["base"]
        + "CHART SPEC:\n"
          "- Use <PieChart>\n"
          "- <Pie dataKey=\"" + c["hint_value"] + "\" nameKey=\"" + c["hint_label"] + "\"\n"
          "       cx=\"50%\" cy=\"50%\" outerRadius={170} innerRadius={80} label>\n"
          "- Map each entry: <Cell fill={COLORS[index % COLORS.length]}>\n"
          "- Add <Tooltip> and <Legend>\n\n"
        + c["chart_rules"]
        + "\nCDNs:\n" + c["cdns"]
    )


def build_line_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a Line Chart HTML page using React + Recharts.\n\n"
        + c["base"]
        + "CHART SPEC:\n"
          "- Use <LineChart>\n"
          "- XAxis dataKey=\"" + c["hint_label"] + "\"\n"
          "- <Line type=\"monotone\" dataKey=\"" + c["hint_value"] + "\"\n"
          "       stroke=\"#3b82f6\" strokeWidth={2} dot={{ fill:\"#3b82f6\", r:4 }}>\n"
          "- Add <CartesianGrid strokeDasharray=\"3 3\">, <Tooltip>, <Legend>, <YAxis>\n\n"
        + c["chart_rules"]
        + "\nCDNs:\n" + c["cdns"]
    )


def build_area_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate an Area Chart HTML page using React + Recharts.\n\n"
        + c["base"]
        + "CHART SPEC:\n"
          "- Use <AreaChart>\n"
          "- XAxis dataKey=\"" + c["hint_label"] + "\"\n"
          "- <Area type=\"monotone\" dataKey=\"" + c["hint_value"] + "\"\n"
          "       stroke=\"#3b82f6\" fill=\"#bfdbfe\" strokeWidth={2}>\n"
          "- Add <CartesianGrid strokeDasharray=\"3 3\">, <Tooltip>, <Legend>, <YAxis>\n\n"
        + c["chart_rules"]
        + "\nCDNs:\n" + c["cdns"]
    )


def build_scatter_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    x = c["numeric_cols"][0] if len(c["numeric_cols"]) > 0 else c["columns"][0]
    y = c["numeric_cols"][1] if len(c["numeric_cols"]) > 1 else c["columns"][-1]
    return (
        "Generate a Scatter Plot HTML page using React + Recharts.\n\n"
        + c["base"]
        + "CHART SPEC:\n"
          "- Use <ScatterChart>\n"
          "- XAxis dataKey=\"" + x + "\" name=\"" + x + "\"\n"
          "- YAxis dataKey=\"" + y + "\" name=\"" + y + "\"\n"
          "- <Scatter name=\"Data\" data={data} fill=\"#3b82f6\">\n"
          "- Add <CartesianGrid>, <Tooltip cursor={{ strokeDasharray:\"3 3\" }}>\n"
          "- Destructure: ScatterChart, Scatter, ZAxis from Recharts\n\n"
        + c["chart_rules"]
        + "\nCDNs:\n" + c["cdns"]
    )


def build_radar_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a Radar/Spider Chart HTML page using React + Recharts.\n\n"
        + c["base"]
        + "CHART SPEC:\n"
          "- Use <RadarChart cx=\"50%\" cy=\"50%\" outerRadius={180}>\n"
          "- <PolarGrid>, <PolarAngleAxis dataKey=\"" + c["hint_label"] + "\">\n"
          "- <PolarRadiusAxis>\n"
          "- <Radar dataKey=\"" + c["hint_value"] + "\" stroke=\"#3b82f6\"\n"
          "        fill=\"#3b82f6\" fillOpacity={0.4}>\n"
          "- Add <Legend>, <Tooltip>\n"
          "- Destructure: RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis\n\n"
        + c["chart_rules"]
        + "\nCDNs:\n" + c["cdns"]
    )


def build_funnel_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a Funnel Chart HTML page using React + Recharts.\n\n"
        + c["base"]
        + "CHART SPEC:\n"
          "- Use <FunnelChart>\n"
          "- <Funnel dataKey=\"" + c["hint_value"] + "\" data={data} isAnimationActive>\n"
          "- <LabelList position=\"right\" fill=\"#000\" stroke=\"none\"\n"
          "             dataKey=\"" + c["hint_label"] + "\">\n"
          "- Color each segment: fill={COLORS[index % COLORS.length]}\n"
          "- Destructure: FunnelChart, Funnel, LabelList from Recharts\n\n"
        + c["chart_rules"]
        + "\nCDNs:\n" + c["cdns"]
    )


def build_heatmap_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a Heatmap HTML page using pure HTML/CSS/JS.\n\n"
        + c["base"]
        + "REQUIREMENTS:\n"
          "- CSS grid layout, color cells by value intensity (white to dark blue scale)\n"
          "- Show row and column labels clearly\n"
          "- Add a color legend bar at the bottom\n"
          "- Tooltip on hover showing exact value\n"
          "- Professional look: dark header, clean grid, rounded container, shadow\n\n"
        + c["vanilla_rules"]
    )


def build_card_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a KPI Dashboard Cards HTML page using pure HTML/CSS/JS.\n\n"
        + c["base"]
        + "REQUIREMENTS:\n"
          "- Compute from data: total count, averages, max, min, sum of numeric fields\n"
          "- Show each metric as a card: big bold number + label + colored icon\n"
          "- CSS grid layout: 3-4 cards per row, responsive\n"
          "- Card style: white bg, border-radius, shadow, colored top-border accent\n"
          "- Different accent color per card (blue, green, orange, purple, red)\n"
          "- Add a summary data table below the cards\n\n"
        + c["vanilla_rules"]
    )


def build_table_prompt(schema_name, query, text_question, rows):
    c         = _ctx(schema_name, query, text_question, rows)
    full_data = json.dumps(rows[:200], indent=2, default=str)
    return (
        "Generate a styled interactive HTML data table page.\n\n"
        "SCHEMA: "  + schema_name     + "\n"
        "SQL: "     + query           + "\n"
        "REQUEST: " + text_question   + "\n"
        "ROWS: "    + str(len(rows))  + "\n"
        "COLUMNS: " + ", ".join(c["columns"]) + "\n\n"
        "DATA:\n"   + full_data       + "\n\n"
        "FEATURES:\n"
        "1. Live search input filtering all columns\n"
        "2. Sortable columns (click header, show asc/desc arrow)\n"
        "3. Zebra striping + hover highlight\n"
        "4. Row count badge (updates with filter)\n"
        "5. Sticky header\n"
        "6. Nulls show as '-', numbers with commas, dates formatted\n"
        "7. Horizontal scroll for wide tables\n"
        "8. Pagination: 20 rows/page with Prev/Next buttons\n\n"
        "STYLE: header #1e293b white text, alt row #f8fafc, "
        "hover #e0f2fe, border #e2e8f0, radius 12px, shadow, Segoe UI font.\n\n"
        + c["vanilla_rules"]
    )


def build_text_prompt(schema_name, query, text_question, rows):
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "Generate a Text Analysis / Narrative Report HTML page.\n\n"
        + c["base"]
        + "REQUIREMENTS:\n"
          "- Write a clear narrative answering the user request\n"
          "- Sections: Executive Summary, Key Findings, Patterns & Trends, Outliers\n"
          "- Stats bar at top: total rows, averages, totals of numeric fields\n"
          "- Highlight key numbers with colored pill badges\n"
          "- Small data table at the bottom\n"
          "- Max-width 860px centered layout\n\n"
          "STYLE:\n"
          "- White card on #f8fafc background\n"
          "- Section headings: bold #1e293b with 4px left blue border accent\n"
          "- Key stat badges: blue pills\n"
          "- Body font: Georgia serif; headings: Segoe UI\n"
          "- Good line-height (1.7), comfortable padding\n\n"
        + c["vanilla_rules"]
    )


def build_auto_prompt(schema_name, query, text_question, rows):
    """No keyword matched — Ollama analyzes data and picks the best format."""
    c = _ctx(schema_name, query, text_question, rows)
    return (
        "You are a senior data visualization engineer.\n"
        "The user did NOT specify a chart type. YOU must decide the best format.\n\n"
        + c["base"]
        + "AVAILABLE FORMATS:\n"
          "| Format      | Best For                                          |\n"
          "|-------------|---------------------------------------------------|\n"
          "| BarChart    | Comparing values across categories               |\n"
          "| LineChart   | Trends over time / ordered sequence               |\n"
          "| AreaChart   | Cumulative trends over time                       |\n"
          "| PieChart    | Parts of a whole, percentages                     |\n"
          "| ScatterChart| Correlation between two numeric variables         |\n"
          "| RadarChart  | Multiple attributes compared across items         |\n"
          "| FunnelChart | Conversion stages, pipeline steps                 |\n"
          "| Heatmap     | Intensity over 2D grid (pure HTML/CSS)            |\n"
          "| KPI Cards   | Summary metrics, totals, averages (pure HTML/CSS) |\n"
          "| Table       | Raw row browsing, many columns, text-heavy data   |\n"
          "| Text Report | Narrative analysis, insights, explanation         |\n\n"
          "DECISION RULES:\n"
          "- Date/time column present -> LineChart or AreaChart\n"
          "- Category + one number -> BarChart\n"
          "- Parts of whole / status/gender breakdown -> PieChart\n"
          "- Two numeric columns -> ScatterChart\n"
          "- User wants insight/summary -> KPI Cards or Text Report\n"
          "- Many columns, raw data -> Table\n"
          "- No clear visual story -> Text Report\n\n"
          "RECHARTS RULES (for BarChart/LineChart/AreaChart/PieChart/ScatterChart/RadarChart/FunnelChart):\n"
        + c["chart_rules"]
        + "CDNs:\n" + c["cdns"]
        + "Recharts destructure:\n" + c["recharts_destruct"]
        + "Colors:\n" + c["colors"] + "\n"
        + "VANILLA RULES (for Heatmap / KPI Cards / Table / Text Report):\n"
        + c["vanilla_rules"]
        + "\nIMPORTANT: First line of your response must be: CHOSEN FORMAT: <format name>\n"
          "Then immediately output the complete HTML.\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# EXTRACT + FIX HTML
# ─────────────────────────────────────────────────────────────────────────────
def extract_html(response_text: str) -> str:
    response_text = response_text.strip()

    # Strip "CHOSEN FORMAT: ..." line if present (from auto prompt)
    response_text = re.sub(r'^CHOSEN FORMAT:.*\n', '', response_text, flags=re.IGNORECASE)

    for pattern in [r'```html\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```']:
        match = re.search(pattern, response_text)
        if match:
            extracted = match.group(1).strip()
            if "<!DOCTYPE" in extracted or "<html" in extracted:
                return fix_js_quotes(extracted)

    if "<!DOCTYPE html>" in response_text:
        start = response_text.find("<!DOCTYPE html>")
        return fix_js_quotes(response_text[start:].strip())

    if "<html" in response_text:
        start = response_text.find("<html")
        return fix_js_quotes(response_text[start:].strip())

    return fix_js_quotes(response_text)


def fix_js_quotes(html: str) -> str:
    """Fix single-quote issues inside Babel script blocks."""
    script_re = r'(<script type="text/babel">)([\s\S]*?)(</script>)'

    def fixer(m):
        content = m.group(2)
        content = re.sub(r"'(#[0-9a-fA-F]{3,8})'", r'"\1"', content)
        content = re.sub(
            r"const COLORS\s*=\s*\[([^\]]+)\]",
            lambda mx: "const COLORS = [" +
                       re.sub(r"['\"]([^'\"]+)['\"]", r'"\1"', mx.group(1)) + "]",
            content
        )
        return m.group(1) + content + m.group(3)

    return re.sub(script_re, fixer, html)