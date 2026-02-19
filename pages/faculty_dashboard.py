import streamlit as st
import os

from sqlalchemy.orm import joinedload

from utils.db_conn import SessionLocal
from db.models import User, Student
from utils.face_utils import mark_attendance, STUDENT_IMG_DIR, CSV_DIR

os.makedirs(STUDENT_IMG_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
def add_student():
    st.subheader("Add Student")
    name = st.text_input("Student Name", key="f_add_name")
    roll_no = st.text_input("Roll Number", key="f_add_roll")
    class_name = st.text_input("Class Name", key="f_add_class")
    username = st.text_input("Username", key="f_add_username")
    password = st.text_input("Password", type="password", key="f_add_pwd")
    files = st.file_uploader("Upload Student Images", type=["jpg","jpeg","png"], accept_multiple_files=True, key="f_add_files")

    if st.button("Save Student"):
        if not all([name, roll_no, class_name, username, password, files]):
            st.error("Fill all fields and upload images")
            return
        db = SessionLocal()
        if db.query(User).filter(User.username==username).first():
            st.error("Username already exists")
            db.close()
            return
        # Create User
        user = User(username=username, password=password, role="student")
        db.add(user)
        db.commit()
        db.refresh(user)
        # Create Student
        student = Student(name=name, roll_no=roll_no, class_name=class_name, user_id=user.id)
        db.add(student)
        db.commit()
        db.refresh(student)
        # Save Images
        folder = os.path.join(STUDENT_IMG_DIR, str(student.id))
        os.makedirs(folder, exist_ok=True)
        for f in files:
            with open(os.path.join(folder, f.name), "wb") as out:
                out.write(f.getbuffer())
        student.images_path = folder
        db.commit()
        db.close()
        st.success(f"Student {name} added successfully with {len(files)} images.")


def manage_students():
    st.subheader("Manage Students")
    db = SessionLocal()
    # eager load user to avoid DetachedInstanceError
    students = db.query(Student).options(joinedload(Student.user)).all()
    stu_names = {f"{s.name} ({s.roll_no})": s for s in students}

    if stu_names:
        choice = st.selectbox("Select Student", list(stu_names.keys()), key="faculty_select_student")
        student = stu_names[choice]

        new_name = st.text_input("Edit Name", value=student.name, key="faculty_edit_name")
        new_roll = st.text_input("Edit Roll", value=student.roll_no, key="faculty_edit_roll")
        new_class = st.text_input("Edit Class", value=student.class_name, key="faculty_edit_class")
        new_username = st.text_input("Edit Username", value=student.user.username if student.user else "",
                                     key="faculty_edit_username")
        new_password = st.text_input("Edit Password", value=student.user.password if student.user else "",
                                     type="password", key="faculty_edit_pwd")

        if st.button("Update Student", key="faculty_update_student"):
            if student.user:
                student.user.username = new_username
                student.user.password = new_password
            student.name = new_name
            student.roll_no = new_roll
            student.class_name = new_class
            db.commit()
            st.success(f"Student {new_name} updated!")

        if st.button("Remove Student", key="faculty_remove_student"):
            if student.images_path and os.path.exists(student.images_path):
                import shutil
                shutil.rmtree(student.images_path)
            if student.user:
                db.delete(student.user)
            db.delete(student)
            db.commit()
            st.success(f"Student {choice} removed!")

    db.close()


# ----------------- Attendance -----------------
def post_attendance():
    st.subheader("Post Attendance for a Session")
    session_name = st.text_input("Session Name")
    class_name = st.text_input("Class Name")
    group_img = st.file_uploader("Upload Group Photo", type=["jpg","jpeg","png"])

    if st.button("Submit Attendance"):
        if not session_name or not class_name or not group_img:
            st.error("Fill all fields and upload group photo")
            return
        
        # Save group image temporarily
        group_path = "temp_group.jpg"
        with open(group_path, "wb") as f:
            f.write(group_img.getbuffer())
        
        try:
            db = SessionLocal()
            csv_path = mark_attendance(db, session_name, class_name, group_path)
            db.close()
            
            st.success(f"✅ Attendance posted for class {class_name}, session {session_name}")
            with open(csv_path, "rb") as f:
                st.download_button("📥 Download CSV", f, file_name=os.path.basename(csv_path))
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(group_path):
                os.remove(group_path)

# ----------------- Main -----------------
def main():
    if "user" not in st.session_state or st.session_state["user"]["role"] != "faculty":
        st.error("Access Denied")
        return
    st.title("👨‍🏫 Faculty Dashboard")
    st.header("Add Student")
    add_student()
    st.write("---")
    st.header("Manage Students")
    manage_students()
    st.write("---")
    st.header("Attendance")
    post_attendance()
