from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user
from pydantic import BaseModel, conlist, confloat, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..ml_pipelines.treatment_recommendations import TreatmentRecommendationEngine, TreatmentRecommendation
from ..ml_pipelines.clinical_summarization import SummarizerFactory
from ..services.patient_service import get_comprehensive_patient_data_for_recommendations, get_patient_comprehensive_data, get_patient_dashboard_data
from ..database import SessionLocal, get_db
from sqlalchemy.orm import Session
from ..models.clinical_guidelines import PatientTreatmentRecommendationLog

intelligence_bp = Blueprint('clinical_intelligence', __name__, url_prefix='/api/intelligence')

class TreatmentRecommendationResponseItem(BaseModel):
    medication_name: str; dosage: str; confidence_score: confloat(ge=0.0, le=1.0)
    rationale: str; contraindications: List[str]; monitoring_requirements: List[str]
    expected_response_time: int
    @classmethod
    def from_dataclass(cls, dc: TreatmentRecommendation): return cls(**dc.__dict__)

class RecommendationResponse(BaseModel):
    patient_id: int; recommendations: List[TreatmentRecommendationResponseItem]
    generation_timestamp: datetime; model_version: Optional[str] = None

class CombinationAnalysisRequest(BaseModel):
    current_medications_rxcuis: List[str]; target_symptoms_dsm_codes: Optional[List[str]] = None

class CombinationAnalysisResponse(BaseModel):
    current_regimen_analysis: Dict; suggested_combinations: List[Dict]
    augmentation_strategies: List[Dict]; optimization_opportunities: List[Dict]

class ClinicalSummaryResponse(BaseModel):
    patient_id: int; summary_timestamp: datetime
    clinical_summary: Dict[str, Any]; model_used: str

class ClinicalSummaryComponent(BaseModel):
    title: str; content_html: str
    severity_level: Optional[str] = None; last_updated: Optional[datetime] = None

class DashboardDataResponse(BaseModel):
    patient_id: int; last_comprehensive_update: datetime
    key_metrics: List[Dict[str, Any]]; active_alerts: List[Dict[str, Any]]
    risk_scores: List[Dict[str, Any]]; summaries: Dict[str, ClinicalSummaryComponent]
    recent_labs_plot_data: Optional[Dict[str, Any]] = None

@intelligence_bp.route('/patients/<int:patient_id>/treatment-recommendations', methods=['GET'])
@jwt_required()
def get_treatment_recommendations_api(patient_id: int):
    current_user_payload = get_current_user(); clinician_id_from_token = current_user_payload.get('sub') if isinstance(current_user_payload, dict) else 1
    db: Session = next(get_db())
    try:
        engine = TreatmentRecommendationEngine(patient_id=patient_id)
        recommendations_dc_list = engine.get_treatment_recommendations(patient_id)
        model_version = engine.get_model_version()
        recommendations_resp_list = [TreatmentRecommendationResponseItem.from_dataclass(rec) for rec in recommendations_dc_list]
        log_entry = PatientTreatmentRecommendationLog(patient_id=patient_id, input_features_json=engine.get_last_input_features(patient_id) or {}, recommendations_json=[rec.dict() for rec in recommendations_resp_list], model_version_used=model_version, clinician_id=clinician_id_from_token)
        db.add(log_entry); db.commit()
        response_data = RecommendationResponse(patient_id=patient_id, recommendations=recommendations_resp_list, generation_timestamp=datetime.utcnow(), model_version=model_version)
        return jsonify(response_data.dict()), 200
    except Exception as e:
        db.rollback(); current_app.logger.error(f'Recs error P{patient_id}: {e}', exc_info=True)
        return jsonify({"error": "Failed to get recommendations", "details": str(e)}), 500
    finally: db.close()

@intelligence_bp.route('/patients/<int:patient_id>/combination-analysis', methods=['POST'])
@jwt_required()
def analyze_combination_api(patient_id: int):
    try:
        req_data_raw = request.get_json()
        if not req_data_raw: return jsonify({"error": "Request payload missing"}), 400
        req_data = CombinationAnalysisRequest(**req_data_raw)
    except Exception as e: return jsonify({"error": "Invalid request payload", "details": str(e)}), 400
    db: Session = next(get_db())
    try:
        engine = TreatmentRecommendationEngine(patient_id=patient_id)
        analysis_results_dict = engine.get_combination_suggestions(patient_id, req_data.current_medications_rxcuis)
        response_model = CombinationAnalysisResponse(**analysis_results_dict)
        return jsonify(response_model.dict()), 200
    except Exception as e:
        current_app.logger.error(f'Combo analysis error P{patient_id}: {e}', exc_info=True)
        return jsonify({"error": "Failed to analyze combination", "details": str(e)}), 500
    finally: db.close()

@intelligence_bp.route('/patients/<int:patient_id>/clinical-summary', methods=['GET'])
@jwt_required()
def get_clinical_summary_api(patient_id: int):
    db: Session = next(get_db())
    try:
        patient_data = get_patient_comprehensive_data(patient_id, db_session=db)
        model_type_arg = request.args.get('model', 'simple')
        summarizer = SummarizerFactory.create_summarizer(model_type=model_type_arg)
        summary_dict = summarizer.summarize_patient_data(patient_data)
        response_data = ClinicalSummaryResponse(patient_id=patient_id, summary_timestamp=datetime.utcnow(), clinical_summary=summary_dict, model_used=model_type_arg)
        return jsonify(response_data.dict()), 200
    except ValueError as ve: return jsonify({"error": "Invalid model type for summarizer", "details": str(ve)}), 400
    except Exception as e:
        current_app.logger.error(f'Clinical summary error P{patient_id}: {e}', exc_info=True)
        return jsonify({"error": "Failed to generate clinical summary", "details": str(e)}), 500
    finally: db.close()

@intelligence_bp.route('/patients/<int:patient_id>/dashboard-data', methods=['GET'])
@jwt_required()
def get_patient_dashboard_data_api(patient_id: int):
    db: Session = next(get_db())
    try:
        dashboard_data_dict = get_patient_dashboard_data(patient_id, db_session=db)
        response_data = DashboardDataResponse(**dashboard_data_dict)
        return jsonify(response_data.dict()), 200
    except Exception as e:
        current_app.logger.error(f'Dashboard data error for P{patient_id}: {e}', exc_info=True)
        return jsonify({"error": "Data formatting error or processing error for dashboard", "details": str(e)}), 500
    finally: db.close()
