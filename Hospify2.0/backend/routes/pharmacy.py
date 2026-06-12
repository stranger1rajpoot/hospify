from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db
from models import Medicine, Invoice, InvoiceItem, Patient
from datetime import datetime, date, timedelta
import random, string

pharmacy_bp = Blueprint('pharmacy', __name__)
billing_bp = Blueprint('billing', __name__)

# ─── PHARMACY ─────────────────────────────────────

@pharmacy_bp.route('/medicines', methods=['GET'])
@jwt_required()
def get_medicines():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    query = Medicine.query.filter_by(hospital_id=hospital_id)

    search = request.args.get('search', '')
    if search:
        query = query.filter(
            (Medicine.name.ilike(f'%{search}%')) |
            (Medicine.generic_name.ilike(f'%{search}%'))
        )
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    meds = query.order_by(Medicine.name).paginate(page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'medicines': [m.to_dict() for m in meds.items],
        'total': meds.total
    }), 200


@pharmacy_bp.route('/medicines', methods=['POST'])
@jwt_required()
def add_medicine():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Medicine name required'}), 400

    med = Medicine(
        hospital_id=hospital_id,
        name=data['name'], generic_name=data.get('generic_name'),
        category=data.get('category'), manufacturer=data.get('manufacturer'),
        batch_no=data.get('batch_no'), barcode=data.get('barcode'),
        unit=data.get('unit', 'tablet'), strength=data.get('strength'),
        purchase_price=data.get('purchase_price', 0),
        sale_price=data.get('sale_price', 0),
        stock_quantity=data.get('stock_quantity', 0),
        min_stock_level=data.get('min_stock_level', 10),
        expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
        location=data.get('location'),
        requires_prescription=data.get('requires_prescription', False)
    )
    db.session.add(med)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Medicine added', 'medicine': med.to_dict()}), 201


@pharmacy_bp.route('/medicines/<int:med_id>', methods=['PUT'])
@jwt_required()
def update_medicine(med_id):
    med = Medicine.query.get_or_404(med_id)
    data = request.get_json()
    updatable = ['name','generic_name','category','manufacturer','unit','strength',
                 'purchase_price','sale_price','stock_quantity','min_stock_level',
                 'location','status','requires_prescription']
    for field in updatable:
        if field in data:
            setattr(med, field, data[field])
    if data.get('expiry_date'):
        med.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Updated', 'medicine': med.to_dict()}), 200


@pharmacy_bp.route('/medicines/<int:med_id>', methods=['DELETE'])
@jwt_required()
def delete_medicine(med_id):
    claims = get_jwt()
    role = claims.get('role')
    if role not in ('super_admin', 'admin', 'pharmacist', 'hospital_admin'):
        return jsonify({'success': False, 'message': 'Only pharmacy/admin staff can delete medicines'}), 403
    med = Medicine.query.get_or_404(med_id)
    db.session.delete(med)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Medicine deleted'}), 200


@pharmacy_bp.route('/medicines/<int:med_id>/restock', methods=['POST'])
@jwt_required()
def restock_medicine(med_id):
    claims = get_jwt()
    role = claims.get('role')
    if role not in ('super_admin', 'admin', 'pharmacist', 'hospital_admin'):
        return jsonify({'success': False, 'message': 'Only pharmacy/admin staff can restock'}), 403
    med = Medicine.query.get_or_404(med_id)
    data = request.get_json() or {}
    qty = int(data.get('quantity', 0))
    if qty <= 0:
        return jsonify({'success': False, 'message': 'Quantity must be > 0'}), 400
    med.stock_quantity = (med.stock_quantity or 0) + qty
    if med.status == 'out_of_stock' and med.stock_quantity > 0:
        med.status = 'available'
    db.session.commit()
    return jsonify({'success': True, 'message': f'Added {qty} units', 'medicine': med.to_dict()}), 200


@pharmacy_bp.route('/medicines/low-stock', methods=['GET'])
@jwt_required()
def low_stock():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    meds = Medicine.query.filter(
        Medicine.hospital_id == hospital_id,
        Medicine.stock_quantity <= Medicine.min_stock_level,
        Medicine.status == 'available'
    ).all()
    return jsonify({'success': True, 'medicines': [m.to_dict() for m in meds], 'count': len(meds)}), 200


