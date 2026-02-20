import os
import pandas as pd
import face_recognition

from db.models import Student, AttendanceSession, AttendanceRecord

STUDENT_IMG_DIR = "student_images"
CSV_DIR = "attendance_csvs"

os.makedirs(CSV_DIR, exist_ok=True)


# ---------------------------
# GET STUDENT FACE ENCODINGS
# ---------------------------
def get_student_encodings(images_path):
    encodings = []

    from PIL import Image
    import numpy as np

    if not os.path.exists(images_path):
        return encodings

    for file_name in os.listdir(images_path):
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(images_path, file_name)

            print("Processing student image:", img_path)

            try:
                # ✅ FORCE CLEAN RGB IMAGE
                pil_img = Image.open(img_path).convert("RGB")
                img = np.array(pil_img)

                faces = face_recognition.face_encodings(img)

                print("Faces detected:", len(faces))

                if faces:
                    encodings.append(faces[0])

            except Exception as e:
                print(f"❌ Error in {img_path}: {e}")
                continue

    return encodings


# ---------------------------
# MATCH FACES
# ---------------------------
def match_faces(group_img_path, class_name, db):
    from PIL import Image
    import numpy as np

    # ✅ FIX: Use PIL instead of OpenCV
    try:
        pil_img = Image.open(group_img_path).convert("RGB")
        group_img = np.array(pil_img)
    except Exception as e:
        raise ValueError(f"Invalid group image: {e}")

    group_encodings = face_recognition.face_encodings(group_img)

    print("Detected faces in group image:", len(group_encodings))

    students = db.query(Student).filter(Student.class_name == class_name).all()
    attendance = {s.id: "Absent" for s in students}

    for student in students:
        if not student.images_path:
            continue

        student_encodings = get_student_encodings(student.images_path)

        if not student_encodings:
            print(f"No encodings for {student.name}")
            continue

        matched = False

        for g_enc in group_encodings:
            results = face_recognition.compare_faces(
                student_encodings,
                g_enc,
                tolerance=0.5
            )

            if True in results:
                matched = True
                break

        if matched:
            attendance[student.id] = "Present"

    return attendance


# ---------------------------
# MARK ATTENDANCE
# ---------------------------
def mark_attendance(db, session_name, class_name, group_img_path):

    attendance = match_faces(group_img_path, class_name, db)

    # Create session
    session = AttendanceSession(session_name=session_name, class_name=class_name)
    db.add(session)
    db.commit()
    db.refresh(session)

    # Insert records
    for student_id, status in attendance.items():
        rec = AttendanceRecord(
            session_id=session.id,
            student_id=student_id,
            status=status
        )
        db.add(rec)

    db.commit()

    # Export CSV
    students = db.query(Student).filter(Student.id.in_(attendance.keys())).all()

    data = []
    for student in students:
        data.append({
            "student_id": student.id,
            "student_name": student.name,
            "roll_no": student.roll_no,
            "status": attendance[student.id]
        })

    df = pd.DataFrame(data)

    csv_path = os.path.join(
        CSV_DIR,
        f"{session.timestamp.date()}_{session_name}_{class_name}.csv"
    )

    df.to_csv(csv_path, index=False)

    session.csv_path = csv_path
    db.commit()

    return csv_path