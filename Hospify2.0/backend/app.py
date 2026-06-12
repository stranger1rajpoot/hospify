import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, jsonify, request
from config import Config
from extensions import db, jwt, cors, mail

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS, "supports_credentials": True, "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]}})

    # Handle CORS preflight for all /api/* routes
    @app.before_request
    def handle_cors_preflight():
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            origin = request.headers.get('Origin', '')
            if origin in Config.CORS_ORIGINS:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response
    mail.init_app(app)

    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.patients import patients_bp
    from routes.appointments import appointments_bp
    from routes.pharmacy import pharmacy_bp, billing_bp
    from routes.lab import lab_bp, prescriptions_bp
    from routes.admin import admin_bp
    from routes.medicines import medicines_bp
    from routes.doctors import doctors_bp
    from routes.nurse import nurse_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(patients_bp, url_prefix='/api/patients')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(pharmacy_bp, url_prefix='/api/pharmacy')
    app.register_blueprint(billing_bp, url_prefix='/api/billing')
    app.register_blueprint(lab_bp, url_prefix='/api/lab')
    app.register_blueprint(prescriptions_bp, url_prefix='/api/prescriptions')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(medicines_bp, url_prefix='/api/medicines')
    app.register_blueprint(doctors_bp, url_prefix='/api/doctors')
    app.register_blueprint(nurse_bp, url_prefix='/api/nurse')

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'success': False, 'message': 'Token has expired', 'error': 'token_expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'success': False, 'message': 'Invalid token', 'error': 'invalid_token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'success': False, 'message': 'Authentication required', 'error': 'authorization_required'}), 401

    # Health check
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok', 'app': 'Hospify API', 'version': '1.0.0'}), 200

    # Create DB tables
    with app.app_context():
        db.create_all()
        _seed_super_admin(app)
        _seed_medicines(app)

    return app


def _seed_super_admin(app):
    """Create default roles and super admin if they don't exist"""
    from models import User, Role
    with app.app_context():
        try:
            roles = ['super_admin', 'hospital_admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician', 'accountant', 'patient']
            for r_name in roles:
                role = Role.query.filter_by(name=r_name).first()
                if not role:
                    db.session.add(Role(name=r_name, description=r_name.replace('_', ' ').title()))
            db.session.commit()

            super_role = Role.query.filter_by(name='super_admin').first()
            if not super_role:
                return
            existing = User.query.filter_by(role_id=super_role.id).first()
            if not existing:
                admin = User(
                    username='superadmin',
                    email='admin@hospify.pk',
                    first_name='Super',
                    last_name='Admin',
                    role_id=super_role.id,
                    is_active=True,
                    is_verified=True
                )
                admin.set_password('Admin@1234')
                db.session.add(admin)
                db.session.commit()
                print("[SUCCESS] Super Admin created: superadmin / Admin@1234")
        except Exception as e:
            print(f"[WARNING] Could not seed roles/super admin: {e}")


def _seed_medicines(app):
    from seed_medicines import seed_medicines
    seed_medicines(app)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