@pharmacy_bp.route('/medicines/expiring', methods=['GET'])
@jwt_required()
def expiring_soon():
    from datetime import timedelta
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    threshold = date.today() + timedelta(days=90)
    meds = Medicine.query.filter(
        Medicine.hospital_id == hospital_id,
        Medicine.expiry_date <= threshold,
        Medicine.expiry_date >= date.today()
    ).all()
    return jsonify({'success': True, 'medicines': [m.to_dict() for m in meds], 'count': len(meds)}), 200


@pharmacy_bp.route('/stats', methods=['GET'])
@jwt_required()
def pharmacy_stats():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    base = Medicine.query.filter_by(hospital_id=hospital_id)
    today = date.today()
    return jsonify({
        'success': True,
        'total_medicines': base.count(),
        'available': base.filter_by(status='available').count(),
        'out_of_stock': base.filter_by(status='out_of_stock').count(),
        'expired': base.filter(Medicine.expiry_date < today).count(),
        'low_stock': base.filter(Medicine.stock_quantity <= Medicine.min_stock_level).count(),
    }), 200


# ─── PHARMACY SALES (POS) ────────────────────────

def _get_walkin_patient(hospital_id):
    """Return (or create) a generic walk-in customer Patient for the hospital."""
    p = Patient.query.filter_by(hospital_id=hospital_id, mrn='WALK-IN').first()
    if p:
        return p
    p = Patient(
        hospital_id=hospital_id,
        mrn='WALK-IN',
        first_name='Walk-in',
        last_name='Customer',
        gender='other',
        status='active',
        patient_type='opd'
    )
    db.session.add(p)
    db.session.commit()
    return p


@pharmacy_bp.route('/sales', methods=['POST'])
@jwt_required()
def create_pharmacy_sale():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    user_id = claims.get('user_id')
    data = request.get_json() or {}

    items = data.get('items') or []
    if not items:
        return jsonify({'success': False, 'message': 'Cart is empty'}), 400

    patient_id = data.get('patient_id')
    if patient_id:
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'success': False, 'message': 'Patient not found'}), 404
    else:
        patient = _get_walkin_patient(hospital_id)

    invoice_no = gen_invoice_no(hospital_id)
    while Invoice.query.filter_by(invoice_no=invoice_no).first():
        invoice_no = gen_invoice_no(hospital_id)

    subtotal = 0.0
    resolved_items = []
    for it in items:
        med = Medicine.query.filter_by(id=it.get('medicine_id'), hospital_id=hospital_id).first()
        if not med:
            return jsonify({'success': False, 'message': f"Medicine #{it.get('medicine_id')} not found"}), 404
        qty = int(it.get('quantity', 1))
        if qty <= 0:
            return jsonify({'success': False, 'message': 'Invalid quantity'}), 400
        if med.stock_quantity < qty:
            return jsonify({'success': False, 'message': f"Insufficient stock for {med.name} (have {med.stock_quantity})"}), 400
        unit_price = float(med.sale_price)
        line_total = round(qty * unit_price, 2)
        subtotal += line_total
        resolved_items.append({'med': med, 'quantity': qty, 'unit_price': unit_price, 'line_total': line_total})

    discount = float(data.get('discount', 0))
    tax_rate = float(data.get('tax_rate', 5))
    tax = round((subtotal - discount) * tax_rate / 100, 2)
    total = round(subtotal - discount + tax, 2)
    paid = float(data.get('paid_amount', total))
    due = round(total - paid, 2)
    status = 'paid' if due <= 0 else ('partial' if paid > 0 else 'pending')

    invoice = Invoice(
        hospital_id=hospital_id, patient_id=patient.id,
        invoice_no=invoice_no, type='pharmacy',
        subtotal=subtotal, discount=discount, tax=tax,
        total_amount=total, paid_amount=paid, due_amount=due,
        payment_method=data.get('payment_method', 'cash'),
        payment_status=status, notes=data.get('notes'),
        generated_by=user_id,
        paid_at=datetime.utcnow() if due <= 0 else None
    )
    db.session.add(invoice)
    db.session.flush()

    for r in resolved_items:
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=f"{r['med'].name} ({r['med'].strength or r['med'].unit})",
            quantity=r['quantity'],
            unit_price=r['unit_price'],
            total_price=r['line_total']
        )
        db.session.add(item)
        r['med'].stock_quantity = (r['med'].stock_quantity or 0) - r['quantity']
        if r['med'].stock_quantity <= 0:
            r['med'].status = 'out_of_stock'
        elif r['med'].status == 'out_of_stock' and r['med'].stock_quantity > 0:
            r['med'].status = 'available'

    db.session.commit()
    return jsonify({'success': True, 'message': 'Sale completed', 'invoice': invoice.to_dict()}), 201


