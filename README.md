#NYC Taxi Mobility Explorer

Full-stack analytics app for the NYC TLC Yellow Taxi dataset: a Python ETL pipeline cleans the raw data, loads it into a normalized SQLite database, a Flask API serves it, and a browser dashboard (HTML/CSS/JS, Leaflet, Chart.js) lets you explore urban mobility patterns.

	
Video walkthrough (5 min)	[FILL: link]
Team participation sheet	[FILL: link]
Technical report (PDF)	docs/technical_report.pdf
GitHub repository	[FILL: link]

Team: Urban Mobility Team 

Member	Area	Main files
Batsinda Keynes Benoit:	Data cleaning / ETL	backend/etl.py, backend/config.py
Batsinde Ange Liana:	Database	backend/schema.sql, backend/indexes.sql, backend/export_dump.py
Nshmiyimana Abdurahim: API and custom algorithm	backend/app.py, backend/algorithms.py, backend/test_algorithms.py
Mucyo Joel:	Frontend	frontend/index.html, frontend/style.css, frontend/app.js

## Project Structure

nyc-mobility/
├── backend/
│   ├── app.py              # Flask REST API server
│   ├── algorithms.py       # Custom data structures & manual DSA implementation
│   ├── config.py           # Database connection & environment configuration
│   ├── etl.py              # Data cleaning, integration, and feature engineering pipeline
│   ├── export_dump.py      # Database schema and dump export utilities
│   ├── schema.sql          # Normalized relational schema
│   ├── indexes.sql         # Performance tuning indexes
│   └── test_algorithms.py  # Unit tests for manual algorithms
├── frontend/
│   ├── index.html          # Interactive dashboard layout
│   ├── style.css           # Responsive dashboard styling
│   └── app.js              # Frontend logic, API integration, and chart rendering
├── data/                   # Raw trip parquet files, CSV lookups, and GeoJSON metadata
├── docs/                   # Technical report builder and video script
├── logs/                   # ETL audit and error logs
├── requirements.txt        # Python dependencies
└── README.md               # Setup and execution instructions

###Prerequisites & Requirements
Python 3.9 or higher

Pip (Python package manager)

Modern web browser (Chrome, Firefox, Edge, or Safari)

#### Installation & Setup Instructions
1. Clone or Open the Repository
Navigate to the root directory containing requirements.txt:

Bash
cd nyc-mobility
2. Install Dependencies
Install all required Python packages:

Bash
pip install -r requirements.txt
3. Run the ETL Pipeline & Initialize Database
Process the raw data files, execute cleaning routines, generate derived features, and populate the database:

Bash
python backend/etl.py
4. Launch the Backend API Server
Start the Flask application server:

Bash
python backend/app.py
(The backend server will run locally at http://localhost:5000)

5. Launch the Frontend Dashboard
Open frontend/index.html directly in your web browser, or serve it via a local live server (e.g., VS Code Live Server) to interact with the dashboard, apply filters, and explore mobility insights.
