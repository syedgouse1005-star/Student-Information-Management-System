
import os

from flask import Flask, request, redirect, url_for, render_template_string, flash
from flask_login import LoginManager, login_required, current_user

from database import get_db, init_db
from auth import auth, Admin, create_admin

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-local-secret")

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

app.register_blueprint(auth)


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    db.close()

    if user:
        return Admin(user["id"], user["username"])
    return None


@app.route("/")
@login_required
def home():
    db = get_db()

    total = db.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    departments = db.execute(
        "SELECT COUNT(DISTINCT department) FROM students"
    ).fetchone()[0]

    average = db.execute(
        "SELECT AVG(cgpa) FROM students"
    ).fetchone()[0] or 0

    search = request.args.get("q", "").strip()
    edit_id = request.args.get("edit", type=int)
    edit_student = None

    students = db.execute("""
        SELECT * FROM students
        WHERE roll LIKE ? OR name LIKE ? OR department LIKE ?
        ORDER BY id DESC
    """, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()

    if edit_id:
        edit_student = db.execute(
            "SELECT * FROM students WHERE id = ?", (edit_id,)
        ).fetchone()

        if not edit_student:
            flash("Student not found.")

    db.close()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Student Information Management System</title>

      <style>
      header .dashboard-logo {
    width: 100px !important;
    height: 100px !important;
    max-width: 100px !important;
    max-height: 100px !important;
    object-fit: contain;
}
        body {
          font-family: Arial, sans-serif;
          background: #eef3f8;
          margin: 0;
          color: #203040;
        }

        header {
          background: #1565c0;
          color: white;
          padding: 20px 5%;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
        }

        main {
          max-width: 1100px;
          margin: 25px auto;
          padding: 0 16px;
        }

        .cards {
          display: flex;
          gap: 14px;
          flex-wrap: wrap;
        }

        .card, .panel {
          background: white;
          padding: 20px;
          border-radius: 12px;
          box-shadow: 0 3px 12px #0001;
          margin-bottom: 18px;
        }

        .card {
          flex: 1;
          min-width: 150px;
        }

        .number {
          font-size: 28px;
          font-weight: bold;
          color: #1565c0;
        }

        input {
          padding: 10px;
          border: 1px solid #ccd4dd;
          border-radius: 6px;
          margin: 5px 4px 5px 0;
          max-width: 100%;
        }

        button, .btn {
          background: #1565c0;
          color: white;
          border: 0;
          border-radius: 6px;
          padding: 10px 14px;
          cursor: pointer;
          text-decoration: none;
          display: inline-block;
        }

        .danger {
          background: #c62828;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          background: white;
        }

        th, td {
          padding: 10px;
          border-bottom: 1px solid #ddd;
          text-align: left;
        }

        th {
          background: #e7effa;
        }

        .table-wrap {
          overflow-x: auto;
        }

        @media(max-width: 600px) {
          header {
            gap: 10px;
          }

          th, td {
            padding: 7px;
            font-size: 13px;
          }
        }
      </style>
    </head>

    <body>
      
<header>
    <div class="brand">
      <img src="{{ url_for('static', filename='logo.png') }}"
           alt="Student Management Logo"
           class="dashboard-logo">

      <div>
        <h2>Student Information Management System</h2>
        <div>Welcome, {{ current_user.username }}</div>
      </div>
    </div>
    
    <a class="btn" href="{{ url_for('auth.logout') }}">Logout</a>
</header>


       
      <main>
        <div class="cards">
          <div class="card">
            Total Students
            <div class="number">{{ total }}</div>
          </div>

          <div class="card">
            Departments
            <div class="number">{{ departments }}</div>
          </div>

          <div class="card">
            Average CGPA
            <div class="number">{{ "%.2f"|format(average) }}</div>
          </div>
        </div>

        {% with messages = get_flashed_messages() %}
          {% for message in messages %}
            <p>{{ message }}</p>
          {% endfor %}
        {% endwith %}

        <section class="panel">
          <h2>{{ "Edit Student" if edit_student else "Add Student" }}</h2>

          <form method="post" action="{{ url_for('save_student') }}">
            <input type="hidden" name="id"
                   value="{{ edit_student.id if edit_student else '' }}">

            <input name="roll" placeholder="Roll Number" required
                   value="{{ edit_student.roll if edit_student else '' }}">

            <input name="name" placeholder="Student Name" required
                   value="{{ edit_student.name if edit_student else '' }}">

            <input name="department" placeholder="Department" required
                   value="{{ edit_student.department if edit_student else '' }}">

            <input name="email" type="email" placeholder="Email"
                   value="{{ (edit_student.email or '') if edit_student else '' }}">

            <input name="semester" type="number" min="1" max="12"
                   placeholder="Semester"
                   value="{{ edit_student.semester if edit_student and edit_student.semester else '' }}">

            <input name="cgpa" type="number" min="0" max="10"
                   step="0.01" placeholder="CGPA" required
                   value="{{ edit_student.cgpa if edit_student else '' }}">

            <input name="attendance" type="number" min="0" max="100"
                   step="0.1" placeholder="Attendance %"
                   value="{{ edit_student.attendance if edit_student else 0 }}">

            <input name="backlogs" type="number" min="0"
                   placeholder="Backlogs"
                   value="{{ edit_student.backlogs if edit_student else 0 }}">

            <button type="submit">
              {{ "Update Student" if edit_student else "Save Student" }}
            </button>

            {% if edit_student %}
              <a class="btn" href="{{ url_for('home') }}">Cancel</a>
            {% endif %}
          </form>
        </section>

        <section class="panel">
          <h2>Student Records</h2>

          <form method="get">
            <input name="q"
                   placeholder="Search roll, name, department"
                   value="{{ search }}">

            <button type="submit">Search</button>
            <a class="btn" href="{{ url_for('home') }}">Clear</a>
          </form>

          <div class="table-wrap">
            <table>
              <tr>
                <th>Roll</th>
                <th>Name</th>
                <th>Department</th>
                <th>Email</th>
                <th>Semester</th>
                <th>CGPA</th>
                <th>Attendance</th>
                <th>Backlogs</th>
                <th>Actions</th>
              </tr>

              {% for s in students %}
              <tr>
                <td>{{ s.roll }}</td>
                <td>{{ s.name }}</td>
                <td>{{ s.department }}</td>
                <td>{{ s.email or '-' }}</td>
                <td>{{ s.semester or '-' }}</td>
                <td>{{ "%.2f"|format(s.cgpa) }}</td>
                <td>{{ s.attendance }}%</td>
                <td>{{ s.backlogs }}</td>

                <td>
                  <a class="btn"
                     href="{{ url_for('edit_student', student_id=s.id) }}">
                    Edit
                  </a>

                  <form method="post"
                        action="{{ url_for('delete_student', student_id=s.id) }}"
                        style="display:inline"
                        onsubmit="return confirm('Delete this student?')">
                    <button class="danger" type="submit">Delete</button>
                  </form>
                </td>
              </tr>

              {% else %}
              <tr>
                <td colspan="9">No student records found.</td>
              </tr>
              {% endfor %}
            </table>
          </div>
        </section>
      </main>
    </body>
    </html>
    """,
    total=total,
    departments=departments,
    average=average,
    students=students,
    search=search,
    edit_student=edit_student)


@app.route("/student/save", methods=["POST"])
@login_required
def save_student():
    roll = request.form.get("roll", "").strip()
    name = request.form.get("name", "").strip()
    department = request.form.get("department", "").strip()
    email = request.form.get("email", "").strip()
    semester = request.form.get("semester") or None
    cgpa = request.form.get("cgpa", type=float)
    attendance = request.form.get("attendance", default="0", type=float)
    backlogs = request.form.get("backlogs", default="0", type=int)
    student_id = request.form.get("id", "").strip()

    if (
        not roll or not name or not department
        or cgpa is None or not 0 <= cgpa <= 10
    ):
        flash("Enter valid details and a CGPA from 0 to 10.")
        return redirect(url_for("home"))

    if not 0 <= attendance <= 100 or backlogs < 0:
        flash("Attendance must be 0–100 and backlogs cannot be negative.")
        return redirect(url_for("home"))

    db = get_db()

    try:
        if student_id:
            db.execute("""
                UPDATE students
                SET roll=?, name=?, department=?, email=?,
                    semester=?, cgpa=?, attendance=?, backlogs=?
                WHERE id=?
            """, (
                roll, name, department, email, semester,
                cgpa, attendance, backlogs, student_id
            ))
        else:
            db.execute("""
                INSERT INTO students
                (roll, name, department, email, semester, cgpa,
                 attendance, backlogs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                roll, name, department, email, semester,
                cgpa, attendance, backlogs
            ))

        db.commit()
        flash("Student saved successfully.")

    except Exception:
        db.rollback()
        flash("Could not save. Check that the roll number is unique.")

    finally:
        db.close()

    return redirect(url_for("home"))


@app.route("/student/edit/<int:student_id>")
@login_required
def edit_student(student_id):
    db = get_db()
    student = db.execute(
        "SELECT id FROM students WHERE id = ?", (student_id,)
    ).fetchone()
    db.close()

    if not student:
        flash("Student not found.")
        return redirect(url_for("home"))

    return redirect(url_for("home", edit=student_id))


@app.route("/student/delete/<int:student_id>", methods=["POST"])
@login_required
def delete_student(student_id):
    db = get_db()
    db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    db.close()

    flash("Student deleted.")
    return redirect(url_for("home"))


def setup_database():
    init_db()

    db = get_db()
    users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    db.close()

    if users == 0:
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD")

        if not password:
            password = "ChangeMe123!"

        create_admin(username, password)


setup_database()


if __name__ == "__main__":
    app.run(debug=True, port=8080)
