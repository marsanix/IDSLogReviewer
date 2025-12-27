"""
Authentication utilities for JWT token management and password hashing.
OWASP Top 10 Compliant:
- A02: Cryptographic Failures - using bcrypt with proper salt
- A07: Auth Failures - secure token handling
"""

import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'change-this-in-production-use-256-bit-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 8

def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt (work factor 12)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def create_token(user_id: int, username: str, role: str) -> str:
    """Create JWT access token."""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict | None:
    """Decode and validate JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def jwt_required(f):
    """Decorator to require valid JWT token for route access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Store user info in Flask's g object for route access
        g.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }
        
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @jwt_required
    def decorated(*args, **kwargs):
        if g.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated
