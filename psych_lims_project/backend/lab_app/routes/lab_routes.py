# backend/lab_app/routes/lab_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity # Assuming JWT for auth
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import datetime
import uuid

from lab_app import db
from lab_app.models import (
    Patient, LabTestDefinition, LabOrder, LabResult,
    CriticalValueAlert, AuditLog, SpecimenType, TestStatus
)
from lab_app.ml_pipelines.lab_feature_engineering import LabAnalyticsEngine

lab_bp = Blueprint('lab_bp', __name__, url_prefix='/api/labs')

# --- Helper Functions ---
def generate_order_number():
    """Generates a unique order number."""
    # Example: LIS-YYYYMMDD-HHMMSS-UUID_SHORT
    now = datetime.datetime.utcnow()
    return f"LIS-{now.strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"

def create_critical_value_alert(lab_result: LabResult, patient: Patient):
    """Creates a critical value alert if the result is critical."""
    if lab_result.abnormal_flag and lab_result.abnormal_flag.lower() in ['critical', 'panic', 'aa', 'a']:
        # Check if an alert already exists for this result to avoid duplicates
        existing_alert = db.session.query(CriticalValueAlert).filter_by(lab_result_id=lab_result.id).first()
        if existing_alert:
            # print(f"Alert already exists for result ID {lab_result.id}. Skipping creation.")
            return existing_alert

        alert = CriticalValueAlert(
            lab_result_id=lab_result.id,
            patient_id=patient.id,
            alert_datetime=datetime.datetime.utcnow(),
            alert_level=lab_result.abnormal_flag, # Or map to a more specific level if needed
            # notified_personnel_id, notification_method - to be handled by a notification system
            notes=f"Critical value detected for test {lab_result.test_definition.test_name}: {lab_result.result_value_text or lab_result.result_numeric} {lab_result.result_units}"
        )
        db.session.add(alert)
        # db.session.commit() # Commit might be handled by calling function or a background task
        # print(f"Created critical value alert for result ID {lab_result.id}")
        return alert
    return None

def acknowledge_critical_alerts_for_result(result_id: int, user_id: str):
    """Acknowledge all critical alerts associated with a given lab result."""
    alerts = db.session.query(CriticalValueAlert).filter_by(lab_result_id=result_id, acknowledgement_datetime=None).all()
    if not alerts:
        return False # No unacknowledged alerts for this result

    for alert in alerts:
        alert.acknowledgement_datetime = datetime.datetime.utcnow()
        alert.acknowledged_by_user_id = user_id
        alert.escalation_status = 'acknowledged'
        # Update LabResult status if applicable (e.g., from CRITICAL to CRITICAL_ACKNOWLEDGED)
        if alert.lab_result and alert.lab_result.status == TestStatus.CRITICAL:
            alert.lab_result.status = TestStatus.CRITICAL_ACKNOWLEDGED

    # db.session.commit() # Commit handled by calling route
    return True


def update_ml_features(patient_id: int):
    """Placeholder: Triggers ML feature recalculation for a patient."""
    # In a real system, this might be a background task or a call to an ML service
    try:
        engine = LabAnalyticsEngine(db.session) # Pass the session
        # This is a simplified call; real implementation might involve more params or async processing
        summary = engine.generate_patient_lab_summary(patient_id)

        # Log that features were updated (or an attempt was made)
        patient = db.session.query(Patient).filter_by(id=patient_id).first()
        if patient:
            patient.ml_features_extracted = True # Mark as extracted
            patient.feature_extraction_date = datetime.datetime.utcnow()
            # db.session.commit() # Commit handled by calling route
        # print(f"ML feature update triggered for patient {patient_id}. Summary keys: {summary.keys()}")
        return True
    except Exception as e:
        # print(f"Error updating ML features for patient {patient_id}: {e}")
        # current_app.logger.error(f"Error updating ML features for patient {patient_id}: {e}")
        return False

# --- API Endpoints ---

