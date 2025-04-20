import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

import { fetchData, fetchAnomalies } from './api/apiClient';

import FilterControls from './components/FilterControls';
import AnomalyTable from './components/AnomalyTable';

function App() {
  // State for data and anomalies
  const [data, setData] = useState([]);
  const [anomalies, setAnomalies] = useState([]);

  // State for applied filters
  const [activeFilters, setActiveFilters] = useState({
    location_abbr: '',
    topic: '',
    year_start: '',
    year_end: '',
    data_value_type: ''
  });

  // State for loading and error handling
  const [loadingData, setLoadingData] = useState(false);
  const [loadingAnomalies, setLoadingAnomalies] = useState(false);
  const [error, setError] = useState(null);

  // Define function to fetch data based on current filters
  // useCallback prevents redefining function on every render unless filters change
  const loadData = useCallback(async (filters) => {
    setLoadingData(true);
    setLoadingAnomalies(true); // set anomaly loading true when refetching base data
    setError(null);

    // Clear prev data + anomalies
    setData([]); 
    setAnomalies([]);

    try {
      // Fetch reg data
      const dataResponse = await fetchData(filters);
      setData(dataResponse.data || []);

      // Fetch anomalies using the same filters + threshold
      const anomalyResponse = await fetchAnomalies(filters);
      setAnomalies(anomalyResponse.data || []);

    } catch (err) {
      console.error("Error fetching data or anomalies:", err);
      setError('Failed to fetch data. Check console and backend status.');
      setData([]);
      setAnomalies([]);
    } finally {
      setLoadingData(false);
      setLoadingAnomalies(false);
    }
  }, []); // No deps, no changes to this func itself

  // Callback func passed to FilterControls - updates activeFilters state + triggers data loading
  const handleFiltersChange = (newFilters) => {
    setActiveFilters(newFilters);
    loadData(newFilters);
  };

  // Fetch initial data when component mounts using default filters
  useEffect(() => {
    loadData(activeFilters);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadData]);

  const isLoading = loadingData || loadingAnomalies;

  return (
    <div className="App">
      <h1>Anomal.io</h1>
      <h2>Border Crossing Entries</h2>
      <main>
        <FilterControls
          onFiltersChange={handleFiltersChange}
          initialFilters={activeFilters}
        />

        {isLoading && <p>Loading...</p>}
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}

        {!isLoading && !error && (
          <>
            <AnomalyTable tableData={data} anomalyData={anomalies} showOnlyAnomalies={activeFilters.showOnlyAnomalies} />
          </>
        )}

        {!isLoading && !error && data.length === 0 && <p>No data found for the selected filters.</p>}
      </main>
    </div>
  );
}

export default App;
