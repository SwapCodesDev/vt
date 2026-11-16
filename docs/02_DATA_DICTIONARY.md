# 2. Data Dictionary & Field Specifications

## 1. Vehicle Details Table (`vehicles`)

The SQLite database table `vehicles` stores the vehicle's initial entry specifications. All column names are strictly lowercase with `_` as spacebar:

| # | Column Name | Type | Constraints | Description & Constraints |
|---|-------------|------|-------------|---------------------------|
| 1 | `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique internal database identifier |
| 2 | `sr_no` | INTEGER | NULLABLE | Automatic internal serial sequence (no user input needed) |
| 3 | `bosch_vin` | VARCHAR(100) | NOT NULL UNIQUE INDEXED | Unique Bosch Vehicle ID (e.g. `CVP_2023_001`). Primary lookup key. |
| 4 | `oem_id` | VARCHAR(100) | NULLABLE INDEXED | OEM Identification No (e.g. `EP07116`, `HBN`). |
| 5 | `oem` | VARCHAR(100) | NOT NULL INDEXED | Manufacturer name (e.g. `TATA`, `MARUTI SUZUKI`, `MG MOTOR`). |
| 6 | `vehicle_name` | VARCHAR(150) | NOT NULL | Model name (e.g. `ALTROZ CNG`, `SAFARI`, `NEXON`). |
| 7 | `type` | VARCHAR(50) | NULLABLE | Pre-production status: `PP` or `NON PP`. |
| 8 | `owner` | VARCHAR(150) | NULLABLE | Responsible engineer or department lead (e.g. `Pankaj Ambatkar (CC/EAS1-IN)`). |
| 9 | `chassis_no` | VARCHAR(100) | NULLABLE INDEXED | Vehicle chassis identification number. |
| 10 | `vehicle_material` | TEXT | NULLABLE | Material come with vehicle: inventory of tools, jacks, cables, and spares. |
| 11 | `spare_parts_link` | TEXT | NULLABLE | Spare parts status or portal URL (e.g. `NO SPARE PARTS AVAILABLE`). |
| 12 | `pdi_status` | VARCHAR(100) | NULLABLE | Pre-Delivery Inspection status (`Completed`, `Pending`, `Passed`). |
| 13 | `vehicle_issues` | TEXT | NULLABLE | Logged issues, sensor calibration alerts, or mechanical faults. |
| 14 | `work_order_received_date` | VARCHAR(50) | NULLABLE | Date when formal maintenance/testing work order was received. |
| 15 | `tpm_confirmation` | VARCHAR(100) | NULLABLE | Total Productive Maintenance sign-off status. |
| 16 | `current_status` | VARCHAR(100) | NULLABLE | Operational condition (e.g. `RECEIVED`, `In Workshop`, `At Location`). |
| 17 | `current_location` | VARCHAR(150) | NOT NULL INDEXED | Automatically derived from latest hop in `vehicle_movements`. |
| 18 | `remark` | TEXT | NULLABLE | General notes, cycle descriptions, or engineering remarks. |
| 19 | `total_hops` | INTEGER | NOT NULL DEFAULT 0 | Automatically maintained count of hops recorded for this vehicle. |
| 20 | `created_at` | DATETIME | NOT NULL | Automatic UTC creation timestamp. |
| 21 | `updated_at` | DATETIME | NOT NULL | Automatic UTC update timestamp. |

> [!NOTE]
> All legacy hop columns (`BOSCH DC-1`, `BOSCH DC-2`, `INCOMING DATE`, `OUTGOING DATE`, `OUTGOING LOCATION`, `INCOMING DATE2`, `RECEIVING LOCATION`, `Date sent to customer`, `Movement_History`) have been separated from `vehicles` and consolidated into `vehicle_movements`.

---

## 2. Hop Details Table (`vehicle_movements`)

Stores every hop in the vehicle's journey lifecycle:

| # | Column Name | Type | Key / Constraints | Description |
|---|-------------|------|-------------------|-------------|
| 1 | `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique movement hop ID |
| 2 | `vehicle_id` | INTEGER | FOREIGN KEY (vehicles.id) INDEXED | References parent vehicle with cascade delete |
| 3 | `hop_sequence` | INTEGER | NOT NULL DEFAULT 1 | Chronological sequence ($1, 2, 3...$) |
| 4 | `source_location` | VARCHAR(150) | NOT NULL | Origin facility for this specific hop |
| 5 | `destination_location` | VARCHAR(150) | NOT NULL | Destination facility for this specific hop |
| 6 | `dispatch_date` | VARCHAR(50) | NULLABLE | Date departed from origin |
| 7 | `arrival_date` | VARCHAR(50) | NULLABLE | Date reached destination |
| 8 | `dc_number` | VARCHAR(100) | NULLABLE | Gate pass or Delivery Challan reference |
| 9 | `movement_purpose` | VARCHAR(150) | NULLABLE | Objective (e.g. Genesis Initial Receipt, Track Testing, Return) |
| 10 | `status` | VARCHAR(100) | NULLABLE DEFAULT 'At Location' | Status at conclusion of hop |
| 11 | `remarks` | TEXT | NULLABLE | Work done or inspection remarks |
| 12 | `created_at` | DATETIME | NOT NULL | Automatic UTC record creation timestamp |
