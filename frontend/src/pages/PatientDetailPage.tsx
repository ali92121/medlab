import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom'; // Assuming react-router-dom
import { patientService, Patient } from '../../services/patientService';

const PatientDetailPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (patientId) {
      setIsLoading(true);
      setError(null);
      patientService.getPatientById(Number(patientId))
        .then(data => {
          setPatient(data);
        })
        .catch(err => {
          console.error('Failed to fetch patient details:', err);
          setError((err as Error).message || 'An unknown error occurred.');
        })
        .finally(() => setIsLoading(false));
    }
  }, [patientId]);

  const handleDelete = async () => {
    if (patient && window.confirm(`Are you sure you want to mark patient ${patient.first_name} ${patient.last_name} as inactive?`)) {
      setIsLoading(true);
      try {
        await patientService.deletePatient(patient.id);
        alert('Patient marked as inactive.');
        // Optionally, update local state or refetch if showing active status directly
        // For now, navigate away or to a list that reflects the change.
        navigate('/patients');
      } catch (err) {
        console.error('Failed to delete patient:', err);
        setError((err as Error).message || 'Failed to delete patient.');
        setIsLoading(false);
      }
    }
  };

  const handleReactivate = async () => {
    if (patient && !patient.is_active && window.confirm(`Are you sure you want to reactivate patient ${patient.first_name} ${patient.last_name}?`)) {
        setIsLoading(true);
        try {
            const updatedPatient = await patientService.reactivatePatient(patient.id);
            setPatient(updatedPatient); // Update state with reactivated patient
            alert('Patient reactivated.');
        } catch (err) {
            console.error('Failed to reactivate patient:', err);
            setError((err as Error).message || 'Failed to reactivate patient.');
        } finally {
            setIsLoading(false);
        }
    }
  };


  // Basic styling
  const detailSectionStyle: React.CSSProperties = { marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid #eee'};
  const labelStyle: React.CSSProperties = { fontWeight: 'bold' };
  const actionButtonsStyle: React.CSSProperties = { marginTop: '20px', display: 'flex', gap: '10px' };


  if (isLoading) return <p>Loading patient details...</p>;
  if (error) return <p style={{ color: 'red' }}>Error: {error}</p>;
  if (!patient) return <p>Patient not found.</p>;

  return (
    <div style={{ padding: '20px', maxWidth: '900px', margin: '0 auto' }}>
      <h1>Patient Details: {patient.first_name} {patient.last_name}</h1>
      <p>Status: {patient.is_active ? <span style={{color: 'green'}}>Active</span> : <span style={{color: 'red'}}>Inactive</span>}</p>

      <div style={detailSectionStyle}>
        <p><span style={labelStyle}>Psychiatry ID:</span> {patient.psychiatry_id || 'N/A'}</p>
        <p><span style={labelStyle}>Date of Birth:</span> {patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A'}</p>
        <p><span style={labelStyle}>Gender:</span> {patient.gender || 'N/A'}</p>
      </div>

      <div style={detailSectionStyle}>
        <h3>Contact Information</h3>
        <p><span style={labelStyle}>Phone:</span> {patient.phone_number || 'N/A'}</p>
        <p><span style={labelStyle}>Email:</span> {patient.email || 'N/A'}</p>
        {patient.address && (
          <>
            <p><span style={labelStyle}>Address:</span> {patient.address.address_line1 || ''}</p>
            <p><span style={labelStyle}>City:</span> {patient.address.city || ''}</p>
            <p><span style={labelStyle}>State/Province:</span> {patient.address.state_province || ''}</p>
            <p><span style={labelStyle}>Postal Code:</span> {patient.address.postal_code || ''}</p>
            <p><span style={labelStyle}>Country:</span> {patient.address.country || ''}</p>
          </>
        )}
      </div>

      <div style={detailSectionStyle}>
        <h3>Emergency Contact</h3>
        {patient.emergency_contact && (
          <>
            <p><span style={labelStyle}>Name:</span> {patient.emergency_contact.name || 'N/A'}</p>
            <p><span style={labelStyle}>Phone:</span> {patient.emergency_contact.phone || 'N/A'}</p>
            <p><span style={labelStyle}>Relationship:</span> {patient.emergency_contact.relationship || 'N/A'}</p>
          </>
        )}
      </div>

      <div style={detailSectionStyle}>
        <h3>Clinical Information</h3>
        <p><span style={labelStyle}>Primary Care Physician:</span> {patient.primary_care_physician || 'N/A'}</p>
      </div>

      <div style={actionButtonsStyle}>
        {/* Link to an Edit page (not yet created but path is illustrative) */}
        {/* <Link to={`/patients/${patient.id}/edit`} style={{ textDecoration: 'none', padding: '10px 15px', backgroundColor: '#007bff', color: 'white', borderRadius: '4px' }}>Edit Patient</Link> */}

        {patient.is_active && (
          <button onClick={handleDelete} disabled={isLoading} style={{padding: '10px 15px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>
            {isLoading ? 'Processing...' : 'Mark as Inactive'}
          </button>
        )}
        {!patient.is_active && (
          <button onClick={handleReactivate} disabled={isLoading} style={{padding: '10px 15px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}>
            {isLoading ? 'Processing...' : 'Reactivate Patient'}
          </button>
        )}
      </div>

      {/* Placeholder for future sections (Assessments, Medications) */}
      <div style={{marginTop: '30px'}}>
        <h2>Assessments</h2>
        {/* SymptomAssessmentGroupForm and StandardizedScaleForm will be integrated here or in a tab */}
        <p>Assessment forms and history will be displayed here.</p>
      </div>
      <div style={{marginTop: '30px'}}>
        <h2>Medications</h2>
        {/* MedicationForm and MedicationHistoryList will be integrated here or in a tab */}
        <p>Medication forms and history will be displayed here.</p>
      </div>

    </div>
  );
};

export default PatientDetailPage;
