import re
import json
from app.db import get_connection
from app.config import OLLAMA_URL, OLLAMA_MODEL,DB_NAME


def get_user_schema_names():
    conn = get_connection()
    cur = conn.cursor()

    query = """
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema','pg_temp_1','public')
    AND schema_name NOT LIKE 'pg_toast%'
    ORDER BY schema_name;
    """

    cur.execute(query)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [row[0] for row in rows]
    
def get_full_schema(schemaName: str):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT 
            t.table_name,
            obj_description(c.oid) AS table_comment,
            col.column_name,
            col.data_type,
            col.is_nullable,
            col.column_default,
            col_description(c.oid, col.ordinal_position) AS column_comment,
            tc.constraint_type,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.tables t
        JOIN pg_class c ON c.relname = t.table_name
        JOIN information_schema.columns col 
            ON col.table_name = t.table_name 
            AND col.table_schema = t.table_schema
        LEFT JOIN information_schema.key_column_usage kcu 
            ON kcu.table_name = col.table_name 
            AND kcu.column_name = col.column_name
            AND kcu.table_schema = col.table_schema
        LEFT JOIN information_schema.table_constraints tc 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.referential_constraints rc
            ON rc.constraint_name = tc.constraint_name
            AND rc.constraint_schema = tc.table_schema
        LEFT JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = rc.unique_constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE t.table_schema = %s
          AND t.table_type = 'BASE TABLE'
        ORDER BY t.table_name, col.ordinal_position, tc.constraint_type;
    """
    cur.execute(query, (schemaName,))
    rows = cur.fetchall()

    # Group by table -> column, collecting all constraints per column
    # Structure: { table_name: { "comment": ..., "columns": { col_name: { ...col_data, "constraints": [...] } } } }
    tables_map = {}
    col_order = {}  # to preserve column order per table

    for row in rows:
        table_name      = row[0]
        table_comment   = row[1]
        column_name     = row[2]
        data_type       = row[3]
        nullable        = row[4]
        column_default  = row[5]
        column_comment  = row[6]
        constraint_type = row[7]
        foreign_table   = row[8]
        foreign_column  = row[9]

        if table_name not in tables_map:
            tables_map[table_name] = {
                "comment": table_comment,
                "columns": {}
            }
            col_order[table_name] = []

        cols = tables_map[table_name]["columns"]
        if column_name not in cols:
            cols[column_name] = {
                "name": column_name,
                "type": data_type,
                "nullable": True if nullable == "YES" else False,
                "default": column_default,
                "constraints": [],
                "description": column_comment
            }
            col_order[table_name].append(column_name)

        # Add constraint if present and not duplicate
        if constraint_type:
            constraint_entry = {"type": constraint_type}
            if constraint_type == "FOREIGN KEY" and foreign_table:
                constraint_entry["references"] = {
                    "table": foreign_table,
                    "column": foreign_column
                }
            if constraint_entry not in cols[column_name]["constraints"]:
                cols[column_name]["constraints"].append(constraint_entry)

    # Build schema_text from the deduplicated map
    schema_text = ""
    for table_name, table_data in tables_map.items():
        schema_text += f"\n\nTABLE: {table_name}\n"
        schema_text += f"Description: {table_data['comment']}\n"
        schema_text += "Columns:\n"
        for col_name in col_order[table_name]:
            col = table_data["columns"][col_name]
            constraints = col["constraints"]

            # Build constraint string
            if constraints:
                constraint_parts = []
                for con in constraints:
                    if con["type"] == "FOREIGN KEY" and "references" in con:
                        ref = con["references"]
                        constraint_parts.append(
                            f"FOREIGN KEY -> {ref['table']}.{ref['column']}"
                        )
                    else:
                        constraint_parts.append(con["type"])
                constraint_info = f" | Constraint: {', '.join(constraint_parts)}"
            else:
                constraint_info = ""

            schema_text += (
                f" - {col['name']} ({col['type']})"
                f" | Nullable: {'YES' if col['nullable'] else 'NO'}"
                f" | Default: {col['default']}"
                f"{constraint_info}"
                f" | Description: {col['description']}\n"
            )

    cur.close()
    conn.close()
    return schema_text


def parse_schema_text(schemaName: str):
    schema_text = get_full_schema(schemaName)
    tables = []
    table_blocks = re.split(r'\n(?=TABLE:)', schema_text.strip())

    for block in table_blocks:
        lines = block.strip().split("\n")
        table_data = {
            "name": "",
            "description": "",
            "columns": []
        }

        for line in lines:
            if line.startswith("TABLE:"):
                table_data["name"] = line.replace("TABLE:", "").strip()

            elif line.startswith("Description:"):
                table_data["description"] = line.replace("Description:", "").strip()

            elif line.strip().startswith("-"):
                # Pattern supports multiple constraints like "PRIMARY KEY, FOREIGN KEY -> other_table.col"
                column_pattern = (
                    r"-\s*(\w+)\s*\((.*?)\)\s*"
                    r"\|\s*Nullable:\s*(YES|NO)\s*"
                    r"\|\s*Default:\s*(.*?)\s*"
                    r"(?:\|\s*Constraint:\s*(.*?)\s*)?"
                    r"\|\s*Description:\s*(.*)"
                )
                match = re.match(column_pattern, line.strip())
                if match:
                    column_name  = match.group(1)
                    data_type    = match.group(2)
                    nullable     = True if match.group(3) == "YES" else False
                    default_val  = match.group(4)
                    raw_constraint = match.group(5)
                    description  = match.group(6)

                    # Parse constraints back into structured format
                    constraints = []
                    if raw_constraint:
                        for part in raw_constraint.split(","):
                            part = part.strip()
                            if "->" in part:
                                # e.g. "FOREIGN KEY -> departments.id"
                                fk_match = re.match(
                                    r"FOREIGN KEY\s*->\s*(\w+)\.(\w+)", part
                                )
                                if fk_match:
                                    constraints.append({
                                        "type": "FOREIGN KEY",
                                        "references": {
                                            "table": fk_match.group(1),
                                            "column": fk_match.group(2)
                                        }
                                    })
                            else:
                                constraints.append({"type": part})

                    table_data["columns"].append({
                        "name": column_name,
                        "type": data_type,
                        "nullable": nullable,
                        "default": default_val,
                        "constraints": constraints,
                        "description": description
                    })

        if table_data["name"]:
            tables.append(table_data)

    return {
        "database": DB_NAME,
        "schemaName": schemaName,
        "tables": tables
    }




def execute_sql_get_db_data_by_schemaName_query(schemaName: str ,query : str):
    conn = get_connection()
    cursor = conn.cursor()
    print("query*")
    updatedQuery =clean_sql_query_and_append_schemaName(schemaName,query)
    print( updatedQuery)
    try:
        cursor.execute(updatedQuery)

        # If SELECT query
        if updatedQuery.strip().lower().startswith("select"):
            print("if ")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            print("rows " , rows)
            result = []
            for row in rows:
                result.append(dict(zip(columns, row)))

            return {
                "status": "success",
                "rows": result
            }

        # If INSERT/UPDATE/DELETE
        else:
            print("else ")
            conn.commit()
            return {
                "status": "success",
                "message": "Query executed successfully"
            }

    except Exception as e:
        print("error ")
        print("error" ,e)
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        cursor.close()
        conn.close()

# def clean_sql_query(sql_text: str) -> str:
#     # Remove markdown code block markers
#     sql_text = sql_text.replace("```sql", "")
#     sql_text = sql_text.replace("```", "")
    
#     return sql_text.strip()

def clean_sql_query_and_append_schemaName(schema_name: str,sql_text: str) -> str:
    
    # 1️⃣ Remove markdown
    sql_text = sql_text.replace("```sql", "")
    sql_text = sql_text.replace("```", "")
    sql_text = sql_text.strip()

    words = sql_text.split()
    new_words = []

    for i in range(len(words)):
        word = words[i]

        # If previous word was FROM or JOIN
        if i > 0 and words[i-1].upper() in ["FROM", "JOIN"]:
            
            # If schema already not added
            if "." not in word:
                word = f"{schema_name}.{word}"

        new_words.append(word)

    return " ".join(new_words)



