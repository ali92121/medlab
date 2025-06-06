import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom'; // Assuming react-router-dom is used
import PatientRegistrationForm from '../../components/forms/PatientRegistrationForm';
import { patientService, PatientCreationPayload } from '../../services/patientService';

const PatientRegistrationPage: React.FC = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: PatientCreationPayload) => {
    setIsLoading(true);
    setError(null);
    try {
      const newPatient = await patientService.createPatient(data);
      console.log('Patient registered successfully:', newPatient);
      // Navigate to the new patient's detail page or patient list
      navigate(`/patients/${newPatient.id}`); // Or navigate('/patients');
    } catch (err) {
      console.error('Failed to register patient:', err);
      setError((err as Error).message || 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: '0 auto' }}>
      <h1>Register New Patient</h1>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      <PatientRegistrationForm onSubmit={handleSubmit} isLoading={isLoading} />
    </div>
  );
};

export default PatientRegistrationPage;
