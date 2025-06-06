import React, { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom'; // Assuming react-router-dom
import { patientService, Patient } from '../../services/patientService';

const PatientsListPage: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [searchParams, setSearchParams] = useSearchParams();
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const currentSearch = searchParams.get('search') || '';

  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState(currentSearch); // For controlled input

  const fetchPatients = useCallback(async (page: number, search: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await patientService.getPatients(page, 10, search); // 10 items per page
      setPatients(data.patients);
      setTotalPages(data.total_pages);
      // Update URL without navigation if params changed by code, not user input
      if (page !== currentPage || search !== currentSearch) {
        setSearchParams({ page: page.toString(), search });
      }
    } catch (err) {
      console.error('Failed to fetch patients:', err);
      setError((err as Error).message || 'An unknown error occurred.');
      setPatients([]); // Clear patients on error
    } finally {
      setIsLoading(false);
    }
  }, [setSearchParams, currentPage, currentSearch]); // Add dependencies

  useEffect(() => {
    fetchPatients(currentPage, currentSearch);
  }, [fetchPatients, currentPage, currentSearch]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSearchParams({ page: '1', search: searchTerm }); // Go to first page on new search
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setSearchParams({ page: newPage.toString(), search: currentSearch });
    }
  };

  // Basic styling (can be moved to CSS files)
  const tableStyle: React.CSSProperties = { width: '100%', borderCollapse: 'collapse', marginTop: '20px' };
  const thStyle: React.CSSProperties = { border: '1px solid #ddd', padding: '8px', backgroundColor: '#f2f2f2', textAlign: 'left' };
  const tdStyle: React.CSSProperties = { border: '1px solid #ddd', padding: '8px' };
  const searchBarStyle: React.CSSProperties = { marginBottom: '20px', display: 'flex', gap: '10px' };
  const paginationStyle: React.CSSProperties = { marginTop: '20px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px' };

  if (isLoading) return <p>Loading patients...</p>;
  if (error) return <p style={{ color: 'red' }}>Error fetching patients: {error}</p>;

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1>Patients List</h1>

      <form onSubmit={handleSearchSubmit} style={searchBarStyle}>
        <input
          type="text"
          placeholder="Search by name or ID..."
          value={searchTerm}
          onChange={handleSearchChange}
          style={{ padding: '8px', flexGrow: 1 }}
        />
        <button type="submit" style={{ padding: '8px 15px'}}>Search</button>
      </form>

      {patients.length === 0 && !isLoading && <p>No patients found.</p>}

      {patients.length > 0 && (
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>Psychiatry ID</th>
              <th style={thStyle}>Date of Birth</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((patient) => (
              <tr key={patient.id}>
                <td style={tdStyle}>{patient.first_name} {patient.last_name}</td>
                <td style={tdStyle}>{patient.psychiatry_id || 'N/A'}</td>
                <td style={tdStyle}>{patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A'}</td>
                <td style={tdStyle}>
                  <Link to={`/patients/${patient.id}`}>View Details</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {totalPages > 1 && (
        <div style={paginationStyle}>
          <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage <= 1}>
            Previous
          </button>
          <span>Page {currentPage} of {totalPages}</span>
          <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage >= totalPages}>
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default PatientsListPage;
