"""
ai_suggestions.py
═══════════════════════════════════════════════════════════════
CONCEPT:
  User loads data → AI looks at columns + sample rows
  → Suggests 3-5 best ways to VIEW that data
  → User clicks one suggestion → renders it

FLOW:
  dbJsonData (full rows)
      ↓
  build_prompt_for_ai_suggestions()   ← you asked for this
      ↓
  Ollama → JSON with 3-5 suggestions
      ↓
  apply_ai_suggestions()              ← transforms data per suggestion
      ↓
  Frontend renders suggestion cards
      ↓
  User clicks → ChartRenderer / table / text renders it
═══════════════════════════════════════════════════════════════
"""

import json
from collections import Counter


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — Analyze columns from actual data (dynamic, no hardcoding)
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_columns(rows: list) -> dict:
    """
    Read the actual data and classify every column automatically.
    Works for ANY schema — employee, project, payroll, inventory, etc.
    """
    if not rows:
        return {"num_cols": [], "str_cols": [], "date_cols": [], "all_cols": []}

    sample     = rows[0]
    all_cols   = list(sample.keys())
    num_cols   = []
    str_cols   = []
    date_cols  = []

    # Date: match as full word or word boundary (e.g. "start_date" yes, "designation" no)
    date_hints_exact = ("date", "time", "created_at", "updated_at",
                        "start_date", "end_date", "join_date", "dob",
                        "month", "year", "period")
    date_hints_contains = ("_date", "_time", "_at", "_month", "_year")

    id_hints   = ("_id", "id", "_no", "_num", "_number", "_code",
                  "_ref", "phone", "mobile", "zip", "pin")

    for col in all_cols:
        val       = sample.get(col)
        col_lower = col.lower()

        # Date detection — exact match or ends with date suffix
        is_date = (col_lower in date_hints_exact or
                   any(col_lower.endswith(h) for h in date_hints_contains))
        if is_date:
            date_cols.append(col)

        # Numeric but looks like an ID/code — treat as categorical
        elif isinstance(val, (int, float)) and val is not None:
            is_id = (col_lower == "id" or
                     col_lower.endswith("_id") or
                     col_lower.endswith("_no") or
                     col_lower.endswith("_code") or
                     any(col_lower.endswith(h) for h in id_hints))
            if is_id:
                str_cols.append(col)   # treat as label, not metric
            else:
                num_cols.append(col)

        elif isinstance(val, str):
            str_cols.append(col)

    # Find best categorical column (2-15 unique values = good for grouping)
    cat_cols = []
    for col in str_cols:
        uv = len(set(str(r.get(col, "")) for r in rows if r.get(col)))
        if 2 <= uv <= 20:
            cat_cols.append((col, uv))
    cat_cols.sort(key=lambda x: x[1])  # sort by unique count ascending

    # Find best name/label column (high uniqueness = identifier)
    name_col = None
    for col in str_cols:
        uv = len(set(str(r.get(col, "")) for r in rows if r.get(col)))
        if uv >= len(rows) * 0.5:
            name_col = col
            break
    if not name_col and str_cols:
        name_col = str_cols[0]

    return {
        "all_cols":  all_cols,
        "num_cols":  num_cols,
        "str_cols":  str_cols,
        "date_cols": date_cols,
        "cat_cols":  [c for c, _ in cat_cols],   # categorical (good for grouping)
        "name_col":  name_col,                    # identifier column
        "total_rows": len(rows),
        "sample_vals": {
            col: list(set(str(r.get(col, "")) for r in rows[:20] if r.get(col)))[:5]
            for col in all_cols
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — BUILD PROMPT FOR AI SUGGESTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _build_valid_suggestions(info: dict, rows: list) -> list:
    """
    Python builds ALL valid suggestion configs from actual data.
    No guessing — every suggestion is proven to have data before Ollama sees it.

    Priority order:
    1. BAR  — best categorical col + numeric col (SUM)
    2. PIE  — best categorical col (COUNT) — good distribution view
    3. BAR2 — second categorical col + numeric col (AVG) if different from #1
    4. LINE/AREA — date col + numeric col (trend) OR second categorical COUNT
    5. TABLE — always valid (show all rows)
    6. CARD  — always valid (key metrics) if numeric cols exist
    """
    raw_cat   = info.get("cat_cols", [])
    num_cols  = info.get("num_cols", [])
    date_cols = info.get("date_cols", [])
    all_cols  = info.get("all_cols", [])
    valid     = []

    # ── Score categorical cols — prefer business-meaningful ones ──────────────
    # Low-value cols: raw IDs, codes, emails, phones, names (too unique)
    low_value = ("_id", "_code", "_no", "_number", "email",
                 "phone", "mobile", "name", "first_name", "last_name",
                 "bank_", "password", "token")

    def cat_score(col):
        cl = col.lower()
        # Penalize low-value columns
        if any(cl.endswith(lv) or lv in cl for lv in low_value):
            return 0
        # Prefer columns with 2-10 unique values (good for grouping)
        uv = len(set(str(r.get(col, "")) for r in rows if r.get(col)))
        if 2 <= uv <= 10:
            return 10 - uv   # fewer unique = higher score (cleaner chart)
        if uv <= 20:
            return 1
        return 0   # too many unique values — not useful for grouping

    # Sort cat_cols by score descending
    cat_cols = sorted(raw_cat, key=cat_score, reverse=True)
    cat_cols = [c for c in cat_cols if cat_score(c) > 0]  # remove zero-score

    def col_exists(col):
        return col and col in all_cols

    def has_data(rows, group_col, val_col=None, agg="count"):
        """Check if this combination actually produces data."""
        if not col_exists(group_col):
            return False
        valid_rows = [r for r in rows if r.get(group_col) not in (None, "", "?")]
        if not valid_rows:
            return False
        if agg in ("sum", "avg") and val_col:
            # Check numeric col has real values
            num_vals = [r.get(val_col) for r in valid_rows if r.get(val_col) is not None]
            return len(num_vals) > 0
        return len(valid_rows) > 0

    # ── 1. BAR — categorical × numeric (SUM) ─────────────────────────────────
    for cat in cat_cols:
        for num in num_cols:
            if has_data(rows, cat, num, "sum"):
                valid.append({
                    "chartType":   "bar",
                    "xKey":        cat,
                    "yKey":        num,
                    "aggregation": "sum",
                    "groupBy":     cat,
                    "_hint":       f"bar_sum_{cat}_{num}"
                })
                break
        if valid:
            break

    # ── 2. PIE — best categorical col (COUNT distribution) ───────────────────
    for cat in cat_cols:
        uv = len(set(str(r.get(cat,"")) for r in rows if r.get(cat)))
        if 2 <= uv <= 10 and has_data(rows, cat, agg="count"):  # 2-10 slices = good pie
            valid.append({
                "chartType":   "pie",
                "xKey":        cat,
                "yKey":        "count",
                "aggregation": "count",
                "groupBy":     cat,
                "_hint":       f"pie_count_{cat}"
            })
            break

    # ── 3. BAR (AVG) — different cat col + numeric ────────────────────────────
    used_cats = {s["groupBy"] for s in valid}
    for cat in cat_cols:
        if cat in used_cats:
            continue
        for num in num_cols:
            if has_data(rows, cat, num, "avg"):
                valid.append({
                    "chartType":   "bar",
                    "xKey":        cat,
                    "yKey":        num,
                    "aggregation": "avg",
                    "groupBy":     cat,
                    "_hint":       f"bar_avg_{cat}_{num}"
                })
                break
        if len(valid) >= 3:
            break

    # ── 4. LINE — date trend OR second categorical count ─────────────────────
    if date_cols and num_cols:
        date_col = date_cols[0]
        num_col  = num_cols[0]
        if has_data(rows, date_col, num_col, "sum"):
            valid.append({
                "chartType":   "line",
                "xKey":        date_col,
                "yKey":        num_col,
                "aggregation": "sum",
                "groupBy":     date_col,
                "_hint":       f"line_trend_{date_col}_{num_col}"
            })
    else:
        # No date — use area chart for second categorical count
        used_cats = {s["groupBy"] for s in valid}
        for cat in cat_cols:
            if cat in used_cats:
                continue
            if has_data(rows, cat, agg="count"):
                valid.append({
                    "chartType":   "area",
                    "xKey":        cat,
                    "yKey":        "count",
                    "aggregation": "count",
                    "groupBy":     cat,
                    "_hint":       f"area_count_{cat}"
                })
                break

    # ── 5. TABLE — always valid ───────────────────────────────────────────────
    valid.append({
        "chartType":   "table",
        "xKey":        None,
        "yKey":        None,
        "aggregation": "none",
        "groupBy":     None,
        "_hint":       "table_all"
    })

    # ── 6. CARD — key metrics, only if numeric cols exist ────────────────────
    if num_cols:
        valid.append({
            "chartType":   "card",
            "xKey":        None,
            "yKey":        num_cols[0],
            "aggregation": "none",
            "groupBy":     None,
            "_hint":       f"card_metrics"
        })

    return valid[:5]  # max 5 suggestions


def build_prompt_for_ai_suggestions(sample_data: list) -> str:
    """
    Two-step approach:
    1. Python pre-validates which suggestions are possible + have real data
    2. Ollama only writes titles and descriptions for those pre-validated configs

    This prevents Ollama from inventing invalid column combinations.
    """
    if not sample_data:
        return ""

    rows   = sample_data if isinstance(sample_data, list) else [sample_data]
    info   = _analyze_columns(rows)

    # Step 1: Python builds valid suggestion configs
    valid_suggestions = _build_valid_suggestions(info, rows)

    if not valid_suggestions:
        return ""

    # Step 2: Tell Ollama EXACTLY what configs to name — no column picking
    configs_block = ""
    for i, s in enumerate(valid_suggestions, 1):
        chart = s["chartType"].upper()
        x     = s["xKey"] or "N/A"
        y     = s["yKey"] or "N/A"
        agg   = s["aggregation"]
        grp   = s["groupBy"] or "N/A"
        configs_block += (
            f"  Config {i}: chartType={chart}, xKey={x}, yKey={y}, "
            f"aggregation={agg}, groupBy={grp}\n"
        )

    # Build column info for context
    col_lines = []
    for col in info["all_cols"]:
        ctype = ("NUMERIC"  if col in info["num_cols"]  else
                 "DATE"     if col in info["date_cols"] else
                 "CATEGORY" if col in info["cat_cols"]  else "ID/TEXT")
        vals = info["sample_vals"].get(col, [])[:2]
        col_lines.append(f"  {col} ({ctype}): e.g. {vals}")
    col_block  = "\n".join(col_lines)
    sample_row = json.dumps(rows[0], default=str)

    prompt = (
        "You are a data analyst writing labels for pre-built chart configs.\n"
        "I already decided WHICH charts to show.\n"
        "Your ONLY job: write a short title and one-sentence description for each.\n\n"
        "DATA CONTEXT:\n"
        f"Columns:\n{col_block}\n\n"
        f"Sample row: {sample_row}\n\n"
        "CHART CONFIGS TO NAME (copy values exactly — do not change them):\n"
        f"{configs_block}\n"
        "STRICT RULES:\n"
        "1. Return EXACTLY the same number of suggestions as configs above.\n"
        "2. Copy chartType/xKey/yKey/aggregation/groupBy EXACTLY as given above.\n"
        "3. Only add title (3-5 words) and description (1 sentence).\n"
        "4. title must describe what the chart shows e.g. Salary by Location.\n"
        "5. description must explain the business insight in one sentence.\n"
        "6. Return ONLY valid JSON. No markdown. No backticks. No extra text.\n\n"
        "RETURN FORMAT:\n"
        "{\n"
        '  "suggestions": [\n'
        '    {"id": 1, "title": "...", "description": "...", '
        '"chartType": "bar", "xKey": "col", "yKey": "col", '
        '"aggregation": "sum", "groupBy": "col"},\n'
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Output ONLY the JSON. Nothing else."
    )

    return prompt


# APPLY — Transform raw data per suggestion (Python, no Ollama needed)
# ─────────────────────────────────────────────────────────────────────────────

def apply_ai_suggestions(full_data: list, ollama_suggestions: list) -> list:
    """
    Two-step process:
      Step 1 — Python builds valid configs from actual data (_build_valid_suggestions)
      Step 2 — Match Ollama titles/descriptions to those configs by index

    Ollama's xKey/yKey/groupBy/aggregation are completely IGNORED.
    Only title and description are taken from Ollama.
    This guarantees every suggestion produces real, correct data.
    """
    if not full_data:
        return []

    rows = full_data if isinstance(full_data, list) else [full_data]
    info = _analyze_columns(rows)

    # Step 1 — Python builds proven-valid configs
    valid_configs = _build_valid_suggestions(info, rows)
    if not valid_configs:
        return []

    # Step 2 — Match Ollama labels to configs (by position)
    # Build lookup: index → {title, description} from Ollama
    ollama_labels = {}
    for i, s in enumerate(ollama_suggestions or []):
        ollama_labels[i] = {
            "title":       s.get("title", ""),
            "description": s.get("description", ""),
        }

    result = []
    for i, cfg in enumerate(valid_configs):
        chart_type  = cfg["chartType"]
        x_key       = cfg["xKey"]
        y_key       = cfg["yKey"]
        aggregation = cfg["aggregation"]
        group_by    = cfg["groupBy"]

        # Get Ollama-provided label (or auto-generate if missing)
        label = ollama_labels.get(i, {})
        title = label.get("title", "").strip()
        desc  = label.get("description", "").strip()

        # Auto-generate title if Ollama didn't provide one
        if not title:
            if chart_type == "table":
                title = "All Records"
            elif chart_type == "card":
                title = "Key Metrics"
            elif group_by and y_key:
                gname = group_by.replace("_", " ").title()
                yname = y_key.replace("_", " ").title()
                aname = {"sum": "Total", "avg": "Average", "count": "Count"}.get(aggregation, "")
                title = f"{aname} {yname} by {gname}".strip()
            else:
                title = f"{chart_type.title()} Chart"

        if not desc:
            if chart_type == "table":
                desc = "View and search all records in this dataset."
            elif chart_type == "card":
                desc = "Key statistical metrics for this dataset."
            elif group_by:
                gname = group_by.replace("_", " ")
                desc  = f"Distribution of data grouped by {gname}."

        try:
            data = _transform(rows, chart_type, x_key, y_key, aggregation, group_by, info)
        except Exception as e:
            print(f"[apply_ai_suggestions] Error on config {i}: {e}")
            data = []

        if not data:
            print(f"  [Config {i+1}] SKIPPED — no data")
            continue

        # For TABLE — only include meaningful columns (exclude sensitive/ID cols)
        if chart_type == "table":
            data = _clean_table_columns(data)

        print(f"  [Config {i+1}] OK {chart_type.upper()} | x={x_key} y={y_key} grp={group_by} agg={aggregation} → {len(data)} rows | title={title}")

        result.append({
            "id":          i + 1,
            "title":       title,
            "description": desc,
            "chartType":   chart_type,
            "xKey":        x_key,
            "yKey":        y_key,
            "aggregation": aggregation,
            "groupBy":     group_by,
            "data":        data,
            "rowCount":    len(data),
        })

    return result


def _clean_table_columns(rows: list) -> list:
    """
    For table view — remove sensitive, useless, and technical columns.
    Keep only human-readable business columns.
    """
    if not rows:
        return rows

    # Columns to always exclude from table view
    exclude_keywords = (
        "password", "token", "secret", "hash", "salt",
        "bank_account", "account_number", "bank_no",
        "phone", "mobile", "email", "fax",
        "description",                    # internal DB description
        "bank_account_number",
    )

    # Also exclude raw ID columns (numeric foreign keys like department_id)
    id_keywords = ("_id",)

    all_keys   = list(rows[0].keys()) if rows else []
    keep_keys  = []

    for k in all_keys:
        kl = k.lower()
        # Skip sensitive
        if any(ex in kl for ex in exclude_keywords):
            continue
        # Skip raw FK id columns (e.g. department_id) — keep primary "id" and codes
        if kl.endswith("_id") and kl != "id":
            continue
        keep_keys.append(k)

    if not keep_keys:
        return rows   # safety — if everything excluded, return all

    return [{k: r.get(k) for k in keep_keys} for r in rows]


def _transform(rows, chart_type, x_key, y_key, aggregation, group_by, info):
    """
    Transform raw rows into chart-ready data based on aggregation type.
    Handles: count, sum, avg, none (raw rows), table, text, card.
    """

    # TABLE — return raw rows as-is
    if chart_type == "table":
        return rows

    # TEXT / CARD — return key statistics
    if chart_type in ("text", "card"):
        return _compute_stats(rows, info)

    # No group_by — return raw rows mapped to x/y
    if not group_by:
        if x_key and y_key:
            return [
                {x_key: r.get(x_key, ""), y_key: r.get(y_key, 0)}
                for r in rows if r.get(x_key) is not None
            ]
        return rows

    # COUNT — count occurrences of each group_by value
    if aggregation == "count":
        # Only count rows that actually HAVE a value in group_by column
        valid_rows = [r for r in rows if r.get(group_by) not in (None, "", "?")]
        if not valid_rows:
            return []
        counts = Counter(str(r.get(group_by)) for r in valid_rows)
        vk = "count"

        # Pie format: [{name, value}]
        if chart_type == "pie":
            return [{"name": k, "value": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]

        # Bar/line/area format: [{group_by: k, count: v}]
        return [
            {group_by: k, vk: v}
            for k, v in sorted(counts.items(), key=lambda x: -x[1])
        ]

    # SUM — sum numeric column per group
    if aggregation == "sum" and y_key:
        totals = {}
        for r in rows:
            k = r.get(group_by)
            if k is None or k == "":
                continue   # skip rows with missing group value
            k = str(k)
            v = r.get(y_key, 0) or 0
            totals[k] = totals.get(k, 0) + (float(v) if v else 0)
        if not totals:
            return []

        vk = f"total_{y_key}"
        if chart_type == "pie":
            return [{"name": k, "value": round(v, 2)} for k, v in sorted(totals.items(), key=lambda x: -x[1])]
        return [
            {group_by: k, vk: round(v, 2)}
            for k, v in sorted(totals.items(), key=lambda x: -x[1])
        ]

    # AVG — average numeric column per group
    if aggregation == "avg" and y_key:
        sums, cnts = {}, {}
        for r in rows:
            k = r.get(group_by)
            if k is None or k == "":
                continue   # skip rows with missing group value
            k = str(k)
            v = r.get(y_key, 0) or 0
            sums[k] = sums.get(k, 0) + (float(v) if v else 0)
            cnts[k] = cnts.get(k, 0) + 1
        if not sums:
            return []

        vk = f"avg_{y_key}"
        if chart_type == "pie":
            return [{"name": k, "value": round(sums[k]/cnts[k], 2)} for k in sums]
        return [
            {group_by: k, vk: round(sums[k]/cnts[k], 2)}
            for k in sorted(sums, key=lambda x: -sums[x])
        ]

    # FALLBACK — raw rows
    return rows


def _compute_stats(rows, info) -> list:
    """Build key metric cards from the data — for text and card views."""
    stats = [{"metric": "Total Records", "value": len(rows)}]

    for col in info.get("num_cols", [])[:4]:
        vals = [r.get(col) for r in rows if r.get(col) is not None]
        if vals:
            col_label = col.replace("_", " ").title()
            stats += [
                {"metric": f"Total {col_label}",   "value": round(sum(vals), 2)},
                {"metric": f"Average {col_label}",  "value": round(sum(vals)/len(vals), 2)},
                {"metric": f"Max {col_label}",      "value": round(max(vals), 2)},
                {"metric": f"Min {col_label}",      "value": round(min(vals), 2)},
            ]

    for col in info.get("cat_cols", [])[:2]:
        counts  = Counter(str(r.get(col, "")) for r in rows if r.get(col))
        top     = counts.most_common(1)
        col_label = col.replace("_", " ").title()
        if top:
            stats.append({"metric": f"Most Common {col_label}", "value": top[0][0]})

    return stats


import requests
from app.config import OLLAMA_URL, OLLAMA_MODEL,OLLAMA_MODEL_INTENT
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

