import axios from 'axios';

// Default Flask dev server
const API_BASE_URL = 'http://127.0.0.1:5000/api'; 

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to fetch data with filters
export const fetchData = (params) => {
  return apiClient.get('/data', { params });
};

// Function to fetch anomalies with filters
export const fetchAnomalies = (params) => {
  return apiClient.get('/anomalies', { params });
};

// Function to fetch filter options
export const fetchFilterOptions = () => {
  return apiClient.get('/filter-options');
};

export default apiClient;
