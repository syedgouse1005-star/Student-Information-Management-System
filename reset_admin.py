
from getpass import getpass
from werkzeug.security import generate_password_hash
from database import get_db

username = input("Enter your admin username: ").strip()
password = getpass("Enter your new password: ")
confirm = getpass("Confirm your new password: ")

if not username or len(password) < 12:
    raise SystemExit("Username is required; password must be at least 12 characters.")

if password != confirm:
    raise SystemExit("Passwords do not match. Please try again.")

db = get_db()

try:
    user = db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()

    password_hash = generate_password_hash(password)

    if user:
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (password_hash, user["id"])
        )
    else:
        existing = db.execute(
            "SELECT id FROM users ORDER BY id LIMIT 1"
        ).fetchone()

        if existing:
            db.execute(
                "UPDATE users SET username = ?, password_hash = ? WHERE id = ?",
                (username, password_hash, existing["id"])
            )
        else:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )

    db.commit()
    print("Admin credentials updated successfully.")

finally:
    db.close()
