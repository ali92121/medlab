from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID as PyUUID
from datetime import datetime
from ..services.caregiver_service import add_caregiver_observation, get_caregiver_observations_for_patient, get_patient_data_for_caregiver
from ..database import get_db
from sqlalchemy.orm import Session

caregiver_bp = Blueprint('caregiver', __name__, url_prefix='/api/caregiver')

class CaregiverObservationRequest(BaseModel):
    caregiver_relationship_id: PyUUID
    mood_rating_1_10: Optional[int] = None; activity_level_1_5: Optional[int] = None
    social_interaction_level_1_5: Optional[int] = None; medication_adherence_observed: Optional[str] = None
    behavioral_notes: Optional[str] = None; concerns_notes: Optional[str] = None

class CaregiverObservationResponseItem(BaseModel):
    id: PyUUID; caregiver_relationship_id: PyUUID; patient_id: int; caregiver_user_id: int
    observation_date: Optional[datetime] = None; mood_rating_1_10: Optional[int] = None
    activity_level_1_5: Optional[int] = None; medication_adherence_observed: Optional[str] = None
    behavioral_notes: Optional[str] = None

class PatientDataForCaregiverResponse(BaseModel):
    patient_id: int; access_level_granted: str; data: Dict[str, Any]

@caregiver_bp.route('/observations', methods=['POST'])
@jwt_required()
def post_caregiver_observation_api():
    caregiver_user_id = 2 # Placeholder
    try:
        req_data_raw = request.get_json(); assert req_data_raw is not None
        req_data = CaregiverObservationRequest(**req_data_raw)
    except Exception as e: return jsonify({"error": "Invalid observation payload", "details": str(e)}), 400
    db: Session = next(get_db())
    try:
        observation_result = add_caregiver_observation(caregiver_user_id=caregiver_user_id, relationship_id=req_data.caregiver_relationship_id, data=req_data.dict(exclude_none=True), db_session=db)
        if observation_result.get("error"): return jsonify(observation_result), 400
        return jsonify(observation_result), 201
    except Exception as e:
        current_app.logger.error(f"Caregiver obs error: {e}", exc_info=True)
        return jsonify({"error": "Failed to add caregiver observation", "details": str(e)}), 500
    finally: db.close()

@caregiver_bp.route('/patients/<int:patient_id>/observations', methods=['GET'])
@jwt_required()
def get_observations_for_patient_api(patient_id: int):
    db: Session = next(get_db())
    try:
        observations_db = get_caregiver_observations_for_patient(patient_id, db)
        observations_resp = [CaregiverObservationResponseItem(**obs.to_dict()) for obs in observations_db]
        return jsonify([item.dict() for item in observations_resp]), 200
    except Exception as e:
        current_app.logger.error(f"Get caregiver obs error: {e}", exc_info=True)
        return jsonify({"error": "Failed to get caregiver observations", "details": str(e)}), 500
    finally: db.close()

@caregiver_bp.route('/patients/<int:patient_id>/view-data', methods=['GET'])
@jwt_required()
def get_patient_info_for_caregiver_view_api(patient_id: int):
    caregiver_user_id = 2 # Placeholder
    db: Session = next(get_db())
    try:
        patient_view_data_dict = get_patient_data_for_caregiver(caregiver_user_id=caregiver_user_id, patient_id=patient_id, db_session=db) # Fix variable name
        if patient_view_data_dict.get("error"): return jsonify(patient_view_data_dict), 403
        response_model = PatientDataForCaregiverResponse(**patient_view_data_dict)
        return jsonify(response_model.dict()), 200
    except Exception as e:
        current_app.logger.error(f"Caregiver view data error: {e}", exc_info=True)
        return jsonify({"error": "Failed to get patient data for caregiver", "details": str(e)}), 500
    finally: db.close()
