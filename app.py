from flask import Flask, render_template, session, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# ---------------- SECRET KEY ----------------
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set")

app.secret_key = SECRET_KEY


# ---------------- DATABASE ----------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")


def get_db_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def init_db():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todo (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            task TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    db.commit()
    cursor.close()
    db.close()


init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/reg_log")
    return render_template("mytodo.html")


@app.route("/reg_log")
def reg_log():
    return render_template("index.html")


# ---------------- AUTH PAGES ----------------
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
        return jsonify({"success": False, "message": "Invalid JSON"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    hashed = generate_password_hash(password)

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed)
        )
        db.commit()
        return jsonify({"success": True, "redirect": "/login_page"})
    except psycopg2.IntegrityError:
        db.rollback()
        return jsonify({"success": False, "message": "Email already exists"}), 409
    except Exception:
        db.rollback()
        return jsonify({"success": False, "message": "Internal server error"}), 500
    finally:
        cursor.close()
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
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT id, password FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not check_password_hash(user["password"], password):
            return jsonify({"error": "Wrong password"}), 401

        session["user_id"] = user["id"]
        return jsonify({"success": True, "redirect": "/todo"})
    finally:
        cursor.close()
        db.close()


# ---------------- TODO PAGE ----------------
@app.route("/todo")
def todo():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("mytodo.html")


# ---------------- PROFILE ----------------
@app.route("/api/profile")
def profile():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT name, email FROM users WHERE id = %s",
            (session["user_id"],)
        )
        return jsonify(cursor.fetchone())
    finally:
        cursor.close()
        db.close()


# ---------------- ADD TASK ----------------
@app.route("/api/add_task", methods=["POST"])
def add_task():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO todo (user_id, title, task, description)
            VALUES (%s, %s, %s, %s)
            """,
            (
                session["user_id"],
                data.get("title"),
                data.get("task"),
                data.get("description", "")
            )
        )
        db.commit()
        return jsonify({"success": True}), 201
    except Exception:
        db.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        cursor.close()
        db.close()


# ---------------- SHOW TASKS ----------------
@app.route("/api/show_task", methods=["GET"])
def show_task():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT id, title, task, description
            FROM todo
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (session["user_id"],)
        )
        return jsonify({"success": True, "tasks": cursor.fetchall()})
    finally:
        cursor.close()
        db.close()


# ---------------- LOGOUT ----------------
@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"success": True, "redirect": "/login_page"})


# ---------------- DELETE TASK ----------------
@app.route("/delete-task", methods=["POST"])
def delete_task():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False}), 400

    task_id = data.get("task_id")
    if not task_id:
        return jsonify({"success": False}), 400

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(
            "DELETE FROM todo WHERE id = %s AND user_id = %s",
            (task_id, user_id)
        )
        db.commit()
        return jsonify({"success": cursor.rowcount == 1})
    except Exception:
        db.rollback()
        return jsonify({"success": False}), 500
    finally:
        cursor.close()
        db.close()


# ---------------- UPDATE TASK ----------------
@app.route("/update-task/<int:taskId>", methods=["PATCH"])
def update_task(taskId):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    fields = []
    values = []

    if "title" in data:
        fields.append("title = %s")
        values.append(data["title"])

    if "task" in data:
        fields.append("task = %s")
        values.append(data["task"])

    if "description" in data:
        fields.append("description = %s")
        values.append(data["description"])

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    query = f"""
        UPDATE todo
        SET {', '.join(fields)}
        WHERE id = %s AND user_id = %s
    """

    values.extend([taskId, user_id])

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute(query, tuple(values))
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found"}), 404

        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()
