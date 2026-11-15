# 4. 24/7 Live Streamed TV & Kiosk Dashboard Guide

## Purpose & Requirements
Company Requirement 2 mandates:
> *"2.1 - All data should be displayed on dashboard"*
> *"2.2 - location wise at how many vehicles quantity"*
> *"single page dashboard that is streamed 24/7 on screen. It should have its own URL. It gets its data from software side. Make a perfect one."*

The dashboard is engineered specifically for control-room wall monitors and shop-floor kiosks:
- **Strictly One-Page Viewport Layout**: Height is strictly constrained to `100vh` with zero window-level vertical scrolling.
- **Clutter-Free Executive Design**: Distracting elements and live clocks have been removed in favor of clean information hierarchy, subtle indicators, and high contrast.
- **Top Location Chips**: Real-time vehicle counts per facility displayed horizontally across the top.
- **Dual-Pane Split Telemetry**: Live movement stream on the left, interactive full-journey roadmap and vehicle specifications on the right.

---

## 1. Dedicated Stream URL
The 24/7 dashboard operates on a dedicated standalone URL:
```
http://<host-ip>:5000/dashboard/kiosk
```
(Alternative alias: `http://<host-ip>:5000/dashboard/tv`)

---

## 2. Dashboard Layout Architecture

### 2.1 Header & Status Bar
- **Bosch Badge & Title**: Official `BOSCH` badge and clean title `Vehicle Tracking`.
- **Official Slogan**: Official Bosch motto `Invented for life`.
- **Refresh in Timer**: Real-time background countdown badge (`Refresh in 10s`) with live pulse beacon.
- **Header Controls (Right-Aligned)**: Fullscreen mode toggle (F11), manual telemetry resync, and exit to home. All clutter and filter inputs have been removed from the header.

### 2.2 Compact Top Executive KPIs Strip
- A sleek, micro-height KPI strip displaying 5 critical fleet metrics:
  - **Total Fleet**: Current total active vehicle units across all operations.
  - **Active Hubs**: Total number of distinct operational locations/facilities currently hosting vehicles.
  - **Total Hops**: Cumulative count of all recorded journey hops and movement legs logged across the entire fleet.
  - **OEM Brands**: Number of active automotive OEM partners (TATA, MG, Maruti Suzuki, Ashok Leyland).
  - **Active Issues**: Live tally of vehicles with open mechanical, electrical, or calibration tickets.
- Dynamically refreshed in place with zero screen flicker every 10 seconds.

### 2.3 Top Horizontal Location Chips (`LOCATION-WISE VEHICLE QUANTITIES (LIVE)`)
- Located immediately beneath the header for instant situational awareness.
- Horizontal, scrollable strip of high-contrast chips displaying:
  - **All Locations**: Total fleet count (e.g. `12 Units`).
  - **Facility Hubs**: Dynamic chips for each location (`TATA MOTORS: 6`, `NATRAX: 2`, `BOSCH PLANT: 2`, `MG GUJRAT: 1`, `MARUTI SUZUKI: 1`).
- **Interactive Filtering**: Clicking any location chip instantly filters the live movement stream on the left to that specific hub.

### 2.4 Left Pane: Live Movement Stream (`LIVE MOVEMENT STREAM`)
- Displays real-time chronological vehicle movements across the fleet with smooth internal scrolling (`overflow-y: auto`).
- Each movement card features:
  - **Bosch VIN** in JetBrains Mono (`CVP_2023_001`), OEM badge (`TATA`), and vehicle model (`ALTROZ CNG`).
  - **Hop Sequence Badge**: Identifies the hop count (`Hop #1`, `Hop #2`, etc.).
  - **Directional Route**: Clear visual transition from Source Location &rarr; Destination Location.
  - **Metadata**: Date and movement purpose (e.g., Return to OEM, Track Testing, Material Movement).
- **Interactive Selection**: Clicking any movement card immediately selects that vehicle and renders its complete multi-hop roadmap on the right pane with highlighted active state.

### 2.5 Right Pane: Vehicle Journey Roadmap & Lifecycle Timeline
- Dedicated pane displaying the complete lifecycle of the selected vehicle:
  - **Vehicle Identity Header**: Bosch VIN badge, OEM & Model, Vehicle Type (PP/Non-PP), and a direct button to open the full 360&deg; tracking view in a new tab.
  - **Executive Specification Strip**:
    - **Current Location & Status**: Active location badge and operational status.
    - **Genesis Start Point**: `RECEIVING LOCATION` and `INCOMING DATE` prominently highlighted as Hop #1 start anchor.
    - **OEM ID & Chassis Number**: Master identification references.
    - **Owner & Material Kit**: Assigned engineer and equipment checklist.
  - **Reported Issues Alert**: Surfaces any mechanical, electrical, or calibration issues along with TPM confirmation status.
  - **Chronological Journey Stepper / Roadmap**:
    - **Hop #1 (Genesis Start)**: Green flag node anchoring the receiving location, incoming date, and initial equipment state.
    - **Intermediate Hops**: Sequential nodes showing route arrows, dispatch/arrival dates, purpose, work done, DC number, and status.
    - **Terminal / Current Hop**: Yellow highlight node indicating the current stationed position.

---

## 3. Zero-Flicker Telemetry Architecture
Traditional web dashboards refresh by reloading the entire browser page (`location.reload()`), causing white flashes, screen flicker, and disrupting observers.

This system employs a **Zero-Flicker Polling Stream**:
1. Background JavaScript (`dashboard-stream.js`) queries `/api/telemetry` every 10 seconds.
2. The endpoint returns the latest aggregated JSON state from the SQLite database, including complete vehicle movement histories (`include_movements=True`).
3. DOM elements (location chips, movement stream cards, and active vehicle roadmap) are mutated dynamically in place.
4. If a vehicle is currently selected by an operator, its roadmap remains selected and auto-updates with any new hops seamlessly.
5. The screen updates with zero visual disruption.

---

## 4. How to Deploy on a 24/7 TV Screen or Shop-Floor Kiosk

### Running in Chrome / Edge Kiosk Mode
On the Windows PC connected to the TV monitor:

```powershell
# Launch Google Chrome in full-screen unattended kiosk mode
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk --noerrdialogs --disable-infobars "http://localhost:5000/dashboard/kiosk"
```

Or for Microsoft Edge:
```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --kiosk "http://localhost:5000/dashboard/kiosk" --edge-kiosk-type=fullscreen
```

### Auto-start on Windows Boot
1. Press `Win + R`, type `shell:startup` and press Enter.
2. Create a shortcut pointing to the kiosk launch command above.
3. On power-on, Windows will automatically open the dashboard in full-screen mode without toolbars or scrollbars.
