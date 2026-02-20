import streamlit as st
import os

from sqlalchemy.orm import joinedload

from utils.db_conn import SessionLocal
from db.models import User, Student

STUDENT_IMG_DIR = "student_images"
os.makedirs(STUDENT_IMG_DIR, exist_ok=True)

def add_faculty():
    st.markdown("### Enter Faculty Details")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            uname = st.text_input("Faculty Username", key="add_faculty_username", placeholder="e.g. fac_smith")
        with col2:
            pwd = st.text_input("Faculty Password", type="password", key="add_faculty_password", placeholder="Enter password")
            
        st.write("")
        if st.button("Save Faculty Record", use_container_width=True, type="primary"):
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
            st.success(f"Faculty {uname} added successfully!")

def manage_faculty():
    db = SessionLocal()
    faculties = db.query(User).filter(User.role=="faculty").all()
    db.close()
    if faculties:
        st.markdown("### Select Faculty to Edit")
        choice = st.selectbox("Search Faculty by Username", [f.username for f in faculties])
        faculty = next(f for f in faculties if f.username == choice)
        
        st.markdown("### Edit Details")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                new_uname = st.text_input("Edit Username", value=faculty.username, key="edit_faculty_uname")
            with col2:
                new_pwd = st.text_input("Edit Password", value=faculty.password, type="password", key="edit_faculty_pwd")
            
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Update Faculty", use_container_width=True, type="primary"):
                    db = SessionLocal()
                    f_db = db.query(User).get(faculty.id)
                    f_db.username = new_uname
                    f_db.password = new_pwd
                    db.commit()
                    db.close()
                    st.success(f"Faculty {new_uname} updated!")
            with c2:
                if st.button("Remove Faculty", use_container_width=True):
                    db = SessionLocal()
                    f_db = db.query(User).get(faculty.id)
                    db.delete(f_db)
                    db.commit()
                    db.close()
                    st.success(f"Faculty {choice} removed!")

def add_student():
    st.markdown("### Enter Student Details")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="e.g. John Doe", key="add_stu_name")
            class_name = st.text_input("Class Name", placeholder="e.g. CS101", key="add_stu_class")
            username = st.text_input("Portal Username", placeholder="e.g. john_123", key="add_stu_username")
        with col2:
            roll_no = st.text_input("Roll Number", placeholder="e.g. 2023CS001", key="add_stu_roll")
            password = st.text_input("Portal Password", type="password", placeholder="Enter password", key="add_stu_password")
            files = st.file_uploader("Upload Student Face Images (Min 3)", type=["jpg","jpeg","png"], accept_multiple_files=True, key="add_stu_files")

        st.write("")
        submit_btn = st.button("Save Student Record", use_container_width=True, type="primary")

        if submit_btn:
            if not all([name, roll_no, class_name, username, password, files]):
                st.error("Fill all fields and upload images.")
                return
            db = SessionLocal()
            # Check if username exists
            if db.query(User).filter(User.username==username).first():
                st.error("Username already exists.")
                db.close()
                return
            # 1. Create User
            user = User(username=username, password=password, role="student")
            db.add(user)
            db.commit()
            db.refresh(user)

            # 2. Create Student
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
    db = SessionLocal()
    # eager load user to avoid DetachedInstanceError
    students = db.query(Student).options(joinedload(Student.user)).all()
    stu_names = {f"{s.name} ({s.roll_no})": s for s in students}

    if stu_names:
        st.markdown("### Select Student to Edit")
        choice = st.selectbox("Search Student by Name or Roll No", list(stu_names.keys()), key="admin_select_student")
        student = stu_names[choice]

        st.markdown("### Edit Details")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Edit Name", value=student.name, key="admin_edit_name")
                new_class = st.text_input("Edit Class", value=student.class_name, key="admin_edit_class")
                new_username = st.text_input("Edit Username", value=student.user.username if student.user else "",
                                             key="admin_edit_username")
            with col2:
                new_roll = st.text_input("Edit Roll", value=student.roll_no, key="admin_edit_roll")
                new_password = st.text_input("Edit Password", value=student.user.password if student.user else "",
                                             type="password", key="admin_edit_pwd")

            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Update Student", use_container_width=True, type="primary", key="admin_update_student"):
                    if student.user:
                        student.user.username = new_username
                        student.user.password = new_password
                    student.name = new_name
                    student.roll_no = new_roll
                    student.class_name = new_class
                    db.commit()
                    st.success(f"Student {new_name} updated!")
                    
            with c2:
                if st.button("Remove Student", use_container_width=True, key="admin_remove_student"):
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
    st.title("Admin Dashboard")
    
    # Hide sidebar for admin
    st.markdown("<style> [data-testid='stSidebar'] { display: none; } </style>", unsafe_allow_html=True)

    # Top Navbar logic
    col1, col2, col3, col4, col5 = st.columns([1,1.5,1.5,1.5,1])
    with col2:
        if st.button("Home", use_container_width=True):
            st.session_state['admin_nav'] = 'home'
            st.rerun()
    with col3:
        if st.button("Faculty Mgt", use_container_width=True):
            st.session_state['admin_nav'] = 'faculty'
            st.rerun()
    with col4:
        if st.button("Student Mgt", use_container_width=True):
            st.session_state['admin_nav'] = 'student'
            st.rerun()
    with col5:
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.pop("user")
            st.rerun()
            
    # Default to home
    if 'admin_nav' not in st.session_state:
        st.session_state['admin_nav'] = 'home'
        
    st.divider()

    if st.session_state['admin_nav'] == 'faculty':
        tab1, tab2 = st.tabs(["Add New Faculty", "Manage Existing Faculty"])
        with tab1:
            add_faculty()
        with tab2:
            manage_faculty()
            
    elif st.session_state['admin_nav'] == 'student':
        tab1, tab2 = st.tabs(["Add New Student", "Manage Existing Students"])
        with tab1:
            add_student()
        with tab2:
            manage_students()
            
    else:
        st.header("Welcome to Admin Portal")
        st.write("Overview of the attendance system.")
        
        # Query database for counts
        db = SessionLocal()
        student_count = db.query(Student).count()
        faculty_count = db.query(User).filter(User.role == "faculty").count()
        db.close()
        
        # Display nicely styled metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total Registered Students", value=student_count)
        with col2:
            st.metric(label="Total Faculty Members", value=faculty_count)
