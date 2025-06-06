import pytest
from sqlalchemy.orm import Session
# Adjust the import path based on the actual location of your models
# Assuming lab_app is accessible in the Python path during tests
from lab_app.models.clinical_guidelines import ClinicalGuideline, GuidelineSource
from lab_app.models.stubs import LOINCConcept, RxNormConcept # If needed for relationships

# Assumption: A db fixture providing a SQLAlchemy Session is available (e.g., from conftest.py or a plugin).
# Example of what such a fixture might look like (if not using a plugin):
# @pytest.fixture(scope="session")
# def engine():
#     from sqlalchemy import create_engine
#     return create_engine("sqlite:///:memory:") # Or your test DB URL
#
# @pytest.fixture(scope="session")
# def tables(engine):
#     from lab_app.database import Base
#     Base.metadata.create_all(engine)
#     yield
#     Base.metadata.drop_all(engine)
#
# @pytest.fixture
# def db(engine, tables):
#     connection = engine.connect()
#     transaction = connection.begin()
#     session = Session(bind=connection)
#     yield session
#     session.close()
#     transaction.rollback()
#     connection.close()

@pytest.fixture
def sample_mdd_guideline(db: Session) -> ClinicalGuideline:
    # Optional: Create dummy LOINC and RxNorm concepts if your relationships need them
    # and they are not nullable / already handled by cascades or existing data.
    # Ensure these are committed if the guideline relies on their persisted state for FKs.
    # However, for unit testing the fixture itself, direct assignment might be mocked
    # or you might ensure the session is clean.

    # Example: Create related concepts if they are required for the FK and not nullable.
    # These would typically be pre-existing in a reference data setup.
    loinc_concept = db.query(LOINCConcept).filter_by(loinc_num="44503-3").first()
    if not loinc_concept:
        loinc_concept = LOINCConcept(loinc_num="44503-3", long_common_name="Depression")
        db.add(loinc_concept)

    rxnorm_concept = db.query(RxNormConcept).filter_by(rxcui="313992").first()
    if not rxnorm_concept:
        rxnorm_concept = RxNormConcept(rxcui="313992", str="Sertraline")
        db.add(rxnorm_concept)
    db.flush() # Flush to get IDs if needed by guideline, or commit if these are independent fixtures

    guideline = ClinicalGuideline(
        condition_loinc_code="44503-3", # Must exist in LOINCConcept table if FK is enforced
        guideline_name="MDD First-Line SSRI",
        source=GuidelineSource.APA,
        version="2023.1",
        applicability_criteria_json={"symptoms": ["MDD.A1 > 2"], "age_range": [18, 65]},
        recommended_treatment_rxnorm="313992", # Must exist in RxNormConcept table if FK is enforced
        starting_dose="50mg QD",
        rationale="Standard first-line for moderate MDD.",
        expected_response_time_weeks=4,
        priority_level=1
    )
    db.add(guideline)
    db.commit() # Commit to save the guideline and make it available for tests
    db.refresh(guideline) # Refresh to get any server-side defaults or updated state
    return guideline
