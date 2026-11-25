# app.py
# Main Flask application: routes (pages) and the admin login.

import hmac
import os
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request,
                   session, url_for)

from db import init_db, run_query

app = Flask(__name__)

# All configuration comes from environment variables (no secrets in the code).
# os.environ[...] stops the app with a clear error if a variable is missing.
app.secret_key = os.environ["SECRET_KEY"]        # signs the session cookie
ADMIN_USERNAME = os.environ["ADMIN_USERNAME"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]

# Create the tables on the first start (does nothing if they already exist).
init_db()


# ---------- Admin protection ----------

def login_required(view):
    """Decorator: only lets the request through if the admin is logged in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------- Public pages ----------

@app.route("/")
def index():
    latest = run_query(
        "SELECT * FROM announcements ORDER BY created_at DESC, id DESC LIMIT 3")
    return render_template("index.html", announcements=latest)


@app.route("/departments")
def departments():
    rows = run_query("SELECT * FROM departments ORDER BY name")
    return render_template("departments.html", departments=rows)


@app.route("/announcements")
def announcements():
    rows = run_query(
        "SELECT * FROM announcements ORDER BY created_at DESC, id DESC")
    return render_template("announcements.html", announcements=rows)


# ---------- Login / logout ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        # compare_digest compares strings in constant time (safer than ==).
        # We encode to bytes because it only accepts ASCII text otherwise.
        user_ok = hmac.compare_digest(username.encode(), ADMIN_USERNAME.encode())
        pass_ok = hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())
        if user_ok and pass_ok:
            session["is_admin"] = True
            return redirect(url_for("admin"))
        flash("Wrong username or password.")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You are logged out.")
    return redirect(url_for("index"))


# ---------- Admin: add, edit, delete announcements ----------

@app.route("/admin")
@login_required
def admin():
    rows = run_query(
        "SELECT * FROM announcements ORDER BY created_at DESC, id DESC")
    return render_template("admin.html", announcements=rows)


def read_form():
    """Read and check the title/content fields. Returns (title, content, ok)."""
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    ok = bool(title) and bool(content) and len(title) <= 200
    if not ok:
        flash("Title and content are required (title: max 200 characters).")
    return title, content, ok


@app.route("/admin/add", methods=["POST"])
@login_required
def add_announcement():
    title, content, ok = read_form()
    if ok:
        run_query("INSERT INTO announcements (title, content) VALUES (%s, %s)",
                  (title, content), fetch="none")
        flash("Announcement added.")
    return redirect(url_for("admin"))


@app.route("/admin/edit/<int:announcement_id>", methods=["GET", "POST"])
@login_required
def edit_announcement(announcement_id):
    if request.method == "POST":
        title, content, ok = read_form()
        if ok:
            run_query("UPDATE announcements SET title = %s, content = %s "
                      "WHERE id = %s",
                      (title, content, announcement_id), fetch="none")
            flash("Announcement updated.")
            return redirect(url_for("admin"))

    row = run_query("SELECT * FROM announcements WHERE id = %s",
                    (announcement_id,), fetch="one")
    if row is None:
        flash("Announcement not found.")
        return redirect(url_for("admin"))
    return render_template("edit.html", announcement=row)


@app.route("/admin/delete/<int:announcement_id>", methods=["POST"])
@login_required
def delete_announcement(announcement_id):
    run_query("DELETE FROM announcements WHERE id = %s",
              (announcement_id,), fetch="none")
    flash("Announcement deleted.")
    return redirect(url_for("admin"))


# Only used when running "python app.py" for quick local tests.
# In Docker and on Render, gunicorn starts the app instead.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
