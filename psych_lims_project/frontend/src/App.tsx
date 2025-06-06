import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import apiClient from './services/api';
import './index.css'; // Ensure Tailwind styles are imported

function HomePage() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    apiClient.get('/health')
      .then(response => {
        if (response.data && response.data.status === 'ok') {
          setHealthStatus('Backend is healthy!');
          console.log('Backend health status: ok');
        } else {
          setHealthStatus('Backend status unknown.');
          console.log('Backend health status: unknown or error', response.data);
        }
      })
      .catch(error => {
        setHealthStatus('Failed to connect to backend.');
        console.error('Error fetching health status:', error);
      });
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Psych LIMS Frontend</h1>
      <p>Backend Health Status: <span className="font-semibold">{healthStatus}</span></p>
      <nav className="mt-4">
        <Link to="/" className="mr-4 text-blue-500 hover:text-blue-700">Home</Link>
        {/* Add other navigation links here as pages are created */}
      </nav>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        {/* Define other routes here */}
      </Routes>
    </Router>
  );
}

export default App;
