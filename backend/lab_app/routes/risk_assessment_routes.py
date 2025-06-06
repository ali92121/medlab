from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user
from pydantic import BaseModel
from typing import List, Dict, Any, Optional # Added Optional
from datetime import datetime
from uuid import UUID as PyUUID
import uuid # For PyUUID creation if needed

from ..ml_pipelines.risk_stratification import predict_patient_risk, get_available_risk_models
from ..services.alert_service import maybe_trigger_risk_alert
from ..database import get_db
from sqlalchemy.orm import Session

risk_bp = Blueprint('risk', __name__, url_prefix='/api/risk')

class RiskAssessmentItem(BaseModel):
    log_id: PyUUID
    risk_model_name: str; risk_model_version: str; risk_type: str
    risk_score: float; risk_level: str
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    contributing_features_json: Optional[Dict[str, Any]] = None
    triggered_alert_id: Optional[PyUUID] = None

class RiskAssessmentResponse(BaseModel):
    patient_id: int
    assessment_timestamp: datetime
    risk_assessments: List[RiskAssessmentItem]

@risk_bp.route('/patients/<int:patient_id>/assess', methods=['POST'])
@jwt_required()
def assess_patient_risk_api(patient_id: int):
    db: Session = next(get_db())
    clinician_id = 1 # Placeholder
    socketio_instance = current_app.extensions.get('socketio')
    if not socketio_instance: print("Warning: SocketIO not found. Risk alerts will not be real-time.")

    try:
        assessment_results_list_of_dicts = predict_patient_risk(patient_id, db_session=db)
        processed_assessments = []
        for res_dict in assessment_results_list_of_dicts:
            log_id_uuid = PyUUID(str(res_dict["log_id"])) if isinstance(res_dict.get("log_id"), (str, uuid.UUID)) else res_dict.get("log_id", uuid.uuid4())
            if socketio_instance and res_dict.get('risk_level') in ['high', 'very_high']:
                alert_obj = maybe_trigger_risk_alert(
                    socketio_instance, db, patient_id, log_id_uuid, res_dict, clinician_id
                )
                if alert_obj: res_dict["triggered_alert_id"] = alert_obj.id

            pydantic_data = {
                "log_id": log_id_uuid,
                "risk_model_name": res_dict.get("risk_model_name"),
                "risk_model_version": res_dict.get("risk_model_version"),
                "risk_type": res_dict.get("risk_type"),
                "risk_score": res_dict.get("risk_score"),
                "risk_level": res_dict.get("risk_level"),
                "triggered_alert_id": res_dict.get("triggered_alert_id")
            }
            processed_assessments.append(RiskAssessmentItem(**pydantic_data))

        db.commit()
        response_data = RiskAssessmentResponse(
            patient_id=patient_id, assessment_timestamp=datetime.utcnow(), risk_assessments=processed_assessments
        )
        return jsonify(response_data.dict()), 200
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Risk assessment error P{patient_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to assess risk", "details": str(e)}), 500
    finally: db.close()

@risk_bp.route('/models/available', methods=['GET'])
@jwt_required()
def get_risk_models_available_api():
    return jsonify(get_available_risk_models()), 200
