from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.query_generator import *
from app.schema_generator import *

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

# @app.get("/schema")
# def get_schema():
#     print("get_schema")
#     return parse_schema_text(get_full_schema())

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
    dbJsonData: str


@app.post("/get-db-level-data-by-schemaName-and-query")
def get_db_data(request: QueryRequest):

    print("method for get db data for given schema name and query")
    if not request.query.strip().lower().startswith("select"):
        return {"error": "Only SELECT queries allowed"}

    dbData = execute_sql_get_db_data_by_schemaName_query(
        request.schemaName,
        request.query
    )
    print("dbData ",dbData)
    return dbData

# @app.get("/get-db-level-data-by-schemaName-and-query")
# def get_db_data_by_schemaName_query(schemaName : str, query: str):
#     print("method for get db data for given schema name and query")
#     dbData=execute_sql_get_db_data_by_schemaName_query(schemaName,query);
#     print("dbData ",dbData)
#     return dbData


@app.get("/generate")
def generate(question: str):
    sql = generate_sql(question)
    print("sql " + sql)
    dbData=execute_sql(sql)
    print("dbData "+ str(dbData))
    return {"dbData": dbData}


@app.post("/execute-sql")
def execute_sql(query: str):
    conn = get_connection()
    cursor = conn.cursor()
    print("query*")
    updatedQuery =clean_sql_query_and_append_schemaName(query,'')
    print( updatedQuery)
    try:
        cursor.execute(updatedQuery)

        # If SELECT query
        if updatedQuery.strip().lower().startswith("select"):
            print("if ")
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            print("rows " + rows)
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
        print("error ,e")
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        cursor.close()
        conn.close()
