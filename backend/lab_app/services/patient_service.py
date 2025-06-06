from sqlalchemy.orm import Session

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

def get_patient_dashboard_data(patient_id: int, db_session: Session):
    from datetime import datetime
    return {
        "patient_id": patient_id, "last_comprehensive_update": datetime.utcnow(),
        "key_metrics": [{"name": "PHQ-9", "value": "15", "trend": "up", "last_assessed": datetime.utcnow().date().isoformat()}],
        "active_alerts": [], "risk_scores": [], "summaries": {},
    }
