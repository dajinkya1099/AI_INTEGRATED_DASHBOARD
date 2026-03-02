from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
from app.query_generator import generate_sql
from app.schema_generator import execute_sql_get_db_data_by_schemaName_query,parse_schema_text,get_user_schema_names
# from app.react_code_generator import generate_react_visualization
# from app.react_code_generator_agent import generate_react_visualization
# from app.visualization_servie  import generate_react_visualization
# from app.visualization_service_with_cache  import generate_react_visualization
# from app.visualization_agent import generate_react_visualization
from app.viz_agent import generate_react_visualization

import time



app = FastAPI()

# ✅ ADD CORS HERE (right after app creation)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Only for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "HRMS AI SQL Engine Running on 8282"}



@app.get("/schemas")
def schemas():
    print("method for get all schema name")
    schemaName=get_user_schema_names()
    print("schemaName ", schemaName)
    return {
        "schemas": schemaName
    }

@app.get("/get-schema-by-schemaName")
def get_schema(schemaName : str):
    print("method for get schema for given schema name")
    schema= parse_schema_text(schemaName)
    print("schema ",schema )
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
  