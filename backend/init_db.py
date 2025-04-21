import sqlite3
import click
import pandas as pd
import os
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    """Connects to configed db"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Closes db connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Clears existing data, creates new table based on schema.sql, and loads data from CSV."""
    db = get_db()

    click.echo("Creating database tables from schema.sql...")
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    click.echo("Tables created.")

    csv_filename = 'Border_Crossing_Entry_Data.csv'
    csv_filepath = os.path.join(current_app.root_path, csv_filename)

    if not os.path.exists(csv_filepath):
        click.echo(f"Warning: {csv_filename} not found at {csv_filepath}. Skipping data loading.")
        return # Stop if CSV dne

    try:
        click.echo(f"Loading data from {csv_filename}...")

        # Read CSV file using pandas
        df = pd.read_csv(csv_filepath)
        click.echo(f"Loaded {len(df)} rows from CSV.")

        rename_map = {
            'Port Name': 'port_name',
            'State': 'state',
            'Port Code': 'port_code',
            'Border': 'border',
            'Date': 'date', 
            'Measure': 'measure',      
            'Value': 'value',        
            'Latitude': 'latitude',  
            'Longitude': 'longitude',   
            'Point': 'point'    
        }
        df.rename(columns=rename_map, inplace=True)
        click.echo("Renamed CSV columns to match database schema.")

        # All columns required
        required_columns = [
            'port_name',
            'state',
            'port_code',
            'border',
            'date',
            'measure',
            'value',
            'latitude',
            'longitude',
            'point'
        ]

        # Check if all required columns exist after renaming
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            original_names_missing = [k for k, v in rename_map.items() if v in missing_cols]
            click.echo(f"Error: Missing required columns in CSV after renaming. ")
            click.echo(f"Required DB columns not found: {missing_cols}")
            if original_names_missing:
                 click.echo(f"Check if these original CSV columns exist: {original_names_missing}")
            else:
                 click.echo(f"Check if columns matching {missing_cols} exist in the CSV and are mapped correctly in the rename_map.")
            return

        df_to_insert = df[required_columns].copy()
        click.echo(f"Selected {len(required_columns)} columns for insertion.")

        numeric_cols = ['port_code', 'value', 'latitude', 'longitude']
        for col in numeric_cols:
             if col in df_to_insert.columns:
                # Coerce errors to NaN for non-numeric values
                df_to_insert[col] = pd.to_numeric(df_to_insert[col], errors='coerce')

        integer_cols = ['port_code', 'value']
        for col in integer_cols:
            if col in df_to_insert.columns:
                df_to_insert[col] = df_to_insert[col].astype('Int64')

        if 'date' in df_to_insert.columns:
            click.echo("Converting 'date' column format to 'YYYY-MM-DD'...")
            date_dt_series = pd.to_datetime(df_to_insert['date'], format='%b %Y', errors='coerce')

            # Format back to 'YYYY-MM-DD' string, NaT will become None/NaN here
            df_to_insert['date'] = date_dt_series.dt.strftime('%Y-%m-%d')
            click.echo("Successfully converted 'date' column format.")
        else:
             click.echo("Warning: 'date' column not found for format conversion.")

        df_to_insert = df_to_insert.where(pd.notnull(df_to_insert), None)

        click.echo("Cleaned numeric data and handled missing values.")
        click.echo("Inserting data into the database (this may take a moment)...")

        table_name = 'border_crossing_entry_data'

        df_to_insert.to_sql(table_name, db, if_exists='append', index=False)

        # Commit transaction
        db.commit() 
        click.echo(f"Successfully inserted {len(df_to_insert)} rows into '{table_name}'.")

    except pd.errors.EmptyDataError:
        click.echo(f"Error: The CSV file '{csv_filename}' is empty.")

    except pd.errors.ParserError as e:
        click.echo(f"Error parsing CSV file '{csv_filename}': {e}")
        click.echo("Please check the CSV format, delimiter, and encoding.")

    except sqlite3.Error as e:
        db.rollback() # Rollback changes on database error
        click.echo(f"Database error during insertion: {e}. Rolled back changes.")

    except KeyError as e:
        click.echo(f"Error: A required column name was not found after renaming: {e}")
        click.echo(f"Check the 'rename_map' and the columns in '{csv_filename}'.")

    except Exception as e:
        db.rollback() # Rollback changes on unexpected error
        click.echo(f"An unexpected error occurred during data loading: {e}. Rolled back changes.")


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear existing data, create new table, load from CSV"""
    init_db()

def init_app(app):
    """Register database funcs with Flask app."""
    app.teardown_appcontext(close_db) 
    app.cli.add_command(init_db_command)
