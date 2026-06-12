from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import LabReport, LabTest, LabReportItem, Patient, Prescription, PrescriptionItem, Doctor, AuditLog, User
from datetime import datetime
import random, string

lab_bp = Blueprint('lab', __name__)
prescriptions_bp = Blueprint('prescriptions', __name__)


def _log_prescription(user_id, hospital_id, action, record_id, old_values=None, new_values=None):
    try:
        log = AuditLog(
            user_id=user_id, hospital_id=hospital_id,
            action=action, module='prescription', record_id=record_id,
            old_values=old_values, new_values=new_values,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(log)
    except:
        pass


# ─── LAB ─────────────────────────────────────────

@lab_bp.route('/tests', methods=['GET'])
@jwt_required()
def get_tests():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    tests = LabTest.query.filter_by(hospital_id=hospital_id, status='active').all()
    return jsonify({'success': True, 'tests': [t.to_dict() for t in tests]}), 200


@lab_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_reports():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    query = LabReport.query.filter_by(hospital_id=hospital_id)

    role = claims.get('role')
    if role == 'patient':
        patient = Patient.query.filter_by(user_id=claims.get('user_id')).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({'success': True, 'reports': [], 'total': 0}), 200

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    reports = query.order_by(LabReport.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'reports': [r.to_dict() for r in reports.items],
        'total': reports.total
    }), 200


@lab_bp.route('/reports', methods=['POST'])
@jwt_required()
def create_report():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    user_id = claims.get('user_id')
    data = request.get_json()

    if not data.get('patient_id') or not data.get('tests'):
        return jsonify({'success': False, 'message': 'Patient and tests required'}), 400

    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

    prefix = f"LAB-{hospital_id:03d}-"
    report_no = prefix + ''.join(random.choices(string.digits, k=6))
    while LabReport.query.filter_by(report_no=report_no).first():
        report_no = prefix + ''.join(random.choices(string.digits, k=6))

    total = sum(
        float(LabTest.query.get(t['test_id']).price)
        for t in data['tests']
        if LabTest.query.get(t['test_id'])
    )

    report = LabReport(
        hospital_id=hospital_id, patient_id=patient.id,
        doctor_id=data.get('doctor_id'),
        report_no=report_no, status='requested',
        priority=data.get('priority', 'routine'),
        clinical_notes=data.get('clinical_notes'),
        total_amount=total, requested_by=user_id
    )
    db.session.add(report)
    db.session.flush()

    for t in data['tests']:
        test = LabTest.query.get(t['test_id'])
        if test:
            item = LabReportItem(report_id=report.id, test_id=test.id)
            db.session.add(item)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Lab report created', 'report': report.to_dict()}), 201


@lab_bp.route('/reports/<int:report_id>/results', methods=['PUT'])
@jwt_required()
def update_results(report_id):
    report = LabReport.query.get_or_404(report_id)
    data = request.get_json()

    for item_data in data.get('results', []):
        item = LabReportItem.query.filter_by(
            report_id=report.id, test_id=item_data['test_id']
        ).first()
        if item:
            item.result_value = item_data.get('result_value')
            item.status = item_data.get('status', 'normal')
            item.notes = item_data.get('notes')

    report.status = 'completed'
    report.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Results updated', 'report': report.to_dict()}), 200


@lab_bp.route('/stats', methods=['GET'])
@jwt_required()
def lab_stats():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    base = LabReport.query.filter_by(hospital_id=hospital_id)
    return jsonify({
        'success': True,
        'total': base.count(),
        'requested': base.filter_by(status='requested').count(),
        'in_progress': base.filter_by(status='in_progress').count(),
        'completed': base.filter_by(status='completed').count(),
    }), 200


# ─── PRESCRIPTIONS ───────────────────────────────

@prescriptions_bp.route('/', methods=['GET'])
@jwt_required()
def get_prescriptions():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    query = Prescription.query.filter_by(hospital_id=hospital_id)
    if role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if doctor:
            query = query.filter_by(doctor_id=doctor.id)
    elif role == 'patient':
        patient = Patient.query.filter_by(user_id=user_id).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({'success': True, 'prescriptions': [], 'total': 0}), 200

    patient_id = request.args.get('patient_id')
    if patient_id:
        query = query.filter_by(patient_id=int(patient_id))

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    prescriptions = query.order_by(Prescription.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'prescriptions': [p.to_dict() for p in prescriptions.items],
        'total': prescriptions.total
    }), 200


@prescriptions_bp.route('/', methods=['POST'])
@jwt_required()
def create_prescription():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    if role not in ['doctor', 'hospital_admin', 'super_admin']:
        return jsonify({'success': False, 'message': 'Only doctors can create prescriptions'}), 403

    data = request.get_json()
    if not data.get('patient_id') or not data.get('medicines'):
        return jsonify({'success': False, 'message': 'Patient and medicines required'}), 400

    doctor = Doctor.query.filter_by(user_id=user_id).first()
    if not doctor and role == 'doctor':
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404

    prefix = f"RX-{hospital_id:03d}-"
    prescription_no = prefix + ''.join(random.choices(string.digits, k=6))
    while Prescription.query.filter_by(prescription_no=prescription_no).first():
        prescription_no = prefix + ''.join(random.choices(string.digits, k=6))

    prescription = Prescription(
        hospital_id=hospital_id, patient_id=data['patient_id'],
        doctor_id=doctor.id if doctor else data.get('doctor_id'),
        appointment_id=data.get('appointment_id'),
        prescription_no=prescription_no,
        diagnosis=data.get('diagnosis'), clinical_notes=data.get('clinical_notes'),
        advice=data.get('advice'),
        follow_up_date=datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date() if data.get('follow_up_date') else None
    )
    db.session.add(prescription)
    db.session.flush()

    for med in data['medicines']:
        item = PrescriptionItem(
            prescription_id=prescription.id,
            medicine_name=med['medicine_name'],
            dosage=med.get('dosage'),
            frequency=med.get('frequency'),
            duration=med.get('duration'),
            route=med.get('route'),
            instructions=med.get('instructions'),
            quantity=med.get('quantity', 1)
        )
        db.session.add(item)

    _log_prescription(user_id, hospital_id, 'create_prescription', prescription.id,
                      new_values={'prescription_no': prescription_no, 'patient_id': data['patient_id']})

    db.session.commit()
    return jsonify({'success': True, 'message': 'Prescription created', 'prescription': prescription.to_dict()}), 201


