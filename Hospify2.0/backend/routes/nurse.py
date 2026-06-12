from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Patient, Vitals
from extensions import db
from functools import wraps

nurse_bp = Blueprint('nurse', __name__)

def require_nurse(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'nurse':
            return jsonify({'success': False, 'message': 'Unauthorized: Nurses only'}), 403
        return fn(*args, **kwargs)
    return wrapper

@nurse_bp.route('/stats', methods=['GET'])
@jwt_required()
@require_nurse
def get_stats():
    # Since we don't have a strict Ward system yet, we'll return some basic stats
    admitted = Patient.query.filter_by(patient_type='ipd').count()
    vitals_count = Vitals.query.count()
    
    return jsonify({
        'success': True,
        'admitted_patients': admitted,
        'critical_patients': 0, # Placeholder
        'medications_due': 0, # Placeholder
        'vitals_recorded': vitals_count
    })

@nurse_bp.route('/ward', methods=['GET'])
@jwt_required()
@require_nurse
def get_ward_patients():
    patients = Patient.query.filter_by(patient_type='ipd').all()
    # Mocking bed/condition for now since we don't have a full ward model
    data = []
    for p in patients:
        data.append({
            'id': p.id,
            'name': f"{p.first_name} {p.last_name}",
            'bed': 'General',
            'condition': 'stable',
            'last_vitals': 'N/A'
        })
    return jsonify({'success': True, 'patients': data})

@nurse_bp.route('/vitals', methods=['GET'])
@jwt_required()
@require_nurse
def get_vitals():
    vitals = Vitals.query.order_by(Vitals.recorded_at.desc()).limit(50).all()
    return jsonify({
        'success': True,
        'vitals': [v.to_dict() for v in vitals]
    })

@nurse_bp.route('/vitals', methods=['POST'])
@jwt_required()
@require_nurse
def record_vitals():
    data = request.json
    nurse_id = get_jwt_identity()
    
    vital = Vitals(
        patient_id=data.get('patient_id'),
        nurse_id=nurse_id,
        temperature=data.get('temperature'),
        pulse=data.get('pulse'),
        blood_pressure_sys=data.get('bp_sys'),
        blood_pressure_dia=data.get('bp_dia'),
        spo2=data.get('spo2'),
        respiratory_rate=data.get('resp_rate'),
        weight=data.get('weight'),
        height=data.get('height'),
        notes=data.get('notes')
    )
    db.session.add(vital)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Vitals recorded successfully',
        'vitals': vital.to_dict()
    }), 201
