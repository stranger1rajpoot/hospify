from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Medicine, Prescription, PrescriptionItem
from sqlalchemy import func
from seed_medicines import DIAGNOSTIC_SUGGESTIONS

medicines_bp = Blueprint('medicines', __name__)


@medicines_bp.route('/frequently-prescribed', methods=['GET'])
@jwt_required()
def frequently_prescribed():
    """Return the current doctor's most frequently prescribed medicines."""
    claims = get_jwt()
    user_id = claims.get('user_id')
    limit = min(int(request.args.get('limit', 20)), 50)

    # Get the doctor record for this user
    from models import Doctor
    doctor = Doctor.query.filter_by(user_id=user_id).first()
    if not doctor:
        # Fallback: return global top meds across the hospital
        hospital_id = claims.get('hospital_id')
        results = db.session.query(
            PrescriptionItem.medicine_name,
            func.count(PrescriptionItem.id).label('prescribe_count')
        ).join(
            Prescription, PrescriptionItem.prescription_id == Prescription.id
        ).filter(
            Prescription.hospital_id == hospital_id
        ).group_by(
            PrescriptionItem.medicine_name
        ).order_by(
            func.count(PrescriptionItem.id).desc()
        ).limit(limit).all()
    else:
        results = db.session.query(
            PrescriptionItem.medicine_name,
            func.count(PrescriptionItem.id).label('prescribe_count')
        ).join(
            Prescription, PrescriptionItem.prescription_id == Prescription.id
        ).filter(
            Prescription.doctor_id == doctor.id
        ).group_by(
            PrescriptionItem.medicine_name
        ).order_by(
            func.count(PrescriptionItem.id).desc()
        ).limit(limit).all()

    meds = [{'name': r[0], 'count': r[1]} for r in results if r[0]]
    return jsonify({'success': True, 'medicines': meds}), 200


@medicines_bp.route('/search', methods=['GET'])
@jwt_required()
def search_medicines():
    """Search medicines by name or generic name."""
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    limit = min(int(request.args.get('limit', 30)), 100)

    query = Medicine.query.filter_by(hospital_id=hospital_id, status='available')
    if q:
        query = query.filter(
            db.or_(
                Medicine.name.ilike(f'%{q}%'),
                Medicine.generic_name.ilike(f'%{q}%')
            )
        )
    if category:
        query = query.filter_by(category=category)

    medicines = query.order_by(Medicine.name).limit(limit).all()
    return jsonify({'success': True, 'medicines': [m.to_dict() for m in medicines]}), 200


@medicines_bp.route('/suggest', methods=['POST'])
@jwt_required()
def suggest_medicines():
    """
    AI-powered medicine suggestion based on diagnosis/chief complaint.
    Uses keyword matching against diagnostic categories to suggest relevant medicines.
    """
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    data = request.get_json() or {}
    text = (data.get('diagnosis', '') + ' ' + data.get('chief_complaint', '')).lower().strip()

    if not text:
        # Return common medicines if no text provided
        common = Medicine.query.filter_by(hospital_id=hospital_id, status='available')\
            .order_by(Medicine.name).limit(10).all()
        return jsonify({'success': True, 'medicines': [m.to_dict() for m in common]}), 200

    # Find matching categories from the diagnostic keywords
    matched_categories = set()
    matches = set()

    # Split text into words and check against diagnostic keywords
    words = text.split()
    for keyword, categories in DIAGNOSTIC_SUGGESTIONS.items():
        if keyword in text:
            matched_categories.update(categories)
            matches.add(keyword)

    # If no category matched, search by text matching medicine name/generic
    if not matched_categories:
        search_term = text.strip()
        meds = Medicine.query.filter(
            Medicine.hospital_id == hospital_id,
            Medicine.status == 'available',
            db.or_(
                Medicine.name.ilike(f'%{search_term}%'),
                Medicine.generic_name.ilike(f'%{search_term}%'),
                Medicine.category.ilike(f'%{search_term}%')
            )
        ).order_by(Medicine.name).limit(15).all()
        return jsonify({
            'success': True,
            'medicines': [m.to_dict() for m in meds],
            'matched_keywords': list(matches)
        }), 200

    # Get medicines from matched categories, prioritize antibiotics & analgesics
    meds = Medicine.query.filter(
        Medicine.hospital_id == hospital_id,
        Medicine.status == 'available',
        Medicine.category.in_(matched_categories)
    ).order_by(Medicine.name).limit(20).all()

    return jsonify({
        'success': True,
        'medicines': [m.to_dict() for m in meds],
        'matched_keywords': list(matches),
        'matched_categories': list(matched_categories)
    }), 200
