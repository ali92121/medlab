from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.sql import func
import uuid
import enum
from ..database import Base
from .stubs import User, Patient

class RelationshipType(enum.Enum):
    SPOUSE = "Spouse"; PARENT = "Parent"; CHILD = "Child"; SIBLING = "Sibling"; GUARDIAN = "Guardian"; OTHER = "Other"

class AccessLevel(enum.Enum):
    NONE = "None"; READ_SUMMARY = "Read Summary"; READ_DETAILED_PRO = "Read Detailed PRO"
    CONTRIBUTE_OBSERVATIONS = "Contribute Observations"; FULL_READ = "Full Read"

class CaregiverRelationship(Base):
    __tablename__ = 'caregiver_relationships'
    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    caregiver_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    relationship_type = Column(SQLEnum(RelationshipType), nullable=False)
    relationship_type_other_description = Column(String)
    access_level = Column(SQLEnum(AccessLevel), nullable=False, default=AccessLevel.NONE)
    patient_consent_given = Column(Boolean, default=False)
    consent_document_url = Column(String)
    access_start_date = Column(DateTime(timezone=True), server_default=func.now())
    access_end_date = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=False)
    patient = relationship("Patient", foreign_keys=[patient_id])
    caregiver = relationship("User", foreign_keys=[caregiver_user_id])
    def to_dict(self):
        return {"id": str(self.id), "patient_id": self.patient_id, "caregiver_user_id": self.caregiver_user_id, "relationship_type": self.relationship_type.value if self.relationship_type else None, "access_level": self.access_level.value if self.access_level else None, "is_active": self.is_active}

class CaregiverObservation(Base):
    __tablename__ = 'caregiver_observations'
    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caregiver_relationship_id = Column(DB_UUID(as_uuid=True), ForeignKey('caregiver_relationships.id'), nullable=False)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True)
    caregiver_user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    observation_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    mood_rating_1_10 = Column(Integer)
    activity_level_1_5 = Column(Integer)
    social_interaction_level_1_5 = Column(Integer)
    medication_adherence_observed = Column(SQLEnum("Yes", "No", "Unsure", "NotApplicable", name="adherence_enum"))
    behavioral_notes = Column(Text)
    concerns_notes = Column(Text)
    relationship_details = relationship("CaregiverRelationship")
    patient = relationship("Patient", foreign_keys=[patient_id])
    caregiver = relationship("User", foreign_keys=[caregiver_user_id])
    def to_dict(self):
        return {"id": str(self.id), "caregiver_relationship_id": str(self.caregiver_relationship_id), "patient_id": self.patient_id, "caregiver_user_id": self.caregiver_user_id, "observation_date": self.observation_date.isoformat() if self.observation_date else None, "mood_rating_1_10": self.mood_rating_1_10, "activity_level_1_5": self.activity_level_1_5, "medication_adherence_observed": self.medication_adherence_observed.value if self.medication_adherence_observed else None, "behavioral_notes": self.behavioral_notes}
