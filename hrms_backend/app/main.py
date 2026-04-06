from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

from urllib3 import request
from app.query_generator import generate_sql
from app.schema_generator import execute_sql_get_db_data_by_schemaName_query,parse_schema_text,get_user_schema_names
# from app.react_code_generator import generate_react_visualization
# from app.react_code_generator_agent import generate_react_visualization
# from app.visualization_servie  import generate_react_visualization
# from app.visualization_service_with_cache  import generate_react_visualization
# from app.visualization_agent import generate_react_visualization
from app.viz_agent import generate_react_visualization, generate_visualization_as_json
from app.model import LoginRequest, SignupRequest, Metric, Module, Assign
from app.security import hash_password, verify_password, create_token
from app.db import get_connection
from fastapi import HTTPException
from app.api import count_all_employees, employees_by_department, fetch_all_departments, get_all_employees, employee_by_marital_status, employees_by_salary, attendance_rate_today, get_single_value, payroll_processed_rate,count_of_all_departments

import smtplib
from email.mime.text import MIMEText
import random

import time
import os
import redis
import json


# from app.react_code_generator_agent import generate_react_visualization
import json
# from app.ai_suggestions import build_prompt_for_ai_suggestions,ollama_model_call_for_ai_suggestions,apply_ai_suggestions
from app.ai_suggestions_update import build_prompt_for_ai_suggestions, apply_ai_suggestions,ollama_model_call_for_ai_suggestions
from app.redis_client import r

app = FastAPI()


from app.dashboard_chat import router as chat_router
app.include_router(chat_router)

# ✅ ADD CORS HERE (right after app creation)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Only for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "dajinkya1099@gmail.com"
EMAIL_PASSWORD = "vpst ighl vqjv qdil"


def send_email_otp(email, otp):

    message = MIMEText(f"Your verification OTP is: {otp}\nThis OTP will expire in 1 minute.")

    message["Subject"] = "OTP Verification"
    message["From"] = EMAIL_SENDER
    message["To"] = email

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()

    server.login(EMAIL_SENDER, EMAIL_PASSWORD)

    server.sendmail(EMAIL_SENDER, email, message.as_string())

    server.quit()

otp_store = {}
OTP_EXPIRY = 60  # 1 minute

@app.get("/")
def home():
    return {"message": "HRMS AI SQL Engine Running on 8282"}


@app.get("/schemas")
def schemas():
    cache_key = "all_schemas"

    # Try reading from Redis cache
    if r:
        try:
            cached_data = r.get(cache_key)
            if cached_data:
                print("Returning all_schemas from cache")
                return {
                    "schemas": json.loads(cached_data),
                    "source": "cache"
                }
        except Exception:
            print("Redis not available")

    # Fetch from database
    print("Fetching all_schemas from DB")
    schemaName = get_user_schema_names()

    # Store in Redis cache
    if r:
        try:
            r.set(cache_key, json.dumps(schemaName), ex=300)
        except Exception:
            pass

    return {
        "schemas": schemaName
    }

@app.get("/get-schema-by-schemaName")
def get_schema(schemaName : str):
    print("method for get schema for given schema name")

    cache_key = f"schema:{schemaName}"

    # Try to get from Redis
    if r:
        try:
            cached_schema = r.get(cache_key)
            if cached_schema:
                print("Returning schema from cache")
                return json.loads(cached_schema)
        except Exception as e:
            print("Redis read error:", e)

    # If not cached → compute
    print("Returning schema from db")
    schema = parse_schema_text(schemaName)
    print("schema ", schema)

    # Store in Redis (10 minutes = 600 sec)
    if r:
        try:
            r.set(cache_key, json.dumps(schema), ex=600)
        except Exception as e:
            print("Redis write error:", e)

    return schema

class QueryRequest(BaseModel):  
    schemaName: str
    query: str
    textQue: str
    dbJsonData: Any


