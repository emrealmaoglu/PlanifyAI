
import OptimizationResults from './components/OptimizationResults';
import { config } from './config';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || 'pk.eyJ1IjoiZW1yZWFsbWFvZ2x1IiwiYSI6ImNtaWh2a3hvODAzM28zZnI0Y28zZHpsOG0ifQ.5_cmH0d6fsegGyMpIScjmA';

function App() {
  return (
    <OptimizationResults
      mapboxToken={MAPBOX_TOKEN}
      apiBaseUrl={config.apiBaseUrl}
      initialCenter={[33.777434, 41.424274]}  // Kastamonu Campus
      initialZoom={15}
    />
  );
}

export default App;

