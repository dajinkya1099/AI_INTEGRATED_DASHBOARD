from app.config import OLLAMA_URL, OLLAMA_MODEL,OLLAMA_MODEL_INTENT
import re
import json
import requests
import pandas as pd
import numpy as np

def build_prompt_for_ai_suggestions(sample_data):

    prompt = f"""
You are a strict data analytics engine.

Your job:
Analyze the given JSON dataset and generate 3 to 5 meaningful dashboard suggestions.

DATASET:
{json.dumps(sample_data, indent=2)}

--------------------------------------------------
ABSOLUTE RULES (MUST FOLLOW STRICTLY)
--------------------------------------------------

1. Return ONLY valid JSON.
2. Do NOT return explanations, text, markdown, or comments.
3. Use ONLY columns that exist in the dataset.
4. Do NOT invent new columns.
5. Remove any field that is not required for that viewType.
6. If ANY rule is violated, regenerate the entire JSON.

--------------------------------------------------
ALLOWED viewType VALUES
--------------------------------------------------

"card"
"chart"
"table"

Never use any other value.

--------------------------------------------------
CARD RULES
--------------------------------------------------

- Must include:
    "title"
    "viewType": "card"
    "metric"
    "operation"

- operation must be one of:
    "sum", "avg", "count", "min", "max"

- metric must be an existing column.
- sum/avg/min/max allowed only on numeric columns.
- count allowed on any column.

- Cards MUST NOT include:
    chartType, xKey, yKey, categoryKey, valueKey,
    columns, sortBy, order, limit

--------------------------------------------------
CHART RULES
--------------------------------------------------

- Must include:
    "title"
    "viewType": "chart"
    "chartType"

- chartType must be:
    "bar", "line", or "pie"

-----------------
BAR / LINE
-----------------

- Must include:
    "xKey"
    "yKey"
    "operation (Depends on title)"

- xKey must be categorical column.
- yKey must be numeric column.
- yKey must be raw numeric column name only.

- operation must be one of:
    "sum", "avg", "count", "min", "max"
    
- Operation must be determined strictly from the title:
    If title contains "Total"     → operation = "sum"
    If title contains "Average"   → operation = "avg"
    If title contains "Count"     → operation = "count"
    If title contains "Highest"   → operation = "max"
    If title contains "Maximum"   → operation = "max"
    If title contains "Lowest"    → operation = "min"
    If title contains "Minimum"   → operation = "min"
    
- If none of these keywords appear in the title:
    DO NOT include "operation"

- Must NOT include:
    metric, categoryKey, valueKey,
    sortBy, order, limit

-----------------
PIE
-----------------

- Must include:
    "categoryKey"
    "valueKey"

- categoryKey must be categorical column.
- valueKey must be numeric column.
- valueKey must be raw column name only.
- NO aggregation keywords like count, sum, avg.

- Must NOT include:
    xKey, yKey, metric, operation,
    sortBy, order, limit

--------------------------------------------------
TABLE RULES
--------------------------------------------------

- Must include:
    "title"
    "viewType": "table"
    "columns"

- columns must be an array of existing dataset columns.

- Ranking is allowed ONLY in table.
- If ranking is used, include:
    "sortBy"
    "order"
    "limit"

- Ranking rules:
    - sortBy must be numeric column
    - "desc" for Top / Highest
    - "asc" for Lowest / Bottom
    - limit must be greater than 0

- Tables MUST NOT include:
    chartType, xKey, yKey,
    categoryKey, valueKey,
    metric, operation

--------------------------------------------------
OUTPUT FORMAT (STRICT)
--------------------------------------------------

Return JSON in this exact structure:

{{
  "suggestions": [
    {{
      "title": "string",
      "viewType": "card | chart | table",
      "chartType": "bar | line | pie",
      "metric": "string",
      "operation": "sum | avg | count | min | max",
      "xKey": "string",
      "yKey": "string",
      "categoryKey": "string",
      "valueKey": "string",
      "columns": ["string"],
      "sortBy": "string",
      "order": "asc | desc",
      "limit": 0
    }}
  ]
}}

Before returning:
- Validate every suggestion against all rules.
- Remove unused fields.
- Return ONLY valid JSON.
"""
    return prompt
#  prompt = f"""
# You are a senior data analyst AI.

# Your task is to intelligently analyze ANY JSON dataset and generate structured dashboard suggestions.

# DATASET:
# {json.dumps(sample_data, indent=2)}

# --------------------------------------------------
# STEP 1 — DATA PROFILING
# --------------------------------------------------
# 1. Detect dataset type:
#    - transactional
#    - master
#    - time_series
#    - summary

# 2. Detect:
#    - Numeric columns
#    - Categorical columns
#    - Date/time columns
#    - Identifier columns

