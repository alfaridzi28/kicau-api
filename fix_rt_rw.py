from app.database import SessionLocal
from app.models import User

db = SessionLocal()
users = db.query(User).all()

count = 0
for u in users:
    updated = False
    
    # Standardize RT
    if u.rt and u.rt.isdigit() and len(u.rt) == 1:
        u.rt = u.rt.zfill(2)
        updated = True
        
    # Standardize RW
    if u.rw and u.rw.isdigit() and len(u.rw) == 1:
        u.rw = u.rw.zfill(2)
        updated = True
        
    # Assign RT/RW to Lurah and Staff if missing
    if u.role in ["lurah", "staff", "superadmin"]:
        if not u.rt:
            u.rt = "01"
            updated = True
        if not u.rw:
            u.rw = "19"
            updated = True
            
    if updated:
        count += 1

db.commit()
db.close()
print(f"Updated {count} users.")
