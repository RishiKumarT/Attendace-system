import streamlit as st
from utils.db_conn import SessionLocal
from db.models import User

def login():
    st.title("Attendance System Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        db = SessionLocal()
        user = db.query(User).filter(User.username==username, User.password==password).first()
        db.close()
        if user:
            st.session_state["user"] = {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
            st.success(f"Logged in as {user.role}")
        else:
            st.error("Invalid credentials")

def main():
    if "user" not in st.session_state:
        login()
    else:
        role = st.session_state["user"]["role"]
        st.sidebar.write(f"Logged in as {st.session_state['user']['username']} ({role})")
        st.sidebar.button("Logout", on_click=lambda: st.session_state.pop("user"))

        if role == "admin":
            import pages.admin_dashboard as admin_page
            admin_page.main()
        elif role == "faculty":
            import pages.faculty_dashboard as faculty_page
            faculty_page.main()
        elif role == "student":
            import pages.student_dashboard as student_page
            student_page.main()
        else:
            st.error("Unknown role")

if __name__ == "__main__":
    main()

# streamlin run app.py