@lab_bp.route('/test-definitions', methods=['GET'])
@jwt_required()
def get_lab_test_definitions():
    """Get all available lab test definitions."""
    try:
        definitions = db.session.query(LabTestDefinition).filter(LabTestDefinition.is_active == True).all()
        return jsonify([
            {
                'id': d.id, 'test_name': d.test_name, 'short_name': d.short_name,
                'loinc_code': d.loinc_code, 'category': d.category, 'methodology': d.methodology,
                'specimen_type_options': d.specimen_type_options, # Already a string representing JSON list
                'reference_ranges': d.reference_ranges, # JSON
                'units': d.units,
                'normal_range_low': d.normal_range_low, 'normal_range_high': d.normal_range_high,
                'critical_range_low': d.critical_range_low, 'critical_range_high': d.critical_range_high,
                'turnaround_time_hours': d.turnaround_time_hours, 'description': d.description,
                'container_type': d.container_type, 'storage_requirements': d.storage_requirements,
                'cost_usd': float(d.cost_usd) if d.cost_usd else None, 'is_active': d.is_active
            } for d in definitions
        ]), 200
    except Exception as e:
        # current_app.logger.error(f"Error fetching lab test definitions: {e}")
        return jsonify({'message': 'Failed to fetch lab test definitions', 'error': str(e)}), 500


@lab_bp.route('/patients/<int:patient_id>/orders', methods=['POST'])
@jwt_required()
def create_lab_order(patient_id: int):
    """Create a new lab order for a patient."""
    data = request.get_json()
    user_id = get_jwt_identity()

    patient = db.session.query(Patient).filter_by(id=patient_id).first()
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    # Validate required fields
    if not data.get('test_definition_ids') or not isinstance(data['test_definition_ids'], list):
        return jsonify({'message': '`test_definition_ids` (list) is required'}), 400

    # Basic validation for specimen type and priority if provided
    specimen_type_str = data.get('specimen_type')
    if specimen_type_str and not hasattr(SpecimenType, specimen_type_str.upper()):
        return jsonify({'message': f"Invalid specimen type: {specimen_type_str}. Valid types: {[s.name for s in SpecimenType]}"}), 400

    priority_str = data.get('priority', 'routine') # Default to routine

    try:
        new_order = LabOrder(
            order_uuid=generate_order_number(), # Use helper for custom ID or rely on default UUID
            patient_id=patient_id,
            ordering_physician_id=data.get('ordering_physician_id', user_id), # Default to JWT identity
            order_datetime=datetime.datetime.fromisoformat(data['order_datetime']) if data.get('order_datetime') else datetime.datetime.utcnow(),
            priority=priority_str,
            status=TestStatus.ORDERED, # Initial status
            specimen_type=SpecimenType[specimen_type_str.upper()] if specimen_type_str else None,
            specimen_collection_datetime=datetime.datetime.fromisoformat(data['specimen_collection_datetime']) if data.get('specimen_collection_datetime') else None,
            notes=data.get('notes'),
            related_diagnoses_codes=data.get('related_diagnoses_codes') # Should be JSON string '["code1", "code2"]'
        )
        db.session.add(new_order)
        db.session.flush() # Get new_order.id for LabResult creation

        # Create individual LabResult entries for each test in the order
        for test_def_id in data['test_definition_ids']:
            test_def = db.session.query(LabTestDefinition).filter_by(id=test_def_id).first()
            if not test_def:
                db.session.rollback() # Rollback if any test definition is invalid
                return jsonify({'message': f'LabTestDefinition with ID {test_def_id} not found'}), 400

            lab_result_entry = LabResult(
                lab_order_id=new_order.id,
                test_definition_id=test_def_id,
                patient_id=patient_id, # Denormalized for easier queries
                status=TestStatus.ORDERED, # Initial status for the result item
                result_type='pending', # Placeholder until result is available
                result_datetime=new_order.order_datetime # Or when results are expected/processed
            )
            db.session.add(lab_result_entry)

        # Log audit
        audit = AuditLog(user_id_source=user_id, action='CREATE_LAB_ORDER', table_name='lab_orders', record_id=new_order.id)
        db.session.add(audit)

        db.session.commit()
        return jsonify({'message': 'Lab order created successfully', 'order_id': new_order.id, 'order_uuid': new_order.order_uuid}), 201

    except IntegrityError as e:
        db.session.rollback()
        # current_app.logger.error(f"Integrity error creating lab order: {e}")
        return jsonify({'message': 'Database integrity error', 'error': str(e.orig)}), 400
    except Exception as e:
        db.session.rollback()
        # current_app.logger.error(f"Error creating lab order: {e}")
        return jsonify({'message': 'Failed to create lab order', 'error': str(e)}), 500


