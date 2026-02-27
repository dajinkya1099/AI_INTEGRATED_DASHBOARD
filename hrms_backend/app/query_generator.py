import requests
from app.config import OLLAMA_URL, OLLAMA_MODEL
from app.schema_generator import *
import json
import re
from fastapi import HTTPException

print("hrms_backend")

def generate_sql(queryRequest):
    prompt = build_prompt_for_query_genrate(queryRequest)
    return ollama_model_call(prompt)

def ollama_model_call(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=800
        )

        print("STATUS:", response.status_code)
        print("RAW RESPONSE:", response.text)

        data = response.json()

        if "response" in data:
            return data["response"]
        else:
            return f"Unexpected response: {data}"

    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"





def build_prompt_for_query_genrate(queryRequest):
    print("Fetching database schema...")
    schema = get_full_schema(queryRequest.schemaName)
    print("Schema fetched successfully"+ schema)
    user_question=queryRequest.textQue
    prompt = f"""
        You are a PostgreSQL expert.

        Use the following database schema with descriptions:

        {schema}

        Rules:
        - Generate only PostgreSQL SQL
        - Use proper JOINs
        - Do not explain
        - only select query generate
        - Return only SQL query

        User Question:
        {user_question}
        """

    return prompt






# import requests
# import json
# import re
# from fastapi import HTTPException

# OLLAMA_URL   = "http://localhost:11434/api/generate"
# OLLAMA_MODEL = "llama3"   # change to your model


# ─────────────────────────────────────────────────────────────────────────────
# Detect what the user wants: table or chart
# ─────────────────────────────────────────────────────────────────────────────
def detect_output_type(text_question: str) -> str:
    """Returns 'table' or 'chart'"""
    table_keywords = ["table", "tabular", "list", "rows", "grid",
                      "show data", "display data", "in table", "as table"]
    q = text_question.lower()
    for kw in table_keywords:
        if kw in q:
            return "table"
    return "chart"


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
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

    output_type = detect_output_type(request.textQue)
    print(f"Output type detected: {output_type}")

    if output_type == "table":
        prompt = build_table_prompt(request.schemaName, request.query, request.textQue, rows)
    else:
        prompt = build_chart_prompt(request.schemaName, request.query, request.textQue, rows)

    print("prompt:", prompt)
    # response = requests.post(
    #     OLLAMA_URL,
    #     json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
    #     timeout=300
    # )
    response = requests.post(
         OLLAMA_URL,
         json={
             "model": OLLAMA_MODEL,
             "prompt": prompt,
             "stream": False
         },
         timeout=800
     )


    print("STATUS:", response.status_code)
    data = response.json()

    if "response" not in data:
        raise HTTPException(status_code=500, detail=f"Unexpected Ollama response: {data}")

    raw_response = data["response"]
    react_code   = extract_react_code(raw_response)

    return {
        "status":       "success",
        "schemaName":   request.schemaName,
        "query":        request.query,
        "textQuestion": request.textQue,
        "outputType":   output_type,
        "reactCode":    react_code
    }