@pharmacy_bp.route('/sales/recent', methods=['GET'])
@jwt_required()
def recent_pharmacy_sales():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    q = Invoice.query.filter_by(hospital_id=hospital_id, type='pharmacy')
    q = q.order_by(Invoice.created_at.desc())
    pag = q.paginate(page=page, per_page=per_page)
    out = []
    for inv in pag.items:
        d = inv.to_dict()
        if inv.patient:
            d['patient_name'] = f"{inv.patient.first_name} {inv.patient.last_name}".strip()
            d['patient_mrn'] = inv.patient.mrn
        out.append(d)
    return jsonify({'success': True, 'invoices': out, 'total': pag.total}), 200


@pharmacy_bp.route('/sales/reports', methods=['GET'])
@jwt_required()
def pharmacy_sales_reports():
    from sqlalchemy import func
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    today = date.today()

    base = Invoice.query.filter_by(hospital_id=hospital_id, type='pharmacy')

    today_revenue = db.session.query(func.coalesce(func.sum(Invoice.paid_amount), 0)).filter(
        Invoice.hospital_id == hospital_id, Invoice.type == 'pharmacy',
        func.date(Invoice.created_at) == today
    ).scalar() or 0

    week_start = today - timedelta(days=today.weekday())
    week_revenue = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
        Invoice.hospital_id == hospital_id, Invoice.type == 'pharmacy',
        func.date(Invoice.created_at) >= week_start
    ).scalar() or 0

    month_start = today.replace(day=1)
    month_revenue = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
        Invoice.hospital_id == hospital_id, Invoice.type == 'pharmacy',
        func.date(Invoice.created_at) >= month_start
    ).scalar() or 0

    last7 = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        s = db.session.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
            Invoice.hospital_id == hospital_id, Invoice.type == 'pharmacy',
            func.date(Invoice.created_at) == d
        ).scalar() or 0
        last7.append({'date': d.isoformat(), 'label': d.strftime('%a'), 'total': float(s)})

    top = db.session.query(
        InvoiceItem.description,
        func.sum(InvoiceItem.quantity).label('qty'),
        func.sum(InvoiceItem.total_price).label('rev')
    ).join(Invoice, InvoiceItem.invoice_id == Invoice.id).filter(
        Invoice.hospital_id == hospital_id, Invoice.type == 'pharmacy'
    ).group_by(InvoiceItem.description).order_by(func.sum(InvoiceItem.quantity).desc()).limit(10).all()

    return jsonify({
        'success': True,
        'today_revenue': float(today_revenue),
        'week_revenue': float(week_revenue),
        'month_revenue': float(month_revenue),
        'total_invoices': base.count(),
        'paid_invoices': base.filter_by(payment_status='paid').count(),
        'pending_invoices': base.filter(Invoice.payment_status.in_(['pending', 'partial'])).count(),
        'daily': last7,
        'top_medicines': [{'name': r[0], 'quantity': int(r[1] or 0), 'revenue': float(r[2] or 0)} for r in top],
    }), 200


# ─── BILLING ─────────────────────────────────────

def gen_invoice_no(hospital_id):
    prefix = f"INV-{hospital_id:03d}-"
    suffix = ''.join(random.choices(string.digits, k=8))
    return prefix + suffix


@billing_bp.route('/invoices', methods=['GET'])
@jwt_required()
def get_invoices():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    query = Invoice.query.filter_by(hospital_id=hospital_id)

    role = claims.get('role')
    if role == 'patient':
        from models import Patient
        patient = Patient.query.filter_by(user_id=claims.get('user_id')).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
        else:
            return jsonify({'success': True, 'invoices': [], 'total': 0}), 200

    status = request.args.get('status')
    if status:
        query = query.filter_by(payment_status=status)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    invoices = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({
        'success': True,
        'invoices': [i.to_dict() for i in invoices.items],
        'total': invoices.total
    }), 200


