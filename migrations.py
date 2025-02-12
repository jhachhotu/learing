from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app import app, db

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("Database tables recreated successfully!")