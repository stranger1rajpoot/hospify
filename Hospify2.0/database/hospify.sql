-- ============================================
-- HOSPIFY - Hospital Management System
-- Database Schema v1.0
-- Pakistani Market Edition
-- ============================================

CREATE DATABASE IF NOT EXISTS hospify_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hospify_db;

-- ============================================
-- HOSPITALS TABLE (Multi-Tenant)
-- ============================================
CREATE TABLE hospitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    address TEXT,
    city VARCHAR(100),
    province VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(150),
    logo_url VARCHAR(255),
    license_no VARCHAR(100),
    type ENUM('clinic','small','medium','large') DEFAULT 'medium',
    status ENUM('active','inactive','suspended') DEFAULT 'active',
    subscription_plan ENUM('basic','standard','premium') DEFAULT 'standard',
    subscription_expiry DATE,
    tax_no VARCHAR(50),
    currency VARCHAR(10) DEFAULT 'PKR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- ROLES TABLE
-- ============================================
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    permissions JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO roles (name, display_name, description) VALUES
('super_admin', 'Super Admin', 'Full system access across all hospitals'),
('hospital_admin', 'Hospital Admin', 'Full access within their hospital'),
('doctor', 'Doctor', 'Patient care, prescriptions, appointments'),
('nurse', 'Nurse', 'Vitals, patient care notes, medication tracking'),
('receptionist', 'Receptionist', 'Patient registration, appointments, billing support'),
('pharmacist', 'Pharmacist', 'Pharmacy inventory, billing, prescriptions'),
('lab_technician', 'Lab Technician', 'Test reports, lab billing, results'),
('accountant', 'Accountant', 'Invoices, payments, financial reports'),
('patient', 'Patient', 'View own records, appointments, reports');

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT,
    role_id INT NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender ENUM('male','female','other'),
    date_of_birth DATE,
    address TEXT,
    city VARCHAR(100),
    profile_image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    remember_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expiry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- ============================================
-- DEPARTMENTS TABLE
-- ============================================
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    code VARCHAR(20),
    description TEXT,
    head_doctor_id INT,
    room_no VARCHAR(50),
    floor VARCHAR(20),
    status ENUM('active','inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ============================================
-- DOCTORS TABLE
-- ============================================
CREATE TABLE doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    hospital_id INT NOT NULL,
    department_id INT,
    specialization VARCHAR(200),
    qualification VARCHAR(300),
    pmdc_no VARCHAR(50),
    experience_years INT DEFAULT 0,
    consultation_fee DECIMAL(10,2) DEFAULT 0.00,
    availability_days VARCHAR(100),
    availability_start TIME,
    availability_end TIME,
    max_patients_per_day INT DEFAULT 30,
    bio TEXT,
    signature_url VARCHAR(255),
    status ENUM('active','inactive','on_leave') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- ============================================
-- PATIENTS TABLE
-- ============================================
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    user_id INT,
    mrn VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    gender ENUM('male','female','other') NOT NULL,
    date_of_birth DATE,
    age INT,
    blood_group ENUM('A+','A-','B+','B-','O+','O-','AB+','AB-','Unknown') DEFAULT 'Unknown',
    phone VARCHAR(20),
    phone_alt VARCHAR(20),
    email VARCHAR(150),
    address TEXT,
    city VARCHAR(100),
    cnic VARCHAR(20),
    emergency_contact_name VARCHAR(150),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relation VARCHAR(50),
    allergies TEXT,
    chronic_conditions TEXT,
    insurance_provider VARCHAR(150),
    insurance_no VARCHAR(100),
    patient_type ENUM('opd','ipd','both') DEFAULT 'opd',
    status ENUM('active','inactive','deceased') DEFAULT 'active',
    registered_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================
-- APPOINTMENTS TABLE
-- ============================================
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    department_id INT,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    token_no INT,
    type ENUM('opd','ipd','telemedicine','follow_up') DEFAULT 'opd',
    status ENUM('scheduled','confirmed','in_progress','completed','cancelled','no_show') DEFAULT 'scheduled',
    chief_complaint TEXT,
    notes TEXT,
    fee DECIMAL(10,2) DEFAULT 0.00,
    fee_paid BOOLEAN DEFAULT FALSE,
    booked_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- ============================================
-- VITALS TABLE
-- ============================================
CREATE TABLE vitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    patient_id INT NOT NULL,
    appointment_id INT,
    temperature DECIMAL(5,2),
    pulse_rate INT,
    blood_pressure_systolic INT,
    blood_pressure_diastolic INT,
    respiratory_rate INT,
    oxygen_saturation DECIMAL(5,2),
    weight DECIMAL(6,2),
    height DECIMAL(6,2),
    bmi DECIMAL(5,2),
    notes TEXT,
    recorded_by INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- ============================================
-- PRESCRIPTIONS TABLE
-- ============================================
CREATE TABLE prescriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_id INT,
    prescription_no VARCHAR(50) UNIQUE NOT NULL,
    diagnosis TEXT,
    clinical_notes TEXT,
    advice TEXT,
    follow_up_date DATE,
    is_dispensed BOOLEAN DEFAULT FALSE,
    dispensed_at TIMESTAMP,
    pdf_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- ============================================
-- PRESCRIPTION ITEMS TABLE
-- ============================================
CREATE TABLE prescription_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medicine_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration VARCHAR(100),
    route VARCHAR(50),
    instructions TEXT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
);

