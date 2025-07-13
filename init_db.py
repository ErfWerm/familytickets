from app import app
from models import db

with app.app_context():
    db.drop_all()   # remove old tables/schema
    db.create_all() # recreate based on current models
    print("✅ Dropped and recreated all tables (tickets.db updated).")
