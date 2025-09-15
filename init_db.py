# init_db.py
from db.models import Base
from utils.db_conn import engine, create_tables

create_tables()
print("✅ Tables created successfully")