-- ============================================
-- MEDICINES TABLE (Pharmacy Inventory)
-- ============================================
CREATE TABLE medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    category VARCHAR(100),
    manufacturer VARCHAR(200),
    batch_no VARCHAR(100),
    barcode VARCHAR(100),
    unit ENUM('tablet','capsule','syrup','injection','cream','drops','sachet','other') DEFAULT 'tablet',
    strength VARCHAR(50),
    purchase_price DECIMAL(10,2) DEFAULT 0.00,
    sale_price DECIMAL(10,2) DEFAULT 0.00,
    stock_quantity INT DEFAULT 0,
    min_stock_level INT DEFAULT 10,
    expiry_date DATE,
    location VARCHAR(100),
    requires_prescription BOOLEAN DEFAULT FALSE,
    status ENUM('available','out_of_stock','expired','discontinued') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ============================================
-- PHARMACY SALES TABLE
-- ============================================
CREATE TABLE pharmacy_sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    patient_id INT,
    prescription_id INT,
    sale_no VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    discount DECIMAL(10,2) DEFAULT 0.00,
    tax DECIMAL(10,2) DEFAULT 0.00,
    paid_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_method ENUM('cash','card','easypaisa','jazzcash','credit') DEFAULT 'cash',
    status ENUM('pending','completed','cancelled','refunded') DEFAULT 'completed',
    sold_by INT,
    sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE SET NULL
);

-- ============================================
-- PHARMACY SALE ITEMS TABLE
-- ============================================
CREATE TABLE pharmacy_sale_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    medicine_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES pharmacy_sales(id) ON DELETE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

