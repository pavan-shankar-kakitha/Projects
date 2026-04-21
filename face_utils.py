import os
import csv
from datetime import datetime

import cv2
import numpy as np
from PIL import Image

# ================= PATHS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CASCADE_PATH = os.path.join(BASE_DIR, "haarcascades", "haarcascade_frontalface_default.xml")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
TRAINER_DIR = os.path.join(BASE_DIR, "trainer")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance.csv")
STUDENTS_FILE = os.path.join(BASE_DIR, "students.csv")

os.makedirs(DATASET_DIR, exist_ok=True)
os.makedirs(TRAINER_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
recognizer = cv2.face.LBPHFaceRecognizer_create()

CONFIDENCE_THRESHOLD = 60   # strict to avoid false matches


# ================= STUDENTS =================
def load_students():
    students = {}
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                students[int(row["id"])] = {
                    "name": row["name"],
                    "parent_email": row["parent_email"]
                }
    return students


def save_student(student_id, name, parent_email):
    if student_id in load_students():
        return False

    file_exists = os.path.exists(STUDENTS_FILE)
    with open(STUDENTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["id", "name", "parent_email"])
        writer.writerow([student_id, name, parent_email])
    return True


def update_student(old_id, new_id, name, parent_email):
    rows = []
    with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["id"]) == old_id:
                row["id"] = str(new_id)
                row["name"] = name
                row["parent_email"] = parent_email
            rows.append(row)

    with open(STUDENTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "parent_email"])
        writer.writeheader()
        writer.writerows(rows)


def delete_student(student_id):
    rows = []
    if os.path.exists(STUDENTS_FILE):
        with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if int(row["id"]) != student_id:
                    rows.append(row)

        with open(STUDENTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "parent_email"])
            writer.writeheader()
            writer.writerows(rows)

    # delete face images
    for file in os.listdir(DATASET_DIR):
        if file.startswith(f"User.{student_id}."):
            os.remove(os.path.join(DATASET_DIR, file))

    train_model()


# ================= FACE DATASET =================
def capture_faces(student_id, max_samples=40):
    cam = cv2.VideoCapture(0)
    count = 0

    while True:
        ret, img = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            count += 1
            cv2.imwrite(
                os.path.join(DATASET_DIR, f"User.{student_id}.{count}.jpg"),
                gray[y:y+h, x:x+w]
            )
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)

        cv2.imshow("Capture Face (ESC to stop)", img)

        if cv2.waitKey(1) == 27 or count >= max_samples:
            break

    cam.release()
    cv2.destroyAllWindows()


def train_model():
    faces, ids = [], []

    for file in os.listdir(DATASET_DIR):
        if file.endswith(".jpg"):
            img = Image.open(os.path.join(DATASET_DIR, file)).convert("L")
            img_np = np.array(img, "uint8")
            sid = int(file.split(".")[1])

            faces.append(img_np)
            ids.append(sid)

    if not faces:
        return False

    recognizer.train(faces, np.array(ids))
    recognizer.write(os.path.join(TRAINER_DIR, "trainer.yml"))
    return True


def load_recognizer():
    path = os.path.join(TRAINER_DIR, "trainer.yml")
    if os.path.exists(path):
        recognizer.read(path)
        return True
    return False


# ================= ATTENDANCE =================
def write_attendance(student_id, name, status, date_str, time_str):
    rows = []

    if os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

    # remove duplicate entry for same student + same date
    rows = [
        r for r in rows
        if not (r["student_id"] == str(student_id) and r["date"] == date_str)
    ]

    rows.append({
        "student_id": student_id,
        "student_name": name,
        "date": date_str,
        "time": time_str,
        "status": status
    })

    with open(ATTENDANCE_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["student_id", "student_name", "date", "time", "status"]
        )
        writer.writeheader()
        writer.writerows(rows)


def take_attendance_once():
    students = load_students()
    if not students:
        return None, "No students registered", False

    if not load_recognizer():
        return None, "Model not trained", False

    today = datetime.now().strftime("%Y-%m-%d")
    time_now = datetime.now().strftime("%H:%M:%S")

    cam = cv2.VideoCapture(0)
    present_ids = set()
    start = datetime.now()

    while (datetime.now() - start).seconds < 10:
        ret, img = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            sid, conf = recognizer.predict(gray[y:y+h, x:x+w])

            if conf < CONFIDENCE_THRESHOLD and sid in students:
                present_ids.add(sid)
                label = students[sid]["name"]
                color = (0,255,0)
            else:
                label = "Unknown"
                color = (0,0,255)

            cv2.rectangle(img, (x,y), (x+w,y+h), color, 2)
            cv2.putText(img, label, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Taking Attendance (ESC)", img)
        if cv2.waitKey(1) == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    if not present_ids:
        return None, None, True

    statuses = {}
    for sid, info in students.items():
        status = "Present" if sid in present_ids else "Absent"
        statuses[sid] = status
        write_attendance(sid, info["name"], status, today, time_now)

    return statuses, None, False
