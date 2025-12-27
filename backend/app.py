from flask import Flask, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from log_parser import LogParser
from auth import hash_password, verify_password, create_token, jwt_required, admin_required
import os
import threading
import time
import json
from datetime import datetime

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e,  Exception) and hasattr(e, 'code'):
          return jsonify(error=str(e)), e.code
    return jsonify(error=str(e)), 500

# Database Configuration
# Use environment variables for flexible configuration
DB_USER = os.environ.get('DB_USER', 'ids_user')
DB_PASS = os.environ.get('DB_PASS', 'ids_password')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3308')
DB_NAME = os.environ.get('DB_NAME', 'ids_logs')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Log Model
class LogEntry(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, index=True)
    event_type = db.Column(db.String(50))
    src_ip = db.Column(db.String(50))
    dest_ip = db.Column(db.String(50))
    src_port = db.Column(db.Integer)
    dest_port = db.Column(db.Integer)
    protocol = db.Column(db.String(20))
    signature = db.Column(db.String(255))
    severity = db.Column(db.Integer)
    payload = db.Column(db.Text) # Store full JSON payload if needed

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'src_ip': self.src_ip,
            'dest_ip': self.dest_ip,
            'src_port': self.src_port,
            'dest_port': self.dest_port,
            'protocol': self.protocol,
            'signature': self.signature,
            'severity': self.severity,
            'payload': self.payload  # Full original JSON from eve.json
        }


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='viewer')  # 'admin' or 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Activity Log Model
class ActivityLog(db.Model):
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(80))
    action = db.Column(db.String(100), nullable=False)  # e.g., 'login', 'view_logs', 'logout'
    page = db.Column(db.String(50))  # e.g., 'dashboard', 'live_logs', 'history'
    details = db.Column(db.Text)  # Additional JSON details
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'page': self.page,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


# Global parser for live view (keeping existing functionality)
# Global parser for live view (keeping existing functionality)
# In Docker, logs are mounted at /app/logs
LOG_FILE = os.environ.get('LOG_FILE', "logs/eve.json")
RULES_FILE = "nmap.rules"
parser = LogParser(LOG_FILE)

# Background Log Watcher
class LogWatcher(threading.Thread):
    def __init__(self, log_file, app):
        super().__init__()
        self.log_file = log_file
        self.app = app
        self.daemon = True
        self.running = True

    def run(self):
        # Wait for file to exist
        while not os.path.exists(self.log_file):
            time.sleep(1)
        
        # Open file and seek to end initially
        f = open(self.log_file, 'r')
        f.seek(0, 2) # Go to end

        while self.running:
            line = f.readline()
            if line:
                try:
                    data = json.loads(line)
                    self.process_log(data)
                except Exception as e:
                    print(f"Error processing log: {e}")
            else:
                time.sleep(0.1)

    def process_log(self, data):
        with self.app.app_context():
            # Extract fields safely
            timestamp_str = data.get('timestamp')
            timestamp = None
            if timestamp_str:
                try:
                    # ISO format handling might need adjustment depending on eve.json precision
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    timestamp = datetime.now()

            event_type = data.get('event_type')
            src_ip = data.get('src_ip')
            dest_ip = data.get('dest_ip')
            src_port = data.get('src_port')
            dest_port = data.get('dest_port')
            proto = data.get('proto')
            
            signature = "N/A"
            severity = 0
            
            if 'alert' in data:
                signature = data['alert'].get('signature', 'Unknown')
                severity = data['alert'].get('severity', 3) # Default to low severity if missing
                
 

            entry = LogEntry(
                timestamp=timestamp,
                event_type=event_type,
                src_ip=src_ip,
                dest_ip=dest_ip,
                src_port=src_port,
                dest_port=dest_port,
                protocol=proto,
                signature=signature,
                severity=severity,
                payload=json.dumps(data)
            )
            db.session.add(entry)
            db.session.commit()



