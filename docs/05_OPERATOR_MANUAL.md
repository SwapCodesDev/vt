# 5. Operator & Administrator Manual

## 1. Quick Start & Application Startup

### Starting the Server
From the project root directory:

```powershell
# Using the project's virtual environment:
.\.venv\Scripts\python.exe run.py
```

Output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://<local-network-ip>:5000
```

The application binds to `0.0.0.0`, allowing other PCs, tablets, and wall-mounted TV monitors on the local network to view the application and dashboard.

---

## 2. Navigating the Application

| URL Route | Purpose | Key Actions |
|---|---|---|
| `http://localhost:5000/` | Main Landing & Quick Search | Instant VIN/OEM ID lookup, fleet KPI summary, location counts |
| `http://localhost:5000/tracking/` | Fleet Vehicle Tracking | Location filter pills, status filters, fleet list, hop logger |
| `http://localhost:5000/tracking/vehicle/<id>` | 360° Vehicle Profile | Inspect all 25 Excel attributes, visual hop timeline, add new hop |
| `http://localhost:5000/data-manager/` | Data Management Hub | Full 25-column SQL data table, edit records, delete records |
| `http://localhost:5000/data-manager/import` | Excel / CSV File Importer | Upload master spreadsheet in Upsert or Overwrite mode |
| `http://localhost:5000/data-manager/export` | Excel Exporter | Download master `.xlsx` file formatted to company specifications |
| `http://localhost:5000/dashboard/kiosk` | 24/7 Live Streamed TV Display | Fullscreen unattended wall monitor dashboard with real-time stream |

---

## 3. Step-by-Step Operator Procedures

### Procedure 1: Finding a Vehicle by Bosch VIN or OEM ID (Requirement 1.3)
1. In the top navigation bar or the home page search bar, enter either:
   - The **Bosch Vehicle ID** (e.g. `CVP_2023_001`, `CVP_2023_004`, `CVP_2023_059`).
   - The **OEM Identification Number** (e.g. `EP07116`, `EP06999`, `EP07138`, `HBN`).
   - The **Chassis Number** (e.g. `PP20251032RP07562`).
2. Press **Enter** or click **Track**.
3. If an exact match is found, the system immediately loads the **360° Vehicle Profile** showing all 25 attributes and complete journey history.

---

### Procedure 2: Logging a Vehicle Movement Hop (Requirement 1.4)
1. On the vehicle's detail page, click **"Log Movement Hop"** (or click the **"+"** icon on the Fleet Tracking table).
2. Review the pre-populated **From Location** (defaults to the vehicle's current location).
3. Enter or select the **To Location** (e.g. `NATRAX`, `TATA MOTORS`, `BOSCH PLANT`, `WORKSHOP`).
4. Enter the **Dispatch Date** and **Arrival Date** (format: `DD-Mon-YY`).
5. Select or describe the **Movement Purpose** (e.g. *Dynamic High-Speed Track Testing*).
6. Enter **Work Done** details (e.g. *ABS and ECU sensor recalibration completed*).
7. Enter the **Gate Pass / Delivery Challan No.** (e.g. `DC-2026-0412`).
8. Click **"Confirm & Record Hop"**.
9. The vehicle's active location and status are immediately updated in SQLite and reflected on the 24/7 TV stream.

---

### Procedure 3: Exporting Data to Excel (Requirement 1.6)
1. Navigate to **Data Manager** (`/data-manager/`) or click the green **Export Excel** button in the header or footer.
2. The browser will immediately download `Vehicle_Master_Data_Export_<timestamp>.xlsx`.
3. Open the file in Microsoft Excel:
   - **Sheet 1 (`Vehicle Master Data`)**: Contains all 25 corporate columns with styled dark-blue headers, borders, and column widths.
   - **Sheet 2 (`Movement Audit Log`)**: Contains the granular chronological log of every hop taken by every vehicle.

---

### Procedure 4: Importing an Excel Master Spreadsheet (Requirement 1.1)
1. Navigate to **Data Manager &rarr; Import Excel / CSV** (`/data-manager/import`).
2. Click **Choose File** and select your `.xlsx`, `.xls`, or `.csv` file.
3. Choose the import mode:
   - **Upsert / Merge (Recommended)**: Matches by `BOSCHVehicle Identification No`. If a vehicle exists, it updates its metadata; if it is new, it creates it. Preserves existing movement history.
   - **Fresh Master Overwrite**: Wipes current SQLite records and re-initializes from scratch.
4. Click **Upload & Synchronize SQL**.
5. The system normalizes headers, imports all rows, initializes genesis hops from `RECEIVING LOCATION` and `INCOMING DATE`, and displays a confirmation message.

---

### Procedure 5: Modifying Records in the SQLite Database
1. Navigate to **Data Manager** (`/data-manager/`).
2. Locate the vehicle in the data grid and click the **Pencil (Edit)** icon.
3. The edit form opens with all 25 fields pre-filled.
4. Modify any field (Owner, PDI status, Problem issues, Dates, Locations, Remarks).
5. Click **"Save to SQLite Database"**.
6. The changes are immediately persisted in `data/vehicle_tracking.db`.
