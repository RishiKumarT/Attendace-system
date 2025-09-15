# from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
# from sqlalchemy.orm import relationship, declarative_base
# from datetime import datetime
#
# Base = declarative_base()
#
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, nullable=False)
#     password = Column(String, nullable=False)   # plain text
#     role = Column(String, nullable=False)       # "admin" / "faculty" / "student"
#
# class Student(Base):
#     __tablename__ = "students"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     roll_no = Column(String, unique=True, nullable=False)
#     class_name = Column(String, nullable=False)
#     username = Column(String, unique=True, nullable=False)
#     password = Column(String, nullable=False)
#     images_path = Column(Text, nullable=True)
#
#     attendance_records = relationship("AttendanceRecord", back_populates="student")
#
# class AttendanceSession(Base):
#     __tablename__ = "attendance_sessions"
#     id = Column(Integer, primary_key=True, index=True)
#     session_name = Column(String, nullable=False)
#     class_name = Column(String, nullable=False)
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     csv_path = Column(Text, nullable=True)
#
#     records = relationship("AttendanceRecord", back_populates="session")
#
# class AttendanceRecord(Base):
#     __tablename__ = "attendance_records"
#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(Integer, ForeignKey("attendance_sessions.id"))
#     student_id = Column(Integer, ForeignKey("students.id"))
#     status = Column(String, default="Absent")
#
#     session = relationship("AttendanceSession", back_populates="records")
#     student = relationship("Student", back_populates="attendance_records")
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# -----------------------
# USERS (Admin/Faculty/Student)
# -----------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)   # plain text for now
    role = Column(String, nullable=False)       # "admin" / "faculty" / "student"

    student = relationship("Student", back_populates="user", uselist=False)  # 1:1 link if role=student

# -----------------------
# STUDENTS
# -----------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_no = Column(String, unique=True, nullable=False)
    class_name = Column(String, nullable=False)
    images_path = Column(Text, nullable=True)   # folder where images are stored

    user_id = Column(Integer, ForeignKey("users.id"))  # link to User for login
    user = relationship("User", back_populates="student")

    attendance_records = relationship("AttendanceRecord", back_populates="student")

# -----------------------
# ATTENDANCE SESSIONS
# -----------------------
class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    csv_path = Column(Text, nullable=True)     # CSV path for this session

    records = relationship("AttendanceRecord", back_populates="session")

# -----------------------
# ATTENDANCE RECORDS
# -----------------------
class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    status = Column(String, default="Absent")

    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("Student", back_populates="attendance_records")
