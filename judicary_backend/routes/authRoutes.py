import os
import bcrypt
from functools import wraps
from flask import request, jsonify, session
from dotenv import load_dotenv
from models.users import User
from models.auth import Auth
from marshmallow import ValidationError
from datetime import datetime, timedelta
import jwt
from Validations.AuthSchema import AuthSchema
from Validations.LoginSchema import LoginSchema

#load  env variables
load_dotenv()
jwtSecretKey = os.getenv('jwtSecretKey')

def authRoutes(app):
    # Dummy login route for testing - bypasses authentication
    @app.route('/dummy-login', methods=['POST'])
    def dummy_login():
        try:
            # Generate JWT token with expiration time set to 24 hours from now
            expiration_time = datetime.utcnow() + timedelta(hours=24)
            token_payload = {
                'sub': 'dummy_user_id',
                'email': 'test@example.com',
                'exp': expiration_time
            }
            token = jwt.encode(token_payload, jwtSecretKey, algorithm='HS256')
            
            # Dummy user profile data
            user_profile_data = {
                'auth_id': 'dummy_auth_id',
                'user_id': 'dummy_user_id',
                'firstName': 'Test',
                'lastName': 'User',
                'email': 'test@example.com',
                'gender': 'Male',
                'phone_number': '1234567890',
                'cnic_number': '12345-1234567-1',
                'organization': 'Test Organization',
                'ntn_number': '0',
                'country': 'Pakistan',
                'province': 'Punjab',
                'city': 'Lahore',
                'address': '123 Test Street',
                'subscription': 'premium'
            }
            
            response_data = {
                'message': 'Logged in successfully (DUMMY)!',
                'token': token,
                'user_profile': user_profile_data
            }
            return jsonify(response_data), 200
        except Exception as e:
            return jsonify({'error': str(e), 'status_code': 500}), 500

    @app.route('/login', methods=['POST'])
    def login():
        try:
            data = request.json
            schema = LoginSchema()
            email = data.get('email')
            password = data.get('password')
            
            try:
                validated_data = schema.load(data)
            except ValidationError as err:
                return jsonify({'error': err.messages}), 400

            # Retrieve user from the database based on the provided email
            auth_user = Auth.objects(email=email).first()

            # Check if user exists and verify the password
            if auth_user and bcrypt.checkpw(password.encode('utf-8'), auth_user.password.encode('utf-8')):
                # Retrieve the associated user profile from the User collection
                user_profile = User.objects(auth_id=auth_user.id).first()

                # Generate JWT token with expiration time set to 24 hours from now
                expiration_time = datetime.utcnow() + timedelta(hours=24)
                token_payload = {
                    'sub': str(auth_user.id),  # Include the subject (user identifier) in the payload
                    'email': email,
                    'exp': expiration_time
                }
                token = jwt.encode(token_payload, jwtSecretKey, algorithm='HS256')
                
                # Include both auth_id and profile_id inside user_profile object
                user_profile_data = user_profile.to_json() if user_profile else {}
                user_profile_data['auth_id'] = str(auth_user.id) if auth_user else None
                user_profile_data['user_id'] = str(user_profile.id) if user_profile else None
                
                # Construct response containing user profile and token
                response_data = {
                    'message': 'Logged in successfully!',
                    'token': token,
                    'user_profile': user_profile_data
                }
                return jsonify(response_data), 200
            else:
                return jsonify({'error': 'Invalid email or password' , "message" : "Login Failed"}), 401 # Use 401 for unauthorized
        except Exception as e:
            return jsonify({'error': str(e), 'status_code': 500}), 500


    #  No need for a logout route in backend as we are using JWT token for authentication
    # @app.route('/logout' , methods =['GET'])
    # def logout():
    #     try:
    #         session.pop('email', None)
    #         return jsonify({'message': 'Logged out successfully'}), 200
    #     except Exception as e:
    #         return jsonify({'error': str(e), 'status_code': 500}), 500

    @app.route('/register', methods=['POST'])
    def register():
        data = request.json
        register_schema = AuthSchema()
        # user_schema = UserSchema()

        try:
            # Validate incoming data for both Auth and User
            validated_auth_data = register_schema.load(data)
        except ValidationError as err:
            # Return validation errors
            return jsonify({'error': err.messages, 'status_code': 400}), 400

        try:
            # Check if the email is already registered
            if 'email' in validated_auth_data and Auth.objects(email=validated_auth_data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400

            # print("validated", validated_auth_data)
            # Encrypt the password before saving
            password = validated_auth_data.pop('password')  # Remove 'password' from validated_auth_data
            encoded_password = password.encode(encoding='utf-8')
            hashed_password = bcrypt.hashpw(encoded_password, bcrypt.gensalt(15))

            # Create Auth document
            auth = Auth(email=validated_auth_data.get('email'), password=hashed_password)  # Use get() to handle if email is not present
            auth.save()

            # Create User document
            user_data = {'auth_id': auth.id}
            user_fields = ['firstName', 'lastName', 'gender', 'phone_number', 'cnic_number', 'organization',
                        'ntn_number', 'country', 'province', 'city', 'address', 'subscription']
            for field in user_fields:
                if field in validated_auth_data:
                    user_data[field] = validated_auth_data[field]

            # If 'ntn_number' is empty, set it to '0'
            if 'ntn_number' in user_data and not user_data['ntn_number']:
                user_data['ntn_number'] = '0'

            user = User(**user_data)
            user.save()

            return jsonify({'message': 'User registered successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e), 'status_code': 500}), 500

    
    @app.route('/authenticate', methods=['GET'])
    @token_required
    def authenticate():
        # Access the current user from the request context
        current_user = request.current_user
        return jsonify({'message': 'Token is valid', 'current_user_id': str(current_user.id)}), 200

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None

        # Check if the request contains a token in the Authorization header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            # Verify and decode the token
            data = jwt.decode(token, jwtSecretKey, algorithms=['HS256'])
            
            # Handle dummy user for testing
            if data['sub'] == 'dummy_user_id':
                # Create a mock user object for dummy login
                class DummyUser:
                    id = 'dummy_user_id'
                    email = 'test@example.com'
                request.current_user = DummyUser()
                return func(*args, **kwargs)
            
            current_user = Auth.objects(id=data['sub']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        if not current_user:
            return jsonify({'error': 'User not found'}), 401

        # Add the current user to the request context
        request.current_user = current_user
        return func(*args, **kwargs)

    return decorated


   