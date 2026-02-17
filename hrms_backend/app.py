from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow React to connect

@app.route("/")
def home():
    return jsonify({"message": "Backend is running!"})

@app.route("/api/data")
def get_data():
    return jsonify({
        "users": 120,
        "revenue": 45000,
        "orders": 320
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
