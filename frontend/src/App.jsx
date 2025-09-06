import { useState } from 'react'
import './App.css'
import Navbar from './components/Navbar.jsx';
import ZoneBarChart from './components/ZoneBarChart.jsx';
import { DateProvider } from './components/Constants.jsx';
import ChartsDateBar from './components/ChartsDateBar.jsx';
import PieChart  from './components/HourlyPieChart.jsx';
import HourlyPieChart from './components/HourlyPieChart.jsx';

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <DateProvider>
      <Navbar />
      <ChartsDateBar />
      <ZoneBarChart />
      <HourlyPieChart/>
      {/* Main content */}
      </DateProvider>
    </>
  )
}

export default App