# 3. Evaluate analytical depth:
#    - high (rich numeric & categorical variation)
#    - medium (limited aggregation possible)
#    - low (mostly reference/master data)

# --------------------------------------------------
# STEP 2 — INTELLIGENT DECISION RULES
# --------------------------------------------------

# • If dataset has date/time variation → suggest trend (line chart).
# • If dataset is master/reference with no numeric measures → avoid fake trends.
# • If dataset lacks analytical depth → suggest count cards or table views only.
# • DO NOT fabricate insights.
# • DO NOT create trends if no time variation exists.
# • DO NOT rank by ID fields.
# • DO NOT hallucinate columns.

# --------------------------------------------------
# STEP 3 — SUGGESTION RULES
# --------------------------------------------------

# Generate 3–5 realistic dashboard suggestions.

# Each suggestion must:
# • Provide real business value
# • Use ONLY existing dataset column names
# • Avoid meaningless rankings
# • Avoid fabricated columns
# • Avoid combining columns into new ones

# --------------------------------------------------
# RANKING ENFORCEMENT RULES
# --------------------------------------------------

# If title contains:
# Top, Highest, Lowest, Best, Worst, Bottom

# THEN:
# • You MUST include: sortBy, order, limit
# • If title includes a number (e.g., Top 5) → limit must match that number
# • "Top" or "Highest" → order must be "desc"
# • "Lowest" or "Bottom" → order must be "asc"
# • If ranking cannot be logically supported → DO NOT generate ranking suggestion

# --------------------------------------------------
# STRUCTURE RULES (VERY STRICT)
# --------------------------------------------------

# Return ONLY valid JSON in the following structure:

# {{
#   "suggestions": [
#     {{
#       "title": "string",

#       "viewType": "card | chart | table",

#       "chartType": "bar | line | pie (required if viewType = chart)",

#       "operation": "sum | avg | count | min | max | none",

#       "xKey": "string (required for bar/line)",
#       "yKey": "string (required for bar/line)",

#       "categoryKey": "string (required for pie)",
#       "valueKey": "string (required for pie)",

#       "metric": "string (required for card)",

#       "columns": ["string"],

#       "sortBy": "string",
#       "order": "asc | desc",
#       "limit": 0
#     }}
#   ]
# }}

# --------------------------------------------------
# FIELD USAGE RULES
# --------------------------------------------------

# 1. Include ONLY fields relevant to the viewType.
# 2. Do NOT include chartType for card or table.
# 3. For bar/line:
#    - xKey and yKey required
#    - do NOT include categoryKey/valueKey
# 4. For pie:
#    - categoryKey and valueKey required
#    - do NOT include xKey/yKey
# 5. For card:
#    - metric and operation required
#    - do NOT include chartType
# 6. For table:
#    - columns required
# 7. Do NOT include fields with null values.
# 8. Do NOT invent columns.
# 9. Do NOT return explanation text.
# 10. Return strictly valid JSON only.

# Rules:
# - Return ONLY valid JSON
# - No explanation
# - No markdown
# - No extra text

# Return strictly JSON.
# """




def ollama_model_call_for_ai_suggestions(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL_INTENT,
                "prompt": prompt,
                "stream": False
            },
            timeout=800
        )
     
        print("RAW RESPONSE:", response.text)
        data = response.json()

        if "response" in data:
            cleaned = data["response"].strip()

            # Remove accidental markdown if model returns ```json
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

            return cleaned
        else:
            return "{}"

    except requests.exceptions.Timeout:
        print("Ollama request timed out.")
        return "{}"

    except requests.exceptions.ConnectionError:
        print("Unable to connect to Ollama server. Check if it is running.")
        return "{}"

    except Exception as e:
        print("Exception in ollama_model_call_for_ai_suggestions:", str(e))
        return "{}"


def convert_numpy_to_native(val):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(val, (np.integer, np.int64, np.int32)):
        return int(val)
    elif isinstance(val, (np.floating, np.float64, np.float32)):
        return float(val)
    elif isinstance(val, (np.ndarray, pd.Series)):
        return val.tolist()
    return val


# def apply_ai_suggestions(data, suggestions):
#     """
#     data: list of dicts -> the actual dataset
#     suggestions: list of dicts -> AI generated suggestions JSON
#     """
#     df = pd.DataFrame(data)
#     result = []

#     for suggestion in suggestions:
#         sug = suggestion.copy()

#         # ---------------------- RANKING ----------------------
#         if "sortBy" in sug and sug["sortBy"] in df.columns:
#             ascending = sug.get("order", "asc") == "asc"
#             df_sorted = df.sort_values(sug["sortBy"], ascending=ascending)
#         else:
#             df_sorted = df

#         # Apply limit if provided
#         if sug.get("limit"):
#             df_sorted = df_sorted.head(sug["limit"])

