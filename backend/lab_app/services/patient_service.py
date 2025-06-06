from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..ml_pipelines.risk_stratification import get_patient_risk_scores
from ..ml_pipelines.clinical_summarization import SummarizerFactory

def get_comprehensive_patient_data_for_recommendations(patient_id: int, db_session: Session):
    return {
        "patient_id": patient_id, "age": 35, "symptoms": {"MDD.A1": 3, "MDD.A2": 2},
        "active_diagnoses_loinc": ["44503-3"], "current_medications_rxcuis": [],
        "past_treatments": [{"medication_rxcui": "197590", "outcome": "failed_tolerability"}],
        "lab_results": {"creatinine": 0.9}, "latest_phq9_score": 16
    }

def get_patient_comprehensive_data(patient_id: int, db_session: Session = None):
    return {
        "patient_id": patient_id, "demographics": {"age": 40, "gender": "Female"},
        "recent_symptoms": [{"date": "2024-07-20", "phq9_score": 18, "gad7_score": 12}],
        "current_medications": [{"name": "Sertraline", "dose": "100mg"}],
        "vital_signs": [{"date": "2024-07-20", "hr": 75, "bp": "120/80"}],
        "latest_phq9_score": 18,
    }

def get_patient_dashboard_data(patient_id: int, db_session: Session) -> Dict[str, Any]:
    risk_scores_list = get_patient_risk_scores(patient_id, db_session=db_session)
    mock_patient_data_for_summarizer = {"patient_id": patient_id, "latest_phq9_score": 15}
    overall_summarizer = SummarizerFactory.create_summarizer('simple')
    overall_summary_dict = overall_summarizer.summarize_patient_data(mock_patient_data_for_summarizer)
    active_alerts_list = [{"type": "MedicationInteraction", "severity": "High", "message": "Sertraline + Tramadol", "timestamp": datetime.utcnow().isoformat()}]
    key_metrics_list = [{"name": "PHQ-9", "value": "15", "trend": "up", "last_assessed": datetime.utcnow().date().isoformat()}]
    recent_labs_plot = {"glucose": [{"date": "2024-07-01", "value": 110}, {"date": "2024-07-15", "value": 115}]}
    dashboard_data_dict = {
        "patient_id": patient_id,
        "last_comprehensive_update": datetime.utcnow(),
        "key_metrics": key_metrics_list,
        "active_alerts": active_alerts_list,
        "risk_scores": risk_scores_list,
        "summaries": {
            "overall_impression": {
                "title": "Overall Impression",
                "content_html": overall_summary_dict.get("symptomSeveritySummary", "<p>Summary N/A.</p>"),
                "severity_level": "moderate",
                "last_updated": datetime.utcnow()
            }
        },
        "recent_labs_plot_data": recent_labs_plot
    }
    return dashboard_data_dict
