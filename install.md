# Installation & Setup Guide

This guide walks you through setting up and running the **Bosch Vehicle Tracking & 24/7 TV Telemetry System** from GitHub on **Windows**, **Linux**, or **macOS**.

---

## 1. Prerequisites

Before getting started, make sure you have the following installed on your machine:

- **Python 3.10+** (Tested with Python 3.11, 3.12, and 3.13)
  - Verify with: `python --version` (or `python3 --version`)
- **Git**
  - Verify with: `git --version`
- **Modern Web Browser** (Google Chrome, Microsoft Edge, Mozilla Firefox)

---

## 2. Step-by-Step Installation

### Step 1: Clone the Repository from GitHub

Open your terminal or PowerShell and clone the project:

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd "Vehicle Tracking"
```

---

### Step 2: Create a Python Virtual Environment

It is recommended to use an isolated virtual environment:

#### Windows:
```powershell
python -m venv .venv
```

#### Linux / macOS:
```bash
python3 -m venv .venv
```

---

### Step 3: Activate the Virtual Environment

#### Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
> *Note:* If PowerShell blocks script execution, run:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run `.\.venv\Scripts\Activate.ps1` again.

#### Windows (Command Prompt):
```cmd
.\.venv\Scripts\activate.bat
```

#### Linux / macOS:
```bash
source .venv/bin/activate
```

---

### Step 4: Install Dependencies

Install all required Python packages using `pip`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Dependencies Installed:
- **`Flask`** (>=3.0.0): Web application framework
- **`Flask-SQLAlchemy`** (>=3.1.0): SQLite ORM database management
- **`pandas`** (>=2.2.0): Data processing and tabular operations
- **`openpyxl`** (>=3.1.2): Read and write formatted Excel (`.xlsx`) files

---

### Step 5: Seed the Master Database & Excel Files

Initialize the SQLite database and create the master Excel workbook by running the seed script:

```bash
python seed_data.py
```

This command will:
1. Initialize the SQLite database schema at `data/vehicle_tracking.db`.
2. Seed the 12 master vehicle records with all 25 company Excel columns.
3. Automatically log **Hop #1 Genesis Start Points** (`RECEIVING LOCATION` & `INCOMING DATE`).
4. Generate rich multi-hop tracking histories (e.g. Bosch Plant &rarr; NATRAX &rarr; OEM Hubs).
5. Generate the formatted two-sheet master Excel workbook at `data/Master_Vehicle_Data.xlsx`.

---

### Step 6: Verify the Installation with Tests

Run the built-in integration test suite to verify that all endpoints, database operations, and export mechanisms are working properly:

```bash
python -m unittest discover tests
```

You should see:
```text
Ran 9 tests in ~0.6s
OK
```

---

### Step 7: Launch the Application

Start the Flask development server:

```bash
python run.py
```

The application will start on **`http://localhost:5000`** (and is accessible on your local network via your machine's IP address: `http://0.0.0.0:5000`).

---

## 3. Application URLs & Endpoints

| View / Feature | URL | Description |
| :--- | :--- | :--- |
| **Home Portal & Quick Search** | `http://localhost:5000/` | Global Bosch VIN / OEM ID search bar, quick navigation, and system overview. |
| **24/7 TV Streamed Dashboard** | `http://localhost:5000/dashboard/kiosk` | Unattended full-screen monitor view with live movement stream & vehicle journey roadmap. |
| **Fleet Tracking Directory** | `http://localhost:5000/tracking/` | Complete vehicle inventory with instant filters by OEM, location, and status. |
| **Vehicle 360° Detail & Hop Logger** | `http://localhost:5000/tracking/vehicle/<id>` | Full lifecycle view, 25-column specs, and modal to log new movement hops. |
| **Data Manager (Excel / SQLite)** | `http://localhost:5000/data-manager/` | Import `.xlsx`/`.csv` files, export master datasets, and modify records in SQLite. |
| **Live Telemetry API** | `http://localhost:5000/api/telemetry` | JSON telemetry endpoint consumed by the 24/7 TV monitor (polled every 10s). |

---

## 4. Setting Up 24/7 Unattended Wall-Mounted TV Monitor

To run the dashboard in unattended full-screen kiosk mode on a wall-mounted TV or control-room monitor:

### Option A: Google Chrome Kiosk Mode (Windows)
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk --noerrdialogs --disable-infobars "http://localhost:5000/dashboard/kiosk"
```

### Option B: Microsoft Edge Kiosk Mode (Windows)
```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --kiosk "http://localhost:5000/dashboard/kiosk" --edge-kiosk-type=fullscreen
```

### Auto-Start on System Boot
1. Press `Win + R`, type `shell:startup`, and press Enter.
2. Right-click and choose **New &rarr; Shortcut**.
3. Paste the browser command above into the shortcut location.
4. On every system reboot, Windows will automatically open the dashboard in full-screen mode.

---

## 5. Production WSGI Server Deployment

For 24/7 production use, run the application using a production WSGI server instead of the built-in Flask development server:

### Windows (Waitress):
```powershell
pip install waitress
waitress-serve --port=5000 --call "run:create_app"
```

### Linux / Docker (Gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "run:create_app()"
```

---

## 6. Troubleshooting & FAQ

### Q: PowerShell shows `File Activate.ps1 cannot be loaded because running scripts is disabled`?
**A:** Run the following command in PowerShell to allow script execution for your current session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Q: Port 5000 is already in use?
**A:** You can change the port in `run.py` or specify the port environment variable:
```powershell
$env:PORT = "5050"
python run.py
```

### Q: How do I reset the database to clean master data?
**A:** Simply rerun the seed script at any time:
```bash
python seed_data.py
```
This safely reseeds the database with all 12 initial vehicles and their complete multi-hop histories.
