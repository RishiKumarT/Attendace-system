from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base

#connection to the database
#DATABASE_URL = "postgresql+psycopg2://postgres:Mohit@005@localhost:5432/attendance_db"
DATABASE_URL = "postgresql+psycopg2://postgres:Mohit%40005@localhost:5432/attendance_db"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)