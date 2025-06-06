from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .stubs import User, Patient

class PROInstrument(Base):
    __tablename__ = 'pro_instruments'
    id = Column(Integer, primary_key=True, index=True)
    instrument_name = Column(String, unique=True, nullable=False)
    version = Column(String)
    description = Column(Text)
    scoring_rules_json = Column(JSON)
    questions_json = Column(JSON)
    is_ema_instrument = Column(Boolean, default=False)

class PROAssignment(Base):
    __tablename__ = 'pro_assignments'
    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    pro_instrument_id = Column(Integer, ForeignKey('pro_instruments.id'), nullable=False)
    assigned_by_clinician_id = Column(Integer, ForeignKey('users.id'))
    assignment_date = Column(DateTime(timezone=True), server_default=func.now())
    frequency = Column(String)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    patient = relationship("Patient")
    instrument = relationship("PROInstrument")
    assigned_by = relationship("User")
    def to_dict(self):
        return {
            "id": str(self.id), "patient_id": self.patient_id,
            "pro_instrument_id": self.pro_instrument_id,
            "instrument_name": self.instrument.instrument_name if self.instrument else None,
            "assigned_by_clinician_id": self.assigned_by_clinician_id,
            "assignment_date": self.assignment_date.isoformat() if self.assignment_date else None,
            "frequency": self.frequency,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active
        }

class PROAssessmentResponse(Base):
    __tablename__ = 'pro_assessment_responses'
    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pro_assignment_id = Column(DB_UUID(as_uuid=True), ForeignKey('pro_assignments.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    submission_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    source = Column(String, default="mobile_app")
    responses_json = Column(JSON, nullable=False)
    calculated_scores_json = Column(JSON)
    ema_prompt_time = Column(DateTime(timezone=True))
    ema_completion_latency_seconds = Column(Integer)
    assignment = relationship("PROAssignment")
    patient = relationship("Patient")
    def to_dict(self):
        return {
            "id": str(self.id), "pro_assignment_id": str(self.pro_assignment_id),
            "patient_id": self.patient_id,
            "submission_timestamp": self.submission_timestamp.isoformat() if self.submission_timestamp else None,
            "source": self.source, "responses_json": self.responses_json,
            "calculated_scores_json": self.calculated_scores_json,
            "ema_prompt_time": self.ema_prompt_time.isoformat() if self.ema_prompt_time else None,
            "ema_completion_latency_seconds": self.ema_completion_latency_seconds
        }