@prescriptions_bp.route('/<int:rx_id>', methods=['GET'])
@jwt_required()
def get_prescription(rx_id):
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    rx = Prescription.query.filter_by(id=rx_id, hospital_id=hospital_id).first_or_404()

    if role == 'patient':
        patient = Patient.query.filter_by(user_id=user_id).first()
        if not patient or rx.patient_id != patient.id:
            return jsonify({'success': False, 'message': 'Permission Denied'}), 403
    elif role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=user_id).first()
        if doctor and rx.doctor_id != doctor.id:
            return jsonify({'success': False, 'message': 'Permission Denied'}), 403
    elif role in ('receptionist', 'pharmacist', 'lab_technician', 'accountant', 'nurse', 'hospital_admin', 'super_admin'):
        pass
    else:
        return jsonify({'success': False, 'message': 'Permission Denied'}), 403

    return jsonify({'success': True, 'prescription': rx.to_dict()}), 200


@prescriptions_bp.route('/<int:rx_id>', methods=['PUT'])
@jwt_required()
def update_prescription(rx_id):
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    if role != 'doctor':
        return jsonify({'success': False, 'message': 'Permission Denied: only the prescribing doctor can edit'}), 403

    rx = Prescription.query.filter_by(id=rx_id, hospital_id=hospital_id).first_or_404()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    if not doctor or rx.doctor_id != doctor.id:
        return jsonify({'success': False, 'message': 'Permission Denied: you can only edit your own prescriptions'}), 403

    if rx.is_dispensed:
        return jsonify({'success': False, 'message': 'Cannot edit a prescription that has already been dispensed'}), 400

    data = request.get_json()
    old_snapshot = {
        'diagnosis': rx.diagnosis, 'clinical_notes': rx.clinical_notes,
        'advice': rx.advice, 'items': [i.to_dict() for i in rx.items]
    }

    if 'diagnosis' in data: rx.diagnosis = data['diagnosis']
    if 'clinical_notes' in data: rx.clinical_notes = data['clinical_notes']
    if 'advice' in data: rx.advice = data['advice']
    if 'follow_up_date' in data and data['follow_up_date']:
        rx.follow_up_date = datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date()

    if 'medicines' in data and isinstance(data['medicines'], list):
        for item in list(rx.items):
            db.session.delete(item)
        db.session.flush()
        for med in data['medicines']:
            item = PrescriptionItem(
                prescription_id=rx.id,
                medicine_name=med['medicine_name'],
                dosage=med.get('dosage'),
                frequency=med.get('frequency'),
                duration=med.get('duration'),
                route=med.get('route'),
                instructions=med.get('instructions'),
                quantity=med.get('quantity', 1)
            )
            db.session.add(item)

    new_snapshot = {
        'diagnosis': rx.diagnosis, 'clinical_notes': rx.clinical_notes,
        'advice': rx.advice, 'items_count': len(data.get('medicines', []))
    }
    _log_prescription(user_id, hospital_id, 'update_prescription', rx.id,
                      old_values=old_snapshot, new_values=new_snapshot)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Prescription updated', 'prescription': rx.to_dict()}), 200


@prescriptions_bp.route('/<int:rx_id>', methods=['DELETE'])
@jwt_required()
def delete_prescription(rx_id):
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    if role != 'doctor':
        return jsonify({'success': False, 'message': 'Permission Denied: only the prescribing doctor can delete'}), 403

    rx = Prescription.query.filter_by(id=rx_id, hospital_id=hospital_id).first_or_404()
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    if not doctor or rx.doctor_id != doctor.id:
        return jsonify({'success': False, 'message': 'Permission Denied: you can only delete your own prescriptions'}), 403

    if rx.is_dispensed:
        return jsonify({'success': False, 'message': 'Cannot delete a prescription that has already been dispensed'}), 400

    rx_no = rx.prescription_no
    _log_prescription(user_id, hospital_id, 'delete_prescription', rx.id,
                      old_values={'prescription_no': rx_no, 'patient_id': rx.patient_id})

    db.session.delete(rx)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Prescription deleted'}), 200


@prescriptions_bp.route('/<int:rx_id>/dispense', methods=['POST'])
@jwt_required()
def dispense_prescription(rx_id):
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    user_id = claims.get('user_id')

    if role not in ('pharmacist', 'hospital_admin', 'super_admin'):
        return jsonify({'success': False, 'message': 'Permission Denied: only pharmacy staff can dispense'}), 403

    rx = Prescription.query.filter_by(id=rx_id, hospital_id=hospital_id).first_or_404()
    if rx.is_dispensed:
        return jsonify({'success': False, 'message': 'Prescription already dispensed'}), 400

    rx.is_dispensed = True
    rx.dispensed_at = datetime.utcnow()
    _log_prescription(user_id, hospital_id, 'dispense_prescription', rx.id,
                      new_values={'prescription_no': rx.prescription_no, 'dispensed_at': str(rx.dispensed_at)})

    db.session.commit()
    return jsonify({'success': True, 'message': 'Prescription dispensed', 'prescription': rx.to_dict()}), 200
