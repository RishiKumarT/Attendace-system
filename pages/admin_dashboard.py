import streamlit as st
import os

from sqlalchemy.orm import joinedload

from utils.db_conn import SessionLocal
from db.models import User, Student

STUDENT_IMG_DIR = "student_images"
os.makedirs(STUDENT_IMG_DIR, exist_ok=True)

def add_faculty():
    st.subheader("Add Faculty")
    uname = st.text_input("Faculty Username", key="add_faculty_username")
    pwd = st.text_input("Faculty Password", type="password", key="add_faculty_password")
    if st.button("Save Faculty"):
        if not uname or not pwd:
            st.error("Fill all fields")
            return
        db = SessionLocal()
        if db.query(User).filter(User.username == uname).first():
            st.error("Username already exists")
            db.close()
            return
        faculty = User(username=uname, password=pwd, role="faculty")
        db.add(faculty)
        db.commit()
        db.close()
        st.success(f"Faculty {uname} added!")

def manage_faculty():
    st.subheader("Manage Faculty")
    db = SessionLocal()
    faculties = db.query(User).filter(User.role=="faculty").all()
    db.close()
    if faculties:
        choice = st.selectbox("Select Faculty", [f.username for f in faculties])
        faculty = next(f for f in faculties if f.username == choice)
        new_uname = st.text_input("Edit Username", value=faculty.username, key="edit_faculty_uname")
        new_pwd = st.text_input("Edit Password", value=faculty.password, type="password", key="edit_faculty_pwd")
        if st.button("Update Faculty"):
            db = SessionLocal()
            f_db = db.query(User).get(faculty.id)
            f_db.username = new_uname
            f_db.password = new_pwd
            db.commit()
            db.close()
            st.success(f"Faculty {new_uname} updated!")
        if st.button("Remove Faculty"):
            db = SessionLocal()
            f_db = db.query(User).get(faculty.id)
            db.delete(f_db)
            db.commit()
            db.close()
            st.success(f"Faculty {choice} removed!")

def add_student():
    st.subheader("Add Student")
    name = st.text_input("Student Name", key="add_stu_name")
    roll_no = st.text_input("Roll Number", key="add_stu_roll")
    class_name = st.text_input("Class Name", key="add_stu_class")
    username = st.text_input("Username", key="add_stu_username")
    password = st.text_input("Password", type="password", key="add_stu_password")
    files = st.file_uploader("Upload Images", type=["jpg","jpeg","png"], accept_multiple_files=True, key="add_stu_files")

    if st.button("Save Student"):
        if not all([name, roll_no, class_name, username, password, files]):
            st.error("Fill all fields and upload images")
            return
        db = SessionLocal()
        # Check if username exists
        if db.query(User).filter(User.username==username).first():
            st.error("Username already exists")
            db.close()
            return
        # 1️⃣ Create User
        user = User(username=username, password=password, role="student")
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2️⃣ Create Student
        student = Student(name=name, roll_no=roll_no, class_name=class_name, user_id=user.id)
        db.add(student)
        db.commit()
        db.refresh(student)

        # Save images
        folder = os.path.join(STUDENT_IMG_DIR, str(student.id))
        os.makedirs(folder, exist_ok=True)
        for f in files:
            with open(os.path.join(folder, f.name), "wb") as out:
                out.write(f.getbuffer())
        student.images_path = folder
        db.commit()
        db.close()
        st.success(f"Student {name} added with {len(files)} images.")


def manage_students():
    st.subheader("Manage Students")
    db = SessionLocal()
    # eager load user to avoid DetachedInstanceError
    students = db.query(Student).options(joinedload(Student.user)).all()
    stu_names = {f"{s.name} ({s.roll_no})": s for s in students}

    if stu_names:
        choice = st.selectbox("Select Student", list(stu_names.keys()), key="admin_select_student")
        student = stu_names[choice]

        new_name = st.text_input("Edit Name", value=student.name, key="admin_edit_name")
        new_roll = st.text_input("Edit Roll", value=student.roll_no, key="admin_edit_roll")
        new_class = st.text_input("Edit Class", value=student.class_name, key="admin_edit_class")
        new_username = st.text_input("Edit Username", value=student.user.username if student.user else "",
                                     key="admin_edit_username")
        new_password = st.text_input("Edit Password", value=student.user.password if student.user else "",
                                     type="password", key="admin_edit_pwd")

        if st.button("Update Student", key="admin_update_student"):
            if student.user:
                student.user.username = new_username
                student.user.password = new_password
            student.name = new_name
            student.roll_no = new_roll
            student.class_name = new_class
            db.commit()
            st.success(f"Student {new_name} updated!")

        if st.button("Remove Student", key="admin_remove_student"):
            if student.images_path and os.path.exists(student.images_path):
                import shutil
                shutil.rmtree(student.images_path)
            if student.user:
                db.delete(student.user)
            db.delete(student)
            db.commit()
            st.success(f"Student {choice} removed!")

    db.close()


# ----------------- Main -----------------
def main():
    if "user" not in st.session_state or st.session_state["user"]["role"] != "admin":
        st.error("Access Denied")
        return
    st.title("👑 Admin Dashboard")
    st.header("Faculty Management")
    add_faculty()
    manage_faculty()
    st.write("---")
    st.header("Student Management")
    add_student()
    manage_students()
