import React, { useState, useEffect } from "react";
import { useDateRange } from "../components/Constants.jsx";
import ChartsDateBar from "../components/ChartsDateBar.jsx";

const ReportsPage = () => {
  const { startDate, endDate, formatDate } = useDateRange();
  
  // State for managing sightings data
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSightingData = async () => {
    if (!startDate || !endDate) return;
    setLoading(true);
    setError(null);
    try {
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/sightings/${formatDate(startDate)}/${formatDate(endDate)}/`
      );
      if (!response.ok) throw new Error(`API request failed: ${response.status}`);
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
      console.error("Error fetching sighting data:", err);
    } finally {
      setLoading(false);
    }
  };

  // Refetch when global dates change
  useEffect(() => {
    fetchSightingData();
  }, [startDate, endDate]);

  // Sort sightings by newest first and format the datetime
  const sortedSightings = React.useMemo(() => {
    return [...data].sort((a, b) => new Date(b.time) - new Date(a.time));
  }, [data]);

  // Helper function to format the datetime for display
  const formatDateTime = (dateTimeString) => {
    try {
      const date = new Date(dateTimeString);
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
    } catch (e) {
      return 'Invalid Date';
    }
  };

  // Individual sighting card component
  const SightingCard = ({ sighting }) => (
    <div style={{
      backgroundColor: '#fff',
      border: '1px solid #e0e0e0',
      borderRadius: '8px',
      padding: '12px 16px',
      marginBottom: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      transition: 'box-shadow 0.2s ease'
    }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', color: '#333', marginBottom: '4px' }}>
            Zone {sighting.zone || sighting.ZoneNumber}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
            {formatDateTime(sighting.time)}
          </div>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center',  // Center the items horizontally
            gap: '16px', 
            fontSize: '11px', 
            color: '#888' 
          }}>
            <span><strong>Count:</strong> {sighting.count || 'N/A'}</span>
            <span><strong>Direction:</strong> {sighting.direction || 'Unknown'}</span>
            {sighting.timeSinceLastSighting && (
              <span><strong>Since Last:</strong> {sighting.timeSinceLastSighting}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        
      {/* Date bar with consistent container width */}
      <div style={{ maxWidth: '800px', margin: '0 auto', width: '101%' }}>
        <ChartsDateBar />
      </div>
      
      {/* Header with stats - same container width */}
      <div style={{ 
        padding: '16px', 
        borderBottom: '1px solid #e0e0e0',
        backgroundColor: '#f8f9fa'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ margin: 0, color: '#333' }}>Orca Sightings</h2>
            <div style={{ fontSize: '14px', color: '#666' }}>
              {loading ? 'Loading...' : `${sortedSightings.length} sightings found`}
            </div>
          </div>
          
          {/* Date range display */}
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#888' }}>
            Showing sightings from {formatDate(startDate)} to {formatDate(endDate)}
          </div>
        </div>
      </div>

      {/* Error state - same container width */}
      {error && (
        <div style={{ padding: '0 16px' }}>
          <div style={{
            maxWidth: '800px',
            margin: '16px auto',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            padding: '12px',
            borderRadius: '4px',
            border: '1px solid #f5c6cb'
          }}>
            Error: {error}
          </div>
        </div>
      )}

      {/* Scrollable sightings list - same container width */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        backgroundColor: '#f8f9fa'
      }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <div>Loading sightings...</div>
          </div>
        ) : sortedSightings.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <div>No sightings found for the selected date range.</div>
            <div style={{ fontSize: '12px', marginTop: '8px' }}>
              Try adjusting your date range or check back later.
            </div>
          </div>
        ) : (
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            {sortedSightings.map((sighting) => (
              <SightingCard key={sighting.id} sighting={sighting} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportsPage;