@app.post("/get-db-level-data-by-schemaName-and-query")
def get_db_data_by_schemaName_and_query(request: QueryRequest):

    print("method for get db data for given schema name and query")
    if not request.query.strip().lower().startswith("select"):
        return {"error": "Only SELECT queries allowed"}

    dbData = execute_sql_get_db_data_by_schemaName_query(
        request.schemaName,
        request.query
    )
    print("dbData ",dbData)
    return dbData

@app.post("/get-db-level-data-by-textQue")
def get_db_data_by_textQue(request: QueryRequest):
    print("method for get db data for given textQue")
    sql = generate_sql(request)
    print("sql " , sql)

    dbData = execute_sql_get_db_data_by_schemaName_query(
        request.schemaName,
        sql
    )
    print("dbData ",dbData)
    return {
        "sql": sql,
        "data": dbData
    }

@app.post("/get-react-code-using-ai")
def get_react_code_using_AI(request: QueryRequest):
    print("method for get db data for given textQue")
    start = time.perf_counter()
    print("get_react_code_using_AI method start Time:",  start)

    react_code = generate_react_visualization(request)
    print("react_code " , react_code)

    # dbData = execute_sql_get_db_data_by_schemaName_query(
    #     request.schemaName,
    #     sql
    # )
    print("dbData ",react_code)
    end = time.perf_counter()
    print("get_react_code_using_AI method end Time:",  end)
    print("get_react_code_using_AI method Planner Time:", end - start)
    return react_code


@app.post("/get-ai-suggestions")
def get_ai_suggestions(request: QueryRequest):
    print("Generating AI Suggestions...")
    print("sample data ",request.dbJsonData)
    # Limit data sent to AI (VERY IMPORTANT)
    sample_data = request.dbJsonData[:10] if isinstance(request.dbJsonData, list) else request.dbJsonData

    prompt = build_prompt_for_ai_suggestions(sample_data)

    ai_response = ollama_model_call_for_ai_suggestions(prompt)
    print("ai_response ",ai_response)
    try:
        # ------------------- SANITIZE -------------------
        # Remove extra whitespace/newlines
        ai_response_clean = ai_response.strip()

        # Optional: Remove markdown code blocks if AI returns ```json ... ```
        if ai_response_clean.startswith("```"):
            ai_response_clean = "\n".join(ai_response_clean.splitlines()[1:-1]).strip()

        # Parse JSON
        parsed = json.loads(ai_response_clean)
        ai_suggestions = parsed.get("suggestions", [])

        # Apply AI suggestions to your full dataset
        final_suggestions = apply_ai_suggestions(request.dbJsonData, ai_suggestions)
        print("Final suggestions:", final_suggestions)

        return final_suggestions

    except json.JSONDecodeError as e:
        print("JSON Parse Error:", e)
        print("AI response was invalid JSON:", ai_response)
        return {"suggestions": []}


@app.post("/get-react-code-as-json")
def get_react_code_as_json(request: QueryRequest):
    return generate_visualization_as_json(request)       

    
    
def get_expensive_dashboard_data():
    time.sleep(2)
    return {"users": 150, "projects": 10}

@app.get("/dashboard")
def dashboard():
    cache_key = "dashboard_data"
    
    cached = r.get(cache_key)
    if cached:
        return {"data": cached, "source": "cache"}

    data = get_expensive_dashboard_data()
    r.set(cache_key, str(data), ex=300)
    
    return {"data": data, "source": "computed"}

# @app.post("/signup")
# def signup(req: SignupRequest):

#     conn = get_connection()
#     cur = conn.cursor()

#     # check username
#     cur.execute("SELECT id FROM hrms.users WHERE username=%s", (req.username,))
#     if cur.fetchone():
#         raise HTTPException(status_code=400, detail="Username exists")

#     # check email
#     cur.execute("SELECT id FROM hrms.users WHERE email=%s", (req.email,))
#     if cur.fetchone():
#         raise HTTPException(status_code=400, detail="Email exists")

