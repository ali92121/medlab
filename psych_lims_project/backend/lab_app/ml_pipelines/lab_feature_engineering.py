# backend/lab_app/ml_pipelines/lab_feature_engineering.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from scipy import stats
from sqlalchemy import desc, func

# Assuming db is initialized elsewhere and models are in lab_app.models
from lab_app.models import LabResult, LabTestDefinition, LabTrendAnalysis, CriticalValueAlert
# db object might be passed to classes or imported if used globally for session creation
from lab_app import db

@dataclass
class LabFeatureSet:
    patient_id: int
    feature_extraction_date: datetime
    lookback_days: int

    current_values: Dict[str, float] = field(default_factory=dict)
    current_flags: Dict[str, str] = field(default_factory=dict)
    trend_slopes: Dict[str, float] = field(default_factory=dict)
    trend_r_squared: Dict[str, float] = field(default_factory=dict)
    stability_coefficients: Dict[str, float] = field(default_factory=dict)
    days_since_last_test: Dict[str, int] = field(default_factory=dict)
    reference_range_ratios: Dict[str, float] = field(default_factory=dict)
    z_scores: Dict[str, float] = field(default_factory=dict)
    percentile_ranks: Dict[str, float] = field(default_factory=dict)
    medication_interaction_flags: Dict[str, bool] = field(default_factory=dict)
    test_frequency_deviations: Dict[str, float] = field(default_factory=dict)
    critical_value_history_counts: Dict[str, int] = field(default_factory=dict)
    abnormal_pattern_flags: Dict[str, bool] = field(default_factory=dict) # Changed from List[str] for consistency

    feature_vector: Optional[np.ndarray] = None
    feature_names: Optional[List[str]] = field(default_factory=list)

    def __post_init__(self):
        if self.feature_vector is None:
            self.feature_vector = np.array([])


