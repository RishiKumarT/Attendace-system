# create_admin.py
from utils.db_conn import SessionLocal
from db.models import User

db = SessionLocal()
admin = User(username="admin", password="admin123", role="admin")
db.add(admin)
db.commit()
db.close()
print("✅ Admin user created")
