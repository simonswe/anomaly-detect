import React, { useState, useEffect } from 'react';
import { fetchFilterOptions } from '../api/apiClient';

function FilterControls({ onFiltersChange, initialFilters }) {

  // Define the initial state structure
  const defaultFilters = {
    port_name: '',
    state: '',
    border: '',
    measure: '',
    date: '',
    port_code: '',
    value_min: '',
    value_max: '', 
    anomaly_type: 'statistical', // Default anomaly type
    threshold: '3.0',            // Default for statistical
    showOnlyAnomalies: false
  };

  const [filters, setFilters] = useState(() => {
    const initial = initialFilters || {};
    return { ...defaultFilters, ...initial };
  });

  // State to hold options fetched from the backend
  const [options, setOptions] = useState({
    port_names: [],
    states: [],
    borders: [],
    measures: [],
    dates: [],
    port_codes: [],
    anomaly_types: []
  });
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [optionsError, setOptionsError] = useState(null);

  // Fetch filter options
  useEffect(() => {
    setLoadingOptions(true);
    setOptionsError(null);
    fetchFilterOptions()
      .then(response => {
        setOptions(response.data || {
            port_names: [], states: [], borders: [], measures: [],
            dates: [], port_codes: [], anomaly_types: []
        });
        setLoadingOptions(false);
      })
      .catch(err => {
        console.error("Error fetching filter options:", err);
        setOptionsError('Failed to load filter options.');
        setLoadingOptions(false);
      });
  }, []);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setFilters(prevFilters => ({
      ...prevFilters,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleApplyFilters = () => {
    onFiltersChange(filters);
  };

  const handleResetFilters = () => {
    setFilters(defaultFilters);
    onFiltersChange(defaultFilters);
  }

  const createOptions = (opts, defaultLabel = "Any") => (
    <>
      <option value="">{defaultLabel}</option>
      {Array.isArray(opts) && opts.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </>
  );

  return (
    <div style={{ border: '1px solid #eee', padding: '15px', margin: '10px 0', background: '#f9f9f9' }}>
      <h2>Filters</h2>
      {loadingOptions && <p>Loading filter options...</p>}
      {optionsError && <p style={{ color: 'red' }}>{optionsError}</p>}

      {!loadingOptions && !optionsError && (
        <>
          {/* Standard Filters */}
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-around', gap: '1rem', marginBottom: '1rem' }}>
             <div>
              <label htmlFor="port_name">Port Name:</label><br />
              <select name="port_name" id="port_name" value={filters.port_name} onChange={handleChange}>
                {createOptions(options.port_names, "Any Port")}
              </select>
            </div>
            <div>
              <label htmlFor="state">State:</label><br />
              <select name="state" id="state" value={filters.state} onChange={handleChange}>
                 {createOptions(options.states, "Any State")}
              </select>
            </div>
            <div>
              <label htmlFor="border">Border:</label><br />
              <select name="border" id="border" value={filters.border} onChange={handleChange}>
                {createOptions(options.borders, "Any Border")}
              </select>
            </div>
             <div>
              <label htmlFor="measure">Measure:</label><br />
               <select name="measure" id="measure" value={filters.measure} onChange={handleChange}>
                 {createOptions(options.measures, "Any Measure")}
               </select>
            </div>
            <div>
                <label htmlFor="date">Date (YYYY-MM-DD):</label><br />
                <select name="date" id="date" value={filters.date} onChange={handleChange}>
                    {createOptions(options.dates, "Any Date")}
                </select>
              </div>
          </div>

          {/* Anomaly Settings */}
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'flex-end', gap: '1rem', borderTop: '1px solid #ddd', paddingTop: '1rem' }}>
             <div>
                <label htmlFor="anomaly_type">Anomaly Detection Method:</label><br />
                <select name="anomaly_type" id="anomaly_type" value={filters.anomaly_type} onChange={handleChange}>
                   {Array.isArray(options.anomaly_types) && options.anomaly_types.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                   ))}
                </select>
             </div>

             {filters.anomaly_type === 'out_of_range' && (
                <>
                   <div>
                    <label htmlFor="value_min">Min Allowed Value:</label><br />
                    <input
                        type="number"
                        name="value_min"
                        id="value_min"
                        value={filters.value_min}
                        onChange={handleChange}
                        placeholder="None"
                        style={{ width: '100px' }}
                        title="Minimum value for Out of Range detection"
                    />
                    </div>
                    <div>
                    <label htmlFor="value_max">Max Allowed Value:</label><br />
                    <input
                        type="number"
                        name="value_max"
                        id="value_max"
                        value={filters.value_max}
                        onChange={handleChange}
                        placeholder="None"
                        style={{ width: '100px' }}
                        title="Maximum value for Out of Range detection"
                    />
                    </div>
                </>
             )}

             {(filters.anomaly_type === 'statistical' || filters.anomaly_type === 'time_series_stl') && (
                <div>
                    <label htmlFor="threshold">
                        {filters.anomaly_type === 'statistical' ? 'Threshold (Std Dev):' : 'Residual Threshold (Std Dev):'}
                    </label><br />
                    <input
                        type="number"
                        step="0.1"
                        min="0.1" // min threshold > 0
                        name="threshold"
                        id="threshold"
                        value={filters.threshold}
                        onChange={handleChange}
                        style={{ width: '80px' }}
                        title={filters.anomaly_type === 'statistical' ? 
                            "Z-score threshold for Statistical detection" : 
                            "Z-score threshold applied to STL residuals"}
                    />
                </div>
             )}

             {/* showOnlyAnomalies checkbox */}
            <div style={{ alignSelf: 'center', paddingBottom: '5px' }}>
              <input
                  type="checkbox"
                  name="showOnlyAnomalies"
                  id="showOnlyAnomalies"
                  checked={filters.showOnlyAnomalies}
                  onChange={handleChange}
                  style={{ marginRight: '5px', verticalAlign: 'middle' }}
              />
              <label htmlFor="showOnlyAnomalies" style={{ verticalAlign: 'middle' }}>
                  Show Only Anomalies
              </label>
            </div>
          </div>
        </>
      )}

       <div style={{ marginTop: '20px', textAlign: 'center' }}>
         <button onClick={handleApplyFilters} style={{ marginRight: '10px', padding: '8px 15px' }}>Apply Filters</button>
         <button onClick={handleResetFilters} style={{ padding: '8px 15px', background: '#ccc' }}>Reset Filters</button>
       </div>
    </div>
  );
}

export default FilterControls;
