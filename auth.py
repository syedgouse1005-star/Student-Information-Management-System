
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db

auth = Blueprint("auth", __name__)


class Admin(UserMixin):
    def __init__(self, user_id, username):
        self.id = str(user_id)
        self.username = username


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            login_user(Admin(user["id"], user["username"]))
            return redirect(url_for("home"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


def create_admin(username, password):
    db = get_db()
    password_hash = generate_password_hash(password)

    db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    db.commit()
    db.close()
