"""Authentication routes – register, login, profile, token refresh."""

import os
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
import jwt as pyjwt
from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate, ValidationError

from models.auth_model import Auth
from models.user_model import User

auth_bp = Blueprint("auth", __name__)

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
JWT_EXPIRY_HOURS = 24


# ---------- Validation schemas ----------

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    gender = fields.Str(validate=validate.OneOf(["male", "female", "other"]))
    phone_number = fields.Str(validate=validate.Length(max=20))
    cnic_number = fields.Str(validate=validate.Length(max=20))
    organization = fields.Str(validate=validate.Length(max=200))
    country = fields.Str(validate=validate.Length(max=100))
    province = fields.Str(validate=validate.Length(max=100))
    city = fields.Str(validate=validate.Length(max=100))
    address = fields.Str(validate=validate.Length(max=500))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)


# ---------- Token helpers ----------

def create_token(auth):
    """Generate a JWT for the given Auth document."""
    payload = {
        "sub": str(auth.id),
        "email": auth.email,
        "role": auth.role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


def token_required(f):
    """Decorator that validates the Bearer token and sets g.current_user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = pyjwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            auth_user = Auth.objects(id=data["sub"]).first()
            if not auth_user:
                return jsonify({"error": "User not found"}), 401
            g.current_user = auth_user
        except pyjwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except pyjwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """Decorator that requires admin role."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)

    return decorated


# ---------- Routes ----------

@auth_bp.route("/register", methods=["POST"])
def register():
    schema = RegisterSchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    if Auth.objects(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    # Hash password
    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt(12)).decode()

    auth = Auth(email=data["email"], password=hashed)
    auth.save()

    # Create user profile
    profile_fields = [
        "first_name", "last_name", "gender", "phone_number",
        "cnic_number", "organization", "country", "province", "city", "address",
    ]
    user_data = {"auth_id": auth.id}
    for field in profile_fields:
        if field in data:
            user_data[field] = data[field]

    user = User(**user_data)
    user.save()

    token = create_token(auth)

    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": user.to_json(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    schema = LoginSchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    auth_user = Auth.objects(email=data["email"]).first()
    if not auth_user or not bcrypt.checkpw(
        data["password"].encode(), auth_user.password.encode()
    ):
        return jsonify({"error": "Invalid email or password"}), 401

    auth_user.last_login = datetime.utcnow()
    auth_user.save()

    user_profile = User.objects(auth_id=auth_user.id).first()
    token = create_token(auth_user)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user_profile.to_json() if user_profile else {"email": auth_user.email},
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_profile():
    user = User.objects(auth_id=g.current_user.id).first()
    return jsonify({
        "auth": g.current_user.to_json_safe(),
        "profile": user.to_json() if user else None,
    }), 200


@auth_bp.route("/me", methods=["PUT"])
@token_required
def update_profile():
    user = User.objects(auth_id=g.current_user.id).first()
    if not user:
        return jsonify({"error": "Profile not found"}), 404

    data = request.json or {}
    allowed = [
        "first_name", "last_name", "gender", "phone_number",
        "organization", "country", "province", "city", "address",
    ]
    for field in allowed:
        if field in data:
            setattr(user, field, data[field])

    user.updated_at = datetime.utcnow()
    user.save()

    return jsonify({"message": "Profile updated", "user": user.to_json()}), 200