#         # ---------------------- CHART ----------------------
#         if sug["viewType"] == "chart":
#             if sug["chartType"] in ["bar", "line"]:
#                 x, y = sug["xKey"], sug["yKey"]
#                 if x not in df.columns or y not in df.columns:
#                     continue  # skip invalid keys
#                 sug["data"] = [
#                     {"x": convert_numpy_to_native(row[x]), "y": convert_numpy_to_native(row[y])}
#                     for _, row in df_sorted.iterrows()
#                 ]

#             elif sug["chartType"] == "pie":
#                 cat, val = sug.get("categoryKey"), sug.get("valueKey")
#                 if cat not in df.columns or val not in df.columns:
#                     continue
#                 grouped = df.groupby(cat)[val].count().reset_index(name="value")
#                 sug["data"] = [
#                     {"name": convert_numpy_to_native(row[cat]), "value": convert_numpy_to_native(row["value"])}
#                     for _, row in grouped.iterrows()
#                 ]

#         # ---------------------- CARD ----------------------
#         elif sug["viewType"] == "card":
#             metric = sug.get("metric")
#             operation = sug.get("operation", "count")
#             if metric not in df.columns and operation != "count":
#                 continue
#             if operation == "count":
#                 sug["value"] = convert_numpy_to_native(len(df))
#             elif operation == "sum":
#                 sug["value"] = convert_numpy_to_native(df[metric].sum())
#             elif operation == "avg":
#                 sug["value"] = convert_numpy_to_native(df[metric].mean())
#             elif operation == "min":
#                 sug["value"] = convert_numpy_to_native(df[metric].min())
#             elif operation == "max":
#                 sug["value"] = convert_numpy_to_native(df[metric].max())
#             else:
#                 sug["value"] = None

#         # ---------------------- TABLE ----------------------
#         elif sug["viewType"] == "table":
#             cols = [col for col in sug.get("columns", []) if col in df.columns]
#             sug["columns"] = cols
#             sug["data"] = [
#     {k: convert_numpy_to_native(v) for k, v in row.items()}
#     for row in df[cols].to_dict("records")
# ]

#         result.append(sug)

#     return {"suggestions": result}



# def apply_ai_suggestions(data, suggestions):
#     """
#     data: list of dicts -> dataset
#     suggestions: list of dicts -> AI generated suggestions
#     """

#     df = pd.DataFrame(data)
#     result = []

#     for suggestion in suggestions:
#         sug = suggestion.copy()

#         # ---------------------- SORTING + LIMIT (COMMON FOR TABLE/RANKING) ----------------------
#         df_sorted = df.copy()

#         sort_by = sug.get("sortBy")
#         order = sug.get("order", "asc").lower()
#         limit = sug.get("limit")

#         if sort_by in df.columns:
#             ascending = (order == "asc")
#             df_sorted = df_sorted.sort_values(by=sort_by, ascending=ascending)

#         if isinstance(limit, int) and limit > 0:
#             df_sorted = df_sorted.head(limit)

#         # ---------------------- CHART ----------------------
#         if sug.get("viewType") == "chart":

#             chart_type = sug.get("chartType")

#             # ----- BAR / LINE -----
#             if chart_type in ["bar", "line"]:
#                 x = sug.get("xKey")
#                 y = sug.get("yKey")

#                 if x not in df.columns or y not in df.columns:
#                     continue

#                 sug["data"] = [
#                     {
#                         "x": convert_numpy_to_native(row[x]),
#                         "y": convert_numpy_to_native(row[y])
#                     }
#                     for _, row in df_sorted.iterrows()
#                 ]
        
#             # ----- PIE -----
#             elif chart_type == "pie":
#                 cat = sug.get("categoryKey")
#                 val = sug.get("valueKey")

#                 if cat not in df.columns or val not in df.columns:
#                     continue

#                 # Group and count (since pie usually represents distribution)
#                 grouped = df.groupby(cat)[val].count().reset_index(name="value")

#                 sug["data"] = [
#                     {
#                         "name": convert_numpy_to_native(row[cat]),
#                         "value": convert_numpy_to_native(row["value"])
#                     }
#                     for _, row in grouped.iterrows()
#                 ]

#         # ---------------------- CARD ----------------------
#         elif sug.get("viewType") == "card":

#             metric = sug.get("metric")
#             operation = sug.get("operation", "count")

#             if operation == "count":
#                 sug["value"] = convert_numpy_to_native(len(df))

#             elif metric in df.columns:
#                 if operation == "sum":
#                     sug["value"] = convert_numpy_to_native(df[metric].sum())

#                 elif operation == "avg":
#                     sug["value"] = convert_numpy_to_native(df[metric].mean())

#                 elif operation == "min":
#                     sug["value"] = convert_numpy_to_native(df[metric].min())

#                 elif operation == "max":
#                     sug["value"] = convert_numpy_to_native(df[metric].max())

