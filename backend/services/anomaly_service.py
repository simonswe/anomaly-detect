import pandas as pd
import numpy as np

class AnomalyService:
    @staticmethod
    def detect_anomalies(df, value_col='value', anomaly_type='statistical', threshold=3.0, min_value=None, max_value=None):
        """
        Detects anomalies in a DataFrame based on specified method.

        Args:
            df (pd.DataFrame): Input DataFrame containing data
            value_col (str): Name of the colunm containing the values to analyze
            anomaly_type (str): Type of anomaly detection
            threshold (float): The Z-score threshold for 'statistical' detection
            min_value (float, optional): The minimum allowed value for 'out_of_range'
            max_value (float, optional): The maximum allowed value for 'out_of_range'

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

        else:
            print(f"Warning: Unknown anomaly_type '{anomaly_type}'. No anomalies detected.")

        return df_result
