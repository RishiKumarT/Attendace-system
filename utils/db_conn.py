from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import Base

#connection to the database
# MySQL connection - update username and password if needed
DATABASE_URL = "mysql+pymysql://root:Rishimysql%40134@localhost:3306/attendance_db"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)