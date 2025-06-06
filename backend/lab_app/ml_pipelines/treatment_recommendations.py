from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
import json

from .clinical_summarization import SummarizerFactory

class LabPredictionModel:
    def predict_future_labs(self, patient_id: int) -> Dict:
        return {"predicted_creatinine_next_month": 1.1}

@dataclass
class TreatmentRecommendation:
    medication_name: str
    dosage: str
    confidence_score: float
    rationale: str
    contraindications: List[str]
    monitoring_requirements: List[str]
    expected_response_time: int  # weeks

class TreatmentRecommendationEngine:
    def __init__(self, patient_id: Optional[int] = None):
        self._treatment_guidelines = self._load_treatment_guidelines()
        self._model_version = "TRE_v_issue_desc_1.0"
        self._last_input_features: Dict[int, Any] = {}

    def _load_treatment_guidelines(self) -> List[Dict]:
        return [
            {
                "id": 1,
                "condition_loinc_code": "44503-3",
                "medication": "Sertraline",
                "starting_dose": "50mg QD",
                "rationale": "First-line SSRI for MDD based on patient profile and guideline A.",
                "contraindications": ["MAOI use within 14 days"],
                "monitoring": ["Monitor for suicidal ideation (first 4 weeks)", "Baseline LFTs"],
                "response_time_weeks": 4,
                "priority": 1,
                "applicability_criteria": {"symptoms": ["MDD.A1 > 2"], "age_range": [18, 65], "min_phq9": 10}
            },
            {
                "id": 2,
                "condition_loinc_code": "44503-3",
                "medication": "Escitalopram",
                "starting_dose": "10mg QD",
                "rationale": "Alternative SSRI for MDD, good tolerability.",
                "contraindications": ["Known hypersensitivity", "QTc prolongation risk"],
                "monitoring": ["Monitor for anxiety initially"],
                "response_time_weeks": 4,
                "priority": 2,
                "applicability_criteria": {"symptoms": ["MDD.A1 > 1"], "age_range": [18, 75], "min_phq9": 8}
            }
        ]

    def _get_comprehensive_patient_data(self, patient_id: int) -> Dict[str, Any]:
        mock_data = {
            "patient_id": patient_id, "age": 35, "symptoms": {"MDD.A1": 3, "MDD.A2": 2},
            "active_diagnoses_loinc": ["44503-3"], "current_medications_rxcuis": [],
            "past_treatments": [{"medication_rxcui": "197590", "outcome": "failed_tolerability"}],
            "lab_results": {"creatinine": 0.9, "potassium": 4.1},
            "allergies_rxcuis": ["aspirin_rxcui_placeholder"], "latest_phq9_score": 16,
        }
        self._last_input_features[patient_id] = mock_data
        return mock_data

    def _matches_criteria(self, patient_data: Dict, guideline: Dict) -> bool:
        criteria = guideline.get("applicability_criteria", {})
        age_range = criteria.get("age_range")
        if age_range and not (age_range[0] <= patient_data.get("age", 0) <= age_range[1]):
            return False
        required_symptoms = criteria.get("symptoms", [])
        for req_symp_str in required_symptoms:
            parts = req_symp_str.split(' ')
            if len(parts) == 3:
                symptom_code, operator, value_str = parts; value = int(value_str)
                patient_symptom_score = patient_data.get("symptoms", {}).get(symptom_code, 0)
                if operator == ">" and not (patient_symptom_score > value): return False
                if operator == ">=" and not (patient_symptom_score >= value): return False
            else:
                if not patient_data.get("symptoms", {}).get(req_symp_str, 0) > 0: return False
        min_phq9 = criteria.get("min_phq9")
        if min_phq9 and patient_data.get("latest_phq9_score", 0) < min_phq9:
            return False
        return True

    def _calculate_confidence(self, patient_data: Dict, guideline: Dict) -> float:
        base_confidence = 0.7
        priority_factor = (5 - guideline.get("priority", 3)) * 0.05
        if patient_data.get("latest_phq9_score",0) > 15 and guideline.get("priority", 3) == 1:
            priority_factor += 0.1
        confidence = base_confidence + priority_factor
        return min(max(confidence, 0.0), 1.0)

    def _check_contraindications(self, patient_data: Dict, guideline: Dict) -> List[str]:
        return guideline.get("contraindications", [])

    def get_treatment_recommendations(self, patient_id: int) -> List[TreatmentRecommendation]:
        patient_data = self._get_comprehensive_patient_data(patient_id)
        recommendations = []
        for guideline in self._treatment_guidelines:
            if self._matches_criteria(patient_data, guideline):
                rec = TreatmentRecommendation(
                    medication_name=guideline['medication'], dosage=guideline['starting_dose'],
                    confidence_score=self._calculate_confidence(patient_data, guideline),
                    rationale=guideline['rationale'],
                    contraindications=self._check_contraindications(patient_data, guideline),
                    monitoring_requirements=guideline['monitoring'],
                    expected_response_time=guideline['response_time_weeks']
                )
                recommendations.append(rec)
        return sorted(recommendations, key=lambda x: x.confidence_score, reverse=True)[:5]

    def get_model_version(self) -> Optional[str]:
        return self._model_version

    def get_last_input_features(self, patient_id: int) -> Dict[str, Any]:
        return self._last_input_features.get(patient_id, {})

    def get_combination_suggestions(self, patient_id: int, current_medications_rxcuis: List[str]) -> Dict:
        patient_data = self._get_comprehensive_patient_data(patient_id)
        patient_data["current_medications_rxcuis_for_combo_analysis"] = current_medications_rxcuis
        current_regimen_analysis = {"effectiveness_score": 0.65, "interaction_alerts": []}
        if "313992" in current_medications_rxcuis and "197590" in current_medications_rxcuis:
             current_regimen_analysis["interaction_alerts"].append("Monitor for QTc prolongation if Aripiprazole dose is high.")
        suggested_combinations = [{"medication_rxcui": "some_adjunct_rxcui", "rationale": "Consider for augmentation."}]
        augmentation_strategies = [{"strategy": "Add psychotherapy (CBT)", "rationale": "Evidence supports combo for MDD."}]
        optimization_opportunities = [{"opportunity": "Review Sertraline dose", "rationale": "Patient may benefit from titration."}]
        self._last_input_features[patient_id] = patient_data
        return {
            "current_regimen_analysis": current_regimen_analysis,
            "suggested_combinations": suggested_combinations,
            "augmentation_strategies": augmentation_strategies,
            "optimization_opportunities": optimization_opportunities
        }
