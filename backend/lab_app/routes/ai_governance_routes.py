from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user
from pydantic import BaseModel # For request/response validation if needed
from typing import List, Dict, Any, Optional
from uuid import UUID as PyUUID
from datetime import datetime

from ..services.governance_service import (
    log_bias_audit_result,
    get_model_bias_history,
    get_data_access_requests,
    create_data_access_request, # Added service
    approve_data_access_request, # Added service
    reject_data_access_request   # Added service
)
# from ..auth.permissions import admin_permission, research_permission # Placeholder
from ..database import get_db
from sqlalchemy.orm import Session
import logging

governance_bp = Blueprint('governance', __name__, url_prefix='/api/governance')
logger = logging.getLogger('ai_governance') # Use the same logger

# --- Pydantic Models (examples, can be expanded) ---
class BiasAuditRequest(BaseModel):
    bias_metrics_json: Dict[str, Any]
    findings_summary: Optional[str] = None
    remediation_actions_taken: Optional[str] = None
    remediation_status: Optional[str] = None

class BiasAuditResponse(BaseModel): # From AIBiasAuditLog.to_dict()
    id: PyUUID; ml_model_metadata_id: PyUUID; audit_timestamp: Optional[datetime] = None
    audited_by_user_id: Optional[int] = None; bias_metrics_json: Dict[str, Any]
    findings_summary: Optional[str] = None; remediation_actions_taken: Optional[str] = None
    remediation_status: Optional[str] = None

class DataAccessRequestCreate(BaseModel):
    research_project_id: Optional[PyUUID] = None
    data_description: str
    purpose: str
    deidentification_level_requested: Optional[str] = "strict"

class DataAccessRequestUpdate(BaseModel): # For approval/rejection
    status: str # "approved" or "rejected"
    conditions_of_use: Optional[str] = None # if approved
    rejection_reason: Optional[str] = None # if rejected

class DataAccessRequestResponse(BaseModel): # From DataAccessRequestLog.to_dict()
    id: PyUUID; requesting_user_id: int; research_project_id: Optional[PyUUID] = None
    request_timestamp: Optional[datetime] = None; data_description: Optional[str] = None
    purpose: Optional[str] = None; status: str
    approved_by_user_id: Optional[int] = None; approval_timestamp: Optional[datetime] = None
    access_end_date: Optional[datetime] = None

# --- API Endpoints ---
@governance_bp.route('/models/<uuid:model_id>/bias-audits', methods=['POST'])
@jwt_required()
# @admin_permission.require(http_exception=403) # Placeholder
def record_bias_audit_api(model_id: PyUUID):
    # current_user = get_current_user()
    # user_id = current_user.get('id')
    user_id = 1 # Placeholder
    db: Session = next(get_db())
    try:
        req_data = BiasAuditRequest(**request.get_json())
        audit_log_model = log_bias_audit_result(
            model_id=model_id, audit_data=req_data.dict(),
            user_id=user_id, db_session=db
        )
        response_data = BiasAuditResponse(**audit_log_model.to_dict())
        return jsonify(response_data.dict()), 201
    except ValueError as ve: # e.g., model_id not found
        return jsonify({"error": "Validation error", "details": str(ve)}), 404
    except Exception as e:
        logger.error(f"Error recording bias audit for model {model_id} by user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to record bias audit", "details": str(e)}), 500
    finally: db.close()

@governance_bp.route('/models/<uuid:model_id>/bias-history', methods=['GET'])
@jwt_required()
# @admin_permission.require(http_exception=403)
def get_model_bias_history_api(model_id: PyUUID):
    db: Session = next(get_db())
    try:
        history_models = get_model_bias_history(model_id, db_session=db)
        response_data = [BiasAuditResponse(**log.to_dict()) for log in history_models]
        return jsonify([item.dict() for item in response_data]), 200
    except Exception as e:
        logger.error(f"Error fetching bias history for model {model_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch bias history", "details": str(e)}), 500
    finally: db.close()

@governance_bp.route('/data-access-requests', methods=['GET'])
@jwt_required()
# @admin_permission.require(http_exception=403) # Or role based: user can see their own, admin sees all
def list_data_access_requests_api():
    # current_user = get_current_user()
    # user_id = current_user.get('id')
    # For admin, status can be a query param. For regular user, only their requests.
    status_filter = request.args.get('status')
    db: Session = next(get_db())
    try:
        # Add logic here to determine if user is admin or regular user to pass correct user_id to service
        requests_models = get_data_access_requests(db_session=db, status=status_filter) # Pass user_id for non-admins
        response_data = [DataAccessRequestResponse(**req.to_dict()) for req in requests_models]
        return jsonify([item.dict() for item in response_data]), 200
    except Exception as e:
        logger.error(f"Error listing data access requests: {e}", exc_info=True)
        return jsonify({"error": "Failed to list data access requests", "details": str(e)}), 500
    finally: db.close()

@governance_bp.route('/data-access-requests', methods=['POST'])
@jwt_required()
# @research_permission.require(http_exception=403) # Users with research role can request
def create_data_access_request_api():
    # current_user = get_current_user()
    # user_id = current_user.get('id')
    user_id = 1 # Placeholder
    db: Session = next(get_db())
    try:
        req_data = DataAccessRequestCreate(**request.get_json())
        request_model = create_data_access_request(data=req_data.dict(), requesting_user_id=user_id, db_session=db)
        response_data = DataAccessRequestResponse(**request_model.to_dict())
        return jsonify(response_data.dict()), 201
    except Exception as e:
        logger.error(f"Error creating data access request by user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to create data access request", "details": str(e)}), 500
    finally: db.close()

@governance_bp.route('/data-access-requests/<uuid:request_id>/status', methods=['PUT'])
@jwt_required()
# @admin_permission.require(http_exception=403) # Only admin/ethics committee can approve/reject
def update_data_access_request_status_api(request_id: PyUUID):
    # current_user = get_current_user()
    # approver_id = current_user.get('id')
    approver_id = 2 # Placeholder for admin/approver user ID
    db: Session = next(get_db())
    try:
        req_data = DataAccessRequestUpdate(**request.get_json())
        updated_request = None
        if req_data.status == "approved":
            updated_request = approve_data_access_request(request_id, approver_id, req_data.conditions_of_use or "", db_session=db)
        elif req_data.status == "rejected":
            updated_request = reject_data_access_request(request_id, approver_id, req_data.rejection_reason or "", db_session=db)
        else:
            return jsonify({"error": "Invalid status provided. Must be 'approved' or 'rejected'."}), 400

        if not updated_request:
            return jsonify({"error": "Data access request not found or update failed."}), 404

        response_data = DataAccessRequestResponse(**updated_request.to_dict())
        return jsonify(response_data.dict()), 200
    except Exception as e:
        logger.error(f"Error updating status for data access request {request_id} by user {approver_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update data access request status", "details": str(e)}), 500
    finally: db.close()