#     # get role_id
#     cur.execute("SELECT id FROM hrms.roles WHERE name=%s", (req.role,))
#     role = cur.fetchone()

#     if not role:
#         raise HTTPException(status_code=400, detail="Invalid role")

#     role_id = role[0]

#     # hash password
#     hashed = hash_password(req.password)

#     # insert user
#     cur.execute("""
#         INSERT INTO hrms.users (email, username, hashed_password, role_id)
#         VALUES (%s, %s, %s, %s)
#     """, (req.email, req.username, hashed, role_id))

#     conn.commit()
#     cur.close()
#     conn.close()

#     return {"success": True}

# =========================
# SEND OTP
# =========================
@app.post("/send-otp")
def send_otp(data: dict):

    email = data.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    otp = str(random.randint(100000, 999999))

    otp_store[email] = {
        "otp": otp,
        "expires_at": time.time() + OTP_EXPIRY
    }

    send_email_otp(email, otp)

    return {"success": True, "message": "OTP sent"}

# =========================
# RESEND OTP
# =========================
@app.post("/resend-otp")
def resend_otp(data: dict):
    return send_otp(data)

# =========================
# VERIFY OTP + SIGNUP
# =========================
@app.post("/verify-otp-signup")
def verify_signup(req: SignupRequest):

    stored = otp_store.get(req.email)

    if not stored:
        raise HTTPException(status_code=400, detail="OTP not found")

    if time.time() > stored["expires_at"]:
        otp_store.pop(req.email)
        raise HTTPException(status_code=400, detail="OTP expired")

    if stored["otp"] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    conn = get_connection()
    cur = conn.cursor()

    # check existing
    cur.execute("SELECT id FROM hrms.users WHERE username=%s", (req.username,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Username exists")

    cur.execute("SELECT id FROM hrms.users WHERE email=%s", (req.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="Email exists")

    # role
    cur.execute("SELECT id FROM hrms.roles WHERE name=%s", (req.role,))
    role = cur.fetchone()

    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    role_id = role[0]

    hashed = hash_password(req.password)

    cur.execute("""
        INSERT INTO hrms.users (email, username, hashed_password, role_id)
        VALUES (%s, %s, %s, %s)
    """, (req.email, req.username, hashed, role_id))

    conn.commit()
    cur.close()
    conn.close()

    otp_store.pop(req.email)

    return {"success": True}

@app.post("/login")
def login(req: LoginRequest):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.username, u.hashed_password, r.name, u.is_active
        FROM hrms.users u
        LEFT JOIN hrms.roles r ON u.role_id = r.id
        WHERE u.username=%s
    """, (req.username,))

    user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    username, hashed_password, role, is_active = user

    if not is_active:
        raise HTTPException(status_code=403, detail="User inactive")

    # verify password
    if not verify_password(req.password, hashed_password):
        raise HTTPException(status_code=400, detail="Invalid password")

    token = create_token({"username": username, "role": role})
    
    cur.close()
    conn.close()

    return {
    "success": True,
    "token": token,   # ✅ real token
    "user": {
        "username": username,
        "role": role
    }
}
    
import json

@app.post("/save-dashboard-config")
def save_config(data: dict):

    user_id = data.get("userId")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO hrms.user_dashboard_config (user_id, dashboard_data)
        VALUES (%s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET dashboard_data = EXCLUDED.dashboard_data
    """, (user_id, json.dumps(data))) 

    conn.commit()
    cur.close()
    conn.close()

    return {"success": True}

@app.get("/get-dashboard-config/{user_id}")
def get_config(user_id: str):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT dashboard_data FROM hrms.user_dashboard_config
        WHERE user_id=%s
    """, (user_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return {"selections": []}

    return row[0]


@app.route("/api/dashboard/modules/<username>")
def get_modules(username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.id, m.module_name
        FROM hrms.dashboard_modules m
        JOIN hrms.user_module_access a ON a.module_id = m.id
        WHERE a.username = %s AND m.is_deleted = FALSE
    """, (username,))

    modules = []

    for mod in cur.fetchall():
        module_id, module_name = mod

        cur.execute("""
            SELECT key, url, type
            FROM hrms.dashboard_metrics
            WHERE module_id = %s AND is_deleted = FALSE
        """, (module_id,))

        metrics = [
            {"key": r[0], "url": r[1], "type": r[2]}
            for r in cur.fetchall()
        ]

        modules.append({
            "module": module_name,
            "metrics": metrics
        })

    return {"selections": modules}


# @app.post("/api/dashboard/modules")
# def create_module(data: Module):
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute(
#         "INSERT INTO hrms.dashboard_modules (module_name) VALUES (%s) RETURNING id",
#         (data.moduleName,)
#     )

#     module_id = cur.fetchone()[0]

#     for m in data.metrics:
#         cur.execute("""
#             INSERT INTO hrms.dashboard_metrics (module_id, key, url, type)
#             VALUES (%s, %s, %s, %s)
#         """, (module_id, m.key, m.url, m.type))

#     conn.commit()
#     return {"message": "Created"}


@app.post("/api/dashboard/modules")
def create_module(data: Module):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO hrms.dashboard_modules (module_name, is_deleted) VALUES (%s, true) RETURNING id",
        (data.moduleName,)
    )

    module_id = cur.fetchone()[0]

    for m in data.metrics:
        cur.execute("""
            INSERT INTO hrms.dashboard_metrics (module_id, key, url, type)
            VALUES (%s, %s, %s, %s)
        """, (module_id, m.key, m.url, m.type))

    conn.commit()
    conn.close()

    return {"message": "Created"}

# 📥 GET ALL MODULES
# @app.get("/api/dashboard/modules")
# def get_modules():
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT id, module_name 
#         FROM hrms.dashboard_modules 
#         WHERE is_deleted = false
#     """)

#     modules = cur.fetchall()
#     result = []

#     for m in modules:
#         module_id = m[0]
#         module_name = m[1]

#         cur.execute("""
#             SELECT key, url, type
#             FROM hrms.dashboard_metrics
#             WHERE module_id = %s AND is_deleted = false
#         """, (module_id,))

#         metrics = [
#             {"key": r[0], "url": r[1], "type": r[2]}
#             for r in cur.fetchall()
#         ]

#         result.append({
#             "id": module_id,
#             "moduleName": module_name,
#             "metrics": metrics
#         })

#     conn.close()
#     return result


# @app.get("/api/dashboard/modules")
# def get_modules():
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT m.module_name, d.key, d.url, d.type
#         FROM hrms.dashboard_modules m
#         JOIN hrms.dashboard_metrics d ON m.id = d.module_id
#         WHERE m.is_deleted = false
#         ORDER BY m.module_name
#     """)

#     rows = cur.fetchall()
#     print("rows ", rows)
#     result = {}

#     for row in rows:
#         module_name = row[0]
#         metric = {
#             "key": row[1],
#             "url": row[2],
#             "type": row[3]
#         }

#         # group by module name
#         if module_name not in result:
#             result[module_name] = []

#         result[module_name].append(metric)

#     conn.close()
#     return result

@app.get("/api/dashboard/modules")
def get_modules():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.id, m.module_name, d.key, d.url, d.type
        FROM hrms.dashboard_modules m
        JOIN hrms.dashboard_metrics d ON m.id = d.module_id
        WHERE m.is_deleted = false
        ORDER BY m.module_name
    """)

    rows = cur.fetchall()
    result = {}

    for row in rows:
        module_id = row[0]
        module_name = row[1]

        metric = {
            "key": row[2],
            "url": row[3],
            "type": row[4]
        }

        if module_name not in result:
            result[module_name] = {
                "id": module_id,
                "metrics": []
            }

        result[module_name]["metrics"].append(metric)

    conn.close()
    return result


# @app.route("/api/dashboard/modules/<int:id>", methods=["DELETE"])
# def delete_module(id):
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute(
#         "UPDATE hrms.dashboard_modules SET is_deleted = TRUE WHERE id = %s",
#         (id,)
#     )

#     cur.execute(
#         "UPDATE hrms.dashboard_metrics SET is_deleted = TRUE WHERE module_id = %s",
#         (id,)
#     )

#     conn.commit()
#     return {"message": "Deleted"}

# ❌ SOFT DELETE
# @app.delete("/api/dashboard/modules/{id}")
# def delete_module(id: int):
#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         UPDATE hrms.dashboard_modules
#         SET is_deleted = true
#         WHERE id = %s
#     """, (id,))

