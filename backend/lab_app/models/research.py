from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean, Index, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.dialects.postgresql import ARRAY # For patient_ids_snapshot if used
from sqlalchemy.sql import func
import uuid
import enum # Though not used in this specific model file, good to have if enums are added later

from ..database import Base
from .stubs import User, Patient # Assuming User and Patient stubs are available

class ResearchProject(Base):
    __tablename__ = 'research_projects'
    # __table_args__ = ({'schema': 'research'}) # Optional schema

    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    principal_investigator_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    irb_approval_number = Column(String)
    irb_expiration_date = Column(DateTime(timezone=True))
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    status = Column(String, default="active")

    data_access_permissions_json = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    pi = relationship("User")

    def to_dict(self): # Example for API responses
        return {
            "id": str(self.id), "project_name": self.project_name, "description": self.description,
            "principal_investigator_user_id": self.principal_investigator_user_id,
            "irb_approval_number": self.irb_approval_number,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ResearchCohort(Base):
    __tablename__ = 'research_cohorts'
    # __table_args__ = ({'schema': 'research'}, Index('idx_cohort_project_name', 'research_project_id', 'cohort_name', unique=True))


    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_project_id = Column(DB_UUID(as_uuid=True), ForeignKey('research_projects.id'), nullable=False)
    cohort_name = Column(String, nullable=False)
    description = Column(Text)
    definition_criteria_json = Column(JSON, nullable=False)
    # patient_ids_snapshot = Column(ARRAY(Integer)) # Example if storing directly
    patient_count = Column(Integer)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by_user_id = Column(Integer, ForeignKey('users.id'))

    project = relationship("ResearchProject")
    creator = relationship("User")

    def to_dict(self): # Example
        return {
            "id": str(self.id), "research_project_id": str(self.research_project_id),
            "cohort_name": self.cohort_name, "patient_count": self.patient_count,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "generated_by_user_id": self.generated_by_user_id
        }


class PhenotypeCluster(Base):
    __tablename__ = 'phenotype_clusters'
    # __table_args__ = ({'schema': 'research_derived'})

    id = Column(Integer, primary_key=True) # Simple integer PK for this derived data
    patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False, index=True, unique=True)
    clustering_run_id = Column(String, nullable=False, index=True)
    cluster_label = Column(Integer, nullable=False, index=True)
    feature_vector_json = Column(JSON)
    silhouette_score_patient = Column(Float)
    run_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient")

class PropensityScoreMatch(Base):
    __tablename__ = 'propensity_score_matches'
    # __table_args__ = ({'schema': 'research_derived'})

    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matching_run_id = Column(String, nullable=False, index=True)
    treatment_group_patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    control_group_patient_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    propensity_score_treatment = Column(Float)
    propensity_score_control = Column(Float)
    match_quality_score = Column(Float)
    matching_covariates_json = Column(JSON)
    run_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    treatment_patient = relationship("Patient", foreign_keys=[treatment_group_patient_id])
    control_patient = relationship("Patient", foreign_keys=[control_group_patient_id])