@lab_bp.route('/patients/<int:patient_id>/orders', methods=['GET'])
@jwt_required()
def get_patient_lab_orders(patient_id: int):
    """Get all lab orders for a specific patient."""
    patient = db.session.query(Patient).filter_by(id=patient_id).first()
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    try:
        orders = db.session.query(LabOrder).filter_by(patient_id=patient_id).order_by(LabOrder.order_datetime.desc()).all()

        orders_data = []
        for order in orders:
            order_dict = {
                'id': order.id, 'order_uuid': order.order_uuid, 'patient_id': order.patient_id,
                'ordering_physician_id': order.ordering_physician_id,
                'order_datetime': order.order_datetime.isoformat(),
                'priority': order.priority,
                'status': order.status.value if order.status else None, # Enum to value
                'specimen_type': order.specimen_type.value if order.specimen_type else None, # Enum to value
                'specimen_collection_datetime': order.specimen_collection_datetime.isoformat() if order.specimen_collection_datetime else None,
                'specimen_received_datetime': order.specimen_received_datetime.isoformat() if order.specimen_received_datetime else None,
                'notes': order.notes,
                'related_diagnoses_codes': order.related_diagnoses_codes, # Already string
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'results_summary': [ # Simplified summary of tests in the order
                    {
                        'result_id': res.id,
                        'test_name': res.test_definition.test_name,
                        'status': res.status.value if res.status else None
                    } for res in order.results # Assuming LabOrder.results relationship
                ]
            }
            orders_data.append(order_dict)
        return jsonify(orders_data), 200

    except Exception as e:
        # current_app.logger.error(f"Error fetching lab orders for patient {patient_id}: {e}")
        return jsonify({'message': 'Failed to fetch lab orders', 'error': str(e)}), 500


@lab_bp.route('/patients/<int:patient_id>/results', methods=['GET'])
@jwt_required()
def get_patient_lab_results(patient_id: int):
    """Get all lab results for a specific patient."""
    patient = db.session.query(Patient).filter_by(id=patient_id).first()
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    try:
        # Eager load related entities to reduce query count
        results = db.session.query(LabResult).options(
            joinedload(LabResult.test_definition),
            joinedload(LabResult.lab_order)
        ).filter_by(patient_id=patient_id).order_by(LabResult.result_datetime.desc()).all()

        results_data = []
        for r in results:
            results_data.append({
                'id': r.id, 'result_uuid': r.result_uuid, 'lab_order_id': r.lab_order_id,
                'test_definition_id': r.test_definition_id,
                'test_name': r.test_definition.test_name if r.test_definition else None,
                'test_category': r.test_definition.category if r.test_definition else None,
                'patient_id': r.patient_id,
                'result_type': r.result_type,
                'result_value_text': r.result_value_text,
                'result_numeric': r.result_numeric,
                'result_units': r.result_units,
                'reference_range': r.reference_range, # This is the string representation from LabResult
                'abnormal_flag': r.abnormal_flag,
                'status': r.status.value if r.status else None, # Enum to value
                'interpretation_notes': r.interpretation_notes,
                'verified_by_user_id': r.verified_by_user_id,
                'result_datetime': r.result_datetime.isoformat(),
                'created_at': r.created_at.isoformat(),
                'updated_at': r.updated_at.isoformat()
            })
        return jsonify(results_data), 200
    except Exception as e:
        # current_app.logger.error(f"Error fetching lab results for patient {patient_id}: {e}")
        return jsonify({'message': 'Failed to fetch lab results', 'error': str(e)}), 500


