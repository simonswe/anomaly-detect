import sqlite3
import pandas as pd
import json
from datetime import datetime # needed for date parsing?

from flask import Blueprint, jsonify, request, current_app
from init_db import get_db
from services.anomaly_service import AnomalyService

data_bp = Blueprint('data_bp', __name__)

@data_bp.route('/status', methods=['GET'])
def status():
    """Returns the status of the API."""
    return jsonify({'status': 'API is running'})

def row_to_dict(row):
    """Converts a sqlite3.Row object to a dictionary."""
    return dict(row) if row else None

@data_bp.route('/data', methods=['GET'])
def get_data():
    """
    Fetches border crossing entry data based on query parameters.
    Supports filtering by: port_name, state, border, measure, date (exact match 'Mmm-YY'),
                           port_code, value_min, value_max.
    """
    db = get_db()
    cursor = db.cursor()

    port_name = request.args.get('port_name')
    state = request.args.get('state')
    border = request.args.get('border')
    measure = request.args.get('measure')
    date = request.args.get('date') # 'Mmm-YY' format
    port_code = request.args.get('port_code', type=int, default=None)

    query = 'SELECT * FROM border_crossing_entry_data WHERE 1=1'
    params = []

    if port_name: query += ' AND port_name = ?'; params.append(port_name)
    if state: query += ' AND state = ?'; params.append(state)
    if border: query += ' AND border = ?'; params.append(border)
    if measure: query += ' AND measure = ?'; params.append(measure)
    if date: query += ' AND date = ?'; params.append(date) # Exact match for 'Mmm-YY'
    if port_code is not None: query += ' AND port_code = ?'; params.append(port_code)

    query += ' ORDER BY date DESC, state ASC, port_name ASC'

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        data = [row_to_dict(row) for row in rows]
        return jsonify(data)
    
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error in /data: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        current_app.logger.error(f"Unexpected error in /data: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@data_bp.route('/anomalies', methods=['GET'])
def get_anomalies():
    """
    Fetches data based on filters and identifies anomalies based on selected type.
    Requires 'anomaly_type' parameter ('statistical' or 'out_of_range').
    Uses 'threshold' for 'statistical', 'value_min'/'value_max' for 'out_of_range'.
    """
    db = get_db()
    cursor = db.cursor()

    anomaly_type = request.args.get('anomaly_type', default='statistical') # Default if not provided
    threshold = request.args.get('threshold', type=float, default=3.0)

    min_value_param = request.args.get('value_min', type=float, default=None)
    max_value_param = request.args.get('value_max', type=float, default=None)

    if anomaly_type not in ['statistical', 'out_of_range']:
         return jsonify({"error": "Invalid 'anomaly_type'. Must be 'statistical' or 'out_of_range'."}), 400
    
    if anomaly_type == 'out_of_range' and min_value_param is None and max_value_param is None:
         return jsonify({"error": "'out_of_range' requires at least 'value_min' or 'value_max' parameter."}), 400

    port_name = request.args.get('port_name')
    state = request.args.get('state')
    border = request.args.get('border')
    measure = request.args.get('measure')
    date = request.args.get('date')
    port_code = request.args.get('port_code', type=int, default=None)

    query = 'SELECT * FROM border_crossing_entry_data WHERE 1=1'
    params = []

    if port_name: query += ' AND port_name = ?'; params.append(port_name)
    if state: query += ' AND state = ?'; params.append(state)
    if border: query += ' AND border = ?'; params.append(border)
    if measure: query += ' AND measure = ?'; params.append(measure)
    if date: query += ' AND date = ?'; params.append(date)
    if port_code is not None: query += ' AND port_code = ?'; params.append(port_code)
    query += ' AND value IS NOT NULL' # Need this to ensure validity for anomaly service

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not rows:
            return jsonify([])

        df = pd.DataFrame([row_to_dict(row) for row in rows])

        if df.empty or 'value' not in df.columns or df['value'].isnull().all():
            return jsonify([])

        # Call to AnomalyService
        df_result = AnomalyService.detect_anomalies(
            df=df,
            value_col='value',
            anomaly_type=anomaly_type,
            threshold=threshold,
            min_value=min_value_param,
            max_value=max_value_param 
        )

        anomalies_df = df_result[df_result['is_anomaly'] == True]
        anomalies_list_compatible = json.loads(anomalies_df.to_json(orient='records', date_format='iso'))

        return jsonify(anomalies_list_compatible)

    except sqlite3.Error as e:
        current_app.logger.error(f"Database error fetching data for /anomalies: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except KeyError as e:
         current_app.logger.error(f"Missing column for anomaly detection (expected 'value'): {str(e)}")
         return jsonify({"error": f"Data processing error: Missing 'value' column."}), 500
    
    except Exception as e:
        current_app.logger.error(f"Error during anomaly detection in /anomalies: {str(e)}")
        return jsonify({"error": f"An error occurred during anomaly detection: {str(e)}"}), 500

@data_bp.route('/filter-options', methods=['GET'])
def get_filter_options():
    """Fetches distinct values for available filters."""
    db = get_db()
    cursor = db.cursor()
    options = {}
    table = 'border_crossing_entry_data'
    try:
        # Port Names (TODO: Add Search Feature)
        cursor.execute(f"SELECT DISTINCT port_name FROM {table} ORDER BY port_name")
        ports = cursor.fetchall()
        options['port_names'] = [{'value': row['port_name'], 'label': row['port_name']} for row in ports]

        # States
        cursor.execute(f"SELECT DISTINCT state FROM {table} ORDER BY state")
        states = cursor.fetchall()
        options['states'] = [{'value': row['state'], 'label': row['state']} for row in states]

        # Borders
        cursor.execute(f"SELECT DISTINCT border FROM {table} ORDER BY border")
        borders = cursor.fetchall()
        options['borders'] = [{'value': row['border'], 'label': row['border']} for row in borders]

        # Measures
        cursor.execute(f"SELECT DISTINCT measure FROM {table} ORDER BY measure")
        measures = cursor.fetchall()
        options['measures'] = [{'value': row['measure'], 'label': row['measure']} for row in measures]

        # Dates (TODO: make chronological)
        cursor.execute(f"SELECT DISTINCT date FROM {table} ORDER BY date")
        dates = cursor.fetchall()
        options['dates'] = [{'value': row['date'], 'label': row['date']} for row in dates]

        # Port Codes (probably not needed ahah)
        cursor.execute(f"SELECT DISTINCT port_code FROM {table} ORDER BY port_code")
        codes = cursor.fetchall()
        options['port_codes'] = [{'value': row['port_code'], 'label': str(row['port_code'])} for row in codes]

        # Anomaly Types
        options['anomaly_types'] = [
            {'value': 'statistical', 'label': 'Statistical (Z-Score)'},
            {'value': 'out_of_range', 'label': 'Out of Range (Min/Max)'}
        ]

        return jsonify(options)
    
    except sqlite3.Error as e:
        current_app.logger.error(f"Database error fetching filter options: {str(e)}")
        return jsonify({"error": f"Database error fetching options: {str(e)}"}), 500
    
    except Exception as e:
        current_app.logger.error(f"Unexpected error fetching filter options: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred fetching options: {str(e)}"}), 500
