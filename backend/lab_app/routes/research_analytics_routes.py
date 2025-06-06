from flask import Blueprint, request, jsonify, Response, stream_with_context, current_app
from flask_jwt_extended import jwt_required, get_current_user
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field # Field for future use if needed
from typing import List, Dict, Any, Optional
from uuid import UUID as PyUUID # For type hinting route params & Pydantic models
import uuid # For PyUUID creation if needed

from ..services.research_service import (
    create_research_project_service,
    define_cohort_service,
    get_cohort_patient_data_stream,
    get_phenotype_clusters_service,
    get_psm_results_service,
    query_aggregated_data_service,
    query_longitudinal_data_service
)
# from ..auth.permissions import research_permission # Assuming a Flask-Principal or similar permission object
from ..database import get_db # Use get_db dependency injector
from sqlalchemy.orm import Session
import logging # For logging in routes if needed

research_bp = Blueprint('research', __name__, url_prefix='/api/research')
logger = logging.getLogger('research_analytics') # Use the same logger name as service

# --- Pydantic Models for Request/Response ---
class ResearchProjectRequest(BaseModel):
    project_name: str
    description: Optional[str] = None
    irb_approval_number: Optional[str] = None
    # principal_investigator_user_id is derived from JWT
    data_access_permissions_json: Optional[Dict[str, Any]] = None

class ResearchProjectResponse(BaseModel): # Example response model
    id: PyUUID
    project_name: str
    description: Optional[str] = None
    principal_investigator_user_id: int
    irb_approval_number: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None # Made optional for mock if not always set
    # Add other fields from ResearchProject.to_dict() if needed

class CohortDefinitionRequest(BaseModel):
    research_project_id: PyUUID
    cohort_name: str
    description: Optional[str] = None
    definition_criteria_json: Dict[str, Any]

class CohortDefinitionResponse(BaseModel): # Example response model
    id: PyUUID
    research_project_id: PyUUID
    cohort_name: str
    patient_count: Optional[int] = None # Optional as it might be async
    generated_at: Optional[datetime] = None
    generated_by_user_id: Optional[int] = None # Made optional for mock
    # Add other fields from ResearchCohort.to_dict()

# --- API Endpoints ---
@research_bp.route('/projects', methods=['POST'])
@jwt_required()
# @research_permission.require(http_exception=403) # Placeholder for permission
def create_research_project_api():
    # current_user = get_current_user() # Assumed to return dict with 'id' or 'sub'
    # user_id = current_user.get('id') or current_user.get('sub')
    user_id = 1 # Placeholder for PI user ID from token
    db: Session = next(get_db())
    try:
        req_data_validated = ResearchProjectRequest(**request.get_json())
        # Pass validated data to service
        project_model = create_research_project_service(
            data=req_data_validated.dict(),
            pi_user_id=user_id,
            db_session=db
        )
        # Convert SQLAlchemy model to Pydantic model for response
        # Assuming project_model has all fields needed by ResearchProjectResponse or a to_dict method
        response_data = ResearchProjectResponse(**project_model.to_dict(), principal_investigator_user_id=user_id) # Ensure all fields are present
        return jsonify(response_data.dict()), 201
    except IntegrityError: # For unique constraint on project_name
        logger.warning(f"Attempt to create research project with duplicate name by user {user_id}.", exc_info=True)
        return jsonify({"error": "Project name already exists"}), 409
    except ValueError as ve: # Custom validation errors from service
        logger.warning(f"Validation error creating research project by user {user_id}: {ve}", exc_info=True)
        return jsonify({"error": "Validation error", "details": str(ve)}), 400
    except Exception as e:
        logger.error(f"Failed to create project by user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to create project", "details": str(e)}), 500
    finally:
        db.close()


@research_bp.route('/cohorts', methods=['POST'])
@jwt_required()
# @research_permission.require(http_exception=403)
def define_research_cohort_api():
    # current_user = get_current_user()
    # user_id = current_user.get('id') or current_user.get('sub')
    user_id = 1 # Placeholder
    db: Session = next(get_db())
    try:
        req_data_validated = CohortDefinitionRequest(**request.get_json())
        cohort_model = define_cohort_service(
            data=req_data_validated.dict(),
            user_id=user_id,
            db_session=db
        )
        # Assuming cohort_model has necessary fields or a to_dict method for CohortDefinitionResponse
        response_data = CohortDefinitionResponse(**cohort_model.to_dict(), generated_by_user_id=user_id)
        return jsonify(response_data.dict()), 201
    except ValueError as ve:
        logger.warning(f"Validation error defining cohort by user {user_id}: {ve}", exc_info=True)
        return jsonify({"error": "Validation error", "details": str(ve)}), 400
    except Exception as e:
        logger.error(f"Failed to define cohort by user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to define cohort", "details": str(e)}), 500
    finally:
        db.close()

