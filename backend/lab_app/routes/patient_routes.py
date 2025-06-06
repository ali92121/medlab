from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.lab_app.models import Patient
import datetime # For audit logging and date handling

patient_bp = Blueprint('patient_bp', __name__)

# Utility for basic audit logging (can be expanded)
def audit_log(action, patient_id=None, details=None):
    # In a real app, this would write to a dedicated audit log table or logging service
    log_message = f"AUDIT: Action='{action}'"
    if patient_id:
        log_message += f", PatientID='{patient_id}'"
    if details:
        log_message += f", Details='{details}'"
    log_message += f", Timestamp='{datetime.datetime.utcnow().isoformat()}'"
    print(log_message) # Basic logging to console for now

@patient_bp.route('', methods=['POST'])
@jwt_required()
def create_patient():
    data = request.get_json()

    # Basic validation
    required_fields = ['first_name', 'last_name'] # Add more as necessary e.g. psychiatry_id
    if not data or not all(field in data and data[field] for field in required_fields):
        return jsonify({'message': 'Missing required fields (first_name, last_name)'}), 400

    # Check for existing patient by psychiatry_id if it's meant to be unique
    if 'psychiatry_id' in data and data['psychiatry_id']:
        existing_patient = Patient.query.filter_by(psychiatry_id=data['psychiatry_id']).first()
        if existing_patient:
            return jsonify({'message': 'Patient with this psychiatry_id already exists'}), 409

    new_patient = Patient(
        psychiatry_id=data.get('psychiatry_id'),
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=datetime.datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date() if data.get('date_of_birth') else None,
        gender=data.get('gender'),
        phone_number=data.get('phone_number'),
        email=data.get('email'),
        address_line1=data.get('address', {}).get('address_line1'),
        city=data.get('address', {}).get('city'),
        state_province=data.get('address', {}).get('state_province'),
        postal_code=data.get('address', {}).get('postal_code'),
        country=data.get('address', {}).get('country'),
        emergency_contact_name=data.get('emergency_contact', {}).get('name'),
        emergency_contact_phone=data.get('emergency_contact', {}).get('phone'),
        emergency_contact_relationship=data.get('emergency_contact', {}).get('relationship'),
        primary_care_physician=data.get('primary_care_physician')
    )

    try:
        db.session.add(new_patient)
        db.session.commit()
        audit_log('CREATE_PATIENT_SUCCESS', patient_id=new_patient.id, details=f"Name: {new_patient.first_name} {new_patient.last_name}")
        return jsonify(new_patient.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        audit_log('CREATE_PATIENT_FAILED', details=str(e))
        return jsonify({'message': 'Failed to create patient', 'error': str(e)}), 500

@patient_bp.route('', methods=['GET'])
@jwt_required()
def get_patients():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', None, type=str)

    query = Patient.query.filter_by(is_active=True)

    if search_term:
        # Basic search on name or psychiatry_id.
        # Note: Searching on encrypted fields is complex and might require specific database solutions
        # or decryption if allowed and secure. For now, assuming fields are not encrypted or search is on non-sensitive identifiers.
        search_ilike = f"%{search_term}%"
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(search_ilike),
                Patient.last_name.ilike(search_ilike),
                Patient.psychiatry_id.ilike(search_ilike)
            )
        )

    query = query.order_by(Patient.last_name.asc(), Patient.first_name.asc())
    paginated_patients = query.paginate(page=page, per_page=per_page, error_out=False)

    patients_list = [patient.to_dict() for patient in paginated_patients.items]

    return jsonify({
        'patients': patients_list,
        'total_pages': paginated_patients.pages,
        'current_page': paginated_patients.page,
        'total_patients': paginated_patients.total
    }), 200

@patient_bp.route('/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if not patient.is_active:
         return jsonify({'message': 'Patient record is inactive'}), 404 # Or treat as 404
    return jsonify(patient.to_dict()), 200

@patient_bp.route('/<int:patient_id>', methods=['PUT'])
@jwt_required()
def update_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if not patient.is_active: # Optionally prevent updates on inactive patients
        return jsonify({'message': 'Cannot update an inactive patient record. Please reactivate first.'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    # Update fields - consider which fields are updatable
    patient.psychiatry_id = data.get('psychiatry_id', patient.psychiatry_id)
    patient.first_name = data.get('first_name', patient.first_name)
    patient.last_name = data.get('last_name', patient.last_name)
    if data.get('date_of_birth'):
        patient.date_of_birth = datetime.datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    patient.gender = data.get('gender', patient.gender)
    patient.phone_number = data.get('phone_number', patient.phone_number)
    patient.email = data.get('email', patient.email)

    address_data = data.get('address', {})
    patient.address_line1 = address_data.get('address_line1', patient.address_line1)
    patient.city = address_data.get('city', patient.city)
    patient.state_province = address_data.get('state_province', patient.state_province)
    patient.postal_code = address_data.get('postal_code', patient.postal_code)
    patient.country = address_data.get('country', patient.country)

    emergency_contact_data = data.get('emergency_contact', {})
    patient.emergency_contact_name = emergency_contact_data.get('name', patient.emergency_contact_name)
    patient.emergency_contact_phone = emergency_contact_data.get('phone', patient.emergency_contact_phone)
    patient.emergency_contact_relationship = emergency_contact_data.get('relationship', patient.emergency_contact_relationship)

    patient.primary_care_physician = data.get('primary_care_physician', patient.primary_care_physician)

    # patient.updated_at is handled by SQLAlchemy's onupdate

    try:
        db.session.commit()
        audit_log('UPDATE_PATIENT_SUCCESS', patient_id=patient.id, details=f"Updated fields for {patient.first_name} {patient.last_name}")
        return jsonify(patient.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        audit_log('UPDATE_PATIENT_FAILED', patient_id=patient.id, details=str(e))
        return jsonify({'message': 'Failed to update patient', 'error': str(e)}), 500

@patient_bp.route('/<int:patient_id>', methods=['DELETE'])
@jwt_required()
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if not patient.is_active:
        return jsonify({'message': 'Patient already inactive'}), 400 # Or 200 if idempotent

    patient.is_active = False
    # patient.updated_at is handled by SQLAlchemy's onupdate

    try:
        db.session.commit()
        audit_log('SOFT_DELETE_PATIENT_SUCCESS', patient_id=patient.id)
        return jsonify({'message': 'Patient marked as inactive successfully'}), 200
    except Exception as e:
        db.session.rollback()
        audit_log('SOFT_DELETE_PATIENT_FAILED', patient_id=patient.id, details=str(e))
        return jsonify({'message': 'Failed to mark patient as inactive', 'error': str(e)}), 500

# Example of how to potentially reactivate a patient (not in original spec, but good for completeness)
@patient_bp.route('/<int:patient_id>/reactivate', methods=['PUT'])
@jwt_required()
def reactivate_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.is_active:
        return jsonify({'message': 'Patient is already active'}), 400

    patient.is_active = True
    # patient.updated_at is handled by SQLAlchemy's onupdate

    try:
        db.session.commit()
        audit_log('REACTIVATE_PATIENT_SUCCESS', patient_id=patient.id)
        return jsonify({'message': 'Patient reactivated successfully', 'patient': patient.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        audit_log('REACTIVATE_PATIENT_FAILED', patient_id=patient.id, details=str(e))
        return jsonify({'message': 'Failed to reactivate patient', 'error': str(e)}), 500
