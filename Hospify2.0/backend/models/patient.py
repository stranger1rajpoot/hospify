from extensions import db
from datetime import datetime

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    mrn = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum('male','female','other'), nullable=False)
    date_of_birth = db.Column(db.Date)
    age = db.Column(db.Integer)
    blood_group = db.Column(db.Enum('A+','A-','B+','B-','O+','O-','AB+','AB-','Unknown'), default='Unknown')
    phone = db.Column(db.String(20))
    phone_alt = db.Column(db.String(20))
    email = db.Column(db.String(150))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    cnic = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(150))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relation = db.Column(db.String(50))
    allergies = db.Column(db.Text)
    chronic_conditions = db.Column(db.Text)
    insurance_provider = db.Column(db.String(150))
    insurance_no = db.Column(db.String(100))
    patient_type = db.Column(db.Enum('opd','ipd','both'), default='opd')
    status = db.Column(db.Enum('active','inactive','deceased'), default='active')
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hospital = db.relationship('Hospital', backref='patients', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'mrn': self.mrn,
            'first_name': self.first_name, 'last_name': self.last_name,
            'full_name': f"{self.first_name} {self.last_name}",
            'gender': self.gender, 'age': self.age,
            'blood_group': self.blood_group, 'phone': self.phone,
            'email': self.email, 'address': self.address, 'city': self.city,
            'cnic': self.cnic, 'allergies': self.allergies,
            'chronic_conditions': self.chronic_conditions,
            'patient_type': self.patient_type, 'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    token_no = db.Column(db.Integer)
    type = db.Column(db.Enum('opd','ipd','telemedicine','follow_up'), default='opd')
    status = db.Column(db.Enum('scheduled','confirmed','in_progress','completed','cancelled','no_show'), default='scheduled')
    chief_complaint = db.Column(db.Text)
    notes = db.Column(db.Text)
    fee = db.Column(db.Numeric(10,2), default=0.00)
    fee_paid = db.Column(db.Boolean, default=False)
    booked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='appointments', lazy=True)
    doctor = db.relationship('Doctor', backref='appointments', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 'patient_id': self.patient_id, 'doctor_id': self.doctor_id,
            'appointment_date': str(self.appointment_date),
            'appointment_time': str(self.appointment_time),
            'token_no': self.token_no, 'type': self.type, 'status': self.status,
            'chief_complaint': self.chief_complaint, 'fee': float(self.fee),
            'fee_paid': self.fee_paid,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}" if self.patient else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Vitals(db.Model):
    __tablename__ = 'vitals'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    temperature = db.Column(db.Numeric(5,2)) # Celsius
    pulse = db.Column(db.Integer)            # bpm
    blood_pressure_sys = db.Column(db.Integer) # mmHg
    blood_pressure_dia = db.Column(db.Integer) # mmHg
    spo2 = db.Column(db.Integer)             # %
    respiratory_rate = db.Column(db.Integer) # breaths per min
    weight = db.Column(db.Numeric(5,2))      # kg
    height = db.Column(db.Numeric(5,2))      # cm
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='vitals', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': f"{self.patient.first_name} {self.patient.last_name}" if self.patient else None,
            'temperature': float(self.temperature) if self.temperature else None,
            'pulse': self.pulse,
            'bp': f"{self.blood_pressure_sys}/{self.blood_pressure_dia}" if self.blood_pressure_sys and self.blood_pressure_dia else None,
            'spo2': self.spo2,
            'respiratory_rate': self.respiratory_rate,
            'weight': float(self.weight) if self.weight else None,
            'height': float(self.height) if self.height else None,
            'notes': self.notes,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
