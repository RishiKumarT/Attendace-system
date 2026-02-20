from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# -----------------------
# USERS
# -----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)

    student = relationship("Student", back_populates="user", uselist=False)


# -----------------------
# STUDENTS
# -----------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    roll_no = Column(String(50), unique=True, nullable=False)
    class_name = Column(String(50), nullable=False)
    images_path = Column(Text, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="student")

    attendance_records = relationship("AttendanceRecord", back_populates="student")


# -----------------------
# ATTENDANCE SESSIONS
# -----------------------
class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(100), nullable=False)
    class_name = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    csv_path = Column(Text, nullable=True)

    records = relationship("AttendanceRecord", back_populates="session")


# -----------------------
# ATTENDANCE RECORDS
# -----------------------
class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    status = Column(String(20), default="Absent")

    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("Student", back_populates="attendance_records")