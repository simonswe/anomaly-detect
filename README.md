# Anomal.io - Border Crossing Anomaly Detection

- **Submission**:
    1.  **Code**: This repo contains the source code.
    2.  **Video Demo**: [\[Link to Loom Video\]](https://www.loom.com/share/4d7288da42d94792a73321ffa994cc4f?sid=998c0008-6106-43cc-871b-c57bd2260c48)

---

## Option 1 Chosen: Working with Government Data

My project implements Option 1, creating a full-stack application to find anomalies in a public dataset

---

## Dataset Selection

- **Dataset Name**: U.S. Border Crossing Entry Data
- **Source**: `Border_Crossing_Entry_Data.csv`
- **Rationale**: I chose this dataset because:
    - Clear, quantifiable data (`Value` column representing counts of crossings) suitable for anomaly detection
    - Multiple dimensions (Port, State, Border, Measure, Date) allowing for interesting filtering and analysis
    - Interesting to explore patterns in border crossings as a Canadian :D (e.g., monthly trends, differences between ports)

---

## My definition of "Anomaly"

In the context of these border crossings, an "anomaly" refers to a data value (a specific monthly crossing count for a given port/measure) that deviates significantly from expectations based on user-defined criteria. I implemented 3 types of anomaly detection:

1.  **Out of Range (Min/Max)**:
    - Flags entries where the `Value` falls outside a user-defined range
    - Useful for identifying absolute outliers, regardless of the distribution of the filtered data

2.  **Statistical (Z-Score)**:
    - Calculates the mean and standard deviation of the `Value` for the subset of data currently selected by the active filters
    - Flags entries where the `Value`'s Z-score (number of standard deviations from the mean) exceeds a user-defined `Threshold` (default set to 3.0)
    - Useful for identifying statistically unusual highs or lows *relative* to the specific group being viewed

3.  **Time Series (STL)**:
    - Uses Seasonal-Trend decomposition using Loess (STL) to break down the time series (for the filtered data, grouped implicitly by the filters applied) into seasonal, trend, and residual components
    - Analyzes *residual* component: noise or remainder after removing seasonality and trend
    - Flags entries where the residual's Z-score exceeds a user-defined `Threshold`

---

## Features

Anomal.io allows users to explore the Border Crossing Entry Data and identify potential anomalies:

1.  **Filtering**: Use dropdown menus and input fields in the "Filters" section to narrow down data shown in table:
    -   Port Name, State, Border, Measure, Date (YYYY-MM-DD)
2.  **Anomaly Detection Method**: Select the method for identifying anomalies:
    -   `Statistical (Z-Score)`: Requires a `Threshold` value
    -   `Out of Range (Min/Max)`: Requires a `Min Allowed Value` and/or `Max Allowed Value`
    -   `Time Series (STL)`: Requires a `Residual Threshold` - works best with minimally filtered data
3.  **Apply Filters**: Click "Apply Filters" button to fetch data matching the standard filters and identify anomalies based on the chosen method & params
4.  **Table Display**:
    -   Data matching the filters is displayed in paginated table (TanStack Table)
    -   Anomalous rows are highlighted
    -   The "Anomaly Info" column explicitly states the reason
5.  **Show Only Anomalies**: Check this box and click "Apply Filters" to display only the rows flagged as anomalies (useful for large datasets)
6.  **Reset Filters**: Click this button to clear all filters and reset anomaly detection settings

---

## Technology Stack

- **Backend**:
    - Language: Python 3
    - Framework: Flask
    - Data Handling: Pandas (for CSV loading & anomaly calculation)
    - Database: SQLite
- **Frontend**:
    - Library: React
    - UI/Table: TanStack Table
    - API Communication: Axios

---

## Escalating Scenarios & Performance Considerations

This project addresses escalating test cases as follows:

-   **Data Size**:
    -   *Small/Medium*: The current architecture (Flask/Pandas/SQLite) handles the ~400k row dataset adequately for interactive filtering on indexed columns and backend anomaly detection. Database initialization takes a noticeable moment but is a one-time setup. API response times for typical filter combinations are reasonable.
    -   *Large*: For datasets scaling into millions+ rows, there could be performance bottlenecks:
        -   **Backend Processing**: Loading large filtered datasets entirely into a Pandas DataFrame for `statistical` or `STL` analysis in the `/anomalies` endpoint becomes memory and CPU intensive
        -   **Database**: SQLite might become slow for complex queries or large data volumes. Could consider upgrading to PostgreSQL as a production database
        -   **Frontend**: Remains responsive due to API-driven filtering and table pagination, but initial load time for large result sets from the API could increase
        - Indices are currently used in SQLite to allow faster access during querying
-   **Feature Depth**:
    -   *Basic*: Threshold-based 'Out of Range'
    -   *Intermediate*: Z-score on filtered data
    -   *Advanced*: Time-series anomaly detection using STL decomposition

---

## Unit Testing

I added unit tests for the backend `AnomalyService` to verify the logic of all the different anomaly detection methods

-   **Location**: `backend/tests/test_anomaly_service.py`
-   **Coverage**: Tests include cases for:
    -   Statistical method (outlier found, no outlier, zero std dev, insufficient data)
    -   Out of Range method (below min, above max, both, none found, no limits provided)
    -   Time Series STL method (outlier found, no outlier, insufficient data, missing/bad date column)
    -   General edge cases (empty DataFrame, missing value column, all NaN values)

-   **How to Run**:
    1.  Navigate to `backend` directory
    2.  Ensure your Python venv is active
    3.  Run the tests using:
        ```
        python -m unittest tests/test_anomaly_service.py
        ```
        
---

## Setup and Installation

**Prerequisites:**

-   Python 3.8+
-   Node.js 16+ and npm

**Steps:**

1.  **Clone Repository:**
    ```
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Prepare Data:**
    -   Ensure `Border_Crossing_Entry_Data.csv` file is inside the `backend/` directory.

3.  **Setup Backend:**
    ```
    cd backend

    # Create and activate virtual env (recommended)
    python -m venv venv
    # On Windows:
    # venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Initialize the database (creates tables and loads data from CSV)
    flask init-db
    # You should see output indicating table creation and data insertion.
    cd ..
    ```

4.  **Setup Frontend:**
    ```
    cd frontend
    npm install
    cd ..
    ```

---

## Running the Application

1.  **Run Backend Server:**
    ```
    cd backend
    # Ensure virtual env is active
    # source venv/bin/activate (or venv\Scripts\activate)
    flask run
    ```
    *(Keep this terminal running)*

2.  **Run Frontend Server:**
    ```
    cd frontend
    npm start
    ```
    *(Keep this terminal running)*

3.  **Access Application:**
    -   Open your web browser and navigate to `http://localhost:3000`.

---
