from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .stubs import Patient
from .alerts import ClinicalAlert # For FK

class PatientRiskAssessmentLog(Base):
    __tablename__ = 'patient_risk_assessment_log'

    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    assessment_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    risk_model_name = Column(String, nullable=False)
    risk_model_version = Column(String, nullable=False)

    risk_type = Column(String, nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String)
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)

    contributing_features_json = Column(JSON)
    input_features_snapshot_json = Column(JSON)

    triggered_alert_id = Column(DB_UUID(as_uuid=True), ForeignKey('clinical_alerts.id'), nullable=True)

    patient = relationship("Patient")
    alert = relationship("ClinicalAlert")

    def to_dict(self):
        return {
            "log_id": str(self.id), "patient_id": self.patient_id,
            "assessment_timestamp": self.assessment_timestamp.isoformat() if self.assessment_timestamp else None,
            "risk_model_name": self.risk_model_name, "risk_model_version": self.risk_model_version,
            "risk_type": self.risk_type, "risk_score": self.risk_score, "risk_level": self.risk_level,
            "contributing_features_json": self.contributing_features_json,
            "triggered_alert_id": str(self.triggered_alert_id) if self.triggered_alert_id else None
        }
