from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID as PyUUID
import uuid # For generating mock UUIDs
from datetime import datetime
from ..models.caregiver_access import CaregiverRelationship, CaregiverObservation, AccessLevel

def add_caregiver_observation(caregiver_user_id: int, relationship_id: PyUUID, data: Dict[str, Any], db_session: Session) -> Dict[str, Any]:
    # Mocked
    if caregiver_user_id == 2 and relationship_id == PyUUID("c1d2e3f4-g5h6-7890-1234-567890abcdef"):
        return {"success": True, "observation_id": str(uuid.uuid4()), "message": "Observation added (mocked)."}
    return {"error": "Mocked: Permission denied or relationship not found."}

def get_caregiver_observations_for_patient(patient_id: int, db_session: Session) -> List[CaregiverObservation]:
    # Mocked
    if patient_id == 1:
        mock_obs = CaregiverObservation(id=uuid.uuid4(), caregiver_relationship_id=PyUUID("c1d2e3f4-g5h6-7890-1234-567890abcdef"), patient_id=patient_id, caregiver_user_id=2, observation_date=datetime.utcnow(), behavioral_notes="Patient seemed well today (mocked).")
        return [mock_obs]
    return []

def get_patient_data_for_caregiver(caregiver_user_id: int, patient_id: int, db_session: Session) -> Dict[str, Any]:
    # Mocked
    if caregiver_user_id == 2 and patient_id == 1:
        return {"patient_id": patient_id, "access_level_granted": AccessLevel.READ_SUMMARY.value, "data": {"summary": "Patient is generally stable. (Mocked)"}}
    return {"error": "Mocked: No access or relationship not found."}
