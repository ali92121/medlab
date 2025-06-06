from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID as PyUUID
from datetime import datetime
from ..models.patient_reported_outcomes import PROInstrument, PROAssignment, PROAssessmentResponse

def get_assigned_pro_instruments_for_patient(patient_id: int, db_session: Session) -> List[PROAssignment]:
    if patient_id == 1: # Mock
        mock_instrument = PROInstrument(instrument_name="PHQ-9 Virtual")
        mock_assignment = PROAssignment(id=PyUUID("a1b2c3d4-e5f6-7890-1234-567890abcdef"), patient_id=patient_id, pro_instrument_id=1, assigned_by_clinician_id=1, assignment_date=datetime.utcnow(), frequency="weekly", start_date=datetime.utcnow(), is_active=True)
        mock_assignment.instrument = mock_instrument
        return [mock_assignment]
    return []

def submit_pro_response(patient_id: int, assignment_id: PyUUID, responses: Dict[str, Any], ema_prompt_time_iso: Optional[str], db_session: Session) -> Dict[str, Any]:
    calculated_scores = {"total_phq9": sum(v for v in responses.values() if isinstance(v, int))}
    if patient_id == 1 and assignment_id == PyUUID("a1b2c3d4-e5f6-7890-1234-567890abcdef"): # Mock
        return {"success": True, "response_id": str(PyUUID(int=1)), "calculated_scores": calculated_scores, "message": "PRO response submitted successfully (mocked)."}
    return {"error": "Mocked: PRO assignment not found or invalid for patient."}

def get_pro_history_for_patient(assignment_id: PyUUID, db_session: Session) -> List[PROAssessmentResponse]:
    if assignment_id == PyUUID("a1b2c3d4-e5f6-7890-1234-567890abcdef"): # Mock
        mock_response = PROAssessmentResponse(id=PyUUID(int=1), pro_assignment_id=assignment_id, patient_id=1, submission_timestamp=datetime.utcnow(), responses_json={"q1": 2, "q2": 3}, calculated_scores_json={"total_phq9": 5})
        return [mock_response]
    return []