#     conn.commit()
#     conn.close()

#     return {"message": "Deleted"}

@app.delete("/api/dashboard/modules/{module_name}")
def delete_module(module_name: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE hrms.dashboard_modules
        SET is_deleted = true
        WHERE module_name = %s
    """, (module_name,))

    conn.commit()
    conn.close()

    return {"message": "Deleted"}

# @app.route("/api/dashboard/assign", methods=["POST"])
# def assign_module():
#     data = request.json

#     conn = get_connection()
#     cur = conn.cursor()

#     cur.execute("""
#         INSERT INTO hrms.user_module_access (username, module_id)
#         VALUES (%s, %s)
#     """, (data["username"], data["moduleId"]))

#     conn.commit()
#     return {"message": "Assigned"}

# 🔐 ASSIGN MODULE TO USER
@app.post("/api/dashboard/assign")
def assign_module(data: Assign):
    print("Assigning module ", data.moduleId, " to user ", data.username)
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO hrms.user_module_access (username, module_id)
        VALUES (%s, %s)
    """, (data.username, data.moduleId))

    conn.commit()
    conn.close()

    return {"message": "Assigned"}

@app.get("/api/dashboard/modules/{username}")
def get_modules_by_user(username: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.module_name, d.key, d.url, d.type
        FROM hrms.dashboard_modules m
        JOIN hrms.dashboard_metrics d ON m.id = d.module_id
        JOIN hrms.user_module_access u ON u.module_id = m.id
        WHERE u.username = %s
        AND m.is_deleted = false
        ORDER BY m.module_name
    """, (username,))

    rows = cur.fetchall()

    result = {}

    for row in rows:
        module_name = row[0]
        metric = {
            "key": row[1],
            "url": row[2],
            "type": row[3]
        }

        if module_name not in result:
            result[module_name] = []

        result[module_name].append(metric)

    conn.close()
    return result

