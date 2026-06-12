from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Doctor, User

doctors_bp = Blueprint('doctors', __name__)


@doctors_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_doctor_profile():
    claims = get_jwt()
    user_id = claims.get('user_id')
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    if not doctor:
        return jsonify({'success': False, 'message': 'Doctor profile not found'}), 404
    return jsonify({'success': True, 'doctor': doctor.to_dict()}), 200
