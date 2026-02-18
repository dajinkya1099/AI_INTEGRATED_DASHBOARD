import requests
from app.config import OLLAMA_URL, OLLAMA_MODEL
from app.schema_generator import *



def generate_sql(user_question):
    try:
        prompt = build_prompt(user_question)

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=200
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



print("hrms_backend")

def build_prompt(user_question):
    print("Fetching database schema...")
    schema = get_full_schema()
    print("Schema fetched successfully"+ schema)

    prompt = f"""
You are a PostgreSQL expert.

Use the following database schema with descriptions:

{schema}

Rules:
- Generate only PostgreSQL SQL
- Use proper JOINs
- Do not explain
- Return only SQL query

User Question:
{user_question}
"""

    return prompt

