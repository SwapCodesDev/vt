# Bosch Vehicle Tracking System & 24/7 Live Streamed Telemetry

A standardized Flask web application for enterprise vehicle tracking, complex multi-hop lifecycle management, bidirectional Excel-to-SQLite synchronization, and unattended 24/7 wall-mounted TV streaming.

---

## Key Features

1. **Multi-Hop Vehicle Tracking & State Engine**:
   - Location-centric vehicle tracking.
   - 360° vehicle detail view supporting instant lookup by **Bosch VIN** (e.g. `CVP_2023_001`) or **OEM Identification No** (e.g. `EP07116`).
   - Supports arbitrary cyclic movement journeys (e.g. `Plant -> Track -> Plant -> OEM -> Plant`).
   - Automated genesis hop initialization anchored on `RECEIVING LOCATION` and `INCOMING DATE`.
2. **Data Management Hub (Excel + SQLite)**:
   - Python inbuilt SQLite storage (`data/vehicle_tracking.db`).
   - Full bidirectional Excel synchronization: import master workbooks (`.xlsx`, `.xls`, `.csv`) and export formatted Excel sheets matching the exact 25-column corporate layout.
   - Web-based record modification and direct database management.
3. **24/7 Live Streamed TV Display (`/dashboard/kiosk`)**:
   - Dedicated standalone URL designed for large TV monitors and shop-floor displays.
   - High-contrast industrial dark mode with zero screen burn-in risk.
   - Real-time digital ticking clock (`HH:MM:SS`) and pulsing live indicator.
   - Location-wise vehicle quantity breakdown cards.
   - Live movement ticker streaming recent hops in real-time with zero-flicker background polling.
4. **Exhaustive Documentation (`docs/`)**:
   - Complete technical architecture, data dictionary, tracking lifecycle guide, kiosk setup, and operator procedures.

---

## Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.13 supported)

### 2. Activate Virtual Environment & Install Dependencies
```powershell
# Dependencies are listed in requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Initialize / Seed Master Data
```powershell
.\.venv\Scripts\python.exe seed_data.py
```
*This populates the SQLite database (`data/vehicle_tracking.db`) with the 12 master vehicle records and generates `data/Master_Vehicle_Data.xlsx`.*

### 4. Run the Application
```powershell
.\.venv\Scripts\python.exe run.py
```

### 5. Access the System
- **Main Home Page**: `http://localhost:5000/`
- **Fleet Tracking & Hops**: `http://localhost:5000/tracking/`
- **Data Management Hub**: `http://localhost:5000/data-manager/`
- **24/7 Live Streamed TV Display**: `http://localhost:5000/dashboard/kiosk`

---

## Project Structure
```
Vehicle Tracking/
├── app/
│   ├── __init__.py               # Application factory
│   ├── models/                   # SQLAlchemy models (Vehicle, VehicleMovement)
│   ├── blueprints/               # Blueprints (main, tracking, data_manager, dashboard, api)
│   ├── services/                 # Business logic (excel_service, tracking_service, dashboard_service)
│   ├── static/                   # CSS (custom, dashboard-tv) and JS (streaming, main)
│   └── templates/                # Jinja2 templates (base, list, detail, kiosk, edit, import)
├── data/                         # SQLite DB and Excel files
├── docs/                         # Detailed architecture, dictionary, guides, manual
├── tests/                        # Automated unit and integration test suite
├── .gitignore                    # Git ignore specifications
├── install.md                    # Detailed step-by-step GitHub installation guide
├── config.py                     # App configuration
├── run.py                        # Entry point
├── seed_data.py                  # Seeder script
└── requirements.txt              # Dependencies
```

---

## Installation & Deployment
For a complete guide covering installation from GitHub across Windows, Linux, and macOS, see [install.md](install.md).
