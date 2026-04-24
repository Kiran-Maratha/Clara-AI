import os
from werkzeug.security import generate_password_hash
from app import create_app
from models import db, Admin
import sqlite3

app = create_app()

with app.app_context():
    # create_all will create the new Admin table if it doesn't exist
    db.create_all()

    # We need to manually add the 'feedback' column to the 'message' table via sqlite raw
    # since create_all() won't alter existing tables.
    db_path = os.path.join(app.instance_path, 'claraai.db')
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE message ADD COLUMN feedback INTEGER")
            conn.commit()
            print("Successfully added 'feedback' column to 'message' table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("Column 'feedback' already exists.")
            else:
                print(f"Error altering table: {e}")
        finally:
            conn.close()
    else:
        print(f"Database not found at {db_path}. Assuming fresh create_all.")

    # Create the root admin user
    master_email = os.getenv("ADMIN_EMAIL")
    master_password = os.getenv("ADMIN_PASSWORD")
    
    existing = Admin.query.filter_by(email=master_email).first()
    
    if not existing:
        admin = Admin(email=master_email, password=generate_password_hash(master_password))
        db.session.add(admin)
        db.session.commit()
        print(f"Created primary admin: {master_email}")
    else:
        print(f"Admin {master_email} already exists.")
