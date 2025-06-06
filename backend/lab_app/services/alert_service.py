from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from uuid import UUID as PyUUID
import uuid

from ..models.alerts import ClinicalAlert, AlertType, AlertSeverity, AlertStatus
from ..models.stubs import Patient, User
from ..models.risk_assessment import PatientRiskAssessmentLog

def create_clinical_alert_db(
    db: Session, patient_id: int, alert_type: AlertType, severity: AlertSeverity,
    message: str, assigned_to_user_id: int, context_json: Optional[Dict] = None,
    triggering_event_id: Optional[str] = None, triggering_event_type: Optional[str] = None,
) -> ClinicalAlert:
    alert = ClinicalAlert(
        patient_id=patient_id, alert_type=alert_type, severity=severity, message=message,
        assigned_to_user_id=assigned_to_user_id, context_json=context_json,
        triggering_event_id=triggering_event_id, triggering_event_type=triggering_event_type,
        status=AlertStatus.NEW
    )
    db.add(alert); db.commit(); db.refresh(alert)
    return alert

def create_and_push_critical_lab_alert(
    socketio_instance: Any, db: Session, patient_id: int,
    lab_name: str, lab_value: str, assigned_clinician_id: int
):
    from ..routes.alert_ws_routes import push_alert_to_clinician
    message = f"Critical Lab: {lab_name} is {lab_value} for patient ID {patient_id}."
    context = {"lab_name": lab_name, "value": lab_value, "patient_id": patient_id}
    alert_db_entry = create_clinical_alert_db(
        db=db, patient_id=patient_id, alert_type=AlertType.CRITICAL_LAB,
        severity=AlertSeverity.CRITICAL, message=message,
        assigned_to_user_id=assigned_clinician_id, context_json=context
    )
    alert_dict = alert_db_entry.to_dict()
    push_alert_to_clinician(socketio_instance, assigned_clinician_id, alert_dict)
    print(f"Critical lab alert created and push attempted for patient {patient_id}.")
    return alert_db_entry

def maybe_trigger_risk_alert(
    socketio_instance: Any, db_session: Session, patient_id: int,
    risk_assessment_log_id: PyUUID, assessment_details: Dict[str, Any],
    assigned_clinician_id: int
):
    from ..routes.alert_ws_routes import push_alert_to_clinician
    risk_level = assessment_details.get("risk_level", "low")
    risk_type = assessment_details.get("risk_type", "unknown_risk")
    alert_to_trigger = None
    if risk_level == "high":
        alert_to_trigger = {"severity": AlertSeverity.HIGH, "message": f"High {risk_type} risk ({assessment_details.get('risk_score', 'N/A')}) for patient ID {patient_id}."}
    elif risk_level == "very_high":
        alert_to_trigger = {"severity": AlertSeverity.CRITICAL, "message": f"Critical {risk_type} risk ({assessment_details.get('risk_score', 'N/A')}) for patient ID {patient_id}."}

    if alert_to_trigger:
        alert_db_entry = create_clinical_alert_db(
            db=db_session, patient_id=patient_id, alert_type=AlertType.HIGH_RISK_SCORE,
            severity=alert_to_trigger["severity"], message=alert_to_trigger["message"],
            assigned_to_user_id=assigned_clinician_id, context_json=assessment_details,
            triggering_event_id=str(risk_assessment_log_id), triggering_event_type="PatientRiskAssessmentLog"
        )
        log_entry = db_session.query(PatientRiskAssessmentLog).filter(PatientRiskAssessmentLog.id == risk_assessment_log_id).first()
        if log_entry:
            log_entry.triggered_alert_id = alert_db_entry.id
            db_session.add(log_entry)
        alert_dict = alert_db_entry.to_dict()
        push_alert_to_clinician(socketio_instance, assigned_clinician_id, alert_dict)
        print(f"Risk alert triggered for patient {patient_id}.")
        return alert_db_entry
    return None