-- ============================================
-- LAB TESTS TABLE
-- ============================================
CREATE TABLE lab_tests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50),
    category VARCHAR(100),
    description TEXT,
    price DECIMAL(10,2) DEFAULT 0.00,
    normal_range VARCHAR(200),
    unit VARCHAR(50),
    turnaround_time VARCHAR(100),
    status ENUM('active','inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ============================================
-- LAB REPORTS TABLE
-- ============================================
CREATE TABLE lab_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT,
    appointment_id INT,
    report_no VARCHAR(50) UNIQUE NOT NULL,
    status ENUM('requested','sample_collected','in_progress','completed','cancelled') DEFAULT 'requested',
    priority ENUM('routine','urgent','stat') DEFAULT 'routine',
    clinical_notes TEXT,
    collected_at TIMESTAMP,
    completed_at TIMESTAMP,
    pdf_url VARCHAR(255),
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    paid_amount DECIMAL(10,2) DEFAULT 0.00,
    requested_by INT,
    processed_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- ============================================
-- LAB REPORT ITEMS TABLE
-- ============================================
CREATE TABLE lab_report_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_id INT NOT NULL,
    test_id INT NOT NULL,
    result_value VARCHAR(255),
    unit VARCHAR(50),
    normal_range VARCHAR(200),
    status ENUM('normal','abnormal','critical') DEFAULT 'normal',
    notes TEXT,
    FOREIGN KEY (report_id) REFERENCES lab_reports(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES lab_tests(id) ON DELETE CASCADE
);

-- ============================================
-- INVOICES TABLE
-- ============================================
CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    patient_id INT NOT NULL,
    invoice_no VARCHAR(50) UNIQUE NOT NULL,
    type ENUM('consultation','pharmacy','lab','admission','other') DEFAULT 'consultation',
    appointment_id INT,
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    discount DECIMAL(10,2) DEFAULT 0.00,
    tax DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    paid_amount DECIMAL(10,2) DEFAULT 0.00,
    due_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_method ENUM('cash','card','easypaisa','jazzcash','credit','insurance') DEFAULT 'cash',
    payment_status ENUM('pending','partial','paid','overdue','cancelled') DEFAULT 'pending',
    due_date DATE,
    notes TEXT,
    generated_by INT,
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- ============================================
-- INVOICE ITEMS TABLE
-- ============================================
CREATE TABLE invoice_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    quantity INT DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

-- ============================================
-- WARD/BED MANAGEMENT TABLE
-- ============================================
CREATE TABLE wards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    type ENUM('general','private','semi_private','icu','nicu','emergency') DEFAULT 'general',
    total_beds INT DEFAULT 0,
    available_beds INT DEFAULT 0,
    floor VARCHAR(20),
    status ENUM('active','inactive') DEFAULT 'active',
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ============================================
-- ADMISSIONS (IPD) TABLE
-- ============================================
CREATE TABLE admissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    ward_id INT,
    bed_no VARCHAR(20),
    admission_date DATETIME NOT NULL,
    discharge_date DATETIME,
    diagnosis TEXT,
    status ENUM('admitted','discharged','transferred') DEFAULT 'admitted',
    admitted_by INT,
    discharged_by INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    FOREIGN KEY (ward_id) REFERENCES wards(id) ON DELETE SET NULL
);

-- ============================================
-- NOTIFICATIONS TABLE
-- ============================================
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT,
    user_id INT,
    type ENUM('appointment','lab','billing','pharmacy','general','alert') DEFAULT 'general',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    channel ENUM('in_app','sms','email') DEFAULT 'in_app',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================
-- AUDIT LOGS TABLE
-- ============================================
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    module VARCHAR(100),
    record_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================
-- EXPENSES TABLE
-- ============================================
CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    category VARCHAR(100),
    description TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash','card','bank_transfer') DEFAULT 'cash',
    expense_date DATE NOT NULL,
    receipt_url VARCHAR(255),
    approved_by INT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- ============================================
-- SYSTEM SETTINGS TABLE
-- ============================================
CREATE TABLE system_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_group VARCHAR(50),
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_setting (hospital_id, setting_key)
);

-- ============================================
-- SAMPLE DATA
-- ============================================

-- Insert demo hospital
INSERT INTO hospitals (name, code, address, city, province, phone, email, type, status, subscription_plan) VALUES
('City General Hospital', 'CGH001', 'Main Boulevard, Gulberg III', 'Lahore', 'Punjab', '+92-42-35761234', 'info@citygeneralhospital.pk', 'large', 'active', 'premium'),
('Shifa Medical Center', 'SMC002', 'F-8 Markaz', 'Islamabad', 'ICT', '+92-51-2874523', 'info@shifamedical.pk', 'medium', 'active', 'standard'),
('Al-Noor Clinic', 'ANC003', 'Saddar Bazaar', 'Karachi', 'Sindh', '+92-21-35641111', 'info@alnoorclinic.pk', 'clinic', 'active', 'basic');

-- Insert default system settings
INSERT INTO system_settings (hospital_id, setting_key, setting_value, setting_group) VALUES
(1, 'currency', 'PKR', 'billing'),
(1, 'tax_rate', '5', 'billing'),
(1, 'opd_token_prefix', 'OPD', 'appointments'),
(1, 'invoice_prefix', 'INV', 'billing'),
(1, 'prescription_prefix', 'RX', 'prescriptions'),
(1, 'lab_report_prefix', 'LAB', 'lab');

