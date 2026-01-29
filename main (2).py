from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore, auth
import os

app = Flask(__name__, static_folder="frontend/dist", static_url_path="")
CORS(app)

# ------------------ FIREBASE INIT ------------------
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ------------------ REGISTER USER ------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    try:
        print(f"Registering user: {data}")
        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Missing email or password"}), 400
            
        email = data["email"].strip().lower()
        
            
        # Check if user already exists in Firestore to provide better error
        existing_user = list(db.collection("users").where("email", "==", email).limit(1).get())
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 400

        # Create user in Firestore directly for this MVP
        import uuid
        uid = str(uuid.uuid4())
        
        user_data = {
            "email": email,
            "password": data["password"], # In production, hash this!
            "role": data.get("role", "student")
        }
        
        db.collection("users").document(uid).set(user_data)
        
        print(f"Created user: {email} with UID: {uid}") # Log for debugging
        
        return jsonify({
            "message": "User registered successfully",
            "uid": uid,
            "email": email,
            "role": user_data["role"]
        })
    except Exception as e:
        print(f"Registration Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

# ------------------ LOGIN USER ------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    try:
        print(f"Login attempt: {data}")
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        email = data.get("email", "").strip().lower()
        if not email.endswith("@college.edu"):
            return jsonify({"error": "Only @college.edu emails are allowed"}), 400
            
        password = data.get("password", "")
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Check if user exists in Firestore
        print(f"Querying for email: '{email}'")
        users_query = db.collection("users").where("email", "==", email).get()
        users_ref = list(users_query)
        print(f"Query results count: {len(users_ref)}")
        
        user_doc = None
        uid = None

        if not users_ref:
            # Try searching all users and checking manually in case of weird whitespace/char issues
            print("Fallback: Searching all users...")
            all_users = db.collection("users").stream()
            for doc in all_users:
                d = doc.to_dict()
                if d.get("email", "").strip().lower() == email:
                    print(f"Fallback found user: {d}")
                    user_doc = d
                    uid = doc.id
                    break
            else:
                print(f"User truly not found in DB: {email}")
                return jsonify({"error": "User not found"}), 404
        else:
            user_doc = users_ref[0].to_dict()
            uid = users_ref[0].id
            print(f"Found user in DB: {user_doc}")
        
        if not user_doc:
             print(f"Error: user_doc is still None for {email}")
             return jsonify({"error": "User data corrupted or not found"}), 500
        
        # Verify password (plain text for MVP, hash in production)
        if str(user_doc.get("password")) != str(password):
            print(f"Password mismatch for {email}")
            return jsonify({"error": "Invalid password"}), 401
            
        return jsonify({
            "email": user_doc["email"],
            "role": user_doc.get("role", "student"),
            "uid": uid
        })
    except Exception as e:
        print(f"Login Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 400

# ------------------ SOCIETY REGISTRATION ------------------
@app.route("/society_register", methods=["POST"])
def society_register():
    data = request.json
    try:
        # data should include: user_id, society_id, answers/form_data
        db.collection("society_registrations").add({
            "user_id": data.get("user_id"),
            "society_id": data.get("society_id"),
            "timestamp": firestore.firestore.SERVER_TIMESTAMP,
            "form_data": data.get("form_data", {})
        })
        return jsonify({"message": "Registration submitted successfully"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 400

# ------------------ LIST FOLLOWS ------------------
@app.route("/follows", methods=["GET"])
def list_follows():
    result = []
    for doc in db.collection("follows").stream():
        d = doc.to_dict() or {}
        d["id"] = doc.id
        result.append(d)
    return jsonify(result)

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

# ------------------ RUN APP ------------------

@app.route("/")
def serve_frontend():
    static_folder = app.static_folder
    if static_folder is None:
        return "Static folder not found", 500
    return send_from_directory(static_folder, "index.html")

@app.route("/<path:path>")
def serve_static_files(path):
    static_folder = app.static_folder
    if static_folder is None:
        return "Static folder not found", 500
    return send_from_directory(static_folder, path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
