from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.sql import func
import uuid
import enum
from ..database import Base
from .stubs import User, Patient, Team

class AlertType(enum.Enum):
    CRITICAL_LAB = "Critical Lab Value"
    MED_INTERACTION = "Medication Interaction"
    HIGH_RISK_SCORE = "High Risk Score"
    PRO_CRISIS_REPORT = "PRO Crisis Report"
    ADHERENCE_ISSUE = "Adherence Issue"
    APPOINTMENT_MISS = "Appointment Missed"

class AlertSeverity(enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class AlertStatus(enum.Enum):
    NEW = "New"
    ACKNOWLEDGED = "Acknowledged"
    RESOLVED = "Resolved"
    SNOOZED = "Snoozed"

class ClinicalAlert(Base):
    __tablename__ = 'clinical_alerts'
    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    message = Column(Text, nullable=False)
    triggering_event_id = Column(String)
    triggering_event_type = Column(String)
    context_json = Column(JSON)
    generated_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.NEW, index=True)
    assigned_to_user_id = Column(Integer, ForeignKey('users.id'), index=True)
    assigned_to_team_id = Column(Integer, ForeignKey('teams.id'), index=True, nullable=True)
    acknowledged_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    acknowledged_timestamp = Column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    resolved_timestamp = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text)
    patient = relationship("Patient")
    assigned_clinician = relationship("User", foreign_keys=[assigned_to_user_id])
    assigned_team = relationship("Team", foreign_keys=[assigned_to_team_id])
    acknowledged_by_clinician = relationship("User", foreign_keys=[acknowledged_by_user_id])
    resolved_by_clinician = relationship("User", foreign_keys=[resolved_by_user_id])
    def to_dict(self):
        return {
            "id": str(self.id), "patient_id": self.patient_id,
            "alert_type": self.alert_type.value, "severity": self.severity.value,
            "message": self.message, "triggering_event_id": self.triggering_event_id,
            "triggering_event_type": self.triggering_event_type, "context_json": self.context_json,
            "generated_timestamp": self.generated_timestamp.isoformat() if self.generated_timestamp else None,
            "status": self.status.value, "assigned_to_user_id": self.assigned_to_user_id,
        }
