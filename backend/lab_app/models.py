from backend.app import db
import datetime

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    # For a real application, psychiatry_id should be unique and perhaps indexed
    # For now, keeping it simple. Consider encryption for sensitive IDs if required by regulations.
    psychiatry_id = db.Column(db.String(100), nullable=True, index=True)

    # Basic patient information
    # These fields would ideally be encrypted if they contain PII/PHI.
    # For this phase, direct storage is used for simplicity.
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(50), nullable=True) # E.g., Male, Female, Other, Prefer not to say

    # Contact Information (simplified)
    phone_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True) # Consider validation if used for communication

    # Address (simplified)
    address_line1 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state_province = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)

    # Emergency Contact (simplified)
    emergency_contact_name = db.Column(db.String(255), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)
    emergency_contact_relationship = db.Column(db.String(100), nullable=True)

    # Clinical Information (very basic for now)
    primary_care_physician = db.Column(db.String(255), nullable=True)
    # More detailed clinical info will be in separate tables (assessments, medications, etc.)

    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # For soft delete
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<Patient {self.first_name} {self.last_name} (ID: {self.psychiatry_id})>'

    def to_dict(self):
        return {
            'id': self.id,
            'psychiatry_id': self.psychiatry_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'phone_number': self.phone_number,
            'email': self.email,
            'address': {
                'address_line1': self.address_line1,
                'city': self.city,
                'state_province': self.state_province,
                'postal_code': self.postal_code,
                'country': self.country
            },
            'emergency_contact': {
                'name': self.emergency_contact_name,
                'phone': self.emergency_contact_phone,
                'relationship': self.emergency_contact_relationship
            },
            'primary_care_physician': self.primary_care_physician,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }

# SymptomAssessment model will be added here later
# StandardizedScaleAssessment model will be added here later
# Medication model will be added here later


class SymptomAssessment(db.Model):
    __tablename__ = 'symptom_assessments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    assessor_type = db.Column(db.String(50), nullable=True)  # 'clinician', 'self_report'

    # Grouping for UI and context
    assessment_context_group = db.Column(db.String(200), nullable=True) # e.g., "Depressive Symptoms", "Anxiety Symptoms", "Manic Symptoms"

    # DSM-5-TR / ICD-11 Related fields
    dsm5tr_criterion_code = db.Column(db.String(50), nullable=True) # e.g., "MDD.A1"
    icd11_symptom_code = db.Column(db.String(50), nullable=True)

    symptom_description = db.Column(db.String(255), nullable=False) # Clinician-entered or pre-defined symptom
    severity_score = db.Column(db.Integer, nullable=True) # e.g., 0-4 scale
    frequency = db.Column(db.String(100), nullable=True) # e.g., 'Daily', 'Multiple times a week'
    duration = db.Column(db.String(100), nullable=True) # e.g., 'Past 2 weeks', 'Over 6 months'

    notes = db.Column(db.Text, nullable=True) # Notes for this specific symptom instance
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref('symptom_assessments', lazy='dynamic'))

    def __repr__(self):
        return f'<SymptomAssessment {self.id} for Patient {self.patient_id} on {self.assessment_date.strftime("%Y-%m-%d")}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'assessment_date': self.assessment_date.isoformat(),
            'assessor_type': self.assessor_type,
            'assessment_context_group': self.assessment_context_group,
            'dsm5tr_criterion_code': self.dsm5tr_criterion_code,
            'icd11_symptom_code': self.icd11_symptom_code,
            'symptom_description': self.symptom_description,
            'severity_score': self.severity_score,
            'frequency': self.frequency,
            'duration': self.duration,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }

class StandardizedScaleAssessment(db.Model):
    __tablename__ = 'standardized_scale_assessments'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    scale_name = db.Column(db.String(100), nullable=False)  # e.g., 'PHQ-9', 'GAD-7', 'HAM-D-17'
    total_score = db.Column(db.Integer, nullable=True)

    # For SQLite, store detailed responses as JSON string in a Text field if db.JSON is problematic.
    # SQLAlchemy's db.JSON type handles this for supported backends (like PostgreSQL, and modern SQLite).
    item_responses = db.Column(db.JSON, nullable=True) # or db.Text for manual JSON handling

    overall_comment = db.Column(db.Text, nullable=True) # Single comment for the overall scale assessment
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    patient = db.relationship('Patient', backref=db.backref('standardized_scale_assessments', lazy='dynamic'))

    def __repr__(self):
        return f'<StandardizedScaleAssessment {self.id} ({self.scale_name}) for Patient {self.patient_id} on {self.assessment_date.strftime("%Y-%m-%d")}>'

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'assessment_date': self.assessment_date.isoformat(),
            'scale_name': self.scale_name,
            'total_score': self.total_score,
            'item_responses': self.item_responses, # Assumes item_responses is JSON serializable
            'overall_comment': self.overall_comment,
            'created_at': self.created_at.isoformat()
        }
