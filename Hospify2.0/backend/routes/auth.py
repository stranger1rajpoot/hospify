from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from extensions import db
from models import User, Role, Hospital, AuditLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def log_action(user_id, hospital_id, action, module, record_id=None):
    try:
        log = AuditLog(
            user_id=user_id, hospital_id=hospital_id,
            action=action, module=module, record_id=record_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(log)
        db.session.commit()
    except:
        pass


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    username_or_email = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username_or_email or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'success': False, 'message': 'Account is deactivated'}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    additional_claims = {
        'role': user.role.name,
        'hospital_id': user.hospital_id,
        'user_id': user.id
    }

    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user.id))

    log_action(user.id, user.hospital_id, 'LOGIN', 'auth')

    return jsonify({
        'success': True,
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400

    required = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 409

    role = Role.query.filter_by(name=data['role']).first()
    if not role:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    # Only allow patient self-registration; others need admin
    if role.name not in ['patient']:
        return jsonify({'success': False, 'message': 'Self-registration only allowed for patients'}), 403

    hospital = None
    if data.get('hospital_id'):
        hospital = Hospital.query.get(data['hospital_id'])
        if not hospital or hospital.status != 'active':
            return jsonify({'success': False, 'message': 'Invalid or inactive hospital'}), 400

    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        gender=data.get('gender'),
        role_id=role.id,
        hospital_id=hospital.id if hospital else None,
        is_active=True,
        is_verified=False
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({'success': False, 'message': 'User not found or inactive'}), 404

    additional_claims = {
        'role': user.role.name,
        'hospital_id': user.hospital_id,
        'user_id': user.id
    }
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    return jsonify({'success': True, 'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify({'success': True, 'user': user.to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user:
        log_action(user.id, user.hospital_id, 'LOGOUT', 'auth')
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()

    if not user.check_password(data.get('current_password', '')):
        return jsonify({'success': False, 'message': 'Current password incorrect'}), 400

    if len(data.get('new_password', '')) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

    user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
