import requests
import json
import re
from fastapi import HTTPException
from app.config import OLLAMA_URL, OLLAMA_MODEL

# OLLAMA_URL   = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "qwen2.5:7b-instruct"
MAX_RETRIES  = 3

RECHARTS_ALL = (
    'const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,\n'
    '        ResponsiveContainer, PieChart, Pie, Cell,\n'
    '        LineChart, Line, AreaChart, Area,\n'
    '        ScatterChart, Scatter,\n'
    '        RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,\n'
    '        FunnelChart, Funnel, LabelList } = Recharts;\n'
    'const COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16"];\n'
)

CDNS = (
    '<script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>\n'
    '<script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>\n'
    '<script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>\n'
    '<script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.js"></script>\n'
    '<script src="https://unpkg.com/@babel/standalone@7.21.3/babel.min.js"></script>\n'
)

BASE_STYLE = """<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',sans-serif; background:#f1f5f9; padding:24px; min-height:100vh; }
.card { background:#fff; border-radius:16px; padding:28px; box-shadow:0 4px 24px rgba(0,0,0,0.08); }
h2 { color:#1e293b; font-size:22px; margin-bottom:6px; font-weight:700; }
.sub { color:#64748b; font-size:13px; margin-bottom:24px; }
</style>"""


# =============================================================================
# CRITICAL POST-PROCESSOR  — fixes all known Ollama output mistakes
# =============================================================================
def post_process_html(html: str) -> str:
    if '<script type="text/babel">' not in html:
        return html

    m = re.search(r'(<script type="text/babel">)([\s\S]*?)(</script>)', html)
    if not m:
        return html

    js = m.group(2)

    # Fix 1: Replace ANY partial Recharts destructure with full one
    if re.search(r'const\s*\{[^}]+\}\s*=\s*Recharts', js):
        js = re.sub(
            r'const\s*\{[^}]+\}\s*=\s*Recharts\s*;?',
            RECHARTS_ALL.strip(),
            js, count=1
        )
    elif 'Recharts' in js:
        js = RECHARTS_ALL + '\n' + js

    # Fix 2: Single-quoted hex colors
    js = re.sub(r"'(#[0-9a-fA-F]{3,8})'", r'"\1"', js)

    # Fix 3: COLORS array normalization
    js = re.sub(
        r'const COLORS\s*=\s*\[([^\]]+)\]',
        lambda mx: 'const COLORS = [' + re.sub(r"['\"]([^'\"]+)['\"]", r'"\1"', mx.group(1)) + ']',
        js
    )

    # Fix 4: createRoot -> render
    js = re.sub(
        r'ReactDOM\.createRoot\([^)]+\)\.render\(\s*<App\s*/>\s*\)',
        'ReactDOM.render(<App />, document.getElementById("root"))',
        js
    )

    # Fix 5: Direct ReactDOM.render(<Chart ...>, root) without App wrapper
    # Ollama sometimes does: ReactDOM.render(\n  <ResponsiveContainer>...</ResponsiveContainer>,\n  document...
    if 'const App' not in js:
        render_m = re.search(
            r'ReactDOM\.render\(\s*\n?\s*(<(?:ResponsiveContainer|BarChart|LineChart|PieChart|AreaChart|ScatterChart|RadarChart)[\s\S]+?)\s*,\s*\n?\s*document\.getElementById\(["\']root["\']\)\s*\)',
            js
        )
        if render_m:
            inner = render_m.group(1).strip()
            replacement = (
                'const App = () => (\n'
                '    <div className="card">\n'
                '        ' + inner + '\n'
                '    </div>\n'
                ');\n'
                'ReactDOM.render(<App />, document.getElementById("root"));'
            )
            js = js[:render_m.start()] + replacement + js[render_m.end():]

    # Fix 6: Ensure ReactDOM.render exists
    if 'ReactDOM.render' not in js and 'const App' in js:
        js += '\nReactDOM.render(<App />, document.getElementById("root"));\n'

    # Fix 7: Remove import statements
    js = re.sub(r'^import\s+.*?;?\s*$', '', js, flags=re.MULTILINE)

    return html[:m.start(1)] + m.group(1) + js + m.group(3) + html[m.end(3):]


