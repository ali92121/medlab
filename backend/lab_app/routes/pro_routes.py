from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user
from pydantic import BaseModel, validator
from typing import List, Dict, Any, Optional
from uuid import UUID as PyUUID
from datetime import datetime
from ..services.pro_service import get_assigned_pro_instruments_for_patient, submit_pro_response, get_pro_history_for_patient
from ..database import get_db
from sqlalchemy.orm import Session

pro_bp = Blueprint('pro', __name__, url_prefix='/api/pro')

class PROSubmissionRequest(BaseModel):
    pro_assignment_id: PyUUID
    responses: Dict[str, Any]
    ema_prompt_time_iso: Optional[str] = None
    @validator('ema_prompt_time_iso')
    def validate_iso_format(cls, value):
        if value:
            try: datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError: raise ValueError('ema_prompt_time_iso must be valid ISO 8601')
        return value

class PROAssignmentItem(BaseModel):
    id: PyUUID; patient_id: int; pro_instrument_id: int; instrument_name: Optional[str] = None
    assigned_by_clinician_id: Optional[int] = None; assignment_date: Optional[datetime] = None
    frequency: Optional[str] = None; start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None; is_active: bool

class PROHistoryItem(BaseModel):
    id: PyUUID; pro_assignment_id: PyUUID; patient_id: int; submission_timestamp: Optional[datetime] = None
    source: Optional[str] = None; responses_json: Dict[str, Any]
    calculated_scores_json: Optional[Dict[str, Any]] = None; ema_prompt_time: Optional[datetime] = None
    ema_completion_latency_seconds: Optional[int] = None

@pro_bp.route('/assignments', methods=['GET'])
@jwt_required()
def get_my_pro_assignments_api():
    patient_id_from_token = 1 # Placeholder
    db: Session = next(get_db())
    try:
        assignments_db = get_assigned_pro_instruments_for_patient(patient_id_from_token, db)
        assignments_resp = [PROAssignmentItem(**asg.to_dict()) for asg in assignments_db]
        return jsonify([item.dict() for item in assignments_resp]), 200
    except Exception as e:
        current_app.logger.error(f"PRO assignments error: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch PRO assignments", "details": str(e)}), 500
    finally: db.close()

@pro_bp.route('/responses', methods=['POST'])
@jwt_required()
def submit_my_pro_response_api():
    patient_id_from_token = 1 # Placeholder
    try:
        req_data_raw = request.get_json(); assert req_data_raw is not None
        req_data = PROSubmissionRequest(**req_data_raw)
    except Exception as e: return jsonify({"error": "Invalid PRO submission payload", "details": str(e)}), 400
    db: Session = next(get_db())
    try:
        submission_result = submit_pro_response(patient_id=patient_id_from_token, assignment_id=req_data.pro_assignment_id, responses=req_data.responses, ema_prompt_time_iso=req_data.ema_prompt_time_iso, db_session=db)
        if submission_result.get("error"): return jsonify(submission_result), 400
        return jsonify(submission_result), 201
    except Exception as e:
        current_app.logger.error(f"PRO submission error: {e}", exc_info=True)
        return jsonify({"error": "Failed to submit PRO response", "details": str(e)}), 500
    finally: db.close()

@pro_bp.route('/history/<uuid:assignment_id>', methods=['GET'])
@jwt_required()
def get_assignment_history_api(assignment_id: PyUUID):
    db: Session = next(get_db())
    try:
        history_db = get_pro_history_for_patient(assignment_id=assignment_id, db_session=db)
        history_resp = [PROHistoryItem(**resp.to_dict()) for resp in history_db]
        return jsonify([item.dict() for item in history_resp]), 200
    except Exception as e:
        current_app.logger.error(f"PRO history error: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch PRO history", "details": str(e)}), 500
    finally: db.close()