@lab_bp.route('/results/<int:result_id>', methods=['PUT'])
@jwt_required()
def update_lab_result(result_id: int):
    """Update a lab result (e.g., add numeric value, interpretation)."""
    data = request.get_json()
    user_id = get_jwt_identity()

    result = db.session.query(LabResult).options(
        joinedload(LabResult.patient),
        joinedload(LabResult.test_definition)
    ).filter_by(id=result_id).first()

    if not result:
        return jsonify({'message': 'Lab result not found'}), 404

    # Fields that can be updated by a lab system/technician
    if 'result_value_text' in data: result.result_value_text = data['result_value_text']
    if 'result_numeric' in data: result.result_numeric = data['result_numeric']
    if 'result_units' in data: result.result_units = data['result_units']
    if 'reference_range' in data: result.reference_range = data['reference_range'] # e.g. "70-110 mg/dL"
    if 'abnormal_flag' in data: result.abnormal_flag = data['abnormal_flag'] # e.g. H, L, A, AA
    if 'interpretation_notes' in data: result.interpretation_notes = data['interpretation_notes']
    if 'status' in data:
        new_status_str = data['status']
        if not hasattr(TestStatus, new_status_str.upper()):
            return jsonify({'message': f"Invalid status: {new_status_str}. Valid: {[s.name for s in TestStatus]}"}), 400
        result.status = TestStatus[new_status_str.upper()]

    if 'result_datetime' in data and data['result_datetime']: # Ensure not empty string
        result.result_datetime = datetime.datetime.fromisoformat(data['result_datetime'])
    else: # If not provided, set to now if status implies completion
        if result.status in [TestStatus.COMPLETED, TestStatus.CRITICAL, TestStatus.CRITICAL_ACKNOWLEDGED]:
            result.result_datetime = datetime.datetime.utcnow()


    if result.status == TestStatus.COMPLETED or result.status == TestStatus.CRITICAL:
        result.verified_by_user_id = user_id # Mark who verified/completed it

    try:
        # Handle critical value alert creation
        if result.status == TestStatus.CRITICAL:
            patient = result.patient # Patient object from joinedload
            if patient:
                create_critical_value_alert(result, patient)
            else: # Should not happen if DB is consistent
                # current_app.logger.error(f"Patient not found for result {result.id} when creating critical alert.")
                db.session.rollback()
                return jsonify({'message': 'Patient data missing for critical alert creation.'}), 500

        # If result status is now "acknowledged", ensure alerts are marked
        if result.status == TestStatus.CRITICAL_ACKNOWLEDGED:
            acknowledge_critical_alerts_for_result(result.id, user_id)

        # Log audit
        audit = AuditLog(user_id_source=user_id, action='UPDATE_LAB_RESULT', table_name='lab_results', record_id=result.id, description=f"Status set to {result.status.value if result.status else 'N/A'}")
        db.session.add(audit)

        db.session.commit()

        # Trigger ML feature update for the patient
        update_ml_features(result.patient_id) # Pass patient_id
        db.session.commit() # Commit changes from update_ml_features

        return jsonify({'message': 'Lab result updated successfully', 'result_id': result.id}), 200
    except IntegrityError as e:
        db.session.rollback()
        # current_app.logger.error(f"Integrity error updating lab result {result_id}: {e}")
        return jsonify({'message': 'Database integrity error', 'error': str(e.orig)}), 400
    except Exception as e:
        db.session.rollback()
        # current_app.logger.error(f"Error updating lab result {result_id}: {e}")
        return jsonify({'message': 'Failed to update lab result', 'error': str(e)}), 500


@lab_bp.route('/patients/<int:patient_id>/analytics', methods=['GET'])
@jwt_required()
def get_patient_lab_analytics(patient_id: int):
    """Get ML-driven lab analytics for a patient."""
    patient = db.session.query(Patient).filter_by(id=patient_id).first()
    if not patient:
        return jsonify({'message': 'Patient not found'}), 404

    try:
        lookback_days = request.args.get('lookback_days', default=365, type=int)
        analytics_engine = LabAnalyticsEngine(db.session) # Pass the current db session
        summary = analytics_engine.generate_patient_lab_summary(patient_id, lookback_days)

        if 'message' in summary and 'No features extracted' in summary['message']:
            return jsonify(summary), 404 # Or 200 with the message, depending on desired behavior

        return jsonify(summary), 200
    except Exception as e:
        # current_app.logger.error(f"Error generating lab analytics for patient {patient_id}: {e}")
        return jsonify({'message': 'Failed to generate lab analytics', 'error': str(e)}), 500