# ─────────────────────────────────────────────────────────────────────────────
# CHART PROMPT  — fixes empty bar by injecting real data + explicit dataKey
# ─────────────────────────────────────────────────────────────────────────────
def build_chart_prompt(schema_name: str, query: str, text_question: str, rows: list) -> str:
    print("build_chart_prompt:")
    sample_row   = rows[0] if rows else {}
    columns      = list(sample_row.keys())
    row_count    = len(rows)
    data_sample  = json.dumps(rows[:50], indent=2, default=str)
    columns_str  = ", ".join(columns)

    # pick obvious label + value columns from first row so model has a hint
    numeric_cols = [k for k, v in sample_row.items()
                    if isinstance(v, (int, float)) and v is not None]
    text_cols    = [k for k, v in sample_row.items()
                    if isinstance(v, str) and v is not None]
    hint_label   = text_cols[0]    if text_cols    else columns[0]
    hint_value   = numeric_cols[0] if numeric_cols else columns[-1]

    return (
        "You are a React + Recharts expert. Generate a COMPLETE self-contained HTML file.\n\n"
        "SCHEMA: " + schema_name + "\n"
        "SQL: " + query + "\n"
        "USER REQUEST: " + text_question + "\n"
        "ROWS: " + str(row_count) + "\n"
        "COLUMNS: " + columns_str + "\n"
        "SUGGESTED LABEL COLUMN: " + hint_label + "\n"
        "SUGGESTED VALUE COLUMN: " + hint_value + "\n\n"
        "ACTUAL DATA (use this exactly inside the component):\n"
        + data_sample + "\n\n"

        "CHART SELECTION:\n"
        "- Bar Chart  -> comparisons, salary, counts\n"
        "- Pie Chart  -> distributions, gender, status %\n"
        "- Line Chart -> trends, dates, time series\n"
        "- Area Chart -> cumulative trends\n\n"

        "CRITICAL RULES - EVERY RULE IS MANDATORY:\n"
        "1. All JavaScript strings use DOUBLE QUOTES only. Never single quotes.\n"
        "2. HARDCODE all data rows from ACTUAL DATA above into the const data = [...] array.\n"
        "3. The dataKey on <Bar>, <Line>, <Area> MUST exactly match a key from the data objects.\n"
        "4. For BarChart you MUST include: <XAxis dataKey=\"LABEL_COLUMN\" /> and <Bar dataKey=\"VALUE_COLUMN\" fill=\"#3b82f6\" />.\n"
        "5. Wrap chart in <ResponsiveContainer width=\"100%\" height={450}>.\n"
        "6. Access Recharts via: const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area } = Recharts;\n"
        "7. Use ReactDOM.render() NOT ReactDOM.createRoot().\n"
        "8. No import statements inside <script type=\"text/babel\">.\n"
        "9. For Pie charts, each <Cell> fill must come from COLORS array using index.\n\n"

        "EXACT CDN SCRIPTS (copy exactly, no changes):\n"
        "<script src=\"https://unpkg.com/react@17/umd/react.production.min.js\"></script>\n"
        "<script src=\"https://unpkg.com/react-dom@17/umd/react-dom.production.min.js\"></script>\n"
        "<script src=\"https://unpkg.com/prop-types@15.8.1/prop-types.min.js\"></script>\n"
        "<script src=\"https://unpkg.com/recharts@2.1.9/umd/Recharts.js\"></script>\n"
        "<script src=\"https://unpkg.com/@babel/standalone@7.21.3/babel.min.js\"></script>\n\n"

        "COMPLETE HTML TEMPLATE TO FOLLOW:\n"
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "    <meta charset=\"UTF-8\">\n"
        "    <title>Chart</title>\n"
        "    [CDN SCRIPTS HERE]\n"
        "    <style>\n"
        "        * { margin: 0; padding: 0; box-sizing: border-box; }\n"
        "        body { font-family: 'Segoe UI', sans-serif; background: #f8fafc; padding: 24px; }\n"
        "        .card { background: #fff; border-radius: 16px; padding: 28px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }\n"
        "        h2 { color: #1e293b; font-size: 22px; margin-bottom: 6px; }\n"
        "        .sub { color: #64748b; font-size: 13px; margin-bottom: 24px; }\n"
        "    </style>\n"
        "</head>\n"
        "<body>\n"
        "    <div id=\"root\"></div>\n"
        "    <script type=\"text/babel\">\n"
        "        const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,\n"
        "                ResponsiveContainer, PieChart, Pie, Cell,\n"
        "                LineChart, Line, AreaChart, Area } = Recharts;\n\n"
        "        const COLORS = [\"#3b82f6\",\"#10b981\",\"#f59e0b\",\"#ef4444\",\"#8b5cf6\",\"#06b6d4\",\"#f97316\",\"#84cc16\"];\n\n"
        "        const App = () => {\n"
        "            const data = [ /* PASTE ALL DATA ROWS HERE */ ];\n\n"
        "            return (\n"
        "                <div className=\"card\">\n"
        "                    <h2>CHART TITLE</h2>\n"
        "                    <p className=\"sub\">SOURCE DESCRIPTION</p>\n"
        "                    <ResponsiveContainer width=\"100%\" height={450}>\n"
        "                        /* CHART COMPONENT HERE */\n"
        "                    </ResponsiveContainer>\n"
        "                </div>\n"
        "            );\n"
        "        };\n\n"
        "        ReactDOM.render(<App />, document.getElementById(\"root\"));\n"
        "    </script>\n"
        "</body>\n"
        "</html>\n\n"
        "OUTPUT: Return ONLY the raw HTML file. No markdown. No backticks. No explanation.\n"
        "Start your response with <!DOCTYPE html>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TABLE PROMPT  — attractive styled HTML table
# ─────────────────────────────────────────────────────────────────────────────
def build_table_prompt(schema_name: str, query: str, text_question: str, rows: list) -> str:
    columns     = list(rows[0].keys()) if rows else []
    row_count   = len(rows)
    data_sample = json.dumps(rows[:200], indent=2, default=str)

    return (
        "You are an HTML/CSS expert. Generate a COMPLETE self-contained attractive HTML table page.\n\n"
        "SCHEMA: " + schema_name + "\n"
        "SQL: " + query + "\n"
        "USER REQUEST: " + text_question + "\n"
        "TOTAL ROWS: " + str(row_count) + "\n"
        "COLUMNS: " + ", ".join(columns) + "\n\n"
        "ACTUAL DATA:\n" + data_sample + "\n\n"

        "REQUIREMENTS:\n"
        "1. Create a beautiful modern styled HTML table with ALL rows from ACTUAL DATA.\n"
        "2. Include a search/filter input at the top that filters rows as user types.\n"
        "3. Include column sorting on click (toggle asc/desc with arrow indicator).\n"
        "4. Alternate row colors (zebra striping).\n"
        "5. Highlight row on hover.\n"
        "6. Show total row count badge.\n"
        "7. Format numbers with commas. Format dates nicely. Show null as dash '-'.\n"
        "8. Sticky header that stays visible when scrolling.\n"
        "9. Responsive with horizontal scroll on small screens.\n"
        "10. Professional dark header, clean white rows.\n\n"

        "STYLE GUIDE:\n"
        "- Font: Segoe UI or system sans-serif\n"
        "- Header bg: #1e293b, text: white\n"
        "- Alternate row: #f8fafc\n"
        "- Hover row: #e0f2fe\n"
        "- Border: 1px solid #e2e8f0\n"
        "- Border radius on container: 12px\n"
        "- Box shadow on table container\n"
        "- Search bar: top, full width, nice rounded input\n"
        "- Row count badge: top right, blue pill\n\n"

        "OUTPUT: Return ONLY the complete raw HTML file.\n"
        "No markdown. No backticks. No explanation.\n"
        "Start your response with <!DOCTYPE html>"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Extract + fix HTML from Ollama response
# ─────────────────────────────────────────────────────────────────────────────
def extract_react_code(response_text: str) -> str:
    response_text = response_text.strip()

    # Remove markdown fences
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
    """Fix single-quote strings inside <script type=text/babel> blocks."""
    script_re = r'(<script type="text/babel">)([\s\S]*?)(</script>)'

    def fixer(m):
        content = m.group(2)
        # Fix hex colors in arrays: '#abc' -> "#abc"
        content = re.sub(r"'(#[0-9a-fA-F]{3,8})'", r'"\1"', content)
        # Normalise COLORS array to all double-quotes
        content = re.sub(
            r"const COLORS\s*=\s*\[([^\]]+)\]",
            lambda mx: "const COLORS = [" +
                       re.sub(r"['\"]([^'\"]+)['\"]", r'"\1"', mx.group(1)) + "]",
            content
        )
        return m.group(1) + content + m.group(3)

    return re.sub(script_re, fixer, html)




# def generate_react_visualization(queryRequest) -> dict:
#     """
#     Generate React visualization code based on query data using Ollama.
#     """
    
#     # Parse dbJsonData if it's a string
#     if isinstance(queryRequest.dbJsonData, str):
#         try:
#             db_data = json.loads(queryRequest.dbJsonData)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=400, detail="Invalid JSON in dbJsonData")
#     else:
#         db_data = queryRequest.dbJsonData

#     # Extract rows from the data
#     rows = db_data.get("rows", []) if isinstance(db_data, dict) else db_data
    
#     if not rows:
#         raise HTTPException(status_code=400, detail="No data rows found in dbJsonData")

#     # Build prompt
#     prompt = build_visualization_prompt(
#         schema_name=queryRequest.schemaName,
#         query=queryRequest.query,
#         text_question=queryRequest.textQue,
#         rows=rows
#     )

#     # Call Ollama
#     response = requests.post(
#         OLLAMA_URL,
#         json={
#             "model": OLLAMA_MODEL,
#             "prompt": prompt,
#             "stream": False
#         },
#         timeout=800
#     )

#     print("STATUS:", response.status_code)
#     print("RAW RESPONSE:", response.text[:500])

#     data = response.json()

#     if "response" not in data:
#         raise HTTPException(status_code=500, detail=f"Unexpected Ollama response: {data}")

#     raw_response = data["response"]
#     react_code = extract_react_code(raw_response)

#     return {
#         "status": "success",
#         "schemaName": queryRequest.schemaName,
#         "query": queryRequest.query,
#         "textQuestion": queryRequest.textQue,
#         "reactCode": react_code
#     }

# def build_visualization_prompt(schema_name: str, query: str, text_question: str, rows: list) -> str:
#     sample_row = rows[0] if rows else {}
#     columns = list(sample_row.keys())
#     row_count = len(rows)
#     data_sample = json.dumps(rows[:50], indent=2, default=str)

#     # Build COLORS outside f-string to avoid conflict
#     colors_array = '["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16"]'
#     columns_str = ', '.join(columns)

#     prompt = """You are a React and data visualization expert. Generate a complete self-contained HTML file with a React chart.

# SCHEMA: """ + schema_name + """
# SQL QUERY: """ + query + """
# USER REQUEST: """ + text_question + """
# TOTAL ROWS: """ + str(row_count) + """
# COLUMNS: """ + columns_str + """

# DATA:
# """ + data_sample + """

# CHART SELECTION RULES:
# - Bar Chart -> salary comparison, counts, rankings, numeric comparisons
# - Pie Chart -> distribution, gender split, status breakdown, percentages  
# - Line Chart -> trends over time, sequential dates
# - Area Chart -> cumulative data over time

# STRICT CODING RULES - NEVER VIOLATE:
# 1. Use ONLY double quotes for ALL strings in JavaScript. Never use single quotes.
# 2. COLORS must be written exactly as: const COLORS = """ + colors_array + """;
# 3. Access Recharts like: const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area } = Recharts;
# 4. Never use import statements
# 5. Use ReactDOM.render() not ReactDOM.createRoot()
# 6. All JSX attribute strings must use double quotes: width="100%" not width='100%'
# 7. Numeric JSX attributes must use braces: height={400} not height="400"

# REQUIRED HTML TEMPLATE - COPY EXACTLY, ONLY FILL IN DATA AND CHART:
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Visualization</title>
#     <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
#     <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
#     <script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
#     <script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.js"></script>
#     <script src="https://unpkg.com/@babel/standalone@7.21.3/babel.min.js"></script>
#     <style>
#         * { margin: 0; padding: 0; box-sizing: border-box; }
#         body { font-family: sans-serif; background: #f8fafc; padding: 20px; }
#         .container { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
#         h2 { color: #1e293b; margin-bottom: 20px; font-size: 20px; }
#     </style>
# </head>
# <body>
#     <div id="root"></div>
#     <script type="text/babel">
#         const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
#                 ResponsiveContainer, PieChart, Pie, Cell,
#                 LineChart, Line, AreaChart, Area } = Recharts;

#         const COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#f97316","#84cc16"];

#         const App = () => {
#             const data = [
#                 /* PUT ACTUAL DATA OBJECTS HERE USING DOUBLE QUOTES ONLY */
#             ];

#             return (
#                 <div className="container">
#                     <h2>PUT CHART TITLE HERE</h2>
#                     <ResponsiveContainer width="100%" height={400}>
#                         /* PUT CHART COMPONENT HERE */
#                     </ResponsiveContainer>
#                 </div>
#             );
#         };

#         ReactDOM.render(<App />, document.getElementById("root"));
#     </script>
# </body>
# </html>

# OUTPUT RULES:
# - Return ONLY raw HTML starting with <!DOCTYPE html>
# - No markdown, no backticks, no explanation
# - Every string in JavaScript must use double quotes
# - Never mix single and double quotes in the same array or object"""

#     return prompt


# def extract_react_code(response_text: str) -> str:
#     response_text = response_text.strip()

#     # Extract from markdown fences if present
#     html_pattern = r'```html\s*([\s\S]*?)\s*```'
#     match = re.search(html_pattern, response_text)
#     if match:
#         code = match.group(1).strip()
#         return fix_quote_issues(code)

#     code_pattern = r'```\s*([\s\S]*?)\s*```'
#     match = re.search(code_pattern, response_text)
#     if match:
#         extracted = match.group(1).strip()
#         if '<!DOCTYPE' in extracted or '<html' in extracted:
#             return fix_quote_issues(extracted)

#     if '<!DOCTYPE html>' in response_text:
#         start = response_text.find('<!DOCTYPE html>')
#         return fix_quote_issues(response_text[start:].strip())

#     if '<html' in response_text:
#         start = response_text.find('<html')
#         return fix_quote_issues(response_text[start:].strip())

#     return fix_quote_issues(response_text)


# def fix_quote_issues(html: str) -> str:
#     """
#     Fix common quote mixing issues that cause Babel syntax errors.
#     Only fixes JavaScript inside <script> tags, not HTML attributes.
#     """
#     # Find script tag content
#     script_pattern = r'(<script type="text/babel">)([\s\S]*?)(</script>)'
    
#     def fix_script_content(match):
#         open_tag  = match.group(1)
#         content   = match.group(2)
#         close_tag = match.group(3)
        
#         # Fix mixed quotes in arrays: ['#abc',"#def"] -> ["#abc","#def"]
#         # Replace single-quoted hex color strings with double-quoted
#         content = re.sub(r"'(#[0-9a-fA-F]{3,6})'", r'"\1"', content)
        
#         # Fix mixed quotes in COLORS array specifically
#         content = re.sub(
#             r"const COLORS\s*=\s*\[([^\]]+)\]",
#             lambda m: "const COLORS = [" + 
#                       re.sub(r"['\"]([^'\"]+)['\"]", r'"\1"', m.group(1)) + 
#                       "]",
#             content
#         )
        
#         return open_tag + content + close_tag

#     fixed = re.sub(script_pattern, fix_script_content, html)
#     return fixed

# def build_visualization_prompt(schema_name: str, query: str, text_question: str, rows: list) -> str:
#     sample_row = rows[0] if rows else {}
#     columns = list(sample_row.keys())
#     row_count = len(rows)
#     data_sample = json.dumps(rows[:50], indent=2, default=str)

#     prompt = f"""You are a React and data visualization expert. Generate a complete self-contained HTML file with a React chart.

# SCHEMA: {schema_name}
# SQL QUERY: {query}
# USER REQUEST: {text_question}
# TOTAL ROWS: {row_count}
# COLUMNS: {', '.join(columns)}

# DATA:
# {data_sample}

# INSTRUCTIONS:
# - Analyze the user request: "{text_question}"
# - Choose the best chart type:
#   * Bar Chart -> salary comparison, counts, rankings
#   * Pie Chart -> distribution, gender, status breakdown
#   * Line Chart -> trends over time, dates
#   * Area Chart -> cumulative data over time
# - Generate ONE complete HTML file only
# - Hardcode the actual data inside the component
# - Include title, tooltips, legend, axis labels
# - Use professional colors
# - Handle null values gracefully

# CRITICAL RULES - FOLLOW EXACTLY:
# 1. Use EXACTLY these CDN script tags in EXACTLY this order - do not change versions or URLs:
#    <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
#    <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
#    <script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
#    <script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.js"></script>
#    <script src="https://unpkg.com/@babel/standalone@7.21.3/babel.min.js"></script>

# 2. Access Recharts components like this ONLY:
#    const {{ BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
#            PieChart, Pie, Cell, LineChart, Line, AreaChart, Area }} = Recharts;

# 3. DO NOT use import statements inside <script type="text/babel">
# 4. DO NOT use React.createElement directly
# 5. Use window.ReactDOM.render() NOT ReactDOM.createRoot()

# REQUIRED EXACT HTML TEMPLATE:
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Visualization</title>
#     <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
#     <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
#     <script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
#     <script src="https://unpkg.com/recharts@2.1.9/umd/Recharts.js"></script>
#     <script src="https://unpkg.com/@babel/standalone@7.21.3/babel.min.js"></script>
#     <style>
#         * {{ margin: 0; padding: 0; box-sizing: border-box; }}
#         body {{ font-family: sans-serif; background: #f8fafc; padding: 20px; }}
#         .container {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
#         h2 {{ color: #1e293b; margin-bottom: 20px; font-size: 20px; }}
#     </style>
# </head>
# <body>
#     <div id="root"></div>
#     <script type="text/babel">
#         const {{ BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
#                 ResponsiveContainer, PieChart, Pie, Cell,
#                 LineChart, Line, AreaChart, Area }} = Recharts;

#         const COLORS = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#f97316','#84cc16'];

#         const App = () => {{
#             const data = [/* REPLACE WITH ACTUAL DATA */];

#             return (
#                 <div className="container">
#                     <h2>Chart Title Here</h2>
#                     <ResponsiveContainer width="100%" height={{400}}>
#                         /* CHART HERE */
#                     </ResponsiveContainer>
#                 </div>
#             );
#         }};

#         ReactDOM.render(<App />, document.getElementById('root'));
#     </script>
# </body>
# </html>

# OUTPUT: Return ONLY the complete HTML. No explanation. No markdown fences. Just raw HTML starting with <!DOCTYPE html>"""

#     return prompt
# def extract_react_code(response_text: str) -> str:
#     """
#     Extract clean HTML from Ollama response.
#     """
#     response_text = response_text.strip()

#     # Try ```html ... ``` block
#     html_pattern = r'```html\s*([\s\S]*?)\s*```'
#     match = re.search(html_pattern, response_text)
#     if match:
#         return match.group(1).strip()

#     # Try generic ``` ... ``` block
#     code_pattern = r'```\s*([\s\S]*?)\s*```'
#     match = re.search(code_pattern, response_text)
#     if match:
#         extracted = match.group(1).strip()
#         if '<!DOCTYPE' in extracted or '<html' in extracted:
#             return extracted

#     # Raw HTML directly in response
#     if '<!DOCTYPE html>' in response_text:
#         start = response_text.find('<!DOCTYPE html>')
#         return response_text[start:].strip()

#     if '<html' in response_text:
#         start = response_text.find('<html')
#         return response_text[start:].strip()

#     return response_text







# def build_visualization_prompt(schema_name: str, query: str, text_question: str, rows: list) -> str:
#     """
#     Build prompt for Ollama to generate React visualization code.
#     """
#     sample_row = rows[0] if rows else {}
#     columns = list(sample_row.keys())
#     row_count = len(rows)

#     # Limit rows to avoid token overflow in local models
#     data_sample = json.dumps(rows[:50], indent=2, default=str)

#     prompt = f"""You are a React and data visualization expert. Generate a complete self-contained HTML file with a React chart.

# SCHEMA: {schema_name}
# SQL QUERY: {query}
# USER REQUEST: {text_question}
# TOTAL ROWS: {row_count}
# COLUMNS: {', '.join(columns)}

# DATA:
# {data_sample}

# INSTRUCTIONS:
# - Analyze the user request: "{text_question}"
# - Choose the best chart type:
#   * Bar Chart -> salary comparison, counts, rankings
#   * Pie Chart -> distribution, gender, status breakdown
#   * Line Chart -> trends over time, dates
#   * Area Chart -> cumulative data over time
# - Generate ONE complete HTML file only
# - Use Recharts library from CDN
# - Hardcode the actual data inside the component
# - Include title, tooltips, legend, axis labels
# - Use professional colors
# - Handle null values gracefully

# REQUIRED HTML STRUCTURE (follow exactly):
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <title>Chart</title>
#     <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
#     <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
#     <script src="https://unpkg.com/recharts@2.8.0/umd/Recharts.js"></script>
#     <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
#     <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
# </head>
# <body>
#     <div id="root"></div>
#     <script type="text/babel">
#         const App = () => {{
#             const data = [/* PUT ACTUAL DATA HERE */];
#             return (
#                 <div>
#                     /* PUT CHART HERE */
#                 </div>
#             );
#         }};
#         ReactDOM.createRoot(document.getElementById('root')).render(<App />);
#     </script>
# </body>
# </html>

# OUTPUT: Return ONLY the complete HTML file. No explanation. No markdown. Just raw HTML starting with <!DOCTYPE html>"""

#     return prompt


# def extract_react_code(response_text: str) -> str:
#     """
#     Extract clean HTML from Ollama response.
#     Handles cases where model wraps in markdown or adds extra text.
#     """

#     # Try ```html ... ``` block first
#     html_pattern = r'```html\s*([\s\S]*?)\s*```'
#     match = re.search(html_pattern, response_text)
#     if match:
#         return match.group(1).strip()

#     # Try generic ``` ... ``` block
#     code_pattern = r'```\s*([\s\S]*?)\s*```'
#     match = re.search(code_pattern, response_text)
#     if match:
#         return match.group(1).strip()

#     # Try to find raw HTML directly
#     if '<!DOCTYPE html>' in response_text:
#         start = response_text.find('<!DOCTYPE html>')
#         return response_text[start:].strip()

#     if '<html' in response_text:
#         start = response_text.find('<html')
#         return response_text[start:].strip()

#     # Return as-is
#     return response_text.strip()