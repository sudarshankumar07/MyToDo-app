from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

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
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
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


# ---------------- AUTH ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    hashed = generate_password_hash(password)

    db = get_db_connection()
    cur = db.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
            (name, email, hashed)
        )
        db.commit()
        return jsonify({"success": True})
    except psycopg2.IntegrityError:
        db.rollback()
        return jsonify({"error": "Email exists"}), 409
    finally:
        cur.close()
        db.close()


@app.route("/user-login", methods=["POST"])
def user_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    db = get_db_connection()
    cur = db.cursor()
    cur.execute(
        "SELECT id,password FROM users WHERE email=%s",
        (email,)
    )
    user = cur.fetchone()
    cur.close()
    db.close()

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = user["id"]
    return jsonify({"success": True, "redirect": "todo"})


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
        "SELECT name,email FROM users WHERE id=%s",
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

    data = request.get_json()
    title = data.get("title")
    task = data.get("task")
    description = data.get("description", "")

    if not title or not task:
        return jsonify({"error": "Missing fields"}), 400

    db = get_db_connection()
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO todo (user_id,title,task,description)
        VALUES (%s,%s,%s,%s)
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
        SELECT id,title,task,description,created_at
        FROM todo
        WHERE user_id=%s
        ORDER BY created_at DESC
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

    data = request.get_json()
    task_id = data.get("task_id")

    db = get_db_connection()
    cur = db.cursor()
    cur.execute(
        "DELETE FROM todo WHERE id=%s AND user_id=%s",
        (task_id, session["user_id"])
    )
    db.commit()
    ok = cur.rowcount == 1
    cur.close()
    db.close()

    return jsonify({"success": ok})


# ---------------- UPDATE TASK ----------------
@app.route("/update-task/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    fields = []
    values = []

    if "title" in data:
        fields.append("title=%s")
        values.append(data["title"])
    if "task" in data:
        fields.append("task=%s")
        values.append(data["task"])
    if "description" in data:
        fields.append("description=%s")
        values.append(data["description"])

    if not fields:
        return jsonify({"error": "Nothing to update"}), 400

    values.extend([task_id, session["user_id"]])

    db = get_db_connection()
    cur = db.cursor()
    cur.execute(
        "UPDATE todo SET " + ", ".join(fields) + " WHERE id=%s AND user_id=%s",
        tuple(values)
    )
    db.commit()
    updated = cur.rowcount
    cur.close()
    db.close()

    if updated == 0:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"success": True})


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)






