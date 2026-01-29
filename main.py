from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

app = Flask(__name__)
CORS(app)

# ------------------ FIREBASE INIT ------------------
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ------------------ HOME TEST ROUTE ------------------
@app.route("/")
def home():
    return "Backend MVP is running!"

# ------------------ REGISTER USER ------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    try:
        user = auth.create_user(
            email=data["email"],
            password=data["password"]
        )
        db.collection("users").document(user.uid).set({
            "email": data["email"],
            "role": data["role"]  # student / admin / president
        })
        return jsonify({"message": "User registered successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ------------------ ADD SOCIETY ------------------
@app.route("/add_society", methods=["POST"])
def add_society():
    data = request.json
    db.collection("societies").add({
        "name": data["name"],
        "description": data["description"]
    })
    return jsonify({"message": "Society added successfully"})

# ------------------ LIST SOCIETIES ------------------
@app.route("/societies", methods=["GET"])
def societies():
    result = []
    for doc in db.collection("societies").stream():
        d = doc.to_dict() or {}
        d["id"] = doc.id
        result.append(d)
    return jsonify(result)

# ------------------ ADD EVENT ------------------
@app.route("/add_event", methods=["POST"])
def add_event():
    data = request.json
    db.collection("events").add({
        "title": data["title"],
        "society": data["society"],
        "date": data["date"]
    })
    return jsonify({"message": "Event added successfully"})

# ------------------ LIST EVENTS ------------------
@app.route("/events", methods=["GET"])
def events():
    result = []
    for doc in db.collection("events").stream():
        d = doc.to_dict() or {}
        d["id"] = doc.id
        result.append(d)
    return jsonify(result)

# ------------------ FOLLOW SOCIETY ------------------
@app.route("/follow", methods=["POST"])
def follow():
    data = request.json
    db.collection("follows").add({
        "user_id": data["user_id"],
        "society": data["society"]
    })
    return jsonify({"message": "Followed society successfully"})

# ------------------ RUN APP ----------------- 

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))  #
    app.run(host="0.0.0.0", port=port)