// Base URL for the API (consistent with patientService)
const API_BASE_URL = '/api'; // Assuming proxy for /api

// Placeholder for fetching JWT token (consistent with patientService)
const getAuthToken = (): string | null => {
  console.warn("getAuthToken() is a placeholder in assessmentService.ts. Implement actual token retrieval.");
  return "dummy-jwt-token-for-dev"; // Replace with actual token retrieval logic
};

// --- Types for Assessment Data ---

// Symptom Assessment Types
export interface SymptomAssessmentPayload {
  assessment_date?: string; // ISO format e.g., YYYY-MM-DDTHH:mm:ss.sssZ. Optional, defaults to now on backend.
  assessor_type?: string; // 'clinician', 'self_report'
  assessment_context_group?: string; // e.g., "Depressive Symptoms"
  dsm5tr_criterion_code?: string;
  icd11_symptom_code?: string;
  symptom_description: string; // Required
  severity_score?: number;
  frequency?: string;
  duration?: string;
  notes?: string;
}

export interface SymptomAssessment extends SymptomAssessmentPayload {
  id: number;
  patient_id: number;
  created_at: string; // ISO string
  assessment_date: string; // ISO string (guaranteed from backend)
}

// Standardized Scale Assessment Types
export interface StandardizedScaleAssessmentPayload {
  assessment_date?: string; // ISO format. Optional, defaults to now on backend.
  scale_name: string; // Required, e.g., 'PHQ-9'
  total_score?: number;
  item_responses?: Record<string, any>; // JSON object for item scores/responses
  overall_comment?: string;
}

export interface StandardizedScaleAssessment extends StandardizedScaleAssessmentPayload {
  id: number;
  patient_id: number;
  created_at: string; // ISO string
  assessment_date: string; // ISO string (guaranteed from backend)
}

// Helper function for API requests (can be refactored into a shared utility)
const request = async <T>(url: string, options: RequestInit = {}): Promise<T> => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ message: 'An unknown error occurred' }));
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// --- Assessment Service Functions ---
export const assessmentService = {
  // Symptom Assessment Endpoints
  createSymptomAssessment: async (patientId: number, data: SymptomAssessmentPayload): Promise<SymptomAssessment> => {
    return request<SymptomAssessment>(`${API_BASE_URL}/patients/${patientId}/symptom-assessments`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getSymptomAssessmentsForPatient: async (patientId: number): Promise<SymptomAssessment[]> => {
    return request<SymptomAssessment[]>(`${API_BASE_URL}/patients/${patientId}/symptom-assessments`);
  },

  // Standardized Scale Assessment Endpoints
  createStandardizedScaleAssessment: async (patientId: number, data: StandardizedScaleAssessmentPayload): Promise<StandardizedScaleAssessment> => {
    return request<StandardizedScaleAssessment>(`${API_BASE_URL}/patients/${patientId}/standardized-scale-assessments`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getStandardizedScaleAssessmentsForPatient: async (patientId: number): Promise<StandardizedScaleAssessment[]> => {
    return request<StandardizedScaleAssessment[]>(`${API_BASE_URL}/patients/${patientId}/standardized-scale-assessments`);
  },
};

console.log('assessmentService.ts loaded with API functions');
