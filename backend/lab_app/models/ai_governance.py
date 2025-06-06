from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base
from .stubs import User # Assuming User stub is available
from .research import ResearchProject # For ForeignKey in DataAccessRequestLog

class MLModelMetadata(Base):
    __tablename__ = 'ml_model_metadata'
    # __table_args__ = ({'schema': 'governance'}) # Optional schema

    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False) # Not unique alone, combined with version
    model_version = Column(String, nullable=False)
    description = Column(Text)
    model_type = Column(String) # e.g., "Risk Stratification", "Treatment Recommendation"
    deployment_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="active") # e.g., active, deprecated, experimental

    training_info_json = Column(JSON)
    governance_info_json = Column(JSON)

    # UniqueConstraint('model_name', 'model_version', name='uq_model_name_version') # Add in DB

    def to_dict(self):
        return {
            "id": str(self.id), "model_name": self.model_name, "model_version": self.model_version,
            "description": self.description, "model_type": self.model_type,
            "deployment_date": self.deployment_date.isoformat() if self.deployment_date else None,
            "status": self.status, "training_info_json": self.training_info_json,
            "governance_info_json": self.governance_info_json
        }

class AIBiasAuditLog(Base):
    __tablename__ = 'ai_bias_audit_log'
    # __table_args__ = ({'schema': 'governance'})

    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ml_model_metadata_id = Column(DB_UUID(as_uuid=True), ForeignKey('ml_model_metadata.id'), nullable=False)
    audit_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    audited_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # Nullable if system generated

    bias_metrics_json = Column(JSON, nullable=False)
    findings_summary = Column(Text)
    remediation_actions_taken = Column(Text)
    remediation_status = Column(String)

    model_metadata = relationship("MLModelMetadata")
    auditor = relationship("User")

    def to_dict(self):
        return {
            "id": str(self.id), "ml_model_metadata_id": str(self.ml_model_metadata_id),
            "audit_timestamp": self.audit_timestamp.isoformat() if self.audit_timestamp else None,
            "audited_by_user_id": self.audited_by_user_id,
            "bias_metrics_json": self.bias_metrics_json, "findings_summary": self.findings_summary,
            "remediation_actions_taken": self.remediation_actions_taken,
            "remediation_status": self.remediation_status
        }

class DataAccessRequestLog(Base):
    __tablename__ = 'data_access_request_log'
    # __table_args__ = ({'schema': 'governance'})

    id = Column(DB_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requesting_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    research_project_id = Column(DB_UUID(as_uuid=True), ForeignKey('research_projects.id'), nullable=True) # May not always be project-specific
    request_timestamp = Column(DateTime(timezone=True), server_default=func.now())

    data_description = Column(Text)
    purpose = Column(Text)
    deidentification_level_requested = Column(String)

    status = Column(String, default="pending") # pending, approved, rejected, expired
    approved_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    approval_timestamp = Column(DateTime(timezone=True), nullable=True)
    access_method = Column(String)
    access_start_date = Column(DateTime(timezone=True), nullable=True)
    access_end_date = Column(DateTime(timezone=True), nullable=True)
    conditions_of_use = Column(Text)

    requester = relationship("User", foreign_keys=[requesting_user_id])
    approver = relationship("User", foreign_keys=[approved_by_user_id])
    project = relationship("ResearchProject")

    def to_dict(self):
        return {
            "id": str(self.id), "requesting_user_id": self.requesting_user_id,
            "research_project_id": str(self.research_project_id) if self.research_project_id else None,
            "request_timestamp": self.request_timestamp.isoformat() if self.request_timestamp else None,
            "data_description": self.data_description, "purpose": self.purpose,
            "status": self.status,
            "approved_by_user_id": self.approved_by_user_id,
            "approval_timestamp": self.approval_timestamp.isoformat() if self.approval_timestamp else None,
            "access_end_date": self.access_end_date.isoformat() if self.access_end_date else None,
        }
