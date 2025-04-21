# Anomal.io - Border Crossing Anomaly Detection

- **Submission**:
    1.  **Code**: This repo contains the source code.
    2.  **Video Demo**: [Link to Loom Video - TO BE ADDED]

---

## Option 1 Chosen: Working with Government Data

My project implements Option 1, creating a full-stack application to find anomalies in a public dataset.

---

## Dataset Selection

- **Dataset Name**: U.S. Border Crossing Entry Data
- **Source**: `Border_Crossing_Entry_Data.csv`
- **Rationale**: This dataset was chosen because:
    - Clear, quantifiable data (`Value` column representing counts of crossings) suitable for anomaly detection.
    - Multiple dimensions (Port, State, Border, Measure, Date) allowing for interesting filtering and analysis.
    - Interesting to explore patterns in border crossings (e.g., monthly trends, differences between ports)

---

## My definition of "Anomaly"

In the context of these border crossings, an "anomaly" refers to a data value (a specific monthly crossing count for a given port/measure) that deviates significantly from expectations based on user-defined criteria. I implemented two types of anomaly detection:

1.  **Out of Range (Min/Max)**:
    - Flags entries where the `Value` falls outside a user-defined range
    - Useful for identifying absolute outliers, regardless of the distribution of the filtered data

2.  **Statistical (Z-Score)**:
    - Calculates the mean and standard deviation of the `Value` for the subset of data currently selected by the active filters
    - Flags entries where the `Value`'s Z-score (number of standard deviations from the mean) exceeds a user-defined `Threshold` (default set to 3.0)
    - Useful for identifying statistically unusual highs or lows *relative* to the specific group being viewed

3.  **Time Series (STL)**:
    - Uses Seasonal-Trend decomposition using Loess (STL) to break down the time series (for the filtered data, grouped implicitly by the filters applied) into seasonal, trend, and residual components. Requires `statsmodels` library
    - Analyzes the *residual* component, which represents the noise or remainder after removing seasonality and trend.
    - Flags entries where the residual's Z-score exceeds a user-defined `Threshold`
    - Useful for identifying points that are unusual even after accounting for predictable seasonal patterns and overall trends. Requires sufficient historical data (at least 2 full seasonal cycles, typically 25+ months for monthly data) for reliable decomposition

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

## Unit Testing

Unit tests have been added for the backend `AnomalyService` to verify the logic of the different anomaly detection methods

-   **Location**: `backend/tests/test_anomaly_detector.py`
-   **Coverage**: Tests include cases for:
    -   Statistical method (outlier found, no outlier, zero std dev, insufficient data).
    -   Out of Range method (below min, above max, both, none found, no limits provided).
    -   Time Series STL method (outlier found, no outlier, insufficient data, missing/bad date column).
    -   General edge cases (empty DataFrame, missing value column, all NaN values).

-   **How to Run Tests**:
    1.  Navigate to `backend` directory
    2.  Ensure your Python venv is active
    3.  Run the tests using:
        ```
        python -m unittest tests/test_anomaly_detector.py
        ```
        
---
