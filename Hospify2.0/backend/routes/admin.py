from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Hospital, User, Role, Department, Doctor, Patient, Appointment, Invoice, AuditLog
from datetime import datetime, date
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)


def require_role(*roles):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') not in roles:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ─── SUPER ADMIN ──────────────────────────────────

@admin_bp.route('/hospitals', methods=['GET'])
@jwt_required()
@require_role('super_admin')
def get_hospitals():
    hospitals = Hospital.query.all()
    return jsonify({'success': True, 'hospitals': [h.to_dict() for h in hospitals]}), 200


@admin_bp.route('/hospitals', methods=['POST'])
@jwt_required()
@require_role('super_admin')
def create_hospital():
    data = request.get_json()
    required = ['name', 'code']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'}), 400

    if Hospital.query.filter_by(code=data['code']).first():
        return jsonify({'success': False, 'message': 'Hospital code already exists'}), 409

    hospital = Hospital(
        name=data['name'], code=data['code'],
        address=data.get('address'), city=data.get('city'),
        province=data.get('province'), phone=data.get('phone'),
        email=data.get('email'), type=data.get('type', 'medium'),
        subscription_plan=data.get('subscription_plan', 'standard'),
        tax_no=data.get('tax_no')
    )
    db.session.add(hospital)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Hospital created', 'hospital': hospital.to_dict()}), 201


@admin_bp.route('/hospitals/<int:hospital_id>', methods=['GET'])
@jwt_required()
@require_role('super_admin')
def get_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    users = User.query.filter_by(hospital_id=hospital_id).all()
    departments = Department.query.filter_by(hospital_id=hospital_id).all()
    return jsonify({
        'success': True,
        'hospital': hospital.to_dict(),
        'users': [u.to_dict() for u in users],
        'departments': [d.to_dict() for d in departments],
        'stats': {
            'total_users': len(users),
            'total_departments': len(departments),
            'total_doctors': sum(1 for u in users if u.role and u.role.name == 'doctor'),
        }
    }), 200


