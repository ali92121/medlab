from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID as PyUUID
import uuid
from datetime import datetime

from ..models.risk_assessment import PatientRiskAssessmentLog

def get_features_for_risk_model(patient_id: int, db_session: Session) -> Dict[str, Any]:
    return {
        "age": 30, "phq9_total_last_7d_avg": 18.5,
        "history_of_attempt": True, "recent_hopelessness_pro": 0.8
    }

def predict_patient_risk(patient_id: int, db_session: Session, socketio_instance: Any = None) -> List[Dict[str, Any]]:
    features = get_features_for_risk_model(patient_id, db_session)
    model_name = "SuicideRiskBERT_v2.1"; model_version = "2.1.0"; risk_type = "suicide_7day_prediction"
    risk_score = 0.1
    if features.get("history_of_attempt"): risk_score += 0.3
    if features.get("phq9_total_last_7d_avg", 0) > 15: risk_score += 0.25
    if features.get("recent_hopelessness_pro", 0) > 0.7: risk_score += 0.2
    risk_score = min(risk_score, 1.0)
    risk_level = "low"
    if risk_score > 0.7: risk_level = "high"
    elif risk_score > 0.4: risk_level = "moderate"
    contributing_features = {
        "phq9_total_last_7d_avg": 0.3 if risk_score > 0.3 else 0.1,
        "history_of_attempt": 0.25 if features.get("history_of_attempt") else 0.0,
        "recent_hopelessness_pro": 0.2 if features.get("recent_hopelessness_pro", 0) > 0.7 else 0.05
    }
    log_entry = PatientRiskAssessmentLog(
        patient_id=patient_id, risk_model_name=model_name, risk_model_version=model_version,
        risk_type=risk_type, risk_score=risk_score, risk_level=risk_level,
        contributing_features_json=contributing_features, input_features_snapshot_json=features,
        assessment_timestamp=datetime.utcnow()
    )
    db_session.add(log_entry)
    assessment_result_dict = log_entry.to_dict()
    assessment_result_dict["log_id"] = str(log_entry.id) if log_entry.id else str(uuid.uuid4())
    return [assessment_result_dict]

def get_available_risk_models() -> List[Dict[str, str]]:
    return [
        {"name": "SuicideRiskModel_v1.2", "version": "1.2.3", "predicts_risk_type": "suicide_7day"},
        {"name": "HospitalizationRiskModel_v0.9", "version": "0.9.1", "predicts_risk_type": "hospitalization_30day"}
    ]

def get_patient_risk_scores(patient_id: int, db_session: Session = None) -> List[Dict[str, Any]]:
    return [
        {"risk_type": "suicide_7day", "score": 0.65, "level": "high", "trend": "increasing"},
        {"risk_type": "hospitalization_30day", "score": 0.30, "level": "moderate", "trend": "stable"}
    ]
