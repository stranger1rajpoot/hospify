from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Patient, Vitals
from datetime import datetime
import random, string

patients_bp = Blueprint('patients', __name__)

def generate_mrn(hospital_id):
    prefix = f"MRN-{hospital_id:03d}-"
    suffix = ''.join(random.choices(string.digits, k=6))
    return prefix + suffix

def role_required(*roles):
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


@patients_bp.route('/', methods=['GET'])
@jwt_required()
def get_patients():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')

    query = Patient.query
    if role != 'super_admin':
        query = query.filter_by(hospital_id=hospital_id)

    search = request.args.get('search', '')
    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.mrn.ilike(f'%{search}%')) |
            (Patient.phone.ilike(f'%{search}%'))
        )

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    patients = query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=per_page)

    return jsonify({
        'success': True,
        'patients': [p.to_dict() for p in patients.items],
        'total': patients.total, 'pages': patients.pages,
        'current_page': page
    }), 200


@patients_bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient(patient_id):
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    patient = Patient.query.get_or_404(patient_id)
    if claims.get('role') != 'super_admin' and patient.hospital_id != hospital_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    return jsonify({'success': True, 'patient': patient.to_dict()}), 200


@patients_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    claims = get_jwt()
    role = claims.get('role')
    user_id = claims.get('user_id')
    
    if role != 'patient':
        return jsonify({'success': False, 'message': 'Not a patient'}), 403
        
    patient = Patient.query.filter_by(user_id=user_id).first()
    if not patient:
        return jsonify({'success': False, 'message': 'Patient profile not found'}), 404
        
    return jsonify({'success': True, 'patient': patient.to_dict()}), 200


@patients_bp.route('/', methods=['POST'])
@jwt_required()
def create_patient():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    data = request.get_json()

    required = ['first_name', 'last_name', 'gender']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'}), 400

    mrn = generate_mrn(hospital_id)
    while Patient.query.filter_by(mrn=mrn).first():
        mrn = generate_mrn(hospital_id)

    patient = Patient(
        hospital_id=hospital_id, mrn=mrn,
        first_name=data['first_name'], last_name=data['last_name'],
        gender=data['gender'],
        date_of_birth=datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
        age=data.get('age'), blood_group=data.get('blood_group', 'Unknown'),
        phone=data.get('phone'), phone_alt=data.get('phone_alt'),
        email=data.get('email'), address=data.get('address'), city=data.get('city'),
        cnic=data.get('cnic'), allergies=data.get('allergies'),
        chronic_conditions=data.get('chronic_conditions'),
        emergency_contact_name=data.get('emergency_contact_name'),
        emergency_contact_phone=data.get('emergency_contact_phone'),
        emergency_contact_relation=data.get('emergency_contact_relation'),
        patient_type=data.get('patient_type', 'opd'),
        registered_by=int(get_jwt().get('user_id'))
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Patient registered', 'patient': patient.to_dict()}), 201


@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    patient = Patient.query.get_or_404(patient_id)
    if claims.get('role') != 'super_admin' and patient.hospital_id != hospital_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    data = request.get_json()
    updatable = ['first_name','last_name','gender','age','blood_group','phone','phone_alt',
                 'email','address','city','cnic','allergies','chronic_conditions',
                 'emergency_contact_name','emergency_contact_phone','emergency_contact_relation',
                 'patient_type','status','insurance_provider','insurance_no']

    for field in updatable:
        if field in data:
            setattr(patient, field, data[field])

    if data.get('date_of_birth'):
        patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()

    db.session.commit()
    return jsonify({'success': True, 'message': 'Patient updated', 'patient': patient.to_dict()}), 200


@patients_bp.route('/<int:patient_id>', methods=['DELETE'])
@jwt_required()
def delete_patient(patient_id):
    claims = get_jwt()
    if claims.get('role') not in ['super_admin', 'hospital_admin']:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    patient = Patient.query.get_or_404(patient_id)
    patient.status = 'inactive'
    db.session.commit()
    return jsonify({'success': True, 'message': 'Patient deactivated'}), 200


@patients_bp.route('/<int:patient_id>/vitals', methods=['GET'])
@jwt_required()
def get_patient_vitals(patient_id):
    vitals = Vitals.query.filter_by(patient_id=patient_id).order_by(Vitals.recorded_at.desc()).limit(20).all()
    return jsonify({'success': True, 'vitals': [v.to_dict() for v in vitals]}), 200


@patients_bp.route('/stats', methods=['GET'])
@jwt_required()
def patient_stats():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    base = Patient.query.filter_by(hospital_id=hospital_id)
    return jsonify({
        'success': True,
        'total': base.count(),
        'active': base.filter_by(status='active').count(),
        'opd': base.filter_by(patient_type='opd').count(),
        'ipd': base.filter_by(patient_type='ipd').count(),
    }), 200
