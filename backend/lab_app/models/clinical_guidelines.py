from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Enum as SQLEnum, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..database import Base
from .stubs import User, Patient, RxNormConcept, LOINCConcept

class GuidelineSource(enum.Enum):
    APA = "APA"
    NICE = "NICE"
    CUSTOM = "Custom"

class ClinicalGuideline(Base):
    __tablename__ = 'clinical_guidelines'

    id = Column(Integer, primary_key=True, index=True)
    condition_loinc_code = Column(String, ForeignKey('loinc_master.loinc_num'))
    guideline_name = Column(String, nullable=False)
    source = Column(SQLEnum(GuidelineSource), nullable=False)
    version = Column(String)

    applicability_criteria_json = Column(JSON)

    recommended_treatment_rxnorm = Column(String, ForeignKey('rxnorm_concepts.rxcui'))
    starting_dose = Column(String)
    titration_schedule = Column(Text)
    max_dose = Column(String)

    rationale = Column(Text)
    contraindication_rxnorms_json = Column(JSON)
    monitoring_requirements_text = Column(Text)
    expected_response_time_weeks = Column(Integer)
    priority_level = Column(Integer, default=3)

    condition_loinc = relationship("LOINCConcept")
    recommended_treatment_concept = relationship("RxNormConcept")

class PatientTreatmentRecommendationLog(Base):
    __tablename__ = 'patient_treatment_recommendation_log'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    recommendation_request_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    input_features_json = Column(JSON, nullable=False)
    recommendations_json = Column(JSON, nullable=False)

    model_version_used = Column(String)
    clinician_id = Column(Integer, ForeignKey('users.id'))

    patient = relationship("Patient")
    clinician = relationship("User")
