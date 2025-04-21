import unittest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.anomaly_service import AnomalyService

class TestAnomalyService(unittest.TestCase):
    def setUp(self):
        """Set up reusable test data with 'YYYY-MM-DD' date format."""
        self.basic_data = pd.DataFrame({
            'id': [1, 2, 3, 4, 5, 6, 7],
            'date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01', '2023-06-01', '2023-07-01'],
            'value': [10.0, 11.0, 10.5, 100.0, 9.8, 10.2, np.nan]
        })

        # Time series data with YYYY-MM-DD dates, including outlier
        dates = pd.date_range(start='2022-01-01', periods=30, freq='MS').strftime('%Y-%m-%d')
        values = [10, 11, 12, 18, 19, 20, 11, 12, 13, 19, 20, 21, # Yr 1
                  10, 11, 12, 18, 19, 500, 11, 12, 13, 19, 20, 21, # Yr 2 (anomaly at id=18)
                  10, 11, 12, 18, 19, 20] # Start of Yr 3
        self.ts_data = pd.DataFrame({
            'id': range(1, 31),
            'date': dates,
            'value': values
        })

        # Data with duplicate dates for STL mapping test
        self.ts_data_duplicates = pd.DataFrame({
            'id': [101, 102, 103, 104, 105, 106, 107, 108],
            # Duplicate dates
            'date': ['2023-01-01', '2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-04-01', '2023-05-01', '2023-06-01'],
            # Make one value anomalous for date group if needed, or rely on STL residual
            'value': [10, 11, 15, 16, 50, 55, 18, 19]
        })
        # Need enough data points around duplicates for STL
        dates_around = pd.date_range(start='2022-01-01', end='2023-12-01', freq='MS').strftime('%Y-%m-%d')
        filler_data = pd.DataFrame({
             'id': range(200, 200 + len(dates_around)),
             'date': dates_around,
             'value': np.random.normal(15, 2, len(dates_around))
        })
        self.ts_data_duplicates_full = pd.concat([filler_data, self.ts_data_duplicates], ignore_index=True)


    # General Edge Case Tests
    def test_empty_dataframe(self):
        df_empty = pd.DataFrame({'id': [], 'date': [], 'value': []}) # Use 'date'
        result = AnomalyService.detect_anomalies(df_empty, 'value')
        self.assertTrue(result.empty or 'is_anomaly' not in result.columns or not result['is_anomaly'].any())

    def test_missing_value_column(self):
        df_missing_col = pd.DataFrame({'id': [1], 'date': ['2023-01-01'], 'other_col': [10]})
        result = AnomalyService.detect_anomalies(df_missing_col, 'value')
        self.assertFalse('is_anomaly' in result.columns and result['is_anomaly'].any())

    def test_all_nan_values(self):
        df_all_nan = pd.DataFrame({'id': [1, 2], 'date': ['2023-01-01', '2023-02-01'], 'value': [np.nan, np.nan]})
        result = AnomalyService.detect_anomalies(df_all_nan, 'value')
        self.assertFalse(result['is_anomaly'].any())
        self.assertTrue(all(r == '' for r in result['anomaly_reason']))

    # Statistical Method Tests
    def test_statistical_finds_outlier(self):
        result = AnomalyService.detect_anomalies(self.basic_data.copy(), 'value', anomaly_type='statistical', threshold=2.0)
        self.assertTrue(result.loc[result['id'] == 4, 'is_anomaly'].iloc[0])
        self.assertFalse(result.loc[result['id'] == 1, 'is_anomaly'].iloc[0])
        self.assertIn("Statistical: Z-score", result.loc[result['id'] == 4, 'anomaly_reason'].iloc[0])
        self.assertFalse(result.loc[result['value'].isna(), 'is_anomaly'].any())

    def test_statistical_no_outliers(self):
        df_no_outliers = pd.DataFrame({'id': [1,2,3], 'date': ['2023-01-01', '2023-02-01', '2023-03-01'], 'value': [10.0, 10.5, 11.0]})
        result = AnomalyService.detect_anomalies(df_no_outliers, 'value', anomaly_type='statistical', threshold=3.0)
        self.assertFalse(result['is_anomaly'].any())

    def test_statistical_zero_std_dev(self):
        df_zero_std = pd.DataFrame({'id': [1,2,3], 'date': ['2023-01-01', '2023-02-01', '2023-03-01'], 'value': [10.0, 10.0, 10.0]})
        result = AnomalyService.detect_anomalies(df_zero_std, 'value', anomaly_type='statistical', threshold=3.0)
        self.assertFalse(result['is_anomaly'].any())

    def test_statistical_insufficient_data(self):
        df_one_point = pd.DataFrame({'id': [1], 'date': ['2023-01-01'], 'value': [10.0]})
        result = AnomalyService.detect_anomalies(df_one_point, 'value', anomaly_type='statistical', threshold=3.0)
        self.assertFalse(result['is_anomaly'].any())

    # Out of Range Method Tests
    def test_out_of_range_below_min(self):
        result = AnomalyService.detect_anomalies(self.basic_data.copy(), 'value', anomaly_type='out_of_range', min_value=9.9)
        self.assertTrue(result.loc[result['id'] == 5, 'is_anomaly'].iloc[0])
        self.assertFalse(result.loc[result['id'] == 1, 'is_anomaly'].iloc[0])
        self.assertIn("below minimum", result.loc[result['id'] == 5, 'anomaly_reason'].iloc[0])
        self.assertFalse(result.loc[result['value'].isna(), 'is_anomaly'].any())

    def test_out_of_range_above_max(self):
        result = AnomalyService.detect_anomalies(self.basic_data.copy(), 'value', anomaly_type='out_of_range', max_value=50.0)
        self.assertTrue(result.loc[result['id'] == 4, 'is_anomaly'].iloc[0])
        self.assertFalse(result.loc[result['id'] == 1, 'is_anomaly'].iloc[0])
        self.assertIn("above maximum", result.loc[result['id'] == 4, 'anomaly_reason'].iloc[0])

    def test_out_of_range_both_min_max(self):
        # Test data where one is below min, another above max
        data_both = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'date': ['2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01'],
            'value': [5.0, 10.0, 15.0, 25.0]
        })
        result = AnomalyService.detect_anomalies(data_both.copy(), 'value', anomaly_type='out_of_range', min_value=8.0, max_value=20.0)

        # Check ID=1 (5.0)
        self.assertTrue(result.loc[result['id'] == 1, 'is_anomaly'].iloc[0])
        self.assertIn("below minimum 8.0", result.loc[result['id'] == 1, 'anomaly_reason'].iloc[0])
        self.assertNotIn("above maximum", result.loc[result['id'] == 1, 'anomaly_reason'].iloc[0])

        # Check ID=4 (25.0)
        self.assertTrue(result.loc[result['id'] == 4, 'is_anomaly'].iloc[0])
        self.assertIn("above maximum 20.0", result.loc[result['id'] == 4, 'anomaly_reason'].iloc[0])
        self.assertNotIn("below minimum", result.loc[result['id'] == 4, 'anomaly_reason'].iloc[0])

        # Check IDs 2 & 3 not anomalies
        self.assertFalse(result.loc[result['id'] == 2, 'is_anomaly'].iloc[0])
        self.assertFalse(result.loc[result['id'] == 3, 'is_anomaly'].iloc[0])

    def test_out_of_range_value_violates_both(self):
         # Test data where one value is below min AND above max (min > max case)
        data_both_violate = pd.DataFrame({'id': [1], 'date': ['2023-01-01'], 'value': [15.0]})
        result = AnomalyService.detect_anomalies(data_both_violate.copy(), 'value', anomaly_type='out_of_range', min_value=20.0, max_value=10.0)
        self.assertTrue(result.loc[result['id'] == 1, 'is_anomaly'].iloc[0])
        reason = result.loc[result['id'] == 1, 'anomaly_reason'].iloc[0]

        # Check if both reasons present
        self.assertIn("below minimum 20.0", reason)
        self.assertIn("above maximum 10.0", reason)

    def test_out_of_range_no_anomalies(self):
        result = AnomalyService.detect_anomalies(self.basic_data.copy(), 'value', anomaly_type='out_of_range', min_value=0.0, max_value=150.0)
        self.assertFalse(result.loc[result['value'].notna(), 'is_anomaly'].any())

    def test_out_of_range_no_min_max_provided(self):
        result = AnomalyService.detect_anomalies(self.basic_data.copy(), 'value', anomaly_type='out_of_range', min_value=None, max_value=None)
        self.assertFalse(result['is_anomaly'].any())


    # Time Series STL Method Tests
    def test_time_series_stl_finds_outlier(self):
        result = AnomalyService.detect_anomalies(self.ts_data.copy(), 'value', anomaly_type='time_series_stl', threshold=3.0, seasonal_period=12)
        anomaly_row = result[result['is_anomaly']]
        self.assertEqual(len(anomaly_row), 1, "Should find exactly one anomaly")
        self.assertEqual(anomaly_row['id'].iloc[0], 18)
        self.assertIn("Time Series STL: Residual Z-score", anomaly_row['anomaly_reason'].iloc[0])

    def test_time_series_stl_no_outliers(self):
        smooth_dates = pd.date_range(start='2022-01-01', periods=30, freq='MS').strftime('%Y-%m-%d')
        smooth_values = 15 + 10 * np.sin(np.linspace(0, 4 * np.pi, 30)) + np.linspace(0, 5, 30)
        df_smooth = pd.DataFrame({'id': range(1, 31), 'date': smooth_dates, 'value': smooth_values})
        result = AnomalyService.detect_anomalies(df_smooth, 'value', anomaly_type='time_series_stl', threshold=3.5, seasonal_period=12)
        self.assertFalse(result['is_anomaly'].any(), "Smooth data failed with threshold 3.5")

    def test_time_series_stl_insufficient_data(self):
        short_ts = self.ts_data.head(20).copy()
        result = AnomalyService.detect_anomalies(short_ts, 'value', anomaly_type='time_series_stl', threshold=3.0, seasonal_period=12)
        self.assertFalse(result['is_anomaly'].any())

    def test_time_series_stl_missing_date_column(self):
        df_no_date = pd.DataFrame({'id': [1, 2], 'value': [10, 11]})
        result = AnomalyService.detect_anomalies(df_no_date, 'value', anomaly_type='time_series_stl')
        self.assertFalse(result['is_anomaly'].any())

    def test_time_series_stl_bad_date_format_in_data(self):
        df_bad_date = self.ts_data.copy()
        df_bad_date.loc[5, 'date'] = 'not-a-date' # Original index 5 -> id 6
        df_bad_date.loc[15, 'date'] = 'Jan 2023' # Original index 15 -> id 16

        result = AnomalyService.detect_anomalies(df_bad_date, 'value', anomaly_type='time_series_stl', threshold=3.0) # Use default period 12

        self.assertFalse(result.loc[result['id'] == 6, 'is_anomaly'].any(), "Row with 'not-a-date' should not be flagged")
        self.assertFalse(result.loc[result['id'] == 16, 'is_anomaly'].any(), "Row with 'Jan 2023' should not be flagged")

    def test_time_series_stl_duplicate_dates(self):
         # Uses self.ts_data_duplicates_full with clear outlier (500) for id=105
         result = AnomalyService.detect_anomalies(self.ts_data_duplicates_full.copy(), 'value', anomaly_type='time_series_stl', threshold=3.0, seasonal_period=12) # Use threshold 3.0

         anomalies = result[result['is_anomaly']]
         flagged_ids = anomalies['id'].tolist()

         self.assertIn(105, flagged_ids, "ID 105 (value 500 on 2023-04-01) should be flagged")

         reason105 = anomalies.loc[anomalies['id'] == 105, 'anomaly_reason'].iloc[0]
         self.assertTrue(reason105.startswith("Time Series STL: Residual Z-score"))

         # Check that rows on non-anomalous dates not flagged
         self.assertNotIn(101, flagged_ids)
         self.assertNotIn(102, flagged_ids)

         # Check some filler data points not flagged
         self.assertNotIn(200, flagged_ids)
         self.assertNotIn(210, flagged_ids)


if __name__ == '__main__':
    unittest.main()
