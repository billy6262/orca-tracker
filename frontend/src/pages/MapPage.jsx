import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import zoneData from '../assets/zone.json';
import { useTimeBucket } from '../components/Constants';

function FixSize() {
  const map = useMap();
  useEffect(() => {
    const t1 = setTimeout(() => map.invalidateSize(), 0);
    const t2 = setTimeout(() => map.invalidateSize(), 250);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [map]);
  return null;
}

function MapPage() {
  const { timeBucket } = useTimeBucket();

  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const bucketLabel = useMemo(() => { //updates bucketlabel on change of timeBucket
    const start = timeBucket * 6;
    const end = (timeBucket + 1) * 6;
    return `${start}-${end}h`;
  }, [timeBucket]);

  const fetchPredictionData = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = import.meta.env.VITE_BACKEND_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/predictions/recent/`
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

  useEffect(() => {
    fetchPredictionData();
  }, [timeBucket]);

  //prediction filtering based on selected time bucket
  const { zoneProb, top5, zoneNames,forecastTime } = useMemo(() => {  //updates on change of data or bucketLabel
    const buckets = Array.isArray(data?.buckets) ? data.buckets : Array.isArray(data) ? data : [];
    const bucketOBJ = buckets.find(
      b => (b.time_bucket || '').toLowerCase() === bucketLabel.toLowerCase() //filtering by bucket label
    );
    let fTime = 'N/A';
    if (bucketOBJ?.forecast_start_time && bucketOBJ?.forecast_end_time) {
      try {
        const startDate = new Date(bucketOBJ.forecast_start_time);
        const endDate = new Date(bucketOBJ.forecast_end_time);
        const startStr = startDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        const endStr = endDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        const dateStr = startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        fTime = `${dateStr} ${startStr}-${endStr}`; // e.g., "Aug 22 03:35 AM-09:35 AM"
      } catch (e) {
        fTime = 'Invalid Date';
      }
    }


    const map = {};
    const names = {};
    let top = [];

    // Check if bucketOBJ exists and has zone_predictions
    if (bucketOBJ?.zone_predictions?.length) {
      bucketOBJ.zone_predictions.forEach(z => {
        map[z.zone_number] = (z.probability ?? 0);
        names[z.zone_number] = z.zone;
      });

      top = [...bucketOBJ.zone_predictions]
        .filter(z => z.is_top_5 === true)
        .map(z => z.zone_number); // Extract just the zone numbers
    }

    return { zoneProb: map, top5: top, zoneNames: names, forecastTime: fTime };
  }, [data, bucketLabel]);

  //style top 5 zones based on probability
  const styleFeatures = (feature) => {
    const prop = feature.properties || {};
    const zoneId = prop.zone;
    const prob = zoneProb[zoneId] ?? 0;
    const isTop5 = top5.includes(zoneId);

    let fillColor = '#fffc33ff'; // default color
    let fillOpacity = 0.4; // default opacity

    if (isTop5) {
      fillColor = '#ff5722'; // highlight color for top 5
      fillOpacity = Math.min(prob * 1.4, 1); // opacity based on probability (0 to 1 scale)
    }

    return {
      color: isTop5 ? '#0d6efd' : '#999',
      weight: 3,
      fillColor,
      fillOpacity
    };
  };

  const onEachFeature = (feature, layer) => {
    const prop = feature.properties || {};
    const zoneId = prop.zone;
    const zoneName = zoneNames[zoneId] || prop.name || 'Unknown';
    const prob = (zoneProb[zoneId] ?? 0) * 100; // convert to percentage
    const displayName = zoneNames[zoneId] || prop.name || 'Unknown Zone';

    layer.bindTooltip(
      `<strong>${displayName}</strong><br/>ID: ${zoneId}<br/>Probability: ${prob.toFixed(2)}%`,
      { sticky: true }
    );
  };

  return (
    <div style={{ position: 'absolute', top: 56, left: 0, right: 0, bottom: 0 }}>
      <MapContainer center={[47.6, -122.6]} zoom={7} style={{ height: '100%', width: '100%' }}>
        <FixSize />
        <TileLayer
          attribution="© OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {zoneData && (
          <GeoJSON
            key={`${bucketLabel}-${Object.keys(zoneProb).length}`} // Force re-render when data changes
            data={zoneData}
            style={styleFeatures}
            onEachFeature={onEachFeature}
            coordsToLatLng={(coords) => [coords[1], coords[0]]}
          />
        )}
      </MapContainer>

      {/* tabulated predictions */}
      <div style={{
        position: 'absolute',
        top: 8,
        right: 8,
        zIndex: 1100,
        background: 'rgba(255,255,255,0.9)',
        padding: '8px 12px',
        border: '1px solid #ccc',
        borderRadius: 6,
        fontSize: 10.5,
        maxWidth: 300
      }}>
        <div><strong>Time Window:</strong> {forecastTime}</div>
        <div><strong>Bucket:</strong> {bucketLabel}</div>
        {loading && <div>Loading...</div>}
        {error && <div style={{ color: '#c00' }}>Error: {error}</div>}
        
        {!loading && !error && top5.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <div><strong>Top 5 Zones:</strong></div>
            <div style={{ marginTop: 4 }}>
              {top5.map((zoneId, index) => {
                const prob = zoneProb[zoneId] ?? 0;
                const name = zoneNames[zoneId] || `Zone ${zoneId}`;
                const percentage = (prob * 100).toFixed(1);
                
                return (
                  <div 
                    key={zoneId} 
                    style={{ 
                      marginBottom: 2, 
                      fontSize: 11,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <span style={{ 
                      maxWidth: '140px', 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {index + 1}. {name}
                    </span>
                    <span style={{ 
                      fontWeight: 'bold',
                      color: prob > 0.5 ? '#d63031' : prob > 0.3 ? '#e17055' : '#74b9ff'
                    }}>
                      {percentage}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
        
        {!loading && !error && top5.length === 0 && (
          <div style={{ marginTop: 8, color: '#999' }}>
            No predictions available
          </div>
        )}
      </div>
    </div>
  );
}

export default MapPage;