import os
import pandas as pd
import cv2
import numpy as np
from utils.db_conn import SessionLocal
from db.models import Student, AttendanceSession, AttendanceRecord

STUDENT_IMG_DIR = "student_images"
CSV_DIR = "attendance_csvs"

os.makedirs(CSV_DIR, exist_ok=True)

# Load face detector cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

def get_student_face_descriptor(student_id, images_path):
    """Get average face descriptor from student's images using template matching"""
    descriptors = []
    
    if not os.path.exists(images_path):
        return None
    
    for file_name in os.listdir(images_path):
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(images_path, file_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                # Take largest face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                face_roi = gray[y:y+h, x:x+w]
                descriptors.append(face_roi)
    
    return descriptors

def match_faces(group_img_path, class_name, db):
    """Match faces in group image with student images"""
    
    group_img = cv2.imread(group_img_path)
    if group_img is None:
        raise ValueError("Could not read group image")
    
    gray_group = cv2.cvtColor(group_img, cv2.COLOR_BGR2GRAY)
    faces_in_group = face_cascade.detectMultiScale(gray_group, 1.3, 5)
    
    # Get all students in the class
    students = db.query(Student).filter(Student.class_name == class_name).all()
    attendance = {s.id: "Absent" for s in students}
    
    # For each student, check if their face is in the group image
    for student in students:
        if not student.images_path:
            continue
        
        student_descriptors = get_student_face_descriptor(student.id, student.images_path)
        if not student_descriptors:
            continue
        
        # Check if any face in group matches this student
        matched = False
        for face_roi in student_descriptors:
            for (x, y, w, h) in faces_in_group:
                group_face = gray_group[y:y+h, x:x+w]
                
                # Resize for comparison
                try:
                    group_face_resized = cv2.resize(group_face, (face_roi.shape[1], face_roi.shape[0]))
                    
                    # Use template matching score
                    result = cv2.matchTemplate(group_face_resized, face_roi, cv2.TM_CCOEFF)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # If similarity is high enough, mark as present
                    if max_val > 3000:  # Threshold for matching
                        matched = True
                        break
                except:
                    continue
            
            if matched:
                break
        
        if matched:
            attendance[student.id] = "Present"
    
    return attendance

def mark_attendance(db, session_name, class_name, group_img_path):
    """Mark attendance for a session based on group image"""
    
    # Get attendance from face matching
    attendance = match_faces(group_img_path, class_name, db)
    
    # Save session to DB
    session = AttendanceSession(session_name=session_name, class_name=class_name)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Save attendance records
    for student_id, status in attendance.items():
        rec = AttendanceRecord(session_id=session.id, student_id=student_id, status=status)
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
    csv_path = os.path.join(CSV_DIR, f"{session.timestamp.date()}_{session_name}_{class_name}.csv")
    df.to_csv(csv_path, index=False)
    session.csv_path = csv_path
    db.commit()
    
    return csv_path
 