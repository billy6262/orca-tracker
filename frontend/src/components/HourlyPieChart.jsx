import React, { useState, useEffect } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";
import { useDateRange } from "./Constants";

// Color palette for the pie chart slices
const COLORS = [
  "#0088FE","#00C49F","#FFBB28","#FF8042",
  "#A28BFF","#FF6699","#33C1FF","#FFAA33",
  "#66CC66","#CC6666","#9966CC","#6699CC",
  "#FF9966","#66FFB3","#B366FF","#FF6666",
  "#66B2FF","#FF66B2","#B2FF66","#FFB266",
  "#66FF66","#FF6666","#6666FF","#CCCC66"
];



const HourlyPieChart = () => {
    // Use global dates from context
    const { startDate, endDate, formatDate } = useDateRange();
    // local variables
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
            `${apiUrl}/api/sightings/byhour/${formatDate(startDate)}/${formatDate(endDate)}/`
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

    // Calculate total sightings
    const totalSightings = data.reduce((sum, entry) => sum + entry.count, 0);

  return (
    <div className="container mt-4">
      <div className="card">
        <div className="card-header">
          <h3 className="card-title mb-0">Orca Sightings by Hour</h3>
        </div>
        <div className="card-body">
          {loading && (
            <div className="text-center my-4">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            </div>
          )}
          {error && (
            <div className="alert alert-danger" role="alert">
              Error loading data: {error}
            </div>
          )}
          {!loading && !error && (
            <>
              {data.length === 0 || totalSightings === 0 ? (
                <div className="alert alert-info" role="alert">
                  No sightings found for the selected date range.
                </div>
              ) : (
                <div style={{ width: "100%", height: "400px" }}>
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie
                        data={data}
                        dataKey="count"
                        nameKey="hour"
                        cx="50%"
                        cy="50%"
                        outerRadius={140}
                        innerRadius={60}
                        paddingAngle={1}
                        label={({ hour, percent }) =>
                          `${hour}:00 (${(percent * 100).toFixed(1)}%)`
                        }
                      >
                        {data.map((entry, index) => (
                          <Cell
                            key={`cell-${entry.hour}`}
                            fill={COLORS[index % COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value, _name, props) => {
                          const pct = totalSightings
                            ? ((value / totalSightings) * 100).toFixed(1)
                            : '0.0';
                          return [`${value} (${pct}%)`, `Hour ${props.payload.hour}:00`];
                        }}
                      />
                      <Legend
                        layout="horizontal"
                        verticalAlign="bottom"
                        align="center"
                        wrapperStyle={{ marginTop: 12 }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}
          {!loading && !error && totalSightings > 0 && (
            <div className="mt-3">
              <small className="text-muted">
                Showing {totalSightings} total sightings across{" "}
                {data.length} hour{data.length !== 1 && "s"} from{" "}
                {formatDate(startDate)} to {formatDate(endDate)}
              </small>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HourlyPieChart;