#                 else:
#                     continue
#             else:
#                 continue

#         # ---------------------- TABLE ----------------------
#         elif sug.get("viewType") == "table":

#             cols = [col for col in sug.get("columns", []) if col in df.columns]

#             if not cols:
#                 continue

#             sug["columns"] = cols

#             temp_df = df_sorted[cols]

#             sug["data"] = [
#                 {
#                     k: convert_numpy_to_native(v)
#                     for k, v in row.items()
#                 }
#                 for row in temp_df.to_dict("records")
#             ]

#         result.append(sug)

#     return {"suggestions": result}


def apply_ai_suggestions(data, suggestions):
    """
    data: list of dicts -> dataset
    suggestions: list of dicts -> AI generated suggestions
    """

    import pandas as pd

    df = pd.DataFrame(data)
    result = []

    for suggestion in suggestions:
        sug = suggestion.copy()

        # ---------------------- SORTING + LIMIT (COMMON FOR TABLE/RANKING) ----------------------
        df_sorted = df.copy()

        sort_by = sug.get("sortBy")
        order = sug.get("order", "asc").lower()
        limit = sug.get("limit")

        if sort_by in df.columns:
            ascending = (order == "asc")
            df_sorted = df_sorted.sort_values(by=sort_by, ascending=ascending)

        if isinstance(limit, int) and limit > 0:
            df_sorted = df_sorted.head(limit)

        # ---------------------- CHART ----------------------
        if sug.get("viewType") == "chart":

            chart_type = sug.get("chartType")

            # ----- BAR / LINE / AREA -----
            if chart_type in ["bar", "line", "area"]:

                x = sug.get("xKey")
                y = sug.get("yKey")
                operation = sug.get("operation")  # no default

                if x not in df.columns or y not in df.columns:
                    continue
                
                if operation is None:
                    title = sug.get("title", "").lower()

            if "total" in title:
                operation = "sum"
            elif "average" in title:
                operation = "avg"
            elif "count" in title:
                operation = "count"
            elif "highest" in title or "maximum" in title:
                operation = "max"
            elif "lowest" in title or "minimum" in title:
                operation = "min"

            if operation is not None:
                sug["operation"] = operation  # inject back


                # If aggregation required
                if operation is not None:

                    if operation == "sum":
                        result_df = df.groupby(x, as_index=False)[y].sum()

                    elif operation == "avg":
                        result_df = df.groupby(x, as_index=False)[y].mean()

                    elif operation == "count":
                        result_df = df.groupby(x, as_index=False)[y].count()

                    elif operation == "min":
                        result_df = df.groupby(x, as_index=False)[y].min()

                    elif operation == "max":
                        result_df = df.groupby(x, as_index=False)[y].max()

                    else:
                        continue  # invalid operation

                else:
                    # No aggregation → use sorted raw data
                    result_df = df_sorted[[x, y]].copy()

                sug["data"] = [
                    {
                        "x": convert_numpy_to_native(row[x]),
                        "y": convert_numpy_to_native(row[y])
                    }
                    for _, row in result_df.iterrows()
                ]

            # ----- PIE -----
            elif chart_type == "pie":
                cat = sug.get("categoryKey")
                val = sug.get("valueKey")

                if cat not in df.columns or val not in df.columns:
                    continue

                # Group and count (since pie usually represents distribution)
                grouped = df.groupby(cat)[val].count().reset_index(name="value")

                sug["data"] = [
                    {
                        "name": convert_numpy_to_native(row[cat]),
                        "value": convert_numpy_to_native(row["value"])
                    }
                    for _, row in grouped.iterrows()
                ]

        # ---------------------- CARD ----------------------
        elif sug.get("viewType") == "card":

            metric = sug.get("metric")
            operation = sug.get("operation", "count")

            if operation == "count":
                sug["value"] = convert_numpy_to_native(len(df))

            elif metric in df.columns:

                if operation == "sum":
                    sug["value"] = convert_numpy_to_native(df[metric].sum())

                elif operation == "avg":
                    sug["value"] = convert_numpy_to_native(df[metric].mean())

                elif operation == "min":
                    sug["value"] = convert_numpy_to_native(df[metric].min())

                elif operation == "max":
                    sug["value"] = convert_numpy_to_native(df[metric].max())

                else:
                    continue
            else:
                continue

        # ---------------------- TABLE ----------------------
        elif sug.get("viewType") == "table":

            cols = [col for col in sug.get("columns", []) if col in df.columns]

            if not cols:
                continue

            sug["columns"] = cols
            temp_df = df_sorted[cols]

            sug["data"] = [
                {
                    k: convert_numpy_to_native(v)
                    for k, v in row.items()
                }
                for row in temp_df.to_dict("records")
            ]

        result.append(sug)

    return {"suggestions": result}