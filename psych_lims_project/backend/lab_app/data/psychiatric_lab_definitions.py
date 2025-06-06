# backend/lab_app/data/psychiatric_lab_definitions.py
from lab_app.models import LabTestDefinition # Assuming models.py is in lab_app
from lab_app import db # Assuming db is in lab_app/__init__.py

PSYCHIATRIC_LAB_DEFINITIONS = [
    # Therapeutic Drug Monitoring (TDM)
    {
        'test_code': 'LITH_LEVEL',
        'test_name': 'Lithium Level',
        'test_category': 'TDM',
        'clinical_indication': 'Monitor lithium toxicity and therapeutic levels; manage bipolar disorder, major depressive disorder (augmentation), schizoaffective disorder.',
        'psychiatric_relevance': 'Essential for safe and effective management of bipolar disorder; prevents toxicity and ensures therapeutic efficacy. Critical for personalized dosing.',
        'medication_monitoring': '["lithium_carbonate", "lithium_citrate"]', # Stored as JSON string
        'specimen_types': '["serum"]', # Stored as JSON string
        'volume_required_ml': 3.0,
        'fasting_required': False,
        'timing_requirements': 'Draw 12 hours after last dose (trough level) for accurate interpretation.',
        'collection_instructions': 'Avoid collecting immediately after a dose. Ensure patient is well-hydrated. Indicate time of last dose on requisition.',
        'reference_ranges': {
            'adult': {
                'maintenance': {'low': 0.6, 'high': 1.2, 'unit': 'mEq/L'},
                'acute': {'low': 0.8, 'high': 1.4, 'unit': 'mEq/L'}
            },
            'elderly': {'low': 0.4, 'high': 0.8, 'unit': 'mEq/L', 'note': 'Lower therapeutic range often due to renal sensitivity.'}
        },
        'critical_values': {'high': 1.5, 'unit': 'mEq/L', 'action': 'Immediate clinical review, consider dose reduction or hold.'},
        'panic_values': {'high': 2.0, 'unit': 'mEq/L', 'action': 'Emergency medical evaluation for acute lithium toxicity (seizures, coma).'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'monthly_to_quarterly',
        'normal_range_percentage': 70.0,
        'minimum_detection_limit': 0.1,
        'maximum_reportable_value': 4.0
    },
    {
        'test_code': 'VPA_LEVEL',
        'test_name': 'Valproic Acid Level',
        'test_category': 'TDM',
        'clinical_indication': 'Monitor valproic acid therapeutic levels for bipolar disorder, seizure control, and migraine prophylaxis.',
        'psychiatric_relevance': 'Mood stabilizer monitoring for bipolar disorder; helps optimize dosing to achieve efficacy while minimizing side effects like hepatotoxicity or thrombocytopenia.',
        'medication_monitoring': '["valproic_acid", "divalproex_sodium", "valproate_sodium"]',
        'specimen_types': '["serum", "plasma"]',
        'volume_required_ml': 3.0,
        'fasting_required': False,
        'timing_requirements': 'Draw immediately before next dose (trough level) for consistent measurement.',
        'collection_instructions': 'Ensure patient adherence to dosing schedule. Indicate time of last dose on requisition.',
        'reference_ranges': {
            'therapeutic': {'low': 50, 'high': 100, 'unit': 'mcg/mL', 'note': 'Some sources cite up to 125 mcg/mL for efficacy.'},
            'toxicity_risk_begins': {'low': 100, 'high': 125, 'unit': 'mcg/mL'},
        },
        'critical_values': {'high': 125, 'unit': 'mcg/mL', 'action': 'Evaluate for toxicity (sedation, GI upset, tremor).'},
        'panic_values': {'high': 150, 'unit': 'mcg/mL', 'action': 'Urgent clinical evaluation for severe toxicity (encephalopathy, coma).'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'monthly_to_quarterly',
        'normal_range_percentage': 75.0,
        'minimum_detection_limit': 5.0,
        'maximum_reportable_value': 200.0
    },
    {
        'test_code': 'CARBA_LEVEL',
        'test_name': 'Carbamazepine Level',
        'test_category': 'TDM',
        'clinical_indication': 'Monitor carbamazepine therapeutic levels for bipolar disorder, trigeminal neuralgia, and seizure disorders.',
        'psychiatric_relevance': 'Monitoring is crucial due to narrow therapeutic index and potential for bone marrow suppression (agranulocytosis, aplastic anemia) and hepatic toxicity. Helps optimize dosing.',
        'medication_monitoring': '["carbamazepine"]',
        'specimen_types': '["serum", "plasma"]',
        'volume_required_ml': 3.0,
        'fasting_required': False,
        'timing_requirements': 'Draw immediately before next dose (trough level).',
        'collection_instructions': 'Indicate time of last dose. Monitor for autoinduction phenomenon after initiation.',
        'reference_ranges': {
            'therapeutic': {'low': 4, 'high': 12, 'unit': 'mcg/mL'}
        },
        'critical_values': {'high': 15, 'unit': 'mcg/mL', 'action': 'Assess for toxicity (dizziness, ataxia, nystagmus).'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'monthly_to_quarterly',
        'normal_range_percentage': 80.0,
        'minimum_detection_limit': 0.5,
        'maximum_reportable_value': 20.0
    },
    {
        'test_code': 'LAMO_LEVEL',
        'test_name': 'Lamotrigine Level',
        'test_category': 'TDM',
        'clinical_indication': 'Monitor lamotrigine levels for bipolar disorder, and seizure disorders. While not always mandatory, helpful for adherence, toxicity, or unexpected non-response.',
        'psychiatric_relevance': 'Used in managing bipolar depression. Levels can be affected by other medications (e.g., valproate increases levels, carbamazepine decreases levels). Monitoring aids in complex polypharmacy.',
        'medication_monitoring': '["lamotrigine"]',
        'specimen_types': '["serum", "plasma"]',
        'volume_required_ml': 3.0,
        'fasting_required': False,
        'timing_requirements': 'Trough level, ideally before next dose.',
        'collection_instructions': 'Note concomitant medications, especially valproate or enzyme-inducing antiepileptics.',
        'reference_ranges': {
            'therapeutic': {'low': 2.5, 'high': 15, 'unit': 'mcg/mL', 'note': 'Reference ranges vary widely; clinical correlation is essential.'}
        },
        'critical_values': {'high': 20, 'unit': 'mcg/mL', 'action': 'Evaluate for toxicity (dizziness, blurred vision, rash).'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'as_needed',
        'normal_range_percentage': 85.0,
        'minimum_detection_limit': 0.1,
        'maximum_reportable_value': 30.0
    },
    {
        'test_code': 'HBA1C',
        'test_name': 'Hemoglobin A1c',
        'test_category': 'Metabolic_Panel',
        'clinical_indication': 'Monitor long-term glucose control over 2-3 months; screen for and diagnose diabetes and prediabetes.',
        'psychiatric_relevance': 'Crucial for monitoring metabolic side effects of atypical antipsychotics (e.g., olanzapine, clozapine, quetiapine), which can induce insulin resistance and type 2 diabetes. Essential for early intervention and metabolic syndrome management.',
        'medication_monitoring': '["olanzapine", "clozapine", "quetiapine", "risperidone", "aripiprazole"]',
        'specimen_types': '["whole_blood"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'normal': {'low': 4.0, 'high': 5.6, 'unit': '%'},
            'prediabetes': {'low': 5.7, 'high': 6.4, 'unit': '%'},
            'diabetes': {'low': 6.5, 'high': None, 'unit': '%'}
        },
        'critical_values': {'high': 10.0, 'unit': '%', 'action': 'Urgent review with patient for diabetes management plan.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'annually_to_semi-annually',
        'normal_range_percentage': 70.0,
        'minimum_detection_limit': 3.0,
        'maximum_reportable_value': 18.0
    },
    {
        'test_code': 'GLUCOSE_FASTING',
        'test_name': 'Fasting Glucose',
        'test_category': 'Metabolic_Panel',
        'clinical_indication': 'Screen for and diagnose diabetes and prediabetes; monitor glucose levels.',
        'psychiatric_relevance': 'Similar to HbA1c, important for monitoring metabolic side effects of antipsychotics. Provides a snapshot of current glucose control. Often ordered in conjunction with lipids.',
        'medication_monitoring': '["olanzapine", "clozapine", "quetiapine", "risperidone"]',
        'specimen_types': '["serum", "plasma"]',
        'volume_required_ml': 2.0,
        'fasting_required': True,
        'timing_requirements': 'Fasting for 8-12 hours prior to collection.',
        'reference_ranges': {
            'normal': {'high': 99, 'unit': 'mg/dL'},
            'prediabetes': {'low': 100, 'high': 125, 'unit': 'mg/dL'},
            'diabetes': {'low': 126, 'high': None, 'unit': 'mg/dL'}
        },
        'critical_values': {'low': 50, 'high': 250, 'unit': 'mg/dL', 'action': 'Investigate hypoglycemia or hyperglycemia, consider immediate intervention.'},
        'panic_values': {'low': 40, 'high': 400, 'unit': 'mg/dL', 'action': 'Emergency medical evaluation.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'annually_to_semi-annually',
        'normal_range_percentage': 75.0,
        'minimum_detection_limit': 20.0,
        'maximum_reportable_value': 600.0
    },
    {
        'test_code': 'LIPID_PANEL_FASTING',
        'test_name': 'Fasting Lipid Panel',
        'test_category': 'Lipid_Panel',
        'clinical_indication': 'Assess risk of cardiovascular disease; monitor lipid-lowering therapy.',
        'psychiatric_relevance': 'Antipsychotics can cause dyslipidemia, increasing cardiovascular risk in a population already vulnerable to premature mortality from cardiovascular disease. Essential for holistic patient management.',
        'medication_monitoring': '["olanzapine", "clozapine", "quetiapine", "risperidone"]',
        'specimen_types': '["serum", "plasma"]',
        'volume_required_ml': 4.0,
        'fasting_required': True,
        'timing_requirements': 'Fasting for 9-12 hours.',
        'reference_ranges': {
            'total_cholesterol': {'high': 199, 'unit': 'mg/dL'},
            'LDL_cholesterol': {'high': 99, 'unit': 'mg/dL'},
            'HDL_cholesterol': {'low': 40, 'unit': 'mg/dL'},
            'triglycerides': {'high': 149, 'unit': 'mg/dL'}
        },
        'critical_values': {'triglycerides_high': 500, 'unit': 'mg/dL', 'action': 'Risk of pancreatitis, urgent review.'},
        'ml_relevant': True,
        'feature_type': 'continuous', # Each component is continuous
        'expected_frequency': 'annually_to_semi-annually',
        'normal_range_percentage': 60.0,
        'minimum_detection_limit': 10.0, # Example for triglycerides
        'maximum_reportable_value': 1000.0 # Example for triglycerides
    },
    {
        'test_code': 'ALT',
        'test_name': 'Alanine Aminotransferase',
        'test_category': 'Liver_Function',
        'clinical_indication': 'Monitor liver function and detect hepatocellular injury.',
        'psychiatric_relevance': 'Many psychiatric medications (e.g., valproic acid, carbamazepine, lamotrigine, antipsychotics like clozapine) can cause hepatotoxicity. Regular monitoring helps detect liver injury early.',
        'medication_monitoring': '["valproic_acid", "carbamazepine", "lamotrigine", "clozapine", "duloxetine", "phenelzine"]',
        'specimen_types': '["serum"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'male': {'low': 10, 'high': 40, 'unit': 'U/L'},
            'female': {'low': 7, 'high': 35, 'unit': 'U/L'}
        },
        'critical_values': {'high': 200, 'unit': 'U/L', 'action': 'Investigate acute liver injury, consider medication review.'},
        'panic_values': {'high': 500, 'unit': 'U/L', 'action': 'Urgent clinical evaluation for severe liver damage.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'monthly_to_quarterly',
        'normal_range_percentage': 90.0,
        'minimum_detection_limit': 1.0,
        'maximum_reportable_value': 2000.0
    },
    {
        'test_code': 'AST',
        'test_name': 'Aspartate Aminotransferase',
        'test_category': 'Liver_Function',
        'clinical_indication': 'Monitor liver function, often alongside ALT, to assess hepatocellular injury.',
        'psychiatric_relevance': 'Similar to ALT, provides insight into potential liver damage from psychiatric medications. Elevated AST/ALT ratio can suggest alcoholic liver disease.',
        'medication_monitoring': '["valproic_acid", "carbamazepine", "clozapine"]',
        'specimen_types': '["serum"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'adult': {'low': 10, 'high': 35, 'unit': 'U/L'}
        },
        'critical_values': {'high': 200, 'unit': 'U/L', 'action': 'Investigate acute liver injury.'},
        'panic_values': {'high': 500, 'unit': 'U/L', 'action': 'Urgent clinical evaluation.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'monthly_to_quarterly',
        'normal_range_percentage': 90.0,
        'minimum_detection_limit': 1.0,
        'maximum_reportable_value': 2000.0
    },
    {
        'test_code': 'CREATININE',
        'test_name': 'Creatinine',
        'test_category': 'Kidney_Function',
        'clinical_indication': 'Assess kidney function and estimate glomerular filtration rate (GFR).',
        'psychiatric_relevance': 'Important for dosage adjustments of renally excreted psychiatric medications (e.g., lithium, gabapentin, pregabalin). Renal impairment can lead to drug accumulation and toxicity.',
        'medication_monitoring': '["lithium", "gabapentin", "pregabalin"]',
        'specimen_types': '["serum"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'male_adult': {'low': 0.74, 'high': 1.35, 'unit': 'mg/dL'},
            'female_adult': {'low': 0.59, 'high': 1.04, 'unit': 'mg/dL'}
        },
        'critical_values': {'high': 4.0, 'unit': 'mg/dL', 'action': 'Investigate acute kidney injury, urgent medication review.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'quarterly_to_annually',
        'normal_range_percentage': 95.0,
        'minimum_detection_limit': 0.1,
        'maximum_reportable_value': 20.0
    },
    {
        'test_code': 'TSH',
        'test_name': 'Thyroid-Stimulating Hormone',
        'test_category': 'Endocrine',
        'clinical_indication': 'Screen for and diagnose thyroid disorders (hypothyroidism, hyperthyroidism).',
        'psychiatric_relevance': 'Thyroid dysfunction can mimic or exacerbate psychiatric symptoms (e.g., hypothyroidism can cause depression, hyperthyroidism can cause anxiety or psychosis). Lithium can induce hypothyroidism.',
        'medication_monitoring': '["lithium"]',
        'specimen_types': '["serum"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'adult': {'low': 0.4, 'high': 4.0, 'unit': 'mIU/L'}
        },
        'critical_values': {'low': 0.1, 'high': 10.0, 'unit': 'mIU/L', 'action': 'Investigate severe hypo/hyperthyroidism.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'annually',
        'normal_range_percentage': 95.0,
        'minimum_detection_limit': 0.01,
        'maximum_reportable_value': 100.0
    },
    {
        'test_code': 'CBC_DIFF',
        'test_name': 'Complete Blood Count with Differential',
        'test_category': 'CBC',
        'clinical_indication': 'Assess overall health, screen for and diagnose conditions like anemia, infection, and leukemia.',
        'psychiatric_relevance': 'Essential for monitoring adverse hematological effects of certain psychiatric medications, particularly clozapine (agranulocytosis) and carbamazepine (aplastic anemia, leukopenia).',
        'medication_monitoring': '["clozapine", "carbamazepine"]',
        'specimen_types': '["whole_blood"]',
        'volume_required_ml': 3.0,
        'fasting_required': False,
        'reference_ranges': {
            'WBC': {'low': 4.0, 'high': 11.0, 'unit': 'x10^9/L'},
            'ANC': {'low': 1.5, 'high': 8.0, 'unit': 'x10^9/L'},
            'platelets': {'low': 150, 'high': 450, 'unit': 'x10^9/L'},
            'hemoglobin': {'male_low': 13.5, 'male_high': 17.5, 'female_low': 12.0, 'female_high': 15.5, 'unit': 'g/dL'}
        },
        'critical_values': {
            'WBC_low': 2.0, 'ANC_low': 1.0, 'platelets_low': 50, 'hemoglobin_low': 7.0,
            'unit': 'various', 'action': 'Urgent clinical evaluation for bone marrow suppression.'
        },
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'weekly_to_monthly',
        'normal_range_percentage': 90.0,
        'minimum_detection_limit': 0.1, # Example for WBC
        'maximum_reportable_value': 50.0 # Example for WBC
    },
    {
        'test_code': 'UDS_COMPREHENSIVE',
        'test_name': 'Comprehensive Urine Drug Screen',
        'test_category': 'Drug_Screening',
        'clinical_indication': 'Screen for illicit substance use or adherence to prescribed medications.',
        'psychiatric_relevance': 'Essential for substance use disorder assessment and treatment monitoring. Helps differentiate psychiatric symptoms from substance-induced conditions, informs treatment planning, and monitors adherence in medication-assisted treatment programs.',
        'specimen_types': '["urine"]',
        'volume_required_ml': 30.0,
        'fasting_required': False,
        'collection_instructions': 'Ensure proper chain of custody for legal purposes if required.',
        'reference_ranges': {
            'negative': {'value': 'Negative'} # Typically reported as Positive/Negative
        },
        'critical_values': {}, # Results are typically "Positive" or "Negative" rather than numerically critical
        'ml_relevant': True,
        'feature_type': 'categorical',
        'expected_frequency': 'as_needed_to_monthly',
        'normal_range_percentage': 50.0,
        'minimum_detection_limit': None, # Varies by analyte
        'maximum_reportable_value': None # Varies by analyte
    },
    {
        'test_code': 'ETHYL_GLUCURONIDE',
        'test_name': 'Ethyl Glucuronide (EtG)',
        'test_category': 'Drug_Screening',
        'clinical_indication': 'Detect recent alcohol consumption (up to 80 hours).',
        'psychiatric_relevance': 'More sensitive marker for alcohol use than traditional alcohol breath tests, useful for monitoring abstinence in patients with alcohol use disorder, particularly in recovery settings or those on medications like disulfiram.',
        'specimen_types': '["urine"]',
        'volume_required_ml': 10.0,
        'fasting_required': False,
        'collection_instructions': 'Urine sample.',
        'reference_ranges': {
            'negative': {'value': '<100 ng/mL'} # Example cutoff
        },
        'critical_values': {},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'as_needed_to_monthly',
        'normal_range_percentage': 70.0,
        'minimum_detection_limit': 50.0,
        'maximum_reportable_value': 50000.0
    },
    {
        'test_code': 'VITAMIN_D_TOTAL',
        'test_name': 'Vitamin D, Total (25-Hydroxy)',
        'test_category': 'Vitamin_Levels',
        'clinical_indication': 'Assess Vitamin D status.',
        'psychiatric_relevance': 'Vitamin D deficiency has been linked to depression, seasonal affective disorder, and cognitive decline. Supplementation may improve outcomes in some psychiatric conditions.',
        'specimen_types': '["serum"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'deficient': {'high': 20, 'unit': 'ng/mL'},
            'insufficient': {'low': 21, 'high': 29, 'unit': 'ng/mL'},
            'sufficient': {'low': 30, 'high': 100, 'unit': 'ng/mL'},
            'toxic': {'low': 101, 'unit': 'ng/mL'}
        },
        'critical_values': {'low': 10, 'high': 150, 'unit': 'ng/mL', 'action': 'Consider aggressive supplementation or investigation of hypervitaminosis D.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'annually',
        'normal_range_percentage': 60.0,
        'minimum_detection_limit': 5.0,
        'maximum_reportable_value': 200.0
    },
    {
        'test_code': 'VITAMIN_B12',
        'test_name': 'Vitamin B12',
        'test_category': 'Vitamin_Levels',
        'clinical_indication': 'Assess Vitamin B12 status.',
        'psychiatric_relevance': 'B12 deficiency can cause neurological and psychiatric symptoms including depression, cognitive impairment, and psychosis, mimicking or worsening mental health conditions. Crucial to rule out in differential diagnosis.',
        'specimen_types': '["serum"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'normal': {'low': 200, 'high': 900, 'unit': 'pg/mL'},
            'borderline': {'low': 150, 'high': 200, 'unit': 'pg/mL'},
            'deficient': {'high': 150, 'unit': 'pg/mL'}
        },
        'critical_values': {'low': 100, 'unit': 'pg/mL', 'action': 'Urgent investigation and supplementation due to neurological risk.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'annually',
        'normal_range_percentage': 90.0,
        'minimum_detection_limit': 50.0,
        'maximum_reportable_value': 2000.0
    },
    {
        'test_code': 'FOLATE',
        'test_name': 'Folate (Red Blood Cell)',
        'test_category': 'Vitamin_Levels',
        'clinical_indication': 'Assess Folate status (RBC Folate is preferred as it reflects tissue stores).',
        'psychiatric_relevance': 'Folate deficiency has been linked to depression and poor response to antidepressants. Essential for neurotransmitter synthesis. Important co-factor for metabolism of homocysteine, high levels of which are associated with cognitive decline and vascular risk.',
        'specimen_types': '["whole_blood"]',
        'volume_required_ml': 2.0,
        'fasting_required': False,
        'reference_ranges': {
            'normal': {'low': 140, 'high': 628, 'unit': 'ng/mL'}
        },
        'critical_values': {'low': 100, 'unit': 'ng/mL', 'action': 'Consider supplementation.'},
        'ml_relevant': True,
        'feature_type': 'continuous',
        'expected_frequency': 'annually',
        'normal_range_percentage': 90.0,
        'minimum_detection_limit': 50.0,
        'maximum_reportable_value': 1000.0
    }
]

def seed_psychiatric_lab_definitions(db_session): # db_session passed as argument
    """Seed database with psychiatric-relevant lab test definitions"""
    # Corrected: Iterate over a copy if modifying, or use a different variable name
    for definition_data in PSYCHIATRIC_LAB_DEFINITIONS:
        # Create a copy to avoid modifying the original dict during iteration if .pop was used
        # However, the provided model doesn't seem to need .pop if all keys match

        test_code = definition_data['test_code']

        existing = db_session.query(LabTestDefinition).filter_by(test_code=test_code).first()
        if not existing:
            # Ensure all keys in definition_data match LabTestDefinition fields
            # For ARRAY fields stored as Text, they are already strings in PSYCHIATRIC_LAB_DEFINITIONS
            lab_def = LabTestDefinition(**definition_data)
            db_session.add(lab_def)
            print(f"Added new lab test definition: {test_code}")
        else:
            print(f"Lab test definition already exists: {test_code}. Skipping.")
            # Optionally, add logic here to update existing definitions
            # For example:
            # for key, value in definition_data.items():
            #     setattr(existing, key, value)
            # print(f"Updated existing lab test definition: {test_code}")

    db_session.commit()
    print("Seeding of psychiatric lab definitions complete.")
