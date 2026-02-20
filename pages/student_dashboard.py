import streamlit as st
import os
from utils.db_conn import SessionLocal
from db.models import Student, AttendanceSession, AttendanceRecord

CSV_DIR = "attendance_csvs"
os.makedirs(CSV_DIR, exist_ok=True)

def view_attendance():
    db = SessionLocal()
    student_id = st.session_state["user"]["id"]
    student = db.query(Student).filter(Student.user_id == student_id).first()
    if not student:
        st.error("Student not found")
        db.close()
        return
    st.subheader(f"Attendance for {student.name} ({student.roll_no}) - Class {student.class_name}")

    sessions = db.query(AttendanceSession).filter(AttendanceSession.class_name == student.class_name).order_by(AttendanceSession.timestamp.desc()).all()
    if not sessions:
        st.info("No attendance records yet")
        db.close()
        return

    for sess in sessions:
        record = db.query(AttendanceRecord).filter(
            AttendanceRecord.session_id == sess.id,
            AttendanceRecord.student_id == student.id
        ).first()
        status = record.status if record else "Absent"
        st.write(f"**Session:** {sess.session_name} | **Date:** {sess.timestamp.date()} | **Status:** {status}")
        if sess.csv_path and os.path.exists(sess.csv_path):
            with open(sess.csv_path, "rb") as f:
                st.download_button(
                    label=f"Download CSV ({sess.session_name})",
                    data=f,
                    file_name=os.path.basename(sess.csv_path),
                    key=f"download_{sess.id}"
                )
    db.close()

def main():
    if "user" not in st.session_state or st.session_state["user"]["role"] != "student":
        st.error("Access Denied")
        return
        
    # Hide sidebar
    st.markdown("<style> [data-testid='stSidebar'] { display: none; } </style>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🎓 Student Dashboard")
    with col2:
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.pop("user")
            st.rerun()
            
    st.divider()
    view_attendance()