# Initialize DB and Watcher
def init_app():
    with app.app_context():
        # Create tables if they don't exist
        try:
            db.create_all()
            
            # Create default admin user if none exists
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
            
            existing_admin = User.query.filter_by(username=admin_username).first()
            if not existing_admin:
                admin_user = User(
                    username=admin_username,
                    password_hash=hash_password(admin_password),
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print(f"Created admin user: {admin_username}")

        except Exception as e:
            print(f"DB Connection failed: {e}")
            
    # Start watcher
    watcher = LogWatcher(LOG_FILE, app)
    watcher.start()

# Routes
@app.route('/')
def index():
    return jsonify({
        "name": "IDS Log Viewer API",
        "status": "running",
        "endpoints": [
            "/api/stats",
            "/api/signatures",
            "/api/history",
            "/api/logs"
        ]
    })

from sqlalchemy import func


# Helper function to log activity
def log_activity(action: str, page: str = None, details: str = None):
    """Log user activity to the database."""
    try:
        user_id = g.current_user.get('user_id') if hasattr(g, 'current_user') else None
        username = g.current_user.get('username') if hasattr(g, 'current_user') else 'anonymous'
        ip_address = request.remote_addr
        
        activity = ActivityLog(
            user_id=user_id,
            username=username,
            action=action,
            page=page,
            details=details,
            ip_address=ip_address
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Failed to log activity: {e}")


# Auth Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not verify_password(password, user.password_hash):
        log_activity('login_failed', details=f'username: {username}')
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = create_token(user.id, user.username, user.role)
    log_activity('login', details=f'user: {username}')
    
    return jsonify({
        'token': token,
        'user': user.to_dict()
    })


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required
def logout():
    log_activity('logout')
    return jsonify({'message': 'Logged out successfully'})


@app.route('/api/auth/me')
@jwt_required
def get_current_user():
    user = User.query.get(g.current_user['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict()})


# User Management Routes (admin only)
@app.route('/api/users', methods=['GET'])
@jwt_required
def get_users():
    if g.current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    users = User.query.all()
    return jsonify({'users': [u.to_dict() for u in users]})


@app.route('/api/users', methods=['POST'])
@jwt_required
def create_user():
    if g.current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'viewer')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()
    
    log_activity('create_user', details=f'created: {username}')
    return jsonify({'user': user.to_dict()}), 201


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required
def delete_user(user_id):
    if g.current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.id == g.current_user['user_id']:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    log_activity('delete_user', details=f'deleted: {username}')
    return jsonify({'message': 'User deleted'})


# Activity Log Route (admin only)
@app.route('/api/activity')
@jwt_required
def get_activity_logs():
    if g.current_user.get('role') != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    limit = request.args.get('limit', 100, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    return jsonify({'activities': [l.to_dict() for l in logs]})


@app.route('/api/stats')
def get_stats():
    # DB-based stats
    total_alerts = LogEntry.query.count()
    severity_high = LogEntry.query.filter_by(severity=1).count()
    severity_medium = LogEntry.query.filter_by(severity=2).count()
    severity_low = LogEntry.query.filter_by(severity=3).count()
    
    # Top signatures
    top_sigs_query = db.session.query(LogEntry.signature, func.count(LogEntry.id))\
        .group_by(LogEntry.signature)\
        .order_by(func.count(LogEntry.id).desc())\
        .limit(5)\
        .all()
    
    top_signatures = {sig: count for sig, count in top_sigs_query}

    return jsonify({
        'total_alerts': total_alerts,
        'severity_high': severity_high,
        'severity_medium': severity_medium,
        'severity_low': severity_low,
        'top_signatures': top_signatures
    })

@app.route('/api/signatures')
def get_signatures():
    signatures = db.session.query(LogEntry.signature).distinct().order_by(LogEntry.signature).all()
    # Flatten list of tuples [(sig,), (sig2,)] -> [sig, sig2]
    return jsonify([sig[0] for sig in signatures if sig[0] and sig[0] not in [None, 'N/A', 'Unknown']])

@app.route('/api/logs')
def get_logs():
    # Live logs from DB (last 50)
    # This is much faster than reading the file
    logs = LogEntry.query.order_by(LogEntry.timestamp.desc()).limit(50).all()
    return jsonify([log.to_dict() for log in logs])

@app.route('/api/history')
def get_history():
    query = LogEntry.query.order_by(LogEntry.timestamp.desc())

    # Filtering
    # 1. Exact signature match (Dropdown)
    sig_filter = request.args.get('signature')
    if sig_filter:
        query = query.filter(LogEntry.signature == sig_filter)

    # 2. General search (Input) - checks signature OR IPs
    search_query = request.args.get('search')
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            db.or_(
                LogEntry.signature.like(search),
                LogEntry.src_ip.like(search),
                LogEntry.dest_ip.like(search)
            )
        )
    
    # 3. Specific IP filters
    src_ip_filter = request.args.get('src_ip')
    if src_ip_filter:
        query = query.filter(LogEntry.src_ip.like(f"%{src_ip_filter}%"))
    
    dest_ip_filter = request.args.get('dest_ip')
    if dest_ip_filter:
        query = query.filter(LogEntry.dest_ip.like(f"%{dest_ip_filter}%"))
    
    
    severity = request.args.get('severity')
    if severity == 'high':
        # Assuming High is 1 (Suricata usually 1=High, 2=Medium, 3=Low)
        query = query.filter(LogEntry.severity == 1)

    # Date Range Filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        try:
            # Append start of day time if only date provided, or handle full ISO
            # Assuming input YYYY-MM-DD from HTML date input
            query = query.filter(LogEntry.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        except ValueError:
            pass # Ignore invalid dates

    if end_date:
        try:
             # Append end of day time
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.filter(LogEntry.timestamp <= end_dt)
        except ValueError:
            pass

    limit = request.args.get('limit', 20, type=int) # Default to 20 per page
    page = request.args.get('page', 1, type=int)
    
    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'meta': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })

@app.route('/api/settings/clear', methods=['POST'])
def clear_db():
    try:
        db.session.query(LogEntry).delete()
        db.session.commit()
        return jsonify({"status": "success", "message": "Database cleared"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Initialize app (DB creation, watcher)
    # We do this in main to avoid issues with specialized runners, though for local python it's fine
    try:
        init_app()
    except Exception as e:
        print(f"Failed to init app: {e}")
        
    app.run(debug=True, host='0.0.0.0', port=5000)
