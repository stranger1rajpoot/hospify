from routes.auth import auth_bp
from routes.patients import patients_bp
from routes.appointments import appointments_bp
from routes.pharmacy import pharmacy_bp, billing_bp
from routes.lab import lab_bp, prescriptions_bp
from routes.admin import admin_bp
from routes.medicines import medicines_bp

__all__ = ['auth_bp', 'patients_bp', 'appointments_bp', 'pharmacy_bp', 'billing_bp', 'lab_bp', 'prescriptions_bp', 'admin_bp', 'medicines_bp']