-- Insert demo departments for hospital 1
INSERT INTO departments (hospital_id, name, code, description) VALUES
(1, 'Cardiology', 'CARD', 'Heart and cardiovascular diseases'),
(1, 'Orthopedics', 'ORTH', 'Bone and joint treatments'),
(1, 'Pediatrics', 'PEDI', 'Children health care'),
(1, 'Gynecology', 'GYNE', 'Women health and maternity'),
(1, 'Neurology', 'NEUR', 'Brain and nervous system'),
(1, 'Emergency', 'EMRG', '24/7 emergency services'),
(1, 'Radiology', 'RADI', 'X-Ray, MRI, CT Scan'),
(1, 'Pharmacy', 'PHRM', 'Medicine dispensing'),
(1, 'Laboratory', 'LABR', 'Diagnostic testing');

-- Insert common lab tests
INSERT INTO lab_tests (hospital_id, name, code, category, price, normal_range, unit, turnaround_time) VALUES
(1, 'Complete Blood Count (CBC)', 'CBC', 'Hematology', 800.00, 'See report', '', '4-6 hours'),
(1, 'Blood Sugar Fasting', 'BSF', 'Biochemistry', 300.00, '70-100', 'mg/dL', '1-2 hours'),
(1, 'Blood Sugar Random', 'BSR', 'Biochemistry', 300.00, '< 140', 'mg/dL', '1 hour'),
(1, 'HbA1c', 'HBA1C', 'Biochemistry', 1200.00, '< 5.7%', '%', '24 hours'),
(1, 'Lipid Profile', 'LIPID', 'Biochemistry', 1500.00, 'See report', '', '24 hours'),
(1, 'Liver Function Test (LFT)', 'LFT', 'Biochemistry', 1800.00, 'See report', '', '24 hours'),
(1, 'Kidney Function Test (KFT)', 'KFT', 'Biochemistry', 1800.00, 'See report', '', '24 hours'),
(1, 'Thyroid Function Test (TFT)', 'TFT', 'Biochemistry', 2500.00, 'See report', '', '24 hours'),
(1, 'Urinalysis', 'URINE', 'Microbiology', 500.00, 'See report', '', '2-4 hours'),
(1, 'ECG', 'ECG', 'Cardiology', 600.00, 'Normal sinus rhythm', '', '30 min'),
(1, 'Chest X-Ray', 'CXR', 'Radiology', 1000.00, 'Clear', '', '1-2 hours'),
(1, 'COVID-19 PCR', 'COVID', 'Microbiology', 4500.00, 'Negative', '', '24-48 hours');

-- Insert sample medicines
INSERT INTO medicines (hospital_id, name, generic_name, category, manufacturer, unit, strength, purchase_price, sale_price, stock_quantity, expiry_date) VALUES
(1, 'Panadol', 'Paracetamol', 'Analgesic', 'GSK', 'tablet', '500mg', 5.00, 8.00, 500, '2026-12-31'),
(1, 'Augmentin', 'Amoxicillin/Clavulanate', 'Antibiotic', 'GSK', 'tablet', '625mg', 85.00, 120.00, 200, '2026-06-30'),
(1, 'Brufen', 'Ibuprofen', 'NSAID', 'Abbott', 'tablet', '400mg', 8.00, 12.00, 350, '2026-09-30'),
(1, 'Risek', 'Omeprazole', 'PPI', 'Getz Pharma', 'capsule', '20mg', 15.00, 22.00, 300, '2026-11-30'),
(1, 'Glucophage', 'Metformin', 'Antidiabetic', 'Merck', 'tablet', '500mg', 12.00, 18.00, 400, '2027-01-31'),
(1, 'Lipitor', 'Atorvastatin', 'Statin', 'Pfizer', 'tablet', '20mg', 45.00, 65.00, 150, '2026-08-31'),
(1, 'Tenormin', 'Atenolol', 'Beta-Blocker', 'AstraZeneca', 'tablet', '50mg', 18.00, 28.00, 250, '2026-10-31'),
(1, 'Amoxil', 'Amoxicillin', 'Antibiotic', 'GSK', 'capsule', '500mg', 20.00, 30.00, 180, '2026-07-31'),
(1, 'Ventolin Inhaler', 'Salbutamol', 'Bronchodilator', 'GSK', 'other', '100mcg', 180.00, 250.00, 80, '2026-05-31'),
(1, 'Calpol Syrup', 'Paracetamol', 'Analgesic', 'GSK', 'syrup', '120mg/5ml', 55.00, 80.00, 120, '2026-04-30');