# =============================================================================
# DETECT OUTPUT TYPE
# =============================================================================
def detect_output_type(text_question: str) -> str:
    q = text_question.lower()
    if any(k in q for k in ["table","tabular","list","rows","grid","show data","in table","as table"]): return "table"
    if any(k in q for k in ["pie","donut","proportion","percentage","breakdown","distribution","split"]): return "pie"
    if any(k in q for k in ["line","trend","over time","timeline","monthly","yearly","daily","time series"]): return "line"
    if any(k in q for k in ["area","cumulative","stacked area"]): return "area"
    if any(k in q for k in ["scatter","correlation"," vs ","bubble"]): return "scatter"
    if any(k in q for k in ["radar","spider","radial"]): return "radar"
    if any(k in q for k in ["funnel","pipeline","stages","conversion"]): return "funnel"
    if any(k in q for k in ["heatmap","heat map","matrix"]): return "heatmap"
    if any(k in q for k in ["card","kpi","summary","metric","stats","overview"]): return "card"
    if any(k in q for k in ["bar","column","compare","rank","salary","amount","graph","chart"]): return "bar"
    if any(k in q for k in ["text","explain","describe","summarize","analyze","insight","report"]): return "text"
    return "auto"


# =============================================================================
# MAIN ENTRY
# =============================================================================
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
        raise HTTPException(status_code=400, detail="No data rows found")

    prompt, output_type = build_visualization_prompt(request.schemaName, request.query, request.textQue, rows)
    print(f"[Visualization] Detected type: {output_type}")

    attempt = 0
    react_code = ""

    while attempt < MAX_RETRIES:
        attempt += 1
        print(f"[Visualization] Attempt {attempt}/{MAX_RETRIES}")

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                    "options": {"num_predict": 2048, "temperature": 0.1,
                                "top_p": 0.9, "top_k": 40, "num_ctx": 4096}
                },
                timeout=800
            )
            data = response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")

        if "response" not in data:
            raise HTTPException(status_code=500, detail=f"Unexpected: {data}")

        raw = data["response"]
        print(f"[Ollama] Length:{len(raw)} | Start: {raw[:150]}")

        react_code = extract_and_wrap_html(raw, rows, output_type)
        react_code = post_process_html(react_code)       # <-- KEY FIX

        issues = validate_html(react_code)
        print(f"[Validation] Issues: {issues}")

        if not issues:
            print("[Visualization] Valid — done")
            break

        react_code = post_process_html(react_code)       # second pass
        if not validate_html(react_code):
            print("[Visualization] Fixed — done")
            break

        if attempt < MAX_RETRIES:
            prompt = build_fix_prompt(react_code, validate_html(react_code))

    return {
        "status": "success", "schemaName": request.schemaName,
        "query": request.query, "textQuestion": request.textQue,
        "outputType": output_type, "reactCode": react_code, "attempts": attempt
    }


# =============================================================================
# SHARED CONTEXT
# =============================================================================
def _ctx(schema_name, query, text_question, rows):
    sample_row   = rows[0] if rows else {}
    columns      = list(sample_row.keys())
    numeric_cols = [k for k, v in sample_row.items() if isinstance(v, (int, float)) and v is not None]
    text_cols    = [k for k, v in sample_row.items() if isinstance(v, str) and v is not None]
    date_cols    = [k for k in text_cols if any(x in k.lower() for x in ["date","time","_at","day","month","year"])]
    hint_label   = date_cols[0] if date_cols else (text_cols[0] if text_cols else columns[0] if columns else "name")
    hint_value   = numeric_cols[0] if numeric_cols else (columns[-1] if columns else "value")
    data_sample  = json.dumps(rows[:15], default=str)
    return {
        "columns": columns, "numeric_cols": numeric_cols, "text_cols": text_cols,
        "date_cols": date_cols, "data_sample": data_sample,
        "hint_label": hint_label, "hint_value": hint_value, "row_count": len(rows),
        "base": f"SCHEMA:{schema_name}\nSQL:{query}\nREQUEST:{text_question}\nROWS:{len(rows)}\nCOLUMNS:{','.join(columns)}\n\nDATA:\n{data_sample}\n\n",
        "chart_rules": (
            "RULES (ALL MANDATORY):\n"
            "1. Output COMPLETE HTML <!DOCTYPE html> to </html>\n"
            "2. ALL JS strings = DOUBLE QUOTES only\n"
            "3. Hardcode ALL rows: const data = [...]\n"
            f'4. XAxis dataKey="{hint_label}"\n'
            f'5. Bar/Line/Area dataKey="{hint_value}"\n'
            "6. ALWAYS: const App = () => (...); ReactDOM.render(<App />, document.getElementById(\"root\"));\n"
            "7. NEVER use import statements in babel\n"
            "8. Output ONLY raw HTML. No markdown, no backticks.\n\n"
        ),
        "vanilla_rules": (
            "RULES:\n1. Complete HTML <!DOCTYPE> to </html>\n"
            "2. Pure HTML+CSS+JS only\n3. Hardcode all data\n"
            "4. Output ONLY raw HTML. No markdown.\n\n"
        ),
    }


