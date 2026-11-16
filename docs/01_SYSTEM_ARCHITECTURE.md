# 1. System Architecture & Technical Specifications

## Overview
The **Bosch Vehicle Tracking & Live Telemetry System** is a standard Flask web application designed for comprehensive automotive fleet management, complex multi-hop lifecycle tracking, bidirectional Excel-to-SQLite synchronization, and unattended 24/7 wall-mounted TV streaming.

```
+---------------------------------------------------------------------------------+
|                                USER INTERFACES                                  |
|  [Standard Web App]         [Data Management Hub]       [24/7 TV Kiosk Screen]  |
|  - Home & Quick Search      - Master Data Table         - Live Ticking Clock    |
|  - 360 Vehicle View         - Excel Import / Export     - Location Quantities   |
|  - Multi-Hop Timeline       - SQL Record Modification   - Real-Time Ticker      |
+--------------------------+------------------------------+-----------------------+
                           |                              |
                           v                              v
+---------------------------------------------------------------------------------+
|                            FLASK APPLICATION CORE                               |
|                                                                                 |
|  +--------------------+  +-----------------------+  +------------------------+  |
|  | Blueprints         |  | Service Layers        |  | REST / Streaming API   |  |
|  | - main             |  | - excel_service       |  | - /api/telemetry       |  |
|  | - tracking         |  | - tracking_service    |  | - /api/suggest         |  |
|  | - data_manager     |  | - dashboard_service   |  | - /api/quick-edit      |  |
|  | - dashboard        |  |                       |  |                        |  |
|  +--------------------+  +-----------------------+  +------------------------+  |
+------------------------------------------+--------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------+
|                             DATA PERSISTENCE LAYER                              |
|                                                                                 |
|  [Inbuilt SQLite Database: data/vehicle_tracking.db]                            |
|  - Table: vehicles (Initial entry specifications in lowercase_with_underscore)  |
|  - Table: vehicle_movements (Normalized 1-to-many Hops: Origin, Dest, Dates)   |
|                                                                                 |
|  [Master Excel Workbooks: data/Master_Vehicle_Data.xlsx]                        |
|  - Sheet 1: vehicles (Normalized vehicle specifications)                        |
|  - Sheet 2: vehicle_movements (Granular hop sequence audit trail)               |
+---------------------------------------------------------------------------------+
```

---

## Key Design Patterns

### 1. Application Factory Pattern (`create_app`)
- Located in `app/__init__.py`.
- Encapsulates application instantiation, extension registration (`db.init_app`), blueprint registration, and context configuration.
- Automatically ensures storage directories (`data/`, `data/uploads/`, `data/exports/`) exist and initializes SQLite database tables on startup.

### 2. Modular Blueprints
- `app/blueprints/main`: Root landing, KPI summary, instant VIN/OEM ID router, and `/settings` display preferences hub.
- `app/blueprints/tracking`: Fleet inventory, location-based filtering, 360° vehicle profiles, and hop logging engine.
- `app/blueprints/data_manager`: Data management hub, Excel import (upsert/overwrite), Excel export, and direct SQLite CRUD.
- `app/blueprints/dashboard`: Standard in-app dashboard (`/dashboard`) and dedicated 24/7 TV kiosk monitor (`/dashboard/kiosk`).
- `app/blueprints/api`: High-performance JSON endpoints for live telemetry polling, autocomplete search, inline record updates, and theme persistence (`/api/theme`).

### 3. Dual Independent Theme Architecture
- **Main Software Theme**: Supports `Light` (default) and `Dark` modes across all desk-facing pages (Home, Fleet Tracking, Data Manager, Detail views).
- **Dashboard Kiosk Theme**: Supports `Dark` (default) and `Light` modes independently for the 24/7 TV kiosk wall monitor.
- **Zero-FOUC Persistence**: Synchronized seamlessly via HTTP cookies (`software_theme`, `dashboard_theme`) and client-side `localStorage` with instant early `<script>` evaluation before DOM paint.

### 3. Service Layer Architecture
- Business logic is strictly decoupled from presentation controllers:
  - `excel_service.py`: Intelligent header normalization, schema mapping, upsert logic, and styled multi-sheet workbook generation.
  - `tracking_service.py`: Hop sequence resolution, active location synchronization, multi-criteria filtering, and genesis hop initialization.
  - `dashboard_service.py`: Real-time fleet aggregations, location quantity breakdown, and alert aggregation.

---

## Inbuilt SQLite Database Architecture
- Python's standard library includes SQLite driver (`sqlite3`), manipulated via SQLAlchemy ORM.
- **Zero Configuration**: SQLite requires no external database server process, credentials, or installation overhead.
- **Persistence**: Stored at `data/vehicle_tracking.db`.
- **Concurrency & WAL Mode**: SQLite handles typical kiosk read loads effortlessly, with writes occurring during imports or hop additions.
