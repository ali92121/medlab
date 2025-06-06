// Base URL for the API. Adjust if your backend runs on a different port/host.
const API_BASE_URL = '/api'; // Assuming proxy is set up in package.json or vite.config.js

// Placeholder for fetching JWT token.
// In a real app, this would come from an auth context, localStorage, etc.
const getAuthToken = (): string | null => {
  // Example: return localStorage.getItem('jwtToken');
  // For now, returning a dummy token if needed for tests, or null
  // This function's actual implementation is outside the scope of this specific task.
  // For @jwt_required() to pass, a valid token is needed.
  // During development, you might use a manually obtained token.
  console.warn("getAuthToken() is a placeholder. Implement actual token retrieval.");
  return "dummy-jwt-token-for-dev"; // Replace with actual token retrieval logic
};

// Define types for Patient data (can be expanded and moved to a types.ts file)
// This should ideally match the structure from Patient.to_dict() in Python
interface PatientAddress {
  address_line1?: string;
  city?: string;
  state_province?: string;
  postal_code?: string;
  country?: string;
}

interface PatientEmergencyContact {
  name?: string;
  phone?: string;
  relationship?: string;
}

export interface Patient {
  id: number;
  psychiatry_id?: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string; // YYYY-MM-DD
  gender?: string;
  phone_number?: string;
  email?: string;
  address?: PatientAddress;
  emergency_contact?: PatientEmergencyContact;
  primary_care_physician?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

// For POST/PUT, we might not have id, created_at, updated_at, is_active
export type PatientCreationPayload = Omit<Patient, 'id' | 'created_at' | 'updated_at' | 'is_active'> & {
  // psychiatry_id is optional on creation if backend auto-generates or it's not always provided
  psychiatry_id?: string;
};
export type PatientUpdatePayload = Partial<PatientCreationPayload>;


interface PaginatedPatientsResponse {
  patients: Patient[];
  total_pages: number;
  current_page: number;
  total_patients: number;
}

// Helper function for API requests
const request = async <T>(url: string, options: RequestInit = {}): Promise<T> => {
  const token = getAuthToken();
  const headers = {
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

// Service functions
export const patientService = {
  createPatient: async (patientData: PatientCreationPayload): Promise<Patient> => {
    return request<Patient>(`${API_BASE_URL}/patients`, {
      method: 'POST',
      body: JSON.stringify(patientData),
    });
  },

  getPatients: async (page = 1, perPage = 10, searchTerm = ''): Promise<PaginatedPatientsResponse> => {
    const queryParams = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });
    if (searchTerm) {
      queryParams.append('search', searchTerm);
    }
    return request<PaginatedPatientsResponse>(`${API_BASE_URL}/patients?${queryParams.toString()}`);
  },

  getPatientById: async (patientId: number): Promise<Patient> => {
    return request<Patient>(`${API_BASE_URL}/patients/${patientId}`);
  },

  updatePatient: async (patientId: number, patientData: PatientUpdatePayload): Promise<Patient> => {
    return request<Patient>(`${API_BASE_URL}/patients/${patientId}`, {
      method: 'PUT',
      body: JSON.stringify(patientData),
    });
  },

  deletePatient: async (patientId: number): Promise<{ message: string }> => {
    return request<{ message: string }>(`${API_BASE_URL}/patients/${patientId}`, {
      method: 'DELETE',
    });
  },

  reactivatePatient: async (patientId: number): Promise<Patient> => {
    return request<Patient>(`${API_BASE_URL}/patients/${patientId}/reactivate`, {
        method: 'PUT',
    });
  },
};

console.log('patientService.ts loaded with API functions');