# =============================================================================
# EXTRACT + WRAP
# =============================================================================
def extract_and_wrap_html(response_text: str, rows: list, output_type: str) -> str:
    response_text = response_text.strip()
    response_text = re.sub(r'^CHOSEN FORMAT:.*\n', '', response_text, flags=re.IGNORECASE)

    for pattern in [r'```html\s*([\s\S]*?)\s*```', r'```\s*([\s\S]*?)\s*```']:
        mm = re.search(pattern, response_text)
        if mm:
            ext = mm.group(1).strip()
            return ext if is_complete_html(ext) else wrap_in_shell(ext, rows)

    for marker in ["<!DOCTYPE html>", "<!doctype html>", "<html"]:
        if marker.lower() in response_text.lower():
            start = response_text.lower().find(marker.lower())
            html  = response_text[start:].strip()
            return html if is_complete_html(html) else wrap_in_shell(html, rows)

    if any(x in response_text for x in ["const App","ReactDOM","BarChart","PieChart","LineChart","const data"]):
        return wrap_in_shell(response_text, rows)

    if any(x in response_text for x in ["<table","<div","<style","<ul"]):
        return _wrap_vanilla_fragment(response_text)

    return build_python_fallback_table(rows)


def is_complete_html(text: str) -> bool:
    t = text.lower()
    return ("<!doctype html>" in t or "<html" in t) and "</html>" in t and len(text) > 300


def wrap_in_shell(code: str, rows: list) -> str:
    is_react = any(x in code for x in ["const App","ReactDOM","BarChart","PieChart","LineChart","Recharts","<Bar","<Line","<Pie"])
    return _wrap_react_shell(code, rows) if is_react else _wrap_vanilla_fragment(code)


def _wrap_react_shell(jsx_code: str, rows: list) -> str:
    if "const data" not in jsx_code:
        jsx_code = f"const data = {json.dumps(rows[:15], default=str)};\n\n" + jsx_code
    if "= Recharts" not in jsx_code:
        jsx_code = RECHARTS_ALL + "\n" + jsx_code
    jsx_code = re.sub(r"ReactDOM\.createRoot\([^)]+\)\.render\(<App\s*/>\);",
                      'ReactDOM.render(<App />, document.getElementById("root"));', jsx_code)
    if "ReactDOM.render" not in jsx_code:
        jsx_code += '\nReactDOM.render(<App />, document.getElementById("root"));\n'
    jsx_code = re.sub(r"'(#[0-9a-fA-F]{3,8})'", r'"\1"', jsx_code)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualization</title>
    {CDNS}
    {BASE_STYLE}
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
{jsx_code}
    </script>
</body>
</html>"""


def _wrap_vanilla_fragment(frag: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Visualization</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:24px}}</style>
</head><body><div style="background:#fff;border-radius:16px;padding:24px;box-shadow:0 4px 24px rgba(0,0,0,0.08)">{frag}</div></body></html>"""


