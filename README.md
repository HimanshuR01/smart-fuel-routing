# smart-fuel-routing
This project is a Django-based API that helps plan road trips across the USA in the most cost-effective way. It finds the best route, suggests where to refuel based on fuel prices and a 500-mile vehicle range, and calculates the total fuel cost assuming 10 MPG. It’s built to be fast, efficient, and production-ready.
## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Load Data from CSV
Import fuel price data using the management command:
```bash
python manage.py import_fuel_data data/fuel-prices-for-be-assessment.csv
```

### 3. Prepare Data
```bash
python manage.py prepare_data
```

### 4. Run Django Server
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`