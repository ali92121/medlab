import datetime
import enum
import uuid
from sqlalchemy import event, inspect, text, Index, CheckConstraint
from lab_app import db
from flask import current_app
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from sqlalchemy.ext.hybrid import hybrid_property
# from sqlalchemy.dialects.postgresql import JSONB # Not for SQLite

# It's better to fetch ENCRYPTION_KEY once, or ensure it's correctly configured in the app context
# For EncryptedType, the key argument is usually passed directly.
# We'll define a helper to get the key from the current app's config.
def get_encryption_key():
    key = current_app.config.get('ENCRYPTION_KEY')
    if not key:
        raise ValueError("ENCRYPTION_KEY not found in Flask app config.")
    # Ensure the key is suitable for AesEngine (e.g., if it needs to be bytes)
    # AesEngine can take a string key; it will hash it to 32 bytes if not already that size.
    return key

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    psychiatry_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    medical_record_number = db.Column(db.String(100), unique=True, nullable=True, index=True)

    # Encrypted Demographics
    # Pass the key directly to EncryptedType.
    # AesEngine is the default, 'pkcs5' is default padding.
    _first_name = db.Column("first_name", EncryptedType(db.String(255), get_encryption_key, AesEngine))
    _last_name = db.Column("last_name", EncryptedType(db.String(255), get_encryption_key, AesEngine))
    _date_of_birth = db.Column("date_of_birth", EncryptedType(db.Date, get_encryption_key, AesEngine))

    gender = db.Column(db.String(50)) # Not typically encrypted unless policy dictates

    _phone_number = db.Column("phone_number", EncryptedType(db.String(30), get_encryption_key, AesEngine), nullable=True)
    _email = db.Column("email", EncryptedType(db.String(255), get_encryption_key, AesEngine), nullable=True)
    _address = db.Column("address", EncryptedType(db.Text, get_encryption_key, AesEngine), nullable=True)

    _emergency_contact_name = db.Column("emergency_contact_name", EncryptedType(db.String(255), get_encryption_key, AesEngine), nullable=True)
    _emergency_contact_phone = db.Column("emergency_contact_phone", EncryptedType(db.String(30), get_encryption_key, AesEngine), nullable=True)
    emergency_contact_relationship = db.Column(db.String(100), nullable=True) # Not typically encrypted

    primary_language = db.Column(db.String(100), nullable=True)
    insurance_provider = db.Column(db.String(200), nullable=True) # Potentially sensitive, consider encryption
    referring_physician = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    ml_features_extracted = db.Column(db.Boolean, default=False)
    feature_extraction_date = db.Column(db.DateTime, nullable=True)

    # Hybrid properties for encrypted fields
    @hybrid_property
    def first_name(self):
        return self._first_name
    @first_name.setter
    def first_name(self, value):
        self._first_name = value

    @hybrid_property
    def last_name(self):
        return self._last_name
    @last_name.setter
    def last_name(self, value):
        self._last_name = value

    @hybrid_property
    def date_of_birth(self):
        return self._date_of_birth
    @date_of_birth.setter
    def date_of_birth(self, value):
        self._date_of_birth = value

    @hybrid_property
    def phone_number(self):
        return self._phone_number
    @phone_number.setter
    def phone_number(self, value):
        self._phone_number = value

    @hybrid_property
    def email(self):
        return self._email
    @email.setter
    def email(self, value):
        self._email = value

    @hybrid_property
    def address(self):
        return self._address
    @address.setter
    def address(self, value):
        self._address = value

    @hybrid_property
    def emergency_contact_name(self):
        return self._emergency_contact_name
    @emergency_contact_name.setter
    def emergency_contact_name(self, value):
        self._emergency_contact_name = value

    @hybrid_property
    def emergency_contact_phone(self):
        return self._emergency_contact_phone
    @emergency_contact_phone.setter
    def emergency_contact_phone(self, value):
        self._emergency_contact_phone = value

