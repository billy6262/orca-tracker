import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar.jsx';
import TimeBucketControl from '../components/timeBucketcontroll.jsx';

const MapLayout = () => {
  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      <TimeBucketControl/>
      <main style={{ flex: 1, overflow: 'hidden' }}>
        <Outlet />
      </main>
    </div>
  );
};

export default MapLayout;