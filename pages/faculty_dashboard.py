import streamlit as st
import os

from sqlalchemy.orm import joinedload

from utils.db_conn import SessionLocal
from db.models import User, Student
from utils.face_utils import mark_attendance, STUDENT_IMG_DIR, CSV_DIR

os.makedirs(STUDENT_IMG_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

def add_student():
    st.markdown("### Enter Student Details")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="e.g. John Doe", key="f_add_name")
            class_name = st.text_input("Class Name", placeholder="e.g. CS101", key="f_add_class")
            username = st.text_input("Portal Username", placeholder="e.g. john_123", key="f_add_username")
        with col2:
            roll_no = st.text_input("Roll Number", placeholder="e.g. 2023CS001", key="f_add_roll")
            password = st.text_input("Portal Password", type="password", placeholder="Enter password", key="f_add_pwd")
            files = st.file_uploader("Upload Student Images (Min 3 recommended)", type=["jpg","jpeg","png"], accept_multiple_files=True, key="f_add_files")

        st.write("")
        submit_btn = st.button("Save Student Record", use_container_width=True, type="primary")

        if submit_btn:
            if not all([name, roll_no, class_name, username, password, files]):
                st.error("Fill all fields and upload images before saving.")
                return
            db = SessionLocal()
            if db.query(User).filter(User.username==username).first():
                st.error("Username already exists. Choose a different one.")
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
            st.success(f"Student {name} added successfully! Uploaded {len(files)} face image(s).")


def manage_students():
    db = SessionLocal()
    # eager load user to avoid DetachedInstanceError
    students = db.query(Student).options(joinedload(Student.user)).all()
    stu_names = {f"{s.name} ({s.roll_no})": s for s in students}

    if stu_names:
        st.markdown("### Select Student to Edit")
        choice = st.selectbox("Search Student by Name or Roll No", list(stu_names.keys()), key="faculty_select_student")
        student = stu_names[choice]

        st.markdown("### Edit Details")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Edit Name", value=student.name, key="faculty_edit_name")
                new_class = st.text_input("Edit Class", value=student.class_name, key="faculty_edit_class")
                new_username = st.text_input("Edit Username", value=student.user.username if student.user else "",
                                             key="faculty_edit_username")
            with col2:
                new_roll = st.text_input("Edit Roll", value=student.roll_no, key="faculty_edit_roll")
                new_password = st.text_input("Edit Password", value=student.user.password if student.user else "",
                                             type="password", key="faculty_edit_pwd")
            
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Update Student", use_container_width=True, type="primary", key="faculty_update_student"):
                    if student.user:
                        student.user.username = new_username
                        student.user.password = new_password
                    student.name = new_name
                    student.roll_no = new_roll
                    student.class_name = new_class
                    db.commit()
                    st.success(f"Student {new_name}'s details successfully updated!")
            with c2:
                if st.button("Remove Student", use_container_width=True, key="faculty_remove_student"):
                    if student.images_path and os.path.exists(student.images_path):
                        import shutil
                        shutil.rmtree(student.images_path)
                    if student.user:
                        db.delete(student.user)
                    db.delete(student)
                    db.commit()
                    st.success(f"Student {choice} totally removed from system!")

    db.close()


# ----------------- Attendance -----------------
def post_attendance():
    st.markdown("### Upload Session Details")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            session_name = st.text_input("Session Name", placeholder="e.g. Python Lecture 1")
        with col2:
            class_name = st.text_input("Class Name", placeholder="e.g. CS101")
            
        group_img = st.file_uploader("Upload Group Photo / Classroom View", type=["jpg","jpeg","png"])

        st.write("")
        if st.button("Process & Submit Attendance", use_container_width=True, type="primary"):
            if not session_name or not class_name or not group_img:
                st.error("Please provide Session Name, Class Name, and a valid Group Photo.")
                return
            
            # Save group image temporarily
            group_path = "temp_group.jpg"
            with open(group_path, "wb") as f:
                f.write(group_img.getbuffer())
            
            try:
                with st.spinner('Scanning faces and matching with database...'):
                    db = SessionLocal()
                    csv_path = mark_attendance(db, session_name, class_name, group_path)
                    db.close()
                
                st.success(f"Attendance recorded successfully for {class_name} during {session_name}!")
                with open(csv_path, "rb") as f:
                    st.download_button("Download CSV Report", f, file_name=os.path.basename(csv_path))
            except Exception as e:
                st.error(f"Error processing images: {str(e)}")
            finally:
                # Clean up temp file
                if os.path.exists(group_path):
                    os.remove(group_path)

# ----------------- Main -----------------
def main():
    if "user" not in st.session_state or st.session_state["user"]["role"] != "faculty":
        st.error("Access Denied")
        return
    st.title("Faculty Dashboard")
    
    # Hide sidebar
    st.markdown("<style> [data-testid='stSidebar'] { display: none; } </style>", unsafe_allow_html=True)
    
    # Top Navbar layout
    col1, col2, col3, col4 = st.columns([1,2,2,1])
    with col2:
        if st.button("Student Management", use_container_width=True):
            st.session_state['faculty_nav'] = 'student'
            st.rerun()
    with col3:
        if st.button("Post Attendance", use_container_width=True):
            st.session_state['faculty_nav'] = 'attendance'
            st.rerun()
    with col4:
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.pop("user")
            st.rerun()
            
    if 'faculty_nav' not in st.session_state:
        st.session_state['faculty_nav'] = 'student'
        
    st.divider()
    
    if st.session_state['faculty_nav'] == 'student':
        tab1, tab2 = st.tabs(["Add New Student", "Manage Existing Students"])
        with tab1:
            add_student()
        with tab2:
            manage_students()
            
    elif st.session_state['faculty_nav'] == 'attendance':
        post_attendance()