class MedicalHistory(db.Model):
    __tablename__ = 'medical_history'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    condition_name = db.Column(db.String(255), nullable=False)
    icd11_code = db.Column(db.String(20), nullable=True)
    dsm5tr_code = db.Column(db.String(20), nullable=True)
    onset_date = db.Column(db.Date, nullable=True)
    resolved_date = db.Column(db.Date, nullable=True)
    severity = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True) # Consider encryption if PHI
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    patient = db.relationship('Patient', backref=db.backref('medical_history_items', lazy='dynamic'))

# class LabTest(db.Model):
#     __tablename__ = 'lab_tests'
#     id = db.Column(db.Integer, primary_key=True)
#     patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
#     test_name = db.Column(db.String(200), nullable=False)
#     test_category = db.Column(db.String(100), nullable=True)
#     test_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
#     # result_summary = db.Column(db.Text, nullable=True) # Placeholder
#     created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
#     patient = db.relationship('Patient', backref=db.backref('lab_tests', lazy='dynamic'))

class SpecimenType(enum.Enum):
    SERUM = "serum"
    PLASMA = "plasma"
    WHOLE_BLOOD = "whole_blood"
    URINE = "urine"
    SALIVA = "saliva"
    CSF = "csf"
    TISSUE = "tissue"

class TestStatus(enum.Enum):
    ORDERED = "ordered"
    COLLECTED = "collected"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CRITICAL = "critical"
    CRITICAL_ACKNOWLEDGED = "critical_acknowledged"

