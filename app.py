import os
import csv
from datetime import datetime
from calendar import month_name

from flask import (
    Flask, render_template, redirect, url_for,
    request, flash, session, send_file
)

from face_utils import (
    load_students, save_student, update_student,
    capture_faces, train_model, take_attendance_once,
    ATTENDANCE_FILE
)

from email_utils import send_attendance_email

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

ADMIN_USERNAME = "sandy"
ADMIN_PASSWORD = "sandy123"


# ================= LOGIN =================
def login_required(view_func):
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    wrapped.__name__ = view_func.__name__
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form.get("username") == ADMIN_USERNAME and
            request.form.get("password") == ADMIN_PASSWORD
        ):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("Invalid username or password", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ================= DASHBOARD =================
@app.route("/")
@login_required
def dashboard():
    students = load_students()
    today = datetime.now().strftime("%Y-%m-%d")

    present = set()
    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["date"] == today and row["status"] == "Present":
                    present.add(row["student_id"])

    return render_template(
        "dashboard.html",
        total_students=len(students),
        today_present=len(present),
        rate=round((len(present) / len(students)) * 100, 2) if students else 0,
        now=datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    )


# ================= STUDENTS =================
@app.route("/students", methods=["GET", "POST"])
@login_required
def students_page():
    if request.method == "POST":
        created = save_student(
            int(request.form["student_id"]),
            request.form["name"],
            request.form["parent_email"]
        )
        flash(
            "Student saved." if created else "Student ID already exists.",
            "success" if created else "danger"
        )
        return redirect(url_for("students_page"))

    return render_template("students.html", students=load_students())


@app.route("/students/<int:student_id>/capture")
@login_required
def capture_student_face(student_id):
    capture_faces(student_id)
    train_model()
    flash("Face captured & model trained.", "success")
    return redirect(url_for("students_page"))


@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    students = load_students()

    if request.method == "POST":
        update_student(
            student_id,
            int(request.form["student_id"]),
            request.form["name"],
            request.form["parent_email"]
        )
        flash("Student updated.", "success")
        return redirect(url_for("students_page"))

    return render_template(
        "edit_student.html",
        sid=student_id,
        info=students[student_id]
    )


# ================= TAKE ATTENDANCE =================
@app.route("/take-attendance", methods=["GET", "POST"])
@login_required
def take_attendance_page():
    if request.method == "POST":
        statuses, error, unknown = take_attendance_once()

        if error or unknown:
            flash("Face not recognised or model not trained.", "danger")
            return redirect(url_for("take_attendance_page"))

        students = load_students()
        today = datetime.now().strftime("%Y-%m-%d")
        time_now = datetime.now().strftime("%I:%M %p")

        mail_count = 0
        for sid, status in statuses.items():
            if status == "Present":
                send_attendance_email(
                    students[sid]["parent_email"],
                    students[sid]["name"],
                    "Present",
                    today,
                    time_now
                )
                mail_count += 1

        flash(f"Attendance taken. Emails sent to {mail_count} parents.", "success")
        return redirect(url_for("take_attendance_page"))

    return render_template("take_attendance.html")


# ================= ATTENDANCE RECORDS (FILTER WORKING) =================
@app.route("/attendance-records", methods=["GET", "POST"])
@login_required
def attendance_records():
    date_filter = request.values.get("date", "").strip()
    status_filter = request.values.get("status", "").strip()

    rows = []

    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):

                if date_filter and row["date"] != date_filter:
                    continue

                if status_filter and row["status"].lower() != status_filter.lower():
                    continue

                rows.append(row)

    return render_template(
        "attendance_records.html",
        rows=rows,
        date_filter=date_filter,
        status_filter=status_filter
    )


@app.route("/attendance-records/download")
@login_required
def download_attendance_csv():
    return send_file(
        ATTENDANCE_FILE,
        as_attachment=True,
        download_name="attendance.csv",
        mimetype="text/csv"
    )


# ================= STATISTICS (MONTH DROPDOWN FIXED) =================
@app.route("/statistics")
@login_required
def statistics():
    students = load_students()

    today = datetime.now()
    month = int(request.args.get("month", today.month))
    year = int(request.args.get("year", today.year))

    total_days_set = set()
    present = {sid: 0 for sid in students}
    absent = {sid: 0 for sid in students}

    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                y, m, _ = map(int, row["date"].split("-"))
                if y == year and m == month:
                    total_days_set.add(row["date"])
                    sid = int(row["student_id"])
                    if row["status"] == "Present":
                        present[sid] += 1
                    else:
                        absent[sid] += 1

    total_days = len(total_days_set)

    stats = []
    for sid, info in students.items():
        percent = round((present[sid] / total_days) * 100, 2) if total_days else 0
        stats.append({
            "id": sid,
            "name": info["name"],
            "present": present[sid],
            "absent": absent[sid],
            "total_days": total_days,
            "percent": percent
        })

    months = [(i, month_name[i]) for i in range(1, 13)]

    return render_template(
        "statistics.html",
        stats=stats,
        months=months,
        selected_month=month,
        selected_year=year,
        month_label=month_name[month],
        total_days=total_days
    )


if __name__ == "__main__":
    app.run(debug=True)
