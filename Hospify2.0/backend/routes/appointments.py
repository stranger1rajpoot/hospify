from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Appointment, Patient, Doctor
from datetime import datetime, date

appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('/', methods=['GET'])
@jwt_required()
def get_appointments():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    query = Appointment.query.filter_by(hospital_id=hospital_id)

    if role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if doctor:
            query = query.filter_by(doctor_id=doctor.id)
    elif role == 'patient':
        patient = Patient.query.filter_by(user_id=user_id).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({'success': False, 'appointments': [], 'total': 0}), 200

    appt_date = request.args.get('date')
    if appt_date:
        query = query.filter_by(appointment_date=datetime.strptime(appt_date, '%Y-%m-%d').date())

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    doctor_id = request.args.get('doctor_id')
    if doctor_id:
        query = query.filter_by(doctor_id=int(doctor_id))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    appts = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time).paginate(page=page, per_page=per_page)

    return jsonify({
        'success': True,
        'appointments': [a.to_dict() for a in appts.items],
        'total': appts.total, 'pages': appts.pages
    }), 200


@appointments_bp.route('/today', methods=['GET'])
@jwt_required()
def today_appointments():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    query = Appointment.query.filter_by(hospital_id=hospital_id, appointment_date=date.today())

    if role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if doctor:
            query = query.filter_by(doctor_id=doctor.id)
    elif role == 'patient':
        patient = Patient.query.filter_by(user_id=user_id).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({'success': True, 'appointments': []}), 200

    appointments = query.order_by(Appointment.appointment_time).all()
    return jsonify({'success': True, 'appointments': [a.to_dict() for a in appointments]}), 200


@appointments_bp.route('/', methods=['POST'])
@jwt_required()
def create_appointment():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    user_id = claims.get('user_id')
    data = request.get_json()

    required = ['patient_id', 'doctor_id', 'appointment_date', 'appointment_time']
    for field in required:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field} is required'}), 400

    patient = Patient.query.get(data['patient_id'])
    if not patient or patient.hospital_id != hospital_id:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

    doctor = Doctor.query.get(data['doctor_id'])
    if not doctor or doctor.hospital_id != hospital_id:
        return jsonify({'success': False, 'message': 'Doctor not found'}), 404

    appt_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    appt_time = datetime.strptime(data['appointment_time'], '%H:%M').time()

    # Generate token
    existing = Appointment.query.filter_by(
        hospital_id=hospital_id, doctor_id=doctor.id, appointment_date=appt_date
    ).count()
    token_no = existing + 1

    appointment = Appointment(
        hospital_id=hospital_id, patient_id=patient.id,
        doctor_id=doctor.id, department_id=data.get('department_id'),
        appointment_date=appt_date, appointment_time=appt_time,
        token_no=token_no, type=data.get('type', 'opd'),
        status='scheduled', chief_complaint=data.get('chief_complaint'),
        notes=data.get('notes'), fee=doctor.consultation_fee,
        booked_by=user_id
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Appointment booked', 'appointment': appointment.to_dict()}), 201


@appointments_bp.route('/<int:appt_id>', methods=['PUT'])
@jwt_required()
def update_appointment(appt_id):
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    appt = Appointment.query.get_or_404(appt_id)
    if appt.hospital_id != hospital_id:
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    data = request.get_json()
    updatable = ['status', 'notes', 'chief_complaint', 'fee_paid']
    for field in updatable:
        if field in data:
            setattr(appt, field, data[field])

    db.session.commit()
    return jsonify({'success': True, 'message': 'Appointment updated', 'appointment': appt.to_dict()}), 200


@appointments_bp.route('/stats', methods=['GET'])
@jwt_required()
def appointment_stats():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    today = date.today()
    base = Appointment.query.filter_by(hospital_id=hospital_id)

    return jsonify({
        'success': True,
        'today': base.filter_by(appointment_date=today).count(),
        'scheduled': base.filter_by(status='scheduled').count(),
        'completed_today': base.filter_by(appointment_date=today, status='completed').count(),
        'cancelled_today': base.filter_by(appointment_date=today, status='cancelled').count(),
    }), 200
