-- Drop table if it exists
DROP TABLE IF EXISTS border_crossing_entry_data;

-- Creation
CREATE TABLE border_crossing_entry_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    port_name TEXT NOT NULL, 
    state TEXT NOT NULL, 
    port_code INTEGER NOT NULL,
    border TEXT NOT NULL,
    date TEXT NOT NULL, -- Change format to 'YYYY-MM-DD' rather than 'Mmm-YY'
    measure TEXT NOT NULL,
    value INTEGER NOT NULL,
    latitude REAL,
    longitude REAL, 
    point TEXT 
);

-- Indices for faster querying on frequently filtered columns
CREATE INDEX IF NOT EXISTS idx_port_name ON border_crossing_entry_data (port_name);
CREATE INDEX IF NOT EXISTS idx_state ON border_crossing_entry_data (state);
CREATE INDEX IF NOT EXISTS idx_port_code ON border_crossing_entry_data (port_code);
CREATE INDEX IF NOT EXISTS idx_border ON border_crossing_entry_data (border);
CREATE INDEX IF NOT EXISTS idx_iso_date ON border_crossing_entry_data (date); -- Index on the standardized date string
CREATE INDEX IF NOT EXISTS idx_measure ON border_crossing_entry_data (measure);
