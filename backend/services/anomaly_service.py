import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL
import warnings

class AnomalyService:
    @staticmethod
    def detect_anomalies(df, value_col='value', anomaly_type='statistical', threshold=3.0, min_value=None, max_value=None, seasonal_period=12):
        """
        Detects anomalies in a DataFrame based on specified method.

        Args:
            df (pd.DataFrame): Input DataFrame containing data
            value_col (str): Name of the colunm containing the values to analyze
            anomaly_type (str): Type of anomaly detection
            threshold (float): The Z-score threshold for 'statistical' detection
            min_value (float, optional): The minimum allowed value for 'out_of_range'
            max_value (float, optional): The maximum allowed value for 'out_of_range'
            seasonal_period (int): The seasonal period for STL (default 12 for monthly data)

        Returns:
            pd.DataFrame: The original DataFrame with two added columns:
                          'is_anomaly' (bool) and 'anomaly_reason' (str).
        """
        if df.empty or value_col not in df.columns:
            df['is_anomaly'] = False
            df['anomaly_reason'] = ''
            return df

        # Ensure value column is numeric, coerce errors, handle potential all-NaN column
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')

        if df[value_col].isnull().all():
            df['is_anomaly'] = False
            df['anomaly_reason'] = ''
            return df

        df_result = df.copy()
        df_result['is_anomaly'] = False
        df_result['anomaly_reason'] = ''

        df_analysis = df.dropna(subset=[value_col]).copy()

        if df_analysis.empty:
            # No valid data to analyze
            return df_result

        if anomaly_type == 'statistical':
            valid_values = df_result[value_col].dropna()
            if len(valid_values) < 2: 
                 # 2 points needed for std dev, if cannot calc => mark nothing as anomaly
                 return df_result

            mean = valid_values.mean()
            std_dev = valid_values.std()

            # Avoid division by zero if standard deviation is 0
            if std_dev is None or pd.isna(std_dev) or std_dev == 0:
                # If std dev 0, all valid values are same, no stat anomalies.
                 return df_result

            # Calc Z-score only for non-null values
            z_scores = df_result[value_col].apply(lambda x: (x - mean) / std_dev if pd.notna(x) else np.nan)

            # Identify anomalies based on threshold
            anomaly_mask = z_scores.abs() > threshold
            df_result.loc[anomaly_mask, 'is_anomaly'] = True

            # Apply reason only where anomaly_mask True, z_score not NaN
            df_result.loc[anomaly_mask & z_scores.notna(), 'anomaly_reason'] = z_scores[anomaly_mask & z_scores.notna()].apply(
                lambda z: f"Statistical: Z-score {z:.2f} exceeds threshold {threshold}"
            )

        elif anomaly_type == 'out_of_range':
            if min_value is None and max_value is None:
                # No range defined, cannot detect this type of anomaly
                 print("Warning: Out of Range detection selected but no min or max provided.")
                 return df_result

            below_min_mask = pd.Series([False] * len(df_result))
            above_max_mask = pd.Series([False] * len(df_result))

            if min_value is not None:
                 below_min_mask = (df_result[value_col].notna()) & (df_result[value_col] < min_value)
                 df_result.loc[below_min_mask, 'is_anomaly'] = True
                 df_result.loc[below_min_mask, 'anomaly_reason'] = df_result.loc[below_min_mask, value_col].apply(
                     lambda v: f"Out of Range: Value {v} is below minimum {min_value}"
                 )


            if max_value is not None:
                 above_max_mask = (df_result[value_col].notna()) & (df_result[value_col] > max_value)
                 df_result.loc[above_max_mask, 'is_anomaly'] = True
                 # Add/Update reason for values above max (potential overlap with below_min if min > max)
                 # If already marked below min, append reason; otherwise set reason
                 df_result.loc[above_max_mask, 'anomaly_reason'] = df_result.loc[above_max_mask].apply(
                    lambda row: (row['anomaly_reason'] + "; " if row['anomaly_reason'] else "") + \
                                f"Out of Range: Value {row[value_col]} is above maximum {max_value}", axis=1
                 )

        elif anomaly_type == 'time_series_stl':
            if 'date' not in df_analysis.columns:
                print("Warning: 'date' column required for time_series_stl not found.")
                return df_result

            df_ts = df_analysis.reset_index().copy()

            original_index_col_name = 'original_index'
            if 'index' in df_ts.columns:
                df_ts.rename(columns={'index': original_index_col_name}, inplace=True)
            else:
                 df_ts[original_index_col_name] = df_analysis.index

            try:
                df_ts['datetime'] = pd.to_datetime(df_ts['date'], format='%Y-%m-%d', errors='coerce')
                df_ts.dropna(subset=['datetime'], inplace=True)

                if df_ts.empty:
                     print("Warning: No valid dates found for STL.")
                     return df_result
                
                # 'datetime' set as working index for STL
                df_ts = df_ts.set_index('datetime').sort_index()
            except Exception as e:
                print(f"Warning: Could not process 'date' column for STL: {e}")
                return df_result

            if len(df_ts) < 2 * seasonal_period:
                print(f"Warning: Insufficient data ({len(df_ts)} points) for STL. Need {2 * seasonal_period}.")
                return df_result

            # STL Decomposition
            try:
                seasonal_smoother_len = max(7, seasonal_period + 1 if seasonal_period % 2 == 0 else seasonal_period)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    stl = STL(endog=df_ts[value_col], period=seasonal_period, seasonal=seasonal_smoother_len, robust=True)
                    result = stl.fit()

                residuals = result.resid # Indexed by datetime
            except ValueError as ve:
                 print(f"ERROR during STL decomposition: {ve}")
                 return df_result
            
            except Exception as e:
                 print(f"UNEXPECTED ERROR during STL decomposition: {e}")
                 return df_result

            # Detect anomalies in residuals
            if len(residuals.dropna()) < 2: return df_result
            resid_mean = residuals.mean(); resid_std = residuals.std()
            if resid_std is None or pd.isna(resid_std) or resid_std == 0: return df_result
            resid_z_scores = (residuals - resid_mean) / resid_std
            anomaly_mask_stl = resid_z_scores.abs() > threshold

            if anomaly_mask_stl.any():
                anomaly_datetime_indices = residuals[anomaly_mask_stl].index

                anomalous_ts_rows_mask = df_ts.index.isin(anomaly_datetime_indices)
                anomalous_ts_rows = df_ts[anomalous_ts_rows_mask]

                if not anomalous_ts_rows.empty:
                    # Get the ORIGINAL index values stored in our preserved column
                    original_indices_to_flag = anomalous_ts_rows[original_index_col_name].unique()

                    # Update the main result DataFrame using these original indices
                    df_result.loc[original_indices_to_flag, 'is_anomaly'] = True

                    # Assign reasons: Create a map from datetime index to reason string
                    relevant_z_scores = resid_z_scores.loc[anomaly_datetime_indices]
                    reason_map = {dt: f"Time Series STL: Residual Z-score {z:.2f} exceeds threshold {threshold}"
                                  for dt, z in relevant_z_scores.items()}

                    # Apply reasons: map datetime index of anomalous_ts_rows to get correct reason string for each row
                    df_result.loc[original_indices_to_flag, 'anomaly_reason'] = anomalous_ts_rows.index.map(reason_map)

        else:
            print(f"Warning: Unknown anomaly_type '{anomaly_type}'. No anomalies detected.")

        return df_result
