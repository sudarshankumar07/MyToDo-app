from flask import Flask, render_template, session, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True
)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")


# ---------------- DATABASE ----------------
def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def init_db():
    db = get_db_connection()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS todo (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            task TEXT NOT NULL,
            description TEXT
        )
    """)

    db.commit()
    cur.close()
    db.close()


init_db()

# ---------------- PAGES ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login_page")
    return render_template("mytodo.html")


@app.route("/login_page")
def login_page():
    return render_template("login.html")


@app.route("/register_page")
def register_page():
    return render_template("register.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400

    hashed = generate_password_hash(password)

    db = get_db_connection()
    cur = db.cursor()

    try:
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed)
        )
        db.commit()
        return jsonify({"success": True})
    except psycopg2.IntegrityError:
        db.rollback()
        return jsonify({"error": "Email already exists"}), 409
    finally:
        cur.close()
        db.close()


# ---------------- LOGIN ----------------
@app.route("/user-login", methods=["POST"])
def user_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db_connection()
    cur = db.cursor()

    cur.execute(
        "SELECT id, password FROM users WHERE email = %s",
        (email,)
    )
    user = cur.fetchone()

    cur.close()
    db.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Wrong password"}), 401

    session["user_id"] = user["id"]
    return jsonify({"success": True})


# ---------------- LOGOUT ----------------
@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# ---------------- PROFILE ----------------
@app.route("/api/profile")
def profile():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cur = db.cursor()

    cur.execute(
        "SELECT name, email FROM users WHERE id = %s",
        (session["user_id"],)
    )
    user = cur.fetchone()

    cur.close()
    db.close()

    return jsonify(user)


# ---------------- ADD TASK ----------------
@app.route("/api/add_task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    title = data.get("title")
    task = data.get("task")
    description = data.get("description", "")

    if not title or not task:
        return jsonify({"error": "Title and task required"}), 400

    db = get_db_connection()
    cur = db.cursor()

    cur.execute(
        """
        INSERT INTO todo (user_id, title, task, description)
        VALUES (%s, %s, %s, %s)
        """,
        (session["user_id"], title, task, description)
    )

    db.commit()
    cur.close()
    db.close()

    return jsonify({"success": True})


# ---------------- SHOW TASKS ----------------
@app.route("/api/show_task")
def show_task():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cur = db.cursor()

    cur.execute(
        """
        SELECT id, title, task, description
        FROM todo
        WHERE user_id = %s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    tasks = cur.fetchall()

    cur.close()
    db.close()

    return jsonify({"tasks": tasks})


# ---------------- DELETE TASK ----------------
@app.route("/delete-task", methods=["POST"])
def delete_task():
    if "user_id" not in session:
        return jsonify({"success": False}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False}), 400

    task_id = data_
