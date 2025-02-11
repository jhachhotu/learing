from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Configurations
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = datetime.timedelta(days=30)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Email Configuration
EMAIL_ADDRESS = "chhotelalyadav8@gmail.com"
EMAIL_PASSWORD = "loaa qasj bpdk gjwd"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6))
    refresh_token = db.Column(db.String(300))

def send_otp_email(to_email, otp):
    try:
        print(f"Attempting to send OTP {otp} to {to_email}")  # Debug log
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = "Your Verification Code"
        
        body = f"""
        Hi there!
        
        Your verification code is: {otp}
        
        Please use this code to verify your account.
        
        Thanks!
        """
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail
        print("Connecting to Gmail...")  # Debug log
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Login
        print("Attempting login...")  # Debug log
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("Login successful!")  # Debug log
        
        # Send email
        print("Sending email...")  # Debug log
        server.send_message(msg)
        print("Email sent successfully!")  # Debug log
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"Email Error: {str(e)}")  # Debug log
        return False

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        print(f"Signup attempt for {email}")  # Debug log
        
        # Validate input
        if not all([email, password, full_name]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Generate OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        print(f"Generated OTP: {otp}")  # Debug log
        
        # Try to send OTP first
        if send_otp_email(email, otp):
            # Create new user
            user = User(
                full_name=full_name,
                email=email,
                password=generate_password_hash(password),
                otp=otp,
                is_verified=False
            )
            
            db.session.add(user)
            db.session.commit()
            
            return jsonify({
                'message': 'Please check your email for verification code',
                'email': email
            }), 200
        else:
            return jsonify({'error': 'Failed to send verification email'}), 500
            
    except Exception as e:
        print(f"Signup Error: {str(e)}")  # Debug log
        return jsonify({'error': str(e)}), 500

# Test route for email
@app.route('/test-email')
def test_email():
    try:
        test_otp = "123456"
        result = send_otp_email(EMAIL_ADDRESS, test_otp)
        
        if result:
            return jsonify({
                'message': 'Test email sent successfully!',
                'otp': test_otp
            }), 200
        else:
            return jsonify({'error': 'Failed to send test email'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

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

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid password'}), 401
            
        if not user.is_verified:
            return jsonify({'error': 'Please verify your email first'}), 401
            
        # Create tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'full_name': user.full_name,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        print(f"Login Error: {str(e)}")  # Debug log
        return jsonify({'error': 'An error occurred during login'}), 500

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)