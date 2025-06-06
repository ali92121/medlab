from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app import db
from backend.lab_app.models import Patient, SymptomAssessment, StandardizedScaleAssessment
import datetime

assessment_bp = Blueprint('assessment_bp', __name__)

# Utility for basic audit logging (can be expanded or imported from a shared utility)
def audit_log(action, patient_id=None, assessment_id=None, details=None):
    log_message = f"AUDIT: Action='{action}'"
    if patient_id:
        log_message += f", PatientID='{patient_id}'"
    if assessment_id:
        log_message += f", AssessmentID='{assessment_id}'"
    if details:
        log_message += f", Details='{details}'"
    log_message += f", Timestamp='{datetime.datetime.utcnow().isoformat()}'"
    print(log_message) # Basic logging to console

# --- SymptomAssessment Endpoints ---

@assessment_bp.route('/patients/<int:patient_id>/symptom-assessments', methods=['POST'])
@jwt_required()
def create_symptom_assessment(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if not patient.is_active:
        return jsonify({'message': 'Cannot add assessment to an inactive patient'}), 400

    data = request.get_json()
    if not data or not data.get('symptom_description'):
        return jsonify({'message': 'Missing required fields (symptom_description)'}), 400

    new_assessment = SymptomAssessment(
        patient_id=patient_id,
        assessment_date=datetime.datetime.strptime(data['assessment_date'], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('assessment_date') else datetime.datetime.utcnow(),
        assessor_type=data.get('assessor_type'),
        assessment_context_group=data.get('assessment_context_group'),
        dsm5tr_criterion_code=data.get('dsm5tr_criterion_code'),
        icd11_symptom_code=data.get('icd11_symptom_code'),
        symptom_description=data['symptom_description'],
        severity_score=data.get('severity_score'),
        frequency=data.get('frequency'),
        duration=data.get('duration'),
        notes=data.get('notes')
    )

    try:
        db.session.add(new_assessment)
        db.session.commit()
        audit_log('CREATE_SYMPTOM_ASSESSMENT_SUCCESS', patient_id=patient_id, assessment_id=new_assessment.id, details=f"Symptom: {new_assessment.symptom_description}")
        return jsonify(new_assessment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        audit_log('CREATE_SYMPTOM_ASSESSMENT_FAILED', patient_id=patient_id, details=str(e))
        return jsonify({'message': 'Failed to create symptom assessment', 'error': str(e)}), 500

@assessment_bp.route('/patients/<int:patient_id>/symptom-assessments', methods=['GET'])
@jwt_required()
def get_symptom_assessments_for_patient(patient_id):
    Patient.query.get_or_404(patient_id) # Ensure patient exists

    assessments = SymptomAssessment.query.filter_by(patient_id=patient_id).order_by(SymptomAssessment.assessment_date.desc()).all()
    return jsonify([assessment.to_dict() for assessment in assessments]), 200

# --- StandardizedScaleAssessment Endpoints ---

@assessment_bp.route('/patients/<int:patient_id>/standardized-scale-assessments', methods=['POST'])
@jwt_required()
def create_standardized_scale_assessment(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if not patient.is_active:
        return jsonify({'message': 'Cannot add assessment to an inactive patient'}), 400

    data = request.get_json()
    if not data or not data.get('scale_name'):
        return jsonify({'message': 'Missing required fields (scale_name)'}), 400

    new_assessment = StandardizedScaleAssessment(
        patient_id=patient_id,
        assessment_date=datetime.datetime.strptime(data['assessment_date'], '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('assessment_date') else datetime.datetime.utcnow(),
        scale_name=data['scale_name'],
        total_score=data.get('total_score'),
        item_responses=data.get('item_responses'), # Expecting a JSON object or dict
        overall_comment=data.get('overall_comment')
    )

    try:
        db.session.add(new_assessment)
        db.session.commit()
        audit_log('CREATE_STANDARDIZED_SCALE_ASSESSMENT_SUCCESS', patient_id=patient_id, assessment_id=new_assessment.id, details=f"Scale: {new_assessment.scale_name}")
        return jsonify(new_assessment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        audit_log('CREATE_STANDARDIZED_SCALE_ASSESSMENT_FAILED', patient_id=patient_id, details=str(e))
        return jsonify({'message': 'Failed to create standardized scale assessment', 'error': str(e)}), 500

@assessment_bp.route('/patients/<int:patient_id>/standardized-scale-assessments', methods=['GET'])
@jwt_required()
def get_standardized_scale_assessments_for_patient(patient_id):
    Patient.query.get_or_404(patient_id) # Ensure patient exists

    assessments = StandardizedScaleAssessment.query.filter_by(patient_id=patient_id).order_by(StandardizedScaleAssessment.assessment_date.desc()).all()
    return jsonify([assessment.to_dict() for assessment in assessments]), 200

# Future: Consider GET by assessment ID, PUT, DELETE for assessments if needed.
