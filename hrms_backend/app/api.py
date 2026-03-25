from app.db import get_connection

def count_all_employees():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM hrms.employees")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count

def get_all_employees():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT e.id, e.employee_code, e.first_name, e.last_name, e.email, e.phone,
               e.date_of_birth, e.gender, e.marital_status, e.designation,
               e.employment_type, e.joining_date, e.probation_end_date,
               e.work_location, e.status, e.basic_salary, e.created_at,
               d.name AS department_name
        FROM hrms.employees e
        LEFT JOIN hrms.departments d ON e.department_id = d.id
        ORDER BY e.first_name
    """)

    columns = [desc[0] for desc in cur.description]
    data = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return data

def employees_by_department():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT d.name AS label, COUNT(e.id) AS value
        FROM hrms.departments d
        LEFT JOIN hrms.employees e 
            ON e.department_id = d.id AND e.status='ACTIVE'
        GROUP BY d.name
        ORDER BY value DESC
    """)

    rows = cur.fetchall()

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    cur.close()
    conn.close()

    return {"labels": labels, "values": values}

def employee_by_marital_status():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT marital_status AS label, COUNT(id) AS value
        FROM hrms.employees
        GROUP BY marital_status
    """)

    rows = cur.fetchall()

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    cur.close()
    conn.close()

    return {"labels": labels, "values": values}

def employees_by_salary():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT first_name AS label, basic_salary AS value
        FROM hrms.employees
    """)

    rows = cur.fetchall()

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    cur.close()
    conn.close()

    return {"labels": labels, "values": values}

def count_departments():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM hrms.departments")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count

def count_active_employees():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM hrms.employees WHERE status='ACTIVE'")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count


def count_present_today():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) FROM hrms.attendance
        WHERE status='PRESENT' AND date = CURRENT_DATE
    """)

    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count


def attendance_rate_today():
    total = count_active_employees()
    present = count_present_today()

    if total == 0:
        return 0.0

    return round((present * 100.0 / total), 2)

def payroll_processed_rate():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM hrms.payroll")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM hrms.payroll WHERE payment_status='PAID'")
    paid = cur.fetchone()[0]

    cur.close()
    conn.close()

    if total == 0:
        return 0.0

    return round((paid * 100.0 / total), 2)

def count_of_all_departments():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM hrms.departments")
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count

def fetch_all_departments():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT d.id, d.name AS department_name, d.description, d.created_at
        FROM hrms.departments d
        ORDER BY d.name
    """)

    columns = [desc[0] for desc in cur.description]
    data = [dict(zip(columns, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return data

def get_single_value(query):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(query)
    value = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {"value": value}

