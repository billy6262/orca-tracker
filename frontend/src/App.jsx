import './App.css';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './layouts/Layout.jsx';
import MapPage from './pages/MapPage.jsx';
import ChartsPage from './pages/ChartsPage.jsx';
//import ReportsPage from './pages/ReportsPage.jsx';
//import AboutPage from './pages/AboutPage.jsx';

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<MapPage />} />
          <Route path="/charts" element={<ChartsPage />} />

          <Route path="*" element={<div className="container">Not Found</div>} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