class LabTestDefinition(db.Model):
    __tablename__ = 'lab_test_definitions'
    id = db.Column(db.Integer, primary_key=True)
    test_name = db.Column(db.String(255), nullable=False, index=True)
    short_name = db.Column(db.String(100), nullable=True, index=True)
    loinc_code = db.Column(db.String(50), nullable=True, index=True)
    category = db.Column(db.String(100), nullable=True, index=True)
    methodology = db.Column(db.String(255), nullable=True)
    specimen_type_options = db.Column(db.Text, nullable=True)  # JSON string for list of SpecimenType enums
    reference_ranges = db.Column(db.JSON, nullable=True) # JSON for complex reference ranges
    units = db.Column(db.String(50), nullable=True)
    normal_range_low = db.Column(db.Float, nullable=True)
    normal_range_high = db.Column(db.Float, nullable=True)
    critical_range_low = db.Column(db.Float, nullable=True)
    critical_range_high = db.Column(db.Float, nullable=True)
    turnaround_time_hours = db.Column(db.Integer, nullable=True) # Expected TAT in hours
    description = db.Column(db.Text, nullable=True)
    container_type = db.Column(db.String(100), nullable=True)
    storage_requirements = db.Column(db.String(255), nullable=True)
    cost_usd = db.Column(db.Numeric(10, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # Commenting out PostgreSQL specific index
    # __table_args__ = (
    #     Index('idx_test_name_fulltext', text('test_name'), postgresql_using='gin'),
    # )
    results = db.relationship('LabResult', backref='test_definition', lazy='dynamic')


class LabOrder(db.Model):
    __tablename__ = 'lab_orders'
    id = db.Column(db.Integer, primary_key=True)
    order_uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    ordering_physician_id = db.Column(db.String(255), nullable=True) # Could be FK to a User/Physician table
    order_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    priority = db.Column(db.String(50), default='routine', nullable=False) # e.g., routine, stat
    status = db.Column(db.Enum(TestStatus), default=TestStatus.ORDERED, nullable=False, index=True)
    specimen_type = db.Column(db.Enum(SpecimenType), nullable=True)
    specimen_collection_datetime = db.Column(db.DateTime, nullable=True)
    specimen_received_datetime = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    related_diagnoses_codes = db.Column(db.Text, nullable=True) # JSON string for list of ICD/DSM codes
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref('lab_orders', lazy='dynamic'))
    results = db.relationship('LabResult', backref='lab_order', lazy='dynamic')


class LabResult(db.Model):
    __tablename__ = 'lab_results'
    id = db.Column(db.Integer, primary_key=True)
    result_uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    lab_order_id = db.Column(db.Integer, db.ForeignKey('lab_orders.id'), nullable=False, index=True)
    test_definition_id = db.Column(db.Integer, db.ForeignKey('lab_test_definitions.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True) # Denormalized for easier queries

    result_type = db.Column(db.String(50), nullable=False) # e.g., numeric, text, range, ordinal
    result_value_text = db.Column(db.Text, nullable=True)
    result_numeric = db.Column(db.Float, nullable=True)
    result_units = db.Column(db.String(50), nullable=True)
    reference_range = db.Column(db.String(255), nullable=True) # e.g., "70-100", "<5.0"
    abnormal_flag = db.Column(db.String(50), nullable=True) # e.g., L, H, A, AA
    status = db.Column(db.Enum(TestStatus), default=TestStatus.PROCESSING, nullable=False, index=True)
    interpretation_notes = db.Column(db.Text, nullable=True)
    verified_by_user_id = db.Column(db.String(255), nullable=True) # Could be FK to User table
    result_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # lab_order = db.relationship('LabOrder', backref=db.backref('results', lazy='dynamic')) # Redundant due to LabOrder.results
    # test_definition = db.relationship('LabTestDefinition', backref=db.backref('results', lazy='dynamic')) # Redundant
    patient = db.relationship('Patient', backref=db.backref('lab_results', lazy='dynamic'))

    __table_args__ = (
        CheckConstraint("result_numeric IS NULL OR result_type = 'numeric'", name='numeric_result_constraint'),
    )


class CriticalValueAlert(db.Model):
    __tablename__ = 'critical_value_alerts'
    id = db.Column(db.Integer, primary_key=True)
    alert_uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    lab_result_id = db.Column(db.Integer, db.ForeignKey('lab_results.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    alert_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    alert_level = db.Column(db.String(50), nullable=False) # e.g., high, low, critical
    notified_personnel_id = db.Column(db.String(255), nullable=True) # Could be FK to User table
    notification_method = db.Column(db.String(100), nullable=True) # e.g., phone, pager, EHR alert
    acknowledgement_datetime = db.Column(db.DateTime, nullable=True)
    acknowledged_by_user_id = db.Column(db.String(255), nullable=True) # Could be FK to User table
    escalation_status = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    lab_result = db.relationship('LabResult', backref=db.backref('alerts', lazy='dynamic'))
    patient = db.relationship('Patient', backref=db.backref('critical_value_alerts', lazy='dynamic'))


class LabTrendAnalysis(db.Model):
    __tablename__ = 'lab_trend_analysis'
    id = db.Column(db.Integer, primary_key=True)
    analysis_uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    test_definition_id = db.Column(db.Integer, db.ForeignKey('lab_test_definitions.id'), nullable=False, index=True)
    analysis_type = db.Column(db.String(100), nullable=False) # e.g., baseline_change, rate_of_change
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    trend_data = db.Column(db.JSON, nullable=True) # Store calculated trend data (e.g., slope, intercept, p-value)
    summary_finding = db.Column(db.Text, nullable=True)
    generated_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref('trend_analyses', lazy='dynamic'))
    test_definition = db.relationship('LabTestDefinition', backref=db.backref('trend_analyses', lazy='dynamic'))


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    user_id_source = db.Column(db.String(255), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(100), nullable=True)
    record_id = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)

# Ensure models are imported in a way that Flask-Migrate can see them.
# Typically, importing 'db' and 'models' in relevant places (e.g., app factory or manage.py) is enough.
# The current lab_app.py and __init__.py structure should be fine.
# Make sure that the models are defined before migrate.init_app(app, db) is called in __init__.py
# This is handled by importing models into the same scope where 'db' is defined and used by Migrate.
# A common pattern is to import models in lab_app/__init__.py after db is defined.
# For now, we will ensure that flask db commands can find the models.
# The models need to be imported by the time `flask db migrate/upgrade` is run.
# This is typically handled by ensuring `lab_app.models` is imported by `lab_app/__init__.py` or `lab_app.py`.

# Add import of models to lab_app/__init__.py
# This will be done by modifying the __init__.py file.
