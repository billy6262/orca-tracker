import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js'; // add this for navbar toggler
import { DateProvider, TimeBucketProvider } from './components/Constants.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <DateProvider>
    <TimeBucketProvider>
      <App />
    </TimeBucketProvider>
  </DateProvider>,
)