# dashboard config related APIs

@app.get("/emp/count/all")
def get_emp_count():
    return {"value": count_all_employees()}


@app.get("/employees/by-department")
def get_emp_dept():
    return employees_by_department()


@app.get("/employees/by-employment-marital-status")
def get_marital():
    return employee_by_marital_status()


@app.get("/employees/by-employment-salary")
def get_salary():
    return employees_by_salary()


@app.get("/get/employee-list")
def get_employee_list():
    return get_all_employees()


@app.get("/attendance/rate-today")
def get_attendance():
    return {"value": attendance_rate_today()}


@app.get("/payroll/processed-rate")
def get_payroll():
    return {"value": payroll_processed_rate()}

@app.get("/department/count")
def count_all_departments():
    return {"value": count_of_all_departments()}

@app.get("/department-list")
def get_all_departments():
    return fetch_all_departments()

@app.get("/get/employee-highest-salary")
def get_highest_salary():
    return get_single_value("SELECT MAX(basic_salary) FROM hrms.employees")


@app.get("/get/employee-average-salary")
def get_average_salary():
    return get_single_value("SELECT ROUND(AVG(basic_salary), 2) FROM hrms.employees")


@app.get("/employees/by-lowest-salary")
def get_lowest_salary():
    return get_single_value("SELECT MIN(basic_salary) FROM hrms.employees")