class LabFeatureEngineer:
    def __init__(self, db_session):
        self.db_session = db_session # Changed from self.db to self.db_session for clarity
        self.scalers: Dict[str, StandardScaler] = {}
        self.reference_populations: Dict[str, Dict] = {}
        self._load_reference_data()

    def _load_reference_data(self):
        # Placeholder: Load pre-computed reference population statistics
        self.reference_populations['LITH_LEVEL'] = {
            'mean': 0.8, 'std': 0.2,
            'percentiles': {10: 0.5, 25: 0.6, 50: 0.8, 75: 1.0, 90: 1.1}
        }
        self.reference_populations['HBA1C'] = {
            'mean': 5.5, 'std': 0.5,
            'percentiles': {10: 5.0, 25: 5.2, 50: 5.5, 75: 5.8, 90: 6.2}
        }
        # Initialize scalers (can be loaded if pre-trained)
        # Fit scalers with some data to avoid NotFittedError, even if it's just placeholder range
        lith_scaler = StandardScaler()
        lith_scaler.fit(np.array([0.4, 0.6, 0.8, 1.0, 1.2, 1.4]).reshape(-1, 1))
        self.scalers['LITH_LEVEL'] = lith_scaler

        hba1c_scaler = StandardScaler()
        hba1c_scaler.fit(np.array([4.0, 5.0, 5.5, 6.0, 6.5, 7.0]).reshape(-1, 1))
        self.scalers['HBA1C'] = hba1c_scaler


    def _get_patient_lab_data(self, patient_id: int, lookback_days: int) -> pd.DataFrame:
        start_date = datetime.utcnow() - timedelta(days=lookback_days)

        results = self.db_session.query(
            LabResult.id.label('result_id'), # Ensure LabResult.id is available for joins/filtering later
            LabResult.result_numeric,
            LabResult.result_date,
            LabResult.abnormal_flag.label('interpretation_flag'), # Use abnormal_flag as interpretation_flag
            LabResult.test_definition_id,
            LabTestDefinition.test_code,
            LabTestDefinition.category.label('test_category'), # Use category as test_category
            LabTestDefinition.reference_ranges, # From definition
            # LabTestDefinition.critical_values,  # From definition - This field does not exist in LabTestDefinition
            # LabResult.reference_range_low.label('result_ref_low'), # Actual applied at result time - This field does not exist
            # LabResult.reference_range_high.label('result_ref_high') # Actual applied at result time - This field does not exist
            # Corrected fields based on LabResult model:
            LabTestDefinition.normal_range_low.label('result_ref_low'),
            LabTestDefinition.normal_range_high.label('result_ref_high')
        ).join(LabTestDefinition, LabResult.test_definition_id == LabTestDefinition.id).filter(
            LabResult.patient_id == patient_id,
            LabResult.result_numeric.isnot(None),
            LabResult.result_date >= start_date,
            # LabTestDefinition.ml_relevant == True  # This field does not exist in LabTestDefinition
        ).order_by(LabResult.result_date).all()

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame([r._asdict() for r in results]) # Use _asdict() for named tuples from query
        if not df.empty:
            df['result_date'] = pd.to_datetime(df['result_date'])
            return df.sort_values(by=['test_code', 'result_date']).reset_index(drop=True)
        return pd.DataFrame()


    def _extract_current_values(self, lab_data: pd.DataFrame) -> Tuple[Dict[str, float], Dict[str, str]]:
        current_values = {}
        current_flags = {}
        if lab_data.empty:
            return current_values, current_flags

        latest_results = lab_data.groupby('test_code').last()
        for test_code, row in latest_results.iterrows():
            current_values[test_code] = row['result_numeric']
            current_flags[test_code] = row['interpretation_flag']
        return current_values, current_flags

    def _extract_temporal_features(self, patient_id: int, lookback_days: int, lab_data: pd.DataFrame, unique_test_codes: List[str]) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float], Dict[str, int]]:
        trend_slopes: Dict[str, float] = {}
        trend_r_squared: Dict[str, float] = {}
        stability_coefficients: Dict[str, float] = {}
        days_since_last: Dict[str, int] = {}

        for test_code in unique_test_codes:
            test_def_id_series = lab_data[lab_data['test_code'] == test_code]['test_definition_id']
            if test_def_id_series.empty:
                continue
            test_def_id = test_def_id_series.iloc[0]

            # Assuming LabTrendAnalysis model has time_window_days, slope, r_squared, coefficient_of_variation, analysis_date
            trend_analysis = self.db_session.query(LabTrendAnalysis).filter(
                LabTrendAnalysis.patient_id == patient_id,
                LabTrendAnalysis.test_definition_id == test_def_id,
                # LabTrendAnalysis.time_window_days == lookback_days # This field does not exist
            ).order_by(desc(LabTrendAnalysis.generated_datetime)).first() # Use generated_datetime for ordering

            if trend_analysis and hasattr(trend_analysis, 'trend_data') and trend_analysis.trend_data:
                 # Assuming trend_data is a JSON field with keys like 'slope', 'r_squared', 'coefficient_of_variation'
                trend_slopes[test_code] = trend_analysis.trend_data.get('slope', 0.0)
                trend_r_squared[test_code] = trend_analysis.trend_data.get('r_squared', 0.0)
                stability_coefficients[test_code] = trend_analysis.trend_data.get('coefficient_of_variation', 0.0)
            else:
                test_results_df = lab_data[lab_data['test_code'] == test_code].sort_values('result_date')
                if len(test_results_df) >= 2:
                    x = (test_results_df['result_date'] - test_results_df['result_date'].min()).dt.days.values
                    y = test_results_df['result_numeric'].values

                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                    trend_slopes[test_code] = slope if np.isfinite(slope) else 0.0
                    trend_r_squared[test_code] = r_value**2 if np.isfinite(r_value) else 0.0

                    if np.mean(y) != 0 and np.isfinite(np.std(y)) and np.isfinite(np.mean(y)):
                        stability_coefficients[test_code] = np.std(y) / np.mean(y)
                    else:
                        stability_coefficients[test_code] = 0.0
                else:
                    trend_slopes[test_code] = 0.0
                    trend_r_squared[test_code] = 0.0
                    stability_coefficients[test_code] = 0.0

            latest_test_date = lab_data[lab_data['test_code'] == test_code]['result_date'].max()
            if pd.notna(latest_test_date): # Check if latest_test_date is not NaT
                days_since_last[test_code] = (datetime.utcnow().replace(tzinfo=None) - latest_test_date.replace(tzinfo=None)).days
            else:
                days_since_last[test_code] = -1

        return trend_slopes, trend_r_squared, stability_coefficients, days_since_last

    def _extract_comparative_features(self, lab_data: pd.DataFrame, unique_test_codes: List[str]) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
        ref_range_ratios: Dict[str, float] = {}
        z_scores_dict: Dict[str, float] = {}
        percentile_ranks_dict: Dict[str, float] = {}

        if lab_data.empty:
            return ref_range_ratios, z_scores_dict, percentile_ranks_dict

        latest_results = lab_data.groupby('test_code').last()

        for test_code in unique_test_codes:
            if test_code not in latest_results.index:
                continue
            row = latest_results.loc[test_code]
            result_numeric = row['result_numeric']
            ref_low = row['result_ref_low'] # This was mapped from LabTestDefinition.normal_range_low
            ref_high = row['result_ref_high'] # This was mapped from LabTestDefinition.normal_range_high


            if pd.notna(ref_low) and pd.notna(ref_high) and (ref_high + ref_low) / 2 != 0:
                mid_point = (ref_low + ref_high) / 2
                ref_range_ratios[test_code] = result_numeric / mid_point
            else:
                ref_range_ratios[test_code] = 0.0

            if test_code in self.reference_populations and self.reference_populations[test_code].get('std', 0) > 0:
                pop_mean = self.reference_populations[test_code]['mean']
                pop_std = self.reference_populations[test_code]['std']
                z_scores_dict[test_code] = (result_numeric - pop_mean) / pop_std
            else:
                z_scores_dict[test_code] = 0.0

            if test_code in self.reference_populations and 'percentiles' in self.reference_populations[test_code]:
                percentile_ranks_dict[test_code] = self._calculate_percentile_from_map(result_numeric, self.reference_populations[test_code]['percentiles'])
            else:
                percentile_ranks_dict[test_code] = 0.5
        return ref_range_ratios, z_scores_dict, percentile_ranks_dict

    def _calculate_percentile_from_map(self, value: float, percentile_map: Dict[int, float]) -> float:
        sorted_percentiles = sorted(percentile_map.items())

        if not sorted_percentiles: return 0.5

        # Find where value fits
        for i, (pct, p_val) in enumerate(sorted_percentiles):
            if value <= p_val:
                if i == 0: return pct / 100.0 # Value is less than or equal to the smallest percentile value
                # Interpolate
                prev_pct, prev_p_val = sorted_percentiles[i-1]
                if p_val == prev_p_val: return pct / 100.0 # Avoid division by zero
                fraction = (value - prev_p_val) / (p_val - prev_p_val)
                return (prev_pct + fraction * (pct - prev_pct)) / 100.0

        return sorted_percentiles[-1][0] / 100.0 # Value is greater than the largest percentile value

    def _extract_clinical_context_features(self, patient_id: int, lab_data: pd.DataFrame, unique_test_codes: List[str]) -> Tuple[Dict[str, bool], Dict[str, float]]:
        med_interaction_flags: Dict[str, bool] = {}
        test_freq_devs: Dict[str, float] = {}

        # Placeholder for patient's current medication list
        # current_meds_simulated = db_session.query(PatientMedication).filter_by(patient_id=patient_id, is_active=True)...
        current_meds_simulated = ['lithium_carbonate', 'olanzapine']

        for test_code in unique_test_codes:
            # LabTestDefinition model does not have 'medication_monitoring' or 'expected_frequency' in the new schema
            # This part would need adjustment if those fields are added or sourced differently
            # For now, defaulting to False/0.0
            med_interaction_flags[test_code] = False
            test_freq_devs[test_code] = 0.0

            # Original logic (commented out due to missing fields in current LabTestDefinition):
            # test_def = self.db_session.query(LabTestDefinition.medication_monitoring, LabTestDefinition.expected_frequency).filter_by(test_code=test_code).first()
            # if test_def:
            #     med_monitoring_str = test_def.medication_monitoring
            #     try:
            #         med_list = pd.read_json(med_monitoring_str, typ='series').tolist() if med_monitoring_str else []
            #     except ValueError:
            #         med_list = []
            #     med_interaction_flags[test_code] = any(med in current_meds_simulated for med in med_list)

            #     test_dates = lab_data[lab_data['test_code'] == test_code]['result_date'].tolist()
            #     if len(test_dates) >= 2 and test_def.expected_frequency:
            #         avg_interval_days = (test_dates[-1] - test_dates[0]).days / (len(test_dates) - 1) if len(test_dates) > 1 else 0

            #         expected_interval_map = {'daily': 1, 'weekly': 7, 'monthly': 30, 'quarterly': 90, 'annually': 365, 'as_needed': 0}
            #         expected_interval_days = expected_interval_map.get(test_def.expected_frequency.lower().split('_to_')[0], 0)

            #         if expected_interval_days > 0 and avg_interval_days > 0 :
            #             test_freq_devs[test_code] = abs(avg_interval_days - expected_interval_days) / expected_interval_days
            #         else:
            #             test_freq_devs[test_code] = 0.0
            #     else:
            #         test_freq_devs[test_code] = 0.0
            # else:
            #     med_interaction_flags[test_code] = False
            #     test_freq_devs[test_code] = 0.0
        return med_interaction_flags, test_freq_devs

    def _extract_risk_features(self, patient_id: int, lab_data: pd.DataFrame, lookback_days: int, unique_test_codes: List[str]) -> Tuple[Dict[str, int], Dict[str, bool]]:
        crit_val_hist_counts: Dict[str, int] = {}
        abnormal_pattern: Dict[str, bool] = {}

        start_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Get result_ids of critical alerts
        # CriticalValueAlert model does not have 'severity' field, use alert_level or similar
        alerted_result_ids_query = self.db_session.query(CriticalValueAlert.lab_result_id).filter(
            CriticalValueAlert.patient_id == patient_id,
            CriticalValueAlert.alert_datetime >= start_date, # Use alert_datetime
            CriticalValueAlert.alert_level.in_(['critical', 'panic']) # Assuming alert_level holds this
        ).distinct().all()
        alerted_result_ids = [item[0] for item in alerted_result_ids_query]

        for test_code in unique_test_codes:
            count = lab_data[
                (lab_data['test_code'] == test_code) &
                (lab_data['result_id'].isin(alerted_result_ids))
            ].shape[0]
            crit_val_hist_counts[test_code] = count

            test_results_for_code = lab_data[lab_data['test_code'] == test_code]
            if not test_results_for_code.empty:
                abnormal_flags = ['high', 'low', 'critical', 'panic', 'abnormal', 'H', 'L', 'A', 'AA'] # Added common flags
                abnormal_count = test_results_for_code[
                    test_results_for_code['interpretation_flag'].astype(str).str.lower().isin(abnormal_flags)
                ].shape[0]
                abnormal_pattern[test_code] = (abnormal_count / len(test_results_for_code)) > 0.5 if len(test_results_for_code) > 0 else False
            else:
                abnormal_pattern[test_code] = False
        return crit_val_hist_counts, abnormal_pattern

    def _construct_feature_vector(self, feature_set: LabFeatureSet, all_test_codes: List[str]) -> Tuple[np.ndarray, List[str]]:
        feature_list = []
        feature_names_list = []

        sorted_test_codes = sorted(list(all_test_codes))

        for test_code in sorted_test_codes:
            prefix = f"{test_code}__"

            feature_list.append(feature_set.current_values.get(test_code, 0.0))
            feature_names_list.append(f"{prefix}current_value")

            current_flag_val = feature_set.current_flags.get(test_code, '').lower()
            feature_list.append(1 if current_flag_val in ['critical', 'panic', 'aa', 'a'] else 0) # Adjusted critical flags
            feature_names_list.append(f"{prefix}is_critical_flag")

            feature_list.append(feature_set.trend_slopes.get(test_code, 0.0))
            feature_names_list.append(f"{prefix}trend_slope")
            feature_list.append(feature_set.trend_r_squared.get(test_code, 0.0))
            feature_names_list.append(f"{prefix}trend_r_squared")
            feature_list.append(feature_set.stability_coefficients.get(test_code, 0.0))
            feature_names_list.append(f"{prefix}stability_coefficient")
            feature_list.append(feature_set.days_since_last_test.get(test_code, -1))
            feature_names_list.append(f"{prefix}days_since_last_test")

            feature_list.append(feature_set.reference_range_ratios.get(test_code, 0.0))
            feature_names_list.append(f"{prefix}reference_range_ratio")
            feature_list.append(feature_set.z_scores.get(test_code, 0.0))
            feature_names_list.append(f"{prefix}z_score")
            feature_list.append(feature_set.percentile_ranks.get(test_code, 0.5))
            feature_names_list.append(f"{prefix}percentile_rank")

            feature_list.append(1 if feature_set.medication_interaction_flags.get(test_code, False) else 0)
            feature_names_list.append(f"{prefix}med_interaction_flag")
            feature_list.append(feature_set.test_frequency_deviations.get(test_code, 0.0))
            feature_names_list.append(f"{prefix}freq_deviation")

            feature_list.append(feature_set.critical_value_history_counts.get(test_code, 0))
            feature_names_list.append(f"{prefix}critical_history_count")
            feature_list.append(1 if feature_set.abnormal_pattern_flags.get(test_code, False) else 0)
            feature_names_list.append(f"{prefix}abnormal_pattern_flag")

        if not feature_list:
            return np.array([]), []

        feature_vector = np.array(feature_list).astype(float)

        if feature_vector.size > 0:
            global_scaler = StandardScaler() # Consider fitting this scaler on a representative dataset, not just current vector
            feature_vector_scaled = global_scaler.fit_transform(feature_vector.reshape(-1, 1)).flatten()
            return feature_vector_scaled, feature_names_list

        return feature_vector, feature_names_list


    def _empty_feature_set(self, patient_id: int, lookback_days: int) -> LabFeatureSet:
        return LabFeatureSet(
            patient_id=patient_id,
            feature_extraction_date=datetime.utcnow(),
            lookback_days=lookback_days
        )

    def extract_patient_lab_features(self, patient_id: int, lookback_days: int = 365) -> LabFeatureSet:
        lab_data_df = self._get_patient_lab_data(patient_id, lookback_days)

        if lab_data_df.empty:
            return self._empty_feature_set(patient_id, lookback_days)

        unique_test_codes = sorted(list(lab_data_df['test_code'].unique()))

        current_vals, current_flgs = self._extract_current_values(lab_data_df)
        trend_slps, trend_r_sq, stability_coeffs, days_last = \
            self._extract_temporal_features(patient_id, lookback_days, lab_data_df, unique_test_codes)
        ref_ratios, z_scrs, percentiles = \
            self._extract_comparative_features(lab_data_df, unique_test_codes)
        med_flags, freq_devs = \
            self._extract_clinical_context_features(patient_id, lab_data_df, unique_test_codes)
        crit_counts, abnormal_flags = \
            self._extract_risk_features(patient_id, lab_data_df, lookback_days, unique_test_codes)

        feature_set = LabFeatureSet(
            patient_id=patient_id,
            feature_extraction_date=datetime.utcnow(),
            lookback_days=lookback_days,
            current_values=current_vals,
            current_flags=current_flgs,
            trend_slopes=trend_slps,
            trend_r_squared=trend_r_sq,
            stability_coefficients=stability_coeffs,
            days_since_last_test=days_last,
            reference_range_ratios=ref_ratios,
            z_scores=z_scrs,
            percentile_ranks=percentiles,
            medication_interaction_flags=med_flags,
            test_frequency_deviations=freq_devs,
            critical_value_history_counts=crit_counts,
            abnormal_pattern_flags=abnormal_flags
        )

        all_test_codes_for_vector = list(lab_data_df['test_code'].unique())
        if all_test_codes_for_vector:
             vec, names = self._construct_feature_vector(feature_set, all_test_codes_for_vector)
             feature_set.feature_vector = vec
             feature_set.feature_names = names
        else:
            feature_set.feature_vector = np.array([])
            feature_set.feature_names = []


        return feature_set

