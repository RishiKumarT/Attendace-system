import streamlit as st
from utils.db_conn import SessionLocal
from db.models import User

st.set_page_config(page_title="Attendance System", layout="centered")

def add_custom_css():
    st.markdown("""
        <style>
        .title-text {
            font-size: 3.5rem !important;
            font-weight: 800;
            color: #0f172a;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .subtitle-text {
            font-size: 1.2rem;
            color: #64748b;
            text-align: center;
            margin-bottom: 3rem;
        }
        /* Custom stylings to ensure a modern look */
        div.stButton > button:first-child {
            border-radius: 8px;
            font-weight: bold;
            padding: 0.5rem 1rem;
        }
        div[data-testid="stTextInput"] input {
            border-radius: 8px;
            border: 1px solid #cbd5e1;
        }
        </style>
    """, unsafe_allow_html=True)

def login():
    st.markdown("<div class='title-text'>Attendance System</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle-text'>Welcome to the modern attendance management portal. Please securely log in below.</div>", unsafe_allow_html=True)
    
    # Using layout columns to center the login container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Create a visual container using standard streamlit elements
        st.markdown("### Login")
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        st.write("") # Add spacing
        submit_button = st.button("Log In", use_container_width=True, type="primary")

        if submit_button:
            db = SessionLocal()
            user = db.query(User).filter(User.username==username, User.password==password).first()
            db.close()
            if user:
                st.session_state["user"] = {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                }
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")

def main():
    add_custom_css()
    
    if "user" not in st.session_state:
        login()
    else:
        role = st.session_state["user"]["role"]
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