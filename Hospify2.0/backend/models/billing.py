from extensions import db
from datetime import datetime

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.Enum('consultation','pharmacy','lab','admission','other'), default='consultation')
    appointment_id = db.Column(db.Integer)
    subtotal = db.Column(db.Numeric(10,2), default=0.00)
    discount = db.Column(db.Numeric(10,2), default=0.00)
    tax = db.Column(db.Numeric(10,2), default=0.00)
    total_amount = db.Column(db.Numeric(10,2), default=0.00)
    paid_amount = db.Column(db.Numeric(10,2), default=0.00)
    due_amount = db.Column(db.Numeric(10,2), default=0.00)
    payment_method = db.Column(db.Enum('cash','card','easypaisa','jazzcash','credit','insurance'), default='cash')
    payment_status = db.Column(db.Enum('pending','partial','paid','overdue','cancelled'), default='pending')
    due_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='invoices', lazy=True)
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'invoice_no': self.invoice_no,
            'patient_id': self.patient_id, 'type': self.type,
            'subtotal': float(self.subtotal), 'discount': float(self.discount),
            'tax': float(self.tax), 'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount), 'due_amount': float(self.due_amount),
            'payment_method': self.payment_method, 'payment_status': self.payment_status,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10,2), nullable=False)
    total_price = db.Column(db.Numeric(10,2), nullable=False)

    def to_dict(self):
        return {
            'id': self.id, 'description': self.description,
            'quantity': self.quantity, 'unit_price': float(self.unit_price),
            'total_price': float(self.total_price)
        }


class LabReport(db.Model):
    __tablename__ = 'lab_reports'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    appointment_id = db.Column(db.Integer)
    report_no = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.Enum('requested','sample_collected','in_progress','completed','cancelled'), default='requested')
    priority = db.Column(db.Enum('routine','urgent','stat'), default='routine')
    clinical_notes = db.Column(db.Text)
    collected_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    pdf_url = db.Column(db.String(255))
    total_amount = db.Column(db.Numeric(10,2), default=0.00)
    paid_amount = db.Column(db.Numeric(10,2), default=0.00)
    requested_by = db.Column(db.Integer)
    processed_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='lab_reports', lazy=True)
    items = db.relationship('LabReportItem', backref='report', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'report_no': self.report_no,
            'patient_id': self.patient_id, 'status': self.status,
            'priority': self.priority, 'total_amount': float(self.total_amount),
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class LabTest(db.Model):
    __tablename__ = 'lab_tests'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10,2), default=0.00)
    normal_range = db.Column(db.String(200))
    unit = db.Column(db.String(50))
    turnaround_time = db.Column(db.String(100))
    status = db.Column(db.Enum('active','inactive'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'code': self.code,
            'category': self.category, 'price': float(self.price),
            'normal_range': self.normal_range, 'unit': self.unit,
            'turnaround_time': self.turnaround_time, 'status': self.status
        }


class LabReportItem(db.Model):
    __tablename__ = 'lab_report_items'
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('lab_reports.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('lab_tests.id'), nullable=False)
    result_value = db.Column(db.String(255))
    unit = db.Column(db.String(50))
    normal_range = db.Column(db.String(200))
    status = db.Column(db.Enum('normal','abnormal','critical'), default='normal')
    notes = db.Column(db.Text)

    test = db.relationship('LabTest', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'test_id': self.test_id,
            'test_name': self.test.name if self.test else None,
            'result_value': self.result_value, 'unit': self.unit,
            'normal_range': self.normal_range, 'status': self.status, 'notes': self.notes
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    type = db.Column(db.Enum('appointment','lab','billing','pharmacy','general','alert'), default='general')
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    channel = db.Column(db.Enum('in_app','sms','email'), default='in_app')
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'type': self.type, 'title': self.title,
            'message': self.message, 'is_read': self.is_read,
            'channel': self.channel,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    module = db.Column(db.String(100))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
