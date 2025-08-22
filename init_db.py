from app import app, db

def init_db():
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Database tables created successfully!")
        print(f"Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    init_db()
