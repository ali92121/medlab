from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum # Python's enum, not SQLAlchemy's

from ..database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    # Add other fields as needed for JWT or clinician info
    # email = Column(String, unique=True, index=True)
    # full_name = Column(String)
    # is_active = Column(Boolean, default=True)
    # patient_id = Column(Integer, ForeignKey('patients.id'), nullable=True) # If user can be a patient

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    # Add other patient demographics or relevant fields
    # e.g., date_of_birth = Column(Date)
    #       gender = Column(String)
    #       allergies = relationship("PatientAllergy", back_populates="patient")

class RxNormConcept(Base):
    __tablename__ = 'rxnorm_concepts'
    rxcui = Column(String, primary_key=True, index=True)
    str = Column(String, nullable=False) # Name of the concept
    # Add other relevant fields like tty (term type) if needed

class LOINCConcept(Base):
    __tablename__ = 'loinc_master' # Matching table name from issue
    loinc_num = Column(String, primary_key=True, index=True) # Matching PK name
    long_common_name = Column(String) # Example field
    # Add other relevant fields

class Team(Base): # Stub for team_id FK in ClinicalAlert
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

# Example of a pre-existing model that might be in the system
# class SymptomAssessment(Base):
#     __tablename__ = 'symptom_assessments'
#     id = Column(Integer, primary_key=True, index=True)
#     patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
#     assessment_date = Column(DateTime(timezone=True), server_default=func.now())
#     phq9_score = Column(Integer)
#     gad7_score = Column(Integer)
#     patient = relationship("Patient")

# class Treatment(Base): # Polymorphic base for treatments
#    __tablename__ = 'treatments'
#    id = Column(Integer, primary_key=True, index=True)
#    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
#    treatment_type = Column(String(50)) # for polymorphic identity
#    start_date = Column(DateTime(timezone=True))
#    end_date = Column(DateTime(timezone=True), nullable=True)
#    outcome = Column(Text, nullable=True)
#    __mapper_args__ = {
#        'polymorphic_identity': 'treatment',
#        'polymorphic_on': treatment_type
#    }
#    patient = relationship("Patient")

# class Pharmacotherapy(Treatment):
#    __tablename__ = 'pharmacotherapies'
#    id = Column(Integer, ForeignKey('treatments.id'), primary_key=True)
#    medication_rxcui = Column(String, ForeignKey('rxnorm_concepts.rxcui'))
#    dosage = Column(String)
#    frequency = Column(String)
#    medication_concept = relationship("RxNormConcept")
#    __mapper_args__ = {
#        'polymorphic_identity': 'pharmacotherapy',
#    }

# class Psychotherapy(Treatment):
#    __tablename__ = 'psychotherapies'
#    id = Column(Integer, ForeignKey('treatments.id'), primary_key=True)
#    therapy_type = Column(String) # e.g., CBT, DBT
#    therapist_id = Column(Integer, ForeignKey('users.id')) # if therapist is a user
#    therapist = relationship("User")
#    __mapper_args__ = {
#        'polymorphic_identity': 'psychotherapy',
#    }
