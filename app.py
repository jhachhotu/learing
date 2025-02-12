from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.exc import SQLAlchemyError
import traceback
from sqlalchemy import text
import os
from dotenv import load_dotenv
from config import MAIL_SETTINGS
import ssl
from flask_mail import Mail, Message
from datetime import timedelta

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)
app.config.update(MAIL_SETTINGS)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
mail = Mail(app)

# Email Configuration - use only these settings
EMAIL_ADDRESS = "chhotusimaria@gmail.com"
EMAIL_PASSWORD = "loaa qasj bpdk gjwd"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)

class PickupRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pickup_date = db.Column(db.DateTime, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    collection_center_id = db.Column(db.Integer, db.ForeignKey('collection_center.id'))
    items = db.relationship('EWasteItem', backref='pickup_request', lazy=True)
    
    # Relationship with user
    user = db.relationship('User', backref='pickup_requests')

class EWasteItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pickup_request_id = db.Column(db.Integer, db.ForeignKey('pickup_request.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    weight = db.Column(db.Float)
    
class ProcessingCenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

class CollectionCenter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    contact_number = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    capacity = db.Column(db.Integer)  # in kg
    waste_types = db.Column(db.String(500))  # Comma-separated list of accepted waste types
    operating_hours = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    pickup_requests = db.relationship('PickupRequest', backref='collection_center', lazy=True)

def send_otp_email(to_email, otp):
    try:
        # Setup the MIME
        message = MIMEMultipart()
        message['From'] = EMAIL_ADDRESS
        message['To'] = to_email
        message['Subject'] = "Your E-Waste Management Verification Code"

        # Create the body of the message
        body = f"""
        Hello!

        Thank you for registering with E-Waste Management.
        Your verification code is: {otp}

        Please enter this code to verify your account.
        This code will expire in 10 minutes.

        Best regards,
        E-Waste Management Team
        """
        
        # Add body to email
        message.attach(MIMEText(body, 'plain'))

        # Create secure SSL context
        context = ssl.create_default_context()

        # Try to log in to server and send email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            
            # Print debug info
            print(f"Attempting to login with email: {EMAIL_ADDRESS}")
            
            # Login to the server
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            
            # Convert the message to string and send
            text = message.as_string()
            server.sendmail(EMAIL_ADDRESS, to_email, text)
            
            print(f"Successfully sent email to {to_email}")
            return True

    except Exception as e:
        print(f"Failed to send email. Error: {str(e)}")
        return False

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Generate OTP
        otp = ''.join(random.choices('0123456789', k=6))
        
        # Try to send email first
        if not send_otp_email(data['email'], otp):
            return jsonify({'error': 'Failed to send verification email. Please try again.'}), 500
        
        # Create new user only if email was sent successfully
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            full_name=data['full_name'],
            email=data['email'],
            password=hashed_password,
            otp=otp
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful! Please check your email for verification code.',
            'email': data['email']
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Signup Error: {str(e)}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password, data['password']):
            if not user.is_verified:
                return jsonify({'error': 'Please verify your email first'}), 401
                
            # Create access token with user ID
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(days=1)
            )
            
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/login')
def login_page():
    return render_template('login.html', 
                         redirect=request.args.get('redirect'),
                         feature=request.args.get('feature'))

@app.route('/verify-otp')
def verify_otp_page():
    return render_template('verify_otp.html')

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if user.otp != data['otp']:
            return jsonify({'error': 'Invalid OTP'}), 400
            
        user.is_verified = True
        user.otp = None
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Email verified successfully',
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        current_user_id = get_jwt_identity()
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        return jsonify({
            'message': f'Hello {user.full_name}!',
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/check-auth')
@jwt_required()
def check_auth():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
        }), 200
    except Exception as e:
        print(f"Auth check error: {str(e)}")  # Debug log
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 401

@app.route('/api/pickup-request', methods=['POST'])
@jwt_required()
def create_pickup_request():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # Find nearest collection center based on pincode
        user_pincode = data.get('pincode')
        collection_center = CollectionCenter.query.filter_by(
            pincode=user_pincode, 
            is_active=True
        ).first()

        if not collection_center:
            # If no center in same pincode, get any active center
            collection_center = CollectionCenter.query.filter_by(is_active=True).first()

        if not collection_center:
            return jsonify({'error': 'No collection centers available'}), 400

        new_request = PickupRequest(
            user_id=current_user_id,
            pickup_date=datetime.datetime.fromisoformat(data['pickup_date'].replace('Z', '+00:00')),
            address=data['address'],
            status='pending',
            collection_center_id=collection_center.id
        )

        # Add items
        for item_data in data['items']:
            item = EWasteItem(
                type=item_data['type'],
                quantity=int(item_data['quantity']),
                description=item_data['description'],
                weight=float(item_data['weight'])
            )
            new_request.items.append(item)

        db.session.add(new_request)
        db.session.commit()

        return jsonify({
            'message': 'Pickup scheduled successfully',
            'request_id': new_request.id,
            'collection_center': {
                'name': collection_center.name,
                'address': collection_center.address,
                'contact': collection_center.contact_number
            }
        }), 201

    except Exception as e:
        print(f"Error creating pickup request: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/pickup-requests', methods=['GET'])
@jwt_required()
def get_pickup_requests():
    try:
        current_user_id = get_jwt_identity()
        requests = PickupRequest.query.filter_by(user_id=current_user_id).all()
        
        return jsonify({
            'requests': [{
                'id': req.id,
                'pickup_date': req.pickup_date.isoformat(),
                'address': req.address,
                'status': req.status,
                'items': [{
                    'type': item.type,
                    'quantity': item.quantity,
                    'description': item.description,
                    'weight': item.weight
                } for item in req.items]
            } for req in requests]
        }), 200
        
    except Exception as e:
        print(f"Error fetching requests: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/processing-centers', methods=['GET'])
def get_processing_centers():
    try:
        centers = ProcessingCenter.query.all()
        return jsonify({
            'centers': [{
                'id': center.id,
                'name': center.name,
                'address': center.address,
                'contact': center.contact,
                'latitude': center.latitude,
                'longitude': center.longitude
            } for center in centers]
        }), 200
        
    except Exception as e:
        print(f"Error fetching processing centers: {str(e)}")
        return jsonify({'error': 'Failed to fetch processing centers'}), 500

@app.route('/api/pickup-request/<int:request_id>/track', methods=['GET'])
@jwt_required()
def track_pickup_request(request_id):
    try:
        current_user_id = get_jwt_identity()
        request = PickupRequest.query.filter_by(
            id=request_id, 
            user_id=current_user_id
        ).first()
        
        if not request:
            return jsonify({'error': 'Pickup request not found'}), 404
            
        return jsonify({
            'id': request.id,
            'status': request.status,
            'pickup_date': request.pickup_date.strftime('%Y-%m-%d %H:%M'),
            'address': request.address,
            'items': [{
                'type': item.type,
                'quantity': item.quantity,
                'description': item.description,
                'weight': item.weight
            } for item in request.items]
        }), 200
        
    except Exception as e:
        print(f"Error tracking pickup request: {str(e)}")
        return jsonify({'error': 'Failed to track pickup request'}), 500

@app.route('/api/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # Create new access token
        access_token = create_access_token(identity=current_user_id)
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        print(f"Token Refresh Error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

# Add a function to check database connection
def check_db_connection():
    try:
        # Use a simple database query
        db.session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False

# Add route to check system status
@app.route('/api/system-status')
def system_status():
    try:
        db_connected = check_db_connection()
        return jsonify({
            'status': 'healthy' if db_connected else 'database_error',
            'database_connected': db_connected,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        print(f"Error checking system status: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/debug/db-schema')
def debug_db_schema():
    try:
        # Get table information
        table_info = {}
        for table in db.metadata.tables.values():
            columns = []
            for column in table.columns:
                columns.append({
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable
                })
            table_info[table.name] = columns
            
        return jsonify({
            'status': 'success',
            'schema': table_info
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Add this route temporarily for testing
@app.route('/test-email')
def test_email():
    result = send_otp_email("rahul21993@gmail.com", "123456")
    return jsonify({
        'success': result,
        'message': 'Email test completed'
    })

# Add route to manage collection centers
@app.route('/api/collection-centers', methods=['GET', 'POST'])
@jwt_required()
def collection_centers():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            new_center = CollectionCenter(
                name=data['name'],
                address=data['address'],
                city=data['city'],
                state=data['state'],
                pincode=data['pincode'],
                contact_number=data['contact_number'],
                email=data['email'],
                capacity=data['capacity'],
                waste_types=','.join(data['waste_types']),
                operating_hours=data['operating_hours']
            )
            
            db.session.add(new_center)
            db.session.commit()
            
            return jsonify({
                'message': 'Collection center added successfully',
                'center_id': new_center.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    # GET method
    centers = CollectionCenter.query.filter_by(is_active=True).all()
    return jsonify({
        'centers': [{
            'id': center.id,
            'name': center.name,
            'address': center.address,
            'city': center.city,
            'state': center.state,
            'pincode': center.pincode,
            'contact_number': center.contact_number,
            'email': center.email,
            'capacity': center.capacity,
            'waste_types': center.waste_types.split(','),
            'operating_hours': center.operating_hours
        } for center in centers]
    }), 200

@app.route('/collection-centers')
def collection_centers_page():
    return render_template('collection_centers.html')

@app.route('/api/collection-center/<int:center_id>/requests')
@jwt_required()
def center_requests(center_id):
    try:
        center = CollectionCenter.query.get_or_404(center_id)
        requests = PickupRequest.query.filter_by(collection_center_id=center_id).all()
        
        return jsonify({
            'center': {
                'name': center.name,
                'address': center.address
            },
            'requests': [{
                'id': req.id,
                'pickup_date': req.pickup_date.isoformat(),
                'address': req.address,
                'status': req.status,
                'items': [{
                    'type': item.type,
                    'quantity': item.quantity,
                    'weight': item.weight
                } for item in req.items]
            } for req in requests]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)