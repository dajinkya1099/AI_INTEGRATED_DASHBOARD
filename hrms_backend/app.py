from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS (important for React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Home Route
@app.get("/")
def home():
    return {"message": "Backend is running!"}


# Dashboard Data Route
@app.get("/api/data")
def get_data():
    return {
        "users": 120,
        "revenue": 45000,
        "orders": 320
    }