@lab_bp.route('/alerts/critical-values', methods=['GET'])
@jwt_required()
def get_critical_value_alerts():
    """Get critical value alerts, optionally filtered by status."""
    status_filter = request.args.get('status') # e.g., 'pending', 'acknowledged'

    query = db.session.query(CriticalValueAlert).options(
        joinedload(CriticalValueAlert.lab_result).joinedload(LabResult.test_definition),
        joinedload(CriticalValueAlert.patient)
    ).order_by(CriticalValueAlert.alert_datetime.desc())

    if status_filter:
        if status_filter.lower() == 'pending':
            query = query.filter(CriticalValueAlert.acknowledgement_datetime.is_(None))
        elif status_filter.lower() == 'acknowledged':
            query = query.filter(CriticalValueAlert.acknowledgement_datetime.isnot(None))
        # Add more status filters if needed, e.g., based on escalation_status

    try:
        alerts = query.all()
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id, 'alert_uuid': alert.alert_uuid,
                'lab_result_id': alert.lab_result_id,
                'patient_id': alert.patient_id,
                'patient_psychiatry_id': alert.patient.psychiatry_id if alert.patient else "N/A",
                'test_name': alert.lab_result.test_definition.test_name if alert.lab_result and alert.lab_result.test_definition else "N/A",
                'result_value': f"{alert.lab_result.result_numeric or alert.lab_result.result_value_text} {alert.lab_result.result_units or ''}".strip(),
                'alert_datetime': alert.alert_datetime.isoformat(),
                'alert_level': alert.alert_level,
                'notified_personnel_id': alert.notified_personnel_id,
                'notification_method': alert.notification_method,
                'acknowledgement_datetime': alert.acknowledgement_datetime.isoformat() if alert.acknowledgement_datetime else None,
                'acknowledged_by_user_id': alert.acknowledged_by_user_id,
                'escalation_status': alert.escalation_status,
                'notes': alert.notes,
                'created_at': alert.created_at.isoformat(),
                'updated_at': alert.updated_at.isoformat()
            })
        return jsonify(alerts_data), 200
    except Exception as e:
        # current_app.logger.error(f"Error fetching critical value alerts: {e}")
        return jsonify({'message': 'Failed to fetch critical value alerts', 'error': str(e)}), 500

@lab_bp.route('/alerts/critical-values/<int:alert_id>/acknowledge', methods=['PUT'])
@jwt_required()
def acknowledge_critical_value_alert(alert_id: int):
    """Acknowledge a specific critical value alert."""
    user_id = get_jwt_identity()
    alert = db.session.query(CriticalValueAlert).options(joinedload(CriticalValueAlert.lab_result)).filter_by(id=alert_id).first()

    if not alert:
        return jsonify({'message': 'Critical value alert not found'}), 404

    if alert.acknowledgement_datetime:
        return jsonify({'message': 'Alert already acknowledged'}), 400

    alert.acknowledgement_datetime = datetime.datetime.utcnow()
    alert.acknowledged_by_user_id = user_id
    alert.escalation_status = 'acknowledged' # Or other appropriate status

    # Optionally, update the related LabResult status if it's still 'CRITICAL'
    if alert.lab_result and alert.lab_result.status == TestStatus.CRITICAL:
        alert.lab_result.status = TestStatus.CRITICAL_ACKNOWLEDGED

    try:
        # Log audit
        audit = AuditLog(user_id_source=user_id, action='ACKNOWLEDGE_CRITICAL_ALERT', table_name='critical_value_alerts', record_id=alert.id)
        db.session.add(audit)
        db.session.commit()
        return jsonify({'message': 'Critical value alert acknowledged successfully', 'alert_id': alert.id}), 200
    except Exception as e:
        db.session.rollback()
        # current_app.logger.error(f"Error acknowledging critical value alert {alert_id}: {e}")
        return jsonify({'message': 'Failed to acknowledge alert', 'error': str(e)}), 500

# Placeholder for registering blueprint with Flask app in main __init__.py or app.py
# from .lab_routes import lab_bp
# app.register_blueprint(lab_bp)
