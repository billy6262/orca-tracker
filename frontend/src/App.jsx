import './App.css';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './layouts/Layout.jsx';
import MapLayout from './layouts/MapLayout.jsx';
import MapPage from './pages/MapPage.jsx';
import ChartsPage from './pages/ChartsPage.jsx';
import ReportsPage from './pages/ReportsPage.jsx';

function App() {
  return (
    <Router>
      <Routes>
        {/* Map route with special layout */}
        <Route element={<MapLayout />}>
          <Route path="/" element={<MapPage />} />
        </Route>
        
        {/* Other routes with normal layout */}
        <Route element={<Layout />}>
          <Route path="/charts" element={<ChartsPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<div className="container">Not Found</div>} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
