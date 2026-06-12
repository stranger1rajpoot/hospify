from extensions import db
from datetime import datetime

class Hospital(db.Model):
    __tablename__ = 'hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(150))
    logo_url = db.Column(db.String(255))
    license_no = db.Column(db.String(100))
    type = db.Column(db.Enum('clinic','small','medium','large'), default='medium')
    status = db.Column(db.Enum('active','inactive','suspended'), default='active')
    subscription_plan = db.Column(db.Enum('basic','standard','premium'), default='standard')
    subscription_expiry = db.Column(db.Date)
    tax_no = db.Column(db.String(50))
    currency = db.Column(db.String(10), default='PKR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'code': self.code,
            'address': self.address, 'city': self.city, 'province': self.province,
            'phone': self.phone, 'email': self.email, 'logo_url': self.logo_url,
            'type': self.type, 'status': self.status,
            'subscription_plan': self.subscription_plan,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