@billing_bp.route('/invoices', methods=['POST'])
@jwt_required()
def create_invoice():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    user_id = claims.get('user_id')
    data = request.get_json()

    if not data.get('patient_id') or not data.get('items'):
        return jsonify({'success': False, 'message': 'Patient and items required'}), 400

    patient = Patient.query.get(data['patient_id'])
    if not patient:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

    invoice_no = gen_invoice_no(hospital_id)
    while Invoice.query.filter_by(invoice_no=invoice_no).first():
        invoice_no = gen_invoice_no(hospital_id)

    subtotal = sum(item.get('quantity', 1) * item.get('unit_price', 0) for item in data['items'])
    discount = float(data.get('discount', 0))
    tax_rate = float(data.get('tax_rate', 5))
    tax = round((subtotal - discount) * tax_rate / 100, 2)
    total = round(subtotal - discount + tax, 2)
    paid = float(data.get('paid_amount', 0))
    due = round(total - paid, 2)
    status = 'paid' if due <= 0 else ('partial' if paid > 0 else 'pending')

    invoice = Invoice(
        hospital_id=hospital_id, patient_id=patient.id,
        invoice_no=invoice_no, type=data.get('type', 'consultation'),
        subtotal=subtotal, discount=discount, tax=tax,
        total_amount=total, paid_amount=paid, due_amount=due,
        payment_method=data.get('payment_method', 'cash'),
        payment_status=status, notes=data.get('notes'),
        generated_by=user_id,
        paid_at=datetime.utcnow() if due <= 0 else None
    )
    db.session.add(invoice)
    db.session.flush()

    for item_data in data['items']:
        item = InvoiceItem(
            invoice_id=invoice.id,
            description=item_data['description'],
            quantity=item_data.get('quantity', 1),
            unit_price=item_data['unit_price'],
            total_price=item_data.get('quantity', 1) * item_data['unit_price']
        )
        db.session.add(item)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Invoice created', 'invoice': invoice.to_dict()}), 201


@billing_bp.route('/invoices/<int:invoice_id>/pay', methods=['POST'])
@jwt_required()
def process_payment(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.get_json()
    amount = float(data.get('amount', 0))
    invoice.paid_amount = float(invoice.paid_amount) + amount
    invoice.due_amount = float(invoice.total_amount) - float(invoice.paid_amount)
    if invoice.due_amount <= 0:
        invoice.payment_status = 'paid'
        invoice.paid_at = datetime.utcnow()
    else:
        invoice.payment_status = 'partial'
    if data.get('payment_method'):
        invoice.payment_method = data['payment_method']
    db.session.commit()
    return jsonify({'success': True, 'message': 'Payment recorded', 'invoice': invoice.to_dict()}), 200


@billing_bp.route('/clear-all', methods=['DELETE'])
@jwt_required()
def clear_all_invoices():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    role = claims.get('role')
    if role not in ('super_admin', 'admin', 'doctor', 'nurse', 'accountant'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    Invoice.query.filter_by(hospital_id=hospital_id).delete()
    db.session.commit()
    return jsonify({'success': True, 'message': 'All invoices cleared'}), 200


@billing_bp.route('/stats', methods=['GET'])
@jwt_required()
def billing_stats():
    claims = get_jwt()
    hospital_id = claims.get('hospital_id')
    today = date.today()
    base = Invoice.query.filter_by(hospital_id=hospital_id)

    from sqlalchemy import func
    today_revenue = db.session.query(func.sum(Invoice.paid_amount)).filter(
        Invoice.hospital_id == hospital_id,
        func.date(Invoice.created_at) == today
    ).scalar() or 0

    total_pending = db.session.query(func.sum(Invoice.due_amount)).filter(
        Invoice.hospital_id == hospital_id,
        Invoice.payment_status.in_(['pending', 'partial'])
    ).scalar() or 0

    return jsonify({
        'success': True,
        'today_revenue': float(today_revenue),
        'total_invoices': base.count(),
        'pending': base.filter_by(payment_status='pending').count(),
        'paid': base.filter_by(payment_status='paid').count(),
        'total_pending_amount': float(total_pending),
    }), 200