@research_bp.route('/cohorts/<uuid:cohort_id>/data-export/csv', methods=['GET'])
@jwt_required()
# @research_permission.require(http_exception=403)
def export_cohort_data_csv_api(cohort_id: PyUUID):
    # current_user = get_current_user()
    # user_id = current_user.get('id') or current_user.get('sub')
    user_id = 1 # Placeholder

    field_list_arg = request.args.getlist('fields')
    deid_level_arg = request.args.get('deid', 'strict')
    db: Session = next(get_db())

    try:
        # This service function is a generator
        data_stream = get_cohort_patient_data_stream(
            cohort_id, user_id=user_id, db_session=db,
            fields=field_list_arg, deid_level=deid_level_arg
        )

        # Stream the CSV data
        # Note: stream_with_context is useful if the generator needs app context
        return Response(stream_with_context(data_stream), mimetype='text/csv',
                       headers={"Content-Disposition": f"attachment;filename=cohort_{cohort_id}_data.csv"})
    except Exception as e:
        logger.error(f"Failed to export data for cohort {cohort_id} by user {user_id}: {e}", exc_info=True)
        # Cannot return JSON for a stream error easily, client might get truncated stream.
        # Best to log thoroughly. A small text error might be possible if no data sent yet.
        return Response(f"Error generating CSV export: {str(e)}", status=500, mimetype='text/plain')
    # finally: db.close() # Session should be closed by get_db context manager if stream finishes/errors


@research_bp.route('/phenotype-clusters/<string:run_id>', methods=['GET'])
@jwt_required()
# @research_permission.require(http_exception=403)
def get_phenotype_cluster_results_api(run_id: str):
    db: Session = next(get_db())
    try:
        clusters_data = get_phenotype_clusters_service(run_id, db_session=db)
        return jsonify(clusters_data), 200
    except Exception as e:
        logger.error(f"Failed to get phenotype clusters for run {run_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve phenotype clusters", "details": str(e)}), 500
    finally:
        db.close()

@research_bp.route('/propensity-scores/<string:run_id>', methods=['GET']) # Added route for PSM
@jwt_required()
# @research_permission.require(http_exception=403)
def get_psm_results_api(run_id: str):
    db: Session = next(get_db())
    try:
        psm_data = get_psm_results_service(run_id, db_session=db)
        return jsonify(psm_data), 200
    except Exception as e:
        logger.error(f"Failed to get PSM results for run {run_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve PSM results", "details": str(e)}), 500
    finally:
        db.close()

# --- Pydantic Models for Step 5.3 ---
class AggregatedDataRequest(BaseModel):
    cohort_id: Optional[PyUUID] = None
    metrics: List[str]
    group_by_fields: List[str]
    time_period_start: Optional[datetime] = None # Changed from date for more flexibility
    time_period_end: Optional[datetime] = None   # Changed from date
    filters_json: Optional[Dict[str, Any]] = None

# No specific Pydantic response model for aggregated data, as structure is dynamic.
# The service returns a Dict which will be passed to jsonify.

class LongitudinalDataRequest(BaseModel): # Added for /longitudinal-plot-data
    cohort_id: Optional[PyUUID] = None
    patient_ids: Optional[List[int]] = None # Or List[str] if using masked IDs
    variable: str # e.g., "PHQ-9_Total", "Lab_Glucose"
    time_period_start: Optional[datetime] = None
    time_period_end: Optional[datetime] = None
    # Additional parameters like aggregation_type (raw, monthly_avg) could be added

# No specific Pydantic response model for longitudinal data, service returns Dict.

# --- API Endpoints for Step 5.3 ---
@research_bp.route('/aggregated-data', methods=['POST'])
@jwt_required()
# @research_permission.require(http_exception=403)
def get_aggregated_research_data_api():
    # current_user = get_current_user()
    # user_id = current_user.get('id')
    user_id = 1 # Placeholder
    db: Session = next(get_db())
    try:
        req_data_validated = AggregatedDataRequest(**request.get_json())
        # Service function will handle complex query building and execution
        aggregated_results = query_aggregated_data_service(
            request_data=req_data_validated.dict(),
            user_id=user_id,
            db_session=db
        )
        return jsonify(aggregated_results), 200
    except ValueError as ve: # For validation errors within service or Pydantic
        logger.warning(f"Validation error for aggregated data request by user {user_id}: {ve}", exc_info=True)
        return jsonify({"error": "Invalid request parameters", "details": str(ve)}), 400
    except Exception as e:
        logger.error(f"Failed to get aggregated research data for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve aggregated data", "details": str(e)}), 500
    finally:
        db.close()

@research_bp.route('/longitudinal-plot-data', methods=['POST'])
@jwt_required()
# @research_permission.require(http_exception=403)
def get_longitudinal_plot_data_api():
    # current_user = get_current_user()
    # user_id = current_user.get('id')
    user_id = 1 # Placeholder
    db: Session = next(get_db())
    try:
        req_data_validated = LongitudinalDataRequest(**request.get_json())
        plot_data = query_longitudinal_data_service(
            request_data=req_data_validated.dict(),
            user_id=user_id,
            db_session=db
        )
        return jsonify(plot_data), 200
    except ValueError as ve:
        logger.warning(f"Validation error for longitudinal data request by user {user_id}: {ve}", exc_info=True)
        return jsonify({"error": "Invalid request parameters", "details": str(ve)}), 400
    except Exception as e:
        logger.error(f"Failed to get longitudinal plot data for user {user_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve longitudinal plot data", "details": str(e)}), 500
    finally:
        db.close()