class LabAnalyticsEngine:
    def __init__(self, db_session):
        self.db_session = db_session
        self.feature_engineer = LabFeatureEngineer(db_session)

    def calculate_trend_for_test(self, patient_id: int, test_definition_id: int, days_back: int) -> Dict:
        start_date = datetime.utcnow() - timedelta(days=days_back)

        results_query = self.db_session.query(LabResult.result_numeric, LabResult.result_date).filter(
            LabResult.patient_id == patient_id,
            LabResult.test_definition_id == test_definition_id,
            LabResult.result_numeric.isnot(None),
            LabResult.result_date >= start_date
        ).order_by(LabResult.result_date).all()

        if len(results_query) < 3: # Require at least 3 points for a meaningful trend
            return {'status': 'insufficient_data', 'message': 'Not enough data points for trend analysis.'}

        df = pd.DataFrame(results_query, columns=['result_numeric', 'result_date'])
        df['days_since_start'] = (df['result_date'] - df['result_date'].min()).dt.days

        slope, intercept, r_value, p_value, std_err = stats.linregress(df['days_since_start'], df['result_numeric'])

        trend_direction = 'stable'
        if pd.notna(slope) and slope > 0.01: trend_direction = 'increasing' # Define thresholds for increasing/decreasing
        elif pd.notna(slope) and slope < -0.01: trend_direction = 'decreasing'

        mean_val = df['result_numeric'].mean()
        std_val = df['result_numeric'].std()
        coefficient_of_variation = (std_val / mean_val) if mean_val != 0 and pd.notna(mean_val) and pd.notna(std_val) else 0.0

        # LabTrendAnalysis model has analysis_uuid, patient_id, test_definition_id, analysis_type, start_date, end_date, trend_data, summary_finding, generated_datetime
        existing_trend = self.db_session.query(LabTrendAnalysis).filter(
            LabTrendAnalysis.patient_id == patient_id,
            LabTrendAnalysis.test_definition_id == test_definition_id,
            # LabTrendAnalysis.time_window_days == days_back # This field is not in the model
            LabTrendAnalysis.start_date == start_date.date(),
            LabTrendAnalysis.end_date == datetime.utcnow().date()
        ).first()

        if not existing_trend:
            existing_trend = LabTrendAnalysis(
                patient_id=patient_id,
                test_definition_id=test_definition_id,
                analysis_type='automated_trend_v1', # Example analysis type
                start_date=start_date.date(),
                end_date=datetime.utcnow().date(),
                # time_window_days=days_back # Not in model
            )
            self.db_session.add(existing_trend)

        trend_data_dict = {
            'trend_direction': trend_direction,
            'slope': slope if pd.notna(slope) else 0.0,
            'r_squared': r_value**2 if pd.notna(r_value) else 0.0,
            'p_value': p_value if pd.notna(p_value) else None,
            'min_value': df['result_numeric'].min(),
            'max_value': df['result_numeric'].max(),
            'mean_value': mean_val if pd.notna(mean_val) else 0.0,
            'median_value': df['result_numeric'].median() if pd.notna(df['result_numeric'].median()) else 0.0,
            'std_deviation': std_val if pd.notna(std_val) else 0.0,
            'coefficient_of_variation': coefficient_of_variation,
            'data_points_count': len(results_query),
            'last_data_point_date': df['result_date'].max().isoformat() if pd.notna(df['result_date'].max()) else None,
        }
        existing_trend.trend_data = trend_data_dict # Store all trend info in JSON field
        existing_trend.summary_finding = f"Trend: {trend_direction}, Slope: {trend_data_dict['slope']:.2f}, R^2: {trend_data_dict['r_squared']:.2f}"
        existing_trend.generated_datetime = datetime.utcnow()

        self.db_session.commit()

        return {
            'status': 'success',
            **trend_data_dict, # Unpack the trend data into the response
            'trend_period_start': start_date.isoformat(),
            'trend_period_end': datetime.utcnow().isoformat()
        }

    def generate_patient_lab_summary(self, patient_id: int, days_back: int = 365) -> Dict:
        feature_set = self.feature_engineer.extract_patient_lab_features(patient_id, days_back)

        if feature_set.feature_vector is None or not feature_set.feature_vector.size:
             return {'message': f'No features extracted for patient {patient_id}.'}


        analytics_summary = {
            'overview': {
                'total_tests_analyzed': len(feature_set.current_values),
                'most_recent_data_extraction': feature_set.feature_extraction_date.isoformat(),
                'analysis_lookback_days': feature_set.lookback_days
            },
            'current_status': {}, 'temporal_insights': {}, 'comparative_insights': {},
            'clinical_context_insights': {}, 'risk_indicators': {},
            'ml_model_input': {
                'feature_vector': feature_set.feature_vector.tolist() if feature_set.feature_vector is not None else [],
                'feature_names': feature_set.feature_names if feature_set.feature_names is not None else []
            },
            'predicted_outcomes': {}
        }

        unique_test_codes_in_features = set()
        if feature_set.current_values: unique_test_codes_in_features.update(feature_set.current_values.keys())
        if feature_set.trend_slopes: unique_test_codes_in_features.update(feature_set.trend_slopes.keys())
        # ... (update with keys from all other feature dicts in feature_set for completeness)


        for test_code in sorted(list(unique_test_codes_in_features)):
            analytics_summary['current_status'][test_code] = {
                'latest_value': feature_set.current_values.get(test_code),
                'latest_flag': feature_set.current_flags.get(test_code),
                'days_since_last': feature_set.days_since_last_test.get(test_code)
            }
            analytics_summary['temporal_insights'][test_code] = {
                'slope': feature_set.trend_slopes.get(test_code),
                'r_squared': feature_set.trend_r_squared.get(test_code),
                'stability_coeff': feature_set.stability_coefficients.get(test_code)
            }
            # ... (populate other sections similarly, checking for key existence)

        # from ..ml_models.prediction_model import PsychiatricOutcomePredictor # Placeholder
        # predictor = PsychiatricOutcomePredictor.load_model('path/to/model.pkl') # Placeholder
        # predictions = predictor.predict(feature_set.feature_vector) # Placeholder
        analytics_summary['predicted_outcomes'] = self._simulate_ml_predictions(feature_set)
        return analytics_summary

    def _simulate_ml_predictions(self, feature_set: LabFeatureSet) -> Dict:
        simulated_predictions = {}
        hba1c_z = feature_set.z_scores.get('HBA1C', 0.0) if feature_set.z_scores else 0.0

        # Assuming 'TRIGLYCERIDES' is a test_code that might appear in reference_range_ratios
        trig_ratio = feature_set.reference_range_ratios.get('TRIGLYCERIDES', 0.0) if feature_set.reference_range_ratios else 0.0


        metabolic_risk_score = (hba1c_z * 0.4) + (trig_ratio * 0.3)
        simulated_predictions['metabolic_syndrome_risk'] = max(0.0, min(1.0, (metabolic_risk_score + 1.0) / 2.0))
        simulated_predictions['metabolic_syndrome_alert'] = simulated_predictions['metabolic_syndrome_risk'] > 0.65

        lithium_level = feature_set.current_values.get('LITH_LEVEL', 0.0) if feature_set.current_values else 0.0
        lithium_slope = feature_set.trend_slopes.get('LITH_LEVEL', 0.0) if feature_set.trend_slopes else 0.0
        lithium_critical_count = feature_set.critical_value_history_counts.get('LITH_LEVEL', 0) if feature_set.critical_value_history_counts else 0


        lithium_toxicity_risk = 0.0
        if lithium_level > 1.2: lithium_toxicity_risk += 0.4
        if lithium_slope > 0.1: lithium_toxicity_risk += 0.3
        if lithium_critical_count > 0: lithium_toxicity_risk += 0.2
        simulated_predictions['lithium_toxicity_risk'] = max(0.0, min(1.0, lithium_toxicity_risk))
        simulated_predictions['lithium_toxicity_alert'] = simulated_predictions['lithium_toxicity_risk'] > 0.5
        return simulated_predictions
