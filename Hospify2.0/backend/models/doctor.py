from extensions import db
from datetime import datetime

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    specialization = db.Column(db.String(200))
    qualification = db.Column(db.String(300))
    pmdc_no = db.Column(db.String(50))
    experience_years = db.Column(db.Integer, default=0)
    consultation_fee = db.Column(db.Numeric(10,2), default=0.00)
    availability_days = db.Column(db.String(100))
    availability_start = db.Column(db.Time)
    availability_end = db.Column(db.Time)
    max_patients_per_day = db.Column(db.Integer, default=30)
    bio = db.Column(db.Text)
    signature_url = db.Column(db.String(255))
    status = db.Column(db.Enum('active','inactive','on_leave'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='doctor_profile', lazy=True)
    department = db.relationship('Department', backref='doctors', lazy=True)

    def to_dict(self):
        user = self.user
        return {
            'id': self.id, 'user_id': self.user_id,
            'full_name': f"Dr. {user.first_name} {user.last_name}" if user else None,
            'specialization': self.specialization, 'qualification': self.qualification,
            'pmdc_no': self.pmdc_no, 'experience_years': self.experience_years,
            'consultation_fee': float(self.consultation_fee),
            'availability_days': self.availability_days,
            'availability_start': str(self.availability_start) if self.availability_start else None,
            'availability_end': str(self.availability_end) if self.availability_end else None,
            'status': self.status, 'bio': self.bio,
            'department': self.department.name if self.department else None
        }


class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(20))
    description = db.Column(db.Text)
    head_doctor_id = db.Column(db.Integer)
    room_no = db.Column(db.String(50))
    floor = db.Column(db.String(20))
    status = db.Column(db.Enum('active','inactive'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'code': self.code,
            'description': self.description, 'room_no': self.room_no,
            'floor': self.floor, 'status': self.status
        }
