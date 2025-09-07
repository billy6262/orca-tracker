import Navbar from '../components/Navbar.jsx';
import ZoneBarChart from '../components/ZoneBarChart.jsx';
import { DateProvider } from '../components/Constants.jsx';
import ChartsDateBar from '../components/ChartsDateBar.jsx';
import HourlyPieChart from '../components/HourlyPieChart.jsx';

function ChartsPage() {
  return (
    <DateProvider>
      <div className="container pt-2 pb-3">
        <ChartsDateBar />
        <div className="row">
          <div className="col-lg-6 mb-4">
            <ZoneBarChart />
          </div>
          <div className="col-lg-6 mb-4">
            <HourlyPieChart />
          </div>
        </div>
      </div>
    </DateProvider>
  );
}

export default ChartsPage;