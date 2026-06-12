from extensions import db
from datetime import datetime

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    prescription_no = db.Column(db.String(50), unique=True, nullable=False)
    diagnosis = db.Column(db.Text)
    clinical_notes = db.Column(db.Text)
    advice = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    is_dispensed = db.Column(db.Boolean, default=False)
    dispensed_at = db.Column(db.DateTime)
    pdf_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='prescriptions', lazy=True)
    doctor = db.relationship('Doctor', backref='prescriptions', lazy=True)
    items = db.relationship('PrescriptionItem', backref='prescription', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        patient_data = None
        if self.patient:
            patient_data = {
                'id': self.patient.id,
                'first_name': self.patient.first_name,
                'last_name': self.patient.last_name,
                'mrn': self.patient.mrn,
                'phone': self.patient.phone
            }
        doctor_data = None
        doctor_name = None
        if self.doctor:
            doctor_name = f"Dr. {self.doctor.user.first_name} {self.doctor.user.last_name}".strip() if self.doctor.user else f"Dr. #{self.doctor.id}"
            doctor_data = {
                'id': self.doctor.id,
                'name': doctor_name,
                'specialization': self.doctor.specialization
            }
        return {
            'id': self.id, 'prescription_no': self.prescription_no,
            'patient_id': self.patient_id, 'doctor_id': self.doctor_id,
            'patient': patient_data, 'doctor': doctor_data, 'doctor_name': doctor_name,
            'diagnosis': self.diagnosis, 'clinical_notes': self.clinical_notes,
            'advice': self.advice,
            'follow_up_date': str(self.follow_up_date) if self.follow_up_date else None,
            'is_dispensed': self.is_dispensed,
            'dispensed_at': self.dispensed_at.isoformat() if self.dispensed_at else None,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PrescriptionItem(db.Model):
    __tablename__ = 'prescription_items'
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    duration = db.Column(db.String(100))
    route = db.Column(db.String(50))
    instructions = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id, 'medicine_name': self.medicine_name,
            'dosage': self.dosage, 'frequency': self.frequency,
            'duration': self.duration, 'route': self.route,
            'instructions': self.instructions, 'quantity': self.quantity
        }


class Medicine(db.Model):
    __tablename__ = 'medicines'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200))
    category = db.Column(db.String(100))
    manufacturer = db.Column(db.String(200))
    batch_no = db.Column(db.String(100))
    barcode = db.Column(db.String(100))
    unit = db.Column(db.Enum('tablet','capsule','syrup','injection','cream','drops','sachet','other'), default='tablet')
    strength = db.Column(db.String(50))
    purchase_price = db.Column(db.Numeric(10,2), default=0.00)
    sale_price = db.Column(db.Numeric(10,2), default=0.00)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    expiry_date = db.Column(db.Date)
    location = db.Column(db.String(100))
    requires_prescription = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum('available','out_of_stock','expired','discontinued'), default='available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'generic_name': self.generic_name,
            'category': self.category, 'manufacturer': self.manufacturer,
            'unit': self.unit, 'strength': self.strength,
            'purchase_price': float(self.purchase_price),
            'sale_price': float(self.sale_price),
            'stock_quantity': self.stock_quantity,
            'min_stock_level': self.min_stock_level,
            'expiry_date': str(self.expiry_date) if self.expiry_date else None,
            'status': self.status, 'requires_prescription': self.requires_prescription
        }