def build_python_fallback_table(rows: list) -> str:
    if not rows:
        return "<html><body><p style='padding:40px'>No data.</p></body></html>"
    columns   = list(rows[0].keys())
    data_json = json.dumps(rows, default=str)
    headers   = "".join(f'<th onclick="st({i})">{c} <span id="a{i}"></span></th>' for i, c in enumerate(columns))
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Data</title>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:#f1f5f9;padding:24px}}
.w{{background:#fff;border-radius:16px;padding:24px;box-shadow:0 4px 24px rgba(0,0,0,0.08)}}
.top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}}
h2{{color:#1e293b;font-size:20px;font-weight:700}}.badge{{background:#3b82f6;color:#fff;padding:4px 14px;border-radius:20px;font-size:13px}}
input{{width:100%;padding:10px 16px;border:1px solid #e2e8f0;border-radius:10px;font-size:14px;margin-bottom:16px;outline:none}}
.sc{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:14px}}
thead th{{background:#1e293b;color:#fff;padding:12px 16px;text-align:left;cursor:pointer;white-space:nowrap;position:sticky;top:0}}
tbody tr:nth-child(even){{background:#f8fafc}}tbody tr:hover{{background:#e0f2fe}}
td{{padding:11px 16px;border-bottom:1px solid #f1f5f9;color:#374151}}.nil{{color:#94a3b8;font-style:italic}}
.pg{{display:flex;justify-content:space-between;align-items:center;margin-top:16px}}
.pg button{{padding:8px 18px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;cursor:pointer;font-weight:600}}
.pg button:disabled{{opacity:.4;cursor:not-allowed}}.pi{{color:#64748b;font-size:13px}}</style></head>
<body><div class="w">
<div class="top"><h2>Query Results</h2><span class="badge" id="badge">0 rows</span></div>
<input id="search" placeholder="Search..." oninput="fil()">
<div class="sc"><table><thead><tr>{headers}</tr></thead><tbody id="tb"></tbody></table></div>
<div class="pg"><button id="prev" onclick="pg(-1)">Prev</button><span class="pi" id="pi"></span><button id="next" onclick="pg(1)">Next</button></div>
</div>
<script>
const D={data_json},C={json.dumps(columns)},PS=20;
let f=[...D],sc=-1,sa=true,cp=1;
function fmt(v){{if(v==null)return '<span class="nil">-</span>';if(typeof v==='number')return v.toLocaleString();return String(v);}}
function render(){{const rows=f.slice((cp-1)*PS,cp*PS);
document.getElementById('tb').innerHTML=rows.map(r=>'<tr>'+C.map(c=>'<td>'+fmt(r[c])+'</td>').join('')+'</tr>').join('');
const tp=Math.ceil(f.length/PS)||1;
document.getElementById('badge').textContent=f.length+' rows';
document.getElementById('pi').textContent='Page '+cp+' of '+tp;
document.getElementById('prev').disabled=cp===1;document.getElementById('next').disabled=cp>=tp;}}
function fil(){{const q=document.getElementById('search').value.toLowerCase();
f=D.filter(r=>C.some(c=>String(r[c]??'').toLowerCase().includes(q)));cp=1;render();}}
function st(i){{const c=C[i];if(sc===i)sa=!sa;else{{sc=i;sa=true;}}
f.sort((a,b)=>{{const av=a[c]??'',bv=b[c]??'';return sa?(av<bv?-1:av>bv?1:0):(av<bv?1:av>bv?-1:0);}});
document.querySelectorAll('[id^=a]').forEach((el,j)=>el.textContent=j===i?(sa?' ↑':' ↓'):'');
cp=1;render();}}
function pg(d){{cp=Math.max(1,Math.min(cp+d,Math.ceil(f.length/PS)||1));render();}}
render();
</script></body></html>"""


# =============================================================================
# VALIDATE + FIX
# =============================================================================
def validate_html(html: str) -> list:
    issues = []
    if not html or len(html) < 200:
        issues.append("HTML too short"); return issues
    if not is_complete_html(html):
        issues.append("Missing complete HTML structure")
    if "text/babel" in html:
        mm = re.search(r'<script type="text/babel">([\s\S]*?)</script>', html)
        if mm:
            js = mm.group(1)
            if "'#" in js:                         issues.append("Single-quoted hex colors")
            if re.search(r"^import\s", js, re.M): issues.append("import statements in babel")
            if "createRoot" in js:                 issues.append("createRoot used")
            if "ReactDOM.render" not in js:        issues.append("Missing ReactDOM.render")
            destruct_m = re.search(r'const\s*\{([^}]+)\}\s*=\s*Recharts', js)
            if destruct_m and "ResponsiveContainer" not in destruct_m.group(1):
                issues.append("ResponsiveContainer missing from Recharts destructure")
    return issues


def auto_fix_html(html: str, issues: list) -> str:
    return post_process_html(html)


def build_fix_prompt(broken_html: str, issues: list) -> str:
    return (
        "Fix ALL issues and return ONLY corrected COMPLETE HTML.\n\n"
        "ISSUES:\n" + "\n".join(f"  - {i}" for i in issues) + "\n\n"
        "RULES:\n1. Double quotes in JS\n2. const App = () => (...); ReactDOM.render(<App />, ...)\n"
        "3. No imports\n4. Complete HTML\n5. Return ONLY raw HTML\n\n"
        "BROKEN HTML:\n" + broken_html[:5000]
    )


# =============================================================================
# PROMPT BUILDERS
# =============================================================================
def build_visualization_prompt(schema_name, query, text_question, rows):
    output_type = detect_output_type(text_question)
    builders = {
        "table": build_table_prompt, "bar": build_bar_prompt, "pie": build_pie_prompt,
        "line": build_line_prompt, "area": build_area_prompt, "scatter": build_scatter_prompt,
        "radar": build_radar_prompt, "funnel": build_funnel_prompt, "heatmap": build_heatmap_prompt,
        "card": build_card_prompt, "text": build_text_prompt, "auto": build_auto_prompt,
    }
    return builders.get(output_type, build_auto_prompt)(schema_name, query, text_question, rows), output_type


CHART_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Visualization</title>
    {cdns}
    {style}
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        {recharts}
        const data = [/* REPLACE: paste all data rows as JSON objects */];
        const App = () => (
            <div className="card">
                <h2>{title}</h2>
                <ResponsiveContainer width="100%" height={{450}}>
                    {chart_jsx}
                </ResponsiveContainer>
            </div>
        );
        ReactDOM.render(<App />, document.getElementById("root"));
    </script>
</body>
</html>"""


def _recharts_prompt(chart_type, c, chart_jsx_spec):
    return (
        f"Generate a COMPLETE {chart_type} HTML file.\n\n"
        f"{c['base']}"
        f"CHART JSX TO USE:\n{chart_jsx_spec}\n\n"
        f"{c['chart_rules']}"
        f"CDNs (copy exactly):\n{CDNS}"
        f"Recharts (copy exactly - includes ResponsiveContainer):\n{RECHARTS_ALL}"
        f"Style (copy exactly):\n{BASE_STYLE}\n"
        f"REQUIRED STRUCTURE:\n{CHART_TEMPLATE}"
    )


def build_bar_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return _recharts_prompt("Bar Chart", c,
        f'<BarChart data={{data}} margin={{{{top:20,right:30,left:20,bottom:20}}}}>\n'
        f'  <CartesianGrid strokeDasharray="3 3" />\n'
        f'  <XAxis dataKey="{c["hint_label"]}" />\n'
        f'  <YAxis />\n'
        f'  <Tooltip />\n'
        f'  <Legend />\n'
        f'  <Bar dataKey="{c["hint_value"]}" fill="#3b82f6" radius={{[6,6,0,0]}} />\n'
        f'</BarChart>'
    )

def build_pie_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return _recharts_prompt("Pie Chart", c,
        f'<PieChart>\n'
        f'  <Pie data={{data}} dataKey="{c["hint_value"]}" nameKey="{c["hint_label"]}"\n'
        f'       cx="50%" cy="50%" outerRadius={{170}} innerRadius={{80}} label>\n'
        f'    {{data.map((_, i) => <Cell key={{i}} fill={{COLORS[i % COLORS.length]}} />)}}\n'
        f'  </Pie>\n'
        f'  <Tooltip />\n'
        f'  <Legend />\n'
        f'</PieChart>'
    )

def build_line_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return _recharts_prompt("Line Chart", c,
        f'<LineChart data={{data}} margin={{{{top:20,right:30,left:20,bottom:20}}}}>\n'
        f'  <CartesianGrid strokeDasharray="3 3" />\n'
        f'  <XAxis dataKey="{c["hint_label"]}" />\n'
        f'  <YAxis />\n'
        f'  <Tooltip />\n'
        f'  <Legend />\n'
        f'  <Line type="monotone" dataKey="{c["hint_value"]}" stroke="#3b82f6" strokeWidth={{2}} />\n'
        f'</LineChart>'
    )

def build_area_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return _recharts_prompt("Area Chart", c,
        f'<AreaChart data={{data}} margin={{{{top:20,right:30,left:20,bottom:20}}}}>\n'
        f'  <CartesianGrid strokeDasharray="3 3" />\n'
        f'  <XAxis dataKey="{c["hint_label"]}" />\n'
        f'  <YAxis />\n'
        f'  <Tooltip />\n'
        f'  <Legend />\n'
        f'  <Area type="monotone" dataKey="{c["hint_value"]}" stroke="#3b82f6" fill="#bfdbfe" />\n'
        f'</AreaChart>'
    )

def build_scatter_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    x = c["numeric_cols"][0] if c["numeric_cols"] else c["columns"][0]
    y = c["numeric_cols"][1] if len(c["numeric_cols"]) > 1 else c["columns"][-1]
    return _recharts_prompt("Scatter Plot", c,
        f'<ScatterChart margin={{{{top:20,right:30,left:20,bottom:20}}}}>\n'
        f'  <CartesianGrid />\n'
        f'  <XAxis dataKey="{x}" name="{x}" />\n'
        f'  <YAxis dataKey="{y}" name="{y}" />\n'
        f'  <Tooltip />\n'
        f'  <Scatter data={{data}} fill="#3b82f6" />\n'
        f'</ScatterChart>'
    )

def build_radar_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return _recharts_prompt("Radar Chart", c,
        f'<RadarChart cx="50%" cy="50%" outerRadius={{180}} data={{data}}>\n'
        f'  <PolarGrid />\n'
        f'  <PolarAngleAxis dataKey="{c["hint_label"]}" />\n'
        f'  <PolarRadiusAxis />\n'
        f'  <Radar dataKey="{c["hint_value"]}" stroke="#3b82f6" fill="#3b82f6" fillOpacity={{0.4}} />\n'
        f'  <Tooltip />\n'
        f'  <Legend />\n'
        f'</RadarChart>'
    )

def build_funnel_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return _recharts_prompt("Funnel Chart", c,
        f'<FunnelChart>\n'
        f'  <Tooltip />\n'
        f'  <Funnel dataKey="{c["hint_value"]}" data={{data}} isAnimationActive>\n'
        f'    <LabelList dataKey="{c["hint_label"]}" position="right" />\n'
        f'  </Funnel>\n'
        f'</FunnelChart>'
    )

def build_heatmap_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return (f"Generate a COMPLETE Heatmap HTML page (pure HTML/CSS/JS).\n\n{c['base']}"
            "CSS grid colored by value intensity. Row/col labels. Color legend.\n\n" + c["vanilla_rules"])

def build_card_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return (f"Generate a COMPLETE KPI Cards Dashboard (pure HTML/CSS/JS).\n\n{c['base']}"
            "Compute: count, sum/avg/max/min of numeric cols. CSS grid cards. Table below.\n\n" + c["vanilla_rules"])

def build_table_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    full = json.dumps(r[:200], default=str)
    return (f"Generate a COMPLETE interactive HTML table.\n\nCOLUMNS:{','.join(c['columns'])}\nDATA:\n{full}\n\n"
            "Live search, sortable cols, zebra rows, sticky header, pagination 20/page.\n\n" + c["vanilla_rules"])

def build_text_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return (f"Generate a COMPLETE Text Analysis Report HTML page.\n\n{c['base']}"
            "Sections: Summary, Findings, Patterns. Stats top. Table bottom.\n\n" + c["vanilla_rules"])

def build_auto_prompt(s, q, t, r):
    c = _ctx(s, q, t, r)
    return (f"Choose BEST visualization and generate COMPLETE HTML.\n\n{c['base']}"
            "Options: BarChart|LineChart|PieChart|AreaChart|ScatterChart|Table|KPI Cards|Text Report\n"
            "- Dates+numbers->Line, Categories+1 number->Bar or Pie, Summary->KPI Cards\n\n"
            + c["chart_rules"]
            + f"CDNs:\n{CDNS}Recharts:\n{RECHARTS_ALL}{BASE_STYLE}\n" + c["vanilla_rules"])