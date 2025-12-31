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


# ---------------- DB ----------------
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    db = get_db_connection()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(150) UNIQUE,
            password TEXT
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
    return render_template("mytodo_
