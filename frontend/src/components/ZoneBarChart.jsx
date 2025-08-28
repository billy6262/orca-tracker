import React, { useState, useEffect } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const ZoneBarChart = () => {
  // Set default date range to last 30 days
  const getDefaultDates = () => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    return { startDate, endDate };
  };

  const [startDate, setStartDate] = useState(getDefaultDates().startDate);
  const [endDate, setEndDate] = useState(getDefaultDates().endDate);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const formatDate = (date) => {
    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
  };

  const fetchSightingData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000';
      const response = await fetch(
        `${apiUrl}/api/sightings/zones/${formatDate(startDate)}/${formatDate(endDate)}/`
      );
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching sighting data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data when component mounts or date range changes
  useEffect(() => {
    fetchSightingData();
  }, [startDate, endDate]);

  const handleDateChange = () => {
    // This will trigger the useEffect above
  };

  return (
    <div className="container mt-4">
      <div className="card">
        <div className="card-header">
          <h3 className="card-title mb-0">Orca Sightings by Zone</h3>
        </div>
        <div className="card-body">
          {/* Date Range Picker */}
          <div className="row mb-4">
            <div className="col-md-6">
              <label className="form-label">Start Date</label>
              <div>
                <DatePicker
                  selected={startDate}
                  onChange={(date) => setStartDate(date)}
                  selectsStart
                  startDate={startDate}
                  endDate={endDate}
                  maxDate={endDate}
                  className="form-control"
                  dateFormat="yyyy-MM-dd"
                />
              </div>
            </div>
            <div className="col-md-6">
              <label className="form-label">End Date</label>
              <div>
                <DatePicker
                  selected={endDate}
                  onChange={(date) => setEndDate(date)}
                  selectsEnd
                  startDate={startDate}
                  endDate={endDate}
                  minDate={startDate}
                  maxDate={new Date()}
                  className="form-control"
                  dateFormat="yyyy-MM-dd"
                />
              </div>
            </div>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="text-center my-4">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="alert alert-danger" role="alert">
              Error loading data: {error}
            </div>
          )}

          {/* Chart */}
          {!loading && !error && (
            <>
              {data.length === 0 ? (
                <div className="alert alert-info" role="alert">
                  No sightings found for the selected date range.
                </div>
              ) : (
                <div style={{ width: '100%', height: '400px' }}>
                  <ResponsiveContainer>
                    <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="zone" 
                        label={{ value: 'Zone Number', position: 'insideBottom', offset: -5 }}
                      />
                      <YAxis 
                        label={{ value: 'Number of Sightings', angle: -90, position: 'outsideRight' ,dx: -25}}
                      />
                      <Tooltip 
                        formatter={(value) => [value, 'Sightings']}
                        labelFormatter={(label) => `Zone ${label}`}
                      />
                      <Legend />
                      <Bar 
                        dataKey="count" 
                        fill="#0d6efd" 
                        name="Sightings"
                        radius={[4, 4, 0, 0]}
                        
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}

          {/* Summary */}
          {!loading && !error && data.length > 0 && (
            <div className="mt-3">
              <small className="text-muted">
                Showing {data.reduce((sum, item) => sum + item.count, 0)} total sightings 
                across {data.length} zones from {formatDate(startDate)} to {formatDate(endDate)}
              </small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ZoneBarChart;

