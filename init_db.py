import os
from app import app, db
from models import User, PickupRequest, EWasteItem, ProcessingCenter, CollectionCenter

def init_db():
    with app.app_context():
        try:
            # Drop all tables first (be careful with this in production!)
            db.drop_all()
            print("Dropped all existing tables")
            
            # Create all database tables
            db.create_all()
            print("\nCreated tables:")
            print("----------------")
            print("1. User")
            print("2. PickupRequest")
            print("3. EWasteItem")
            print("4. ProcessingCenter")
            print("5. CollectionCenter")
            
            # Verify tables were created
            print("\nDatabase tables created successfully!")
            print(f"Database location: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Check if database file exists and has content
            db_path = os.path.join(os.path.dirname(__file__), 'e-waste.db')
            if os.path.exists(db_path):
                print(f"\nDatabase file info:")
                print(f"Size: {os.path.getsize(db_path)} bytes")
                print(f"Last modified: {os.path.getmtime(db_path)}")
            else:
                print("\nWARNING: Database file not found!")
                
        except Exception as e:
            print(f"\nError initializing database: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
