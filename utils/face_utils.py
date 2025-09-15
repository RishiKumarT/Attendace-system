import face_recognition
import os
import pandas as pd
from utils.db_conn import SessionLocal
from db.models import Student, AttendanceSession, AttendanceRecord

STUDENT_IMG_DIR = "student_images"
CSV_DIR = "attendance_csvs"

os.makedirs(CSV_DIR, exist_ok=True)

def load_student_encodings(db, class_name):
    known_encodings, student_ids = [], []
    students = db.query(Student).filter(Student.class_name == class_name).all()

    for student in students:
        if not student.images_path:
            continue
        folder = student.images_path
        for file_name in os.listdir(folder):
            if file_name.lower().endswith((".jpg",".jpeg",".png")):
                img_path = os.path.join(folder, file_name)
                img = face_recognition.load_image_file(img_path)
                encs = face_recognition.face_encodings(img)
                if encs:
                    known_encodings.append(encs[0])
                    student_ids.append(student.id)
    return known_encodings, student_ids

def mark_attendance(db, session_name, class_name, group_img_path):
    known_encodings, student_ids = load_student_encodings(db, class_name)
    attendance = {sid: "Absent" for sid in student_ids}

    group_img = face_recognition.load_image_file(group_img_path)
    face_locs = face_recognition.face_locations(group_img)
    face_encs = face_recognition.face_encodings(group_img, face_locs)

    for enc in face_encs:
        matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.5)
        distances = face_recognition.face_distance(known_encodings, enc)
        if len(distances) > 0:
            best = distances.argmin()
            if matches[best]:
                sid = student_ids[best]
                attendance[sid] = "Present"

    # Save session to DB
    session = AttendanceSession(session_name=session_name, class_name=class_name)
    db.add(session)
    db.commit()
    db.refresh(session)

    # Save attendance records
    for sid, status in attendance.items():
        rec = AttendanceRecord(session_id=session.id, student_id=sid, status=status)
        db.add(rec)
    db.commit()

    # Export CSV
    df = pd.DataFrame([{"student_id": sid, "status": status} for sid, status in attendance.items()])
    csv_path = os.path.join(CSV_DIR, f"{session.timestamp.date()}_{session_name}_{class_name}.csv")
    df.to_csv(csv_path, index=False)
    session.csv_path = csv_path
    db.commit()

    return csv_path
 