@admin_bp.route('/hospitals/<int:hospital_id>', methods=['PUT'])
@jwt_required()
@require_role('super_admin')
def update_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    data = request.get_json()
    updatable = ['name','address','city','province','phone','email','type','status','subscription_plan','tax_no']
    for field in updatable:
        if field in data:
            setattr(hospital, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Hospital updated', 'hospital': hospital.to_dict()}), 200


@admin_bp.route('/hospitals/<int:hospital_id>', methods=['DELETE'])
@jwt_required()
@require_role('super_admin')
def delete_hospital(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    if hospital.code == 'HQ':
        return jsonify({'success': False, 'message': 'Cannot delete the headquarters hospital'}), 400
    user_count = User.query.filter_by(hospital_id=hospital_id).count()
    if user_count > 0:
        return jsonify({'success': False, 'message': f'Cannot delete: {user_count} user(s) still belong to this hospital. Reassign or delete them first.'}), 400
    name = hospital.name
    db.session.delete(hospital)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Hospital "{name}" deleted'}), 200


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    claims = get_jwt()
    role = claims.get('role')
    hospital_id = claims.get('hospital_id')

    query = User.query
    if role != 'super_admin':
        query = query.filter_by(hospital_id=hospital_id)

    role_filter = request.args.get('role')
    if role_filter:
        role_obj = Role.query.filter_by(name=role_filter).first()
        if role_obj:
            query = query.filter_by(role_id=role_obj.id)

    users = query.all()
    return jsonify({'success': True, 'users': [u.to_dict() for u in users]}), 200


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def create_user():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role_name = claims.get('role')
    data = request.get_json()

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

    if role_name == 'hospital_admin' and data['role'] == 'super_admin':
        return jsonify({'success': False, 'message': 'Cannot create super admin'}), 403

    target_hospital_id = hospital_id
    if role_name == 'super_admin' and data.get('hospital_id'):
        target_hospital_id = data['hospital_id']

    user = User(
        username=data['username'], email=data['email'],
        first_name=data['first_name'], last_name=data['last_name'],
        phone=data.get('phone'), gender=data.get('gender'),
        role_id=role.id, hospital_id=target_hospital_id,
        is_active=True, is_verified=True
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.flush()

    if data['role'] == 'doctor':
        doctor = Doctor(
            user_id=user.id, hospital_id=target_hospital_id,
            department_id=data.get('department_id'),
            specialization=data.get('specialization'),
            qualification=data.get('qualification'),
            pmdc_no=data.get('pmdc_no'),
            consultation_fee=data.get('consultation_fee', 0)
        )
        db.session.add(doctor)

    db.session.commit()
    return jsonify({'success': True, 'message': 'User created', 'user': user.to_dict()}), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    updatable = ['first_name','last_name','phone','gender','address','city','is_active']
    for field in updatable:
        if field in data:
            setattr(user, field, data[field])
    if data.get('password'):
        user.set_password(data['password'])
    db.session.commit()
    return jsonify({'success': True, 'message': 'User updated', 'user': user.to_dict()}), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted'}), 200


@admin_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def dashboard_stats():
    claims = get_jwt()
    role = claims.get('role')
    hospital_id = claims.get('hospital_id')
    today = date.today()

    if role == 'super_admin':
        total_hospitals = Hospital.query.count()
        total_patients = Patient.query.count()
        total_users = User.query.count()
        total_revenue = db.session.query(func.sum(Invoice.paid_amount)).scalar() or 0
        today_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
            func.date(Invoice.created_at) == today
        ).scalar() or 0
        today_appts = Appointment.query.filter_by(appointment_date=today).count()
    else:
        total_hospitals = 1
        total_patients = Patient.query.filter_by(hospital_id=hospital_id).count()
        total_users = User.query.filter_by(hospital_id=hospital_id).count()
        total_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter_by(hospital_id=hospital_id).scalar() or 0
        today_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
            Invoice.hospital_id == hospital_id,
            func.date(Invoice.created_at) == today
        ).scalar() or 0
        today_appts = Appointment.query.filter_by(hospital_id=hospital_id, appointment_date=today).count()

    return jsonify({
        'success': True,
        'total_hospitals': total_hospitals,
        'total_patients': total_patients,
        'total_users': total_users,
        'total_revenue': float(total_revenue),
        'today_revenue': float(today_revenue),
        'today_appointments': today_appts,
    }), 200


@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    depts = Department.query.filter_by(hospital_id=hospital_id, status='active').all()
    return jsonify({'success': True, 'departments': [d.to_dict() for d in depts]}), 200


@admin_bp.route('/departments', methods=['POST'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def create_department():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Department name required'}), 400
    target_hospital = data.get('hospital_id') if claims.get('role') == 'super_admin' else hospital_id
    dept = Department(
        hospital_id=target_hospital or hospital_id, name=data['name'],
        code=data.get('code'), description=data.get('description'),
        room_no=data.get('room_no'), floor=data.get('floor')
    )
    db.session.add(dept)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Department created', 'department': dept.to_dict()}), 201


@admin_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def update_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    data = request.get_json()
    updatable = ['name', 'code', 'description', 'room_no', 'floor', 'status']
    for field in updatable:
        if field in data:
            setattr(dept, field, data[field])
    db.session.commit()
    return jsonify({'success': True, 'message': 'Department updated', 'department': dept.to_dict()}), 200


@admin_bp.route('/departments/<int:dept_id>', methods=['DELETE'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Department deleted'}), 200


@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@require_role('super_admin', 'hospital_admin')
def get_audit_logs():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')

    query = AuditLog.query
    if role != 'super_admin':
        query = query.filter_by(hospital_id=hospital_id)

    page = request.args.get('page', 1, type=int)
    logs = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=50)
    return jsonify({
        'success': True,
        'logs': [{
            'id': l.id, 'user_id': l.user_id, 'action': l.action,
            'module': l.module, 'ip_address': l.ip_address,
            'created_at': l.created_at.isoformat() if l.created_at else None
        } for l in logs.items],
        'total': logs.total
    }), 200


@admin_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    roles = Role.query.all()
    return jsonify({'success': True, 'roles': [r.to_dict() for r in roles]}), 200
