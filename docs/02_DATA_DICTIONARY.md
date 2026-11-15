# 2. Data Dictionary & Field Specifications

## Master Excel Attributes vs. Database Schema

The SQLite database table `vehicles` maps 1:1 with the company's 25-column master Excel spreadsheet layout:

| # | Master Excel Column Header | DB Field Name | Data Type | Nullable | Description & Constraints |
|---|----------------------------|---------------|-----------|----------|---------------------------|
| 1 | `SR.NO` | `sr_no` | INTEGER | Yes | Master serial number sequence |
| 2 | `BOSCHVehicle Identification No` | `bosch_vin` | VARCHAR(100) | **NO (PK/UK)** | Unique Bosch Vehicle ID (e.g. `CVP_2023_001`). Primary lookup key. |
| 3 | `OEM` | `oem` | VARCHAR(100) | **NO** | Manufacturer name (e.g. `TATA`, `MARUTI SUZUKI`, `MG MOTOR`). Indexed. |
| 4 | `VEHICLE NAME` | `vehicle_name` | VARCHAR(150) | **NO** | Model name (e.g. `ALTROZ CNG`, `SAFARI`, `NEXON`). |
| 5 | `OEM Identification No` | `oem_id_no` | VARCHAR(100) | Yes | OEM internal tag/part number (e.g. `EP07116`, `HBN`). Indexed. |
| 6 | `Type` | `vehicle_type` | VARCHAR(50) | Yes | Pre-production status: `PP` or `NON PP`. |
| 7 | `BOSCH DC-1` | `bosch_dc1` | VARCHAR(100) | Yes | Initial Delivery Challan number from Bosch gate. |
| 8 | `BOSCH DC-2` | `bosch_dc2` | VARCHAR(100) | Yes | Secondary Delivery Challan number for external transit. |
| 9 | `Owner` | `owner` | VARCHAR(150) | Yes | Responsible engineer or department lead (e.g. `Pankaj Ambatkar (CC/EAS1-IN)`). |
| 10 | `INCOMING DATE` | `incoming_date` | VARCHAR(50) | Yes | **Start Point Arrival Date** (e.g. `02-Feb-23`). Anchors Hop #1. |
| 11 | `CHASSIS NO` | `chassis_no` | VARCHAR(100) | Yes | Vehicle chassis identification number. Indexed. |
| 12 | `MATERIAL COME WITH VEHICLE` | `material_with_vehicle` | TEXT | Yes | Inventory of tools, jacks, cables, and spares received with vehicle. |
| 13 | `Spare Parts Link` | `spare_parts_link` | TEXT | Yes | Spare parts status or portal URL (e.g. `NO SPARE PARTS AVAILABLE`). |
| 14 | `OUTGOING DATE` | `outgoing_date` | VARCHAR(50) | Yes | Date dispatched from Bosch facility. |
| 15 | `OUTGOING LOCATION` | `outgoing_location` | VARCHAR(150) | Yes | Destination of departure (e.g. `NATRAX`, `TATA MOTORS`). |
| 16 | `INCOMING DATE2` | `incoming_date2` | VARCHAR(50) | Yes | Return date when vehicle re-enters after external testing. |
| 17 | `CURRENT STATUS` | `current_status` | VARCHAR(100) | Yes | Operational condition (e.g. `Received`, `Dispatched`, `In Workshop`, `At Location`). |
| 18 | `RECEIVING LOCATION` | `receiving_location` | VARCHAR(150) | Yes | **Start Point Facility** (e.g. `BOSCH PLANT`, `WORKSHOP`). Anchors Hop #1. |
| 19 | `Date sent to customer` | `date_sent_to_customer` | VARCHAR(50) | Yes | Date handed over to customer/OEM. |
| 20 | `PDI STATUS` | `pdi_status` | VARCHAR(100) | Yes | Pre-Delivery Inspection status (`Completed`, `Pending`, `Passed`). |
| 21 | `VEHICLE PROBLEM/ISSUES` | `vehicle_problem_issues` | TEXT | Yes | Logged issues, sensor calibration alerts, or mechanical faults. |
| 22 | `WORK ORDER RECEIVED DATE` | `work_order_received_date` | VARCHAR(50) | Yes | Date when formal maintenance/testing work order was received. |
| 23 | `TPM COMFIRMATION` | `tpm_confirmation` | VARCHAR(100) | Yes | Total Productive Maintenance sign-off status. |
| 24 | `REMARK` | `remark` | TEXT | Yes | General notes, cycle descriptions, or engineering remarks. |
| 25 | `Movement_History` | `movement_history_summary`| TEXT | Yes | Serialized summary of all lifecycle hops. |

---

## 2. Multi-Hop Journey Table (`vehicle_movements`)

Stores every hop in the vehicle's lifecycle:

| Field Name | Type | Key | Description |
|------------|------|-----|-------------|
| `id` | INTEGER | Primary Key | Unique movement hop ID |
| `vehicle_id` | INTEGER | Foreign Key | References `vehicles.id` with CASCADE delete |
| `hop_sequence` | INTEGER | - | Chronological sequence (1, 2, 3, ...) |
| `source_location` | VARCHAR(150) | - | Origin point for this specific hop |
| `destination_location` | VARCHAR(150) | - | Destination point for this specific hop |
| `dispatch_date` | VARCHAR(50) | - | Date departed from source |
| `arrival_date` | VARCHAR(50) | - | Date reached destination |
| `movement_purpose` | VARCHAR(150) | - | Objective (e.g. Track Testing, Return, OEM Review) |
| `work_done` | TEXT | - | Detailed description of tasks performed |
| `dc_number` | VARCHAR(100) | - | Gate pass or Delivery Challan reference |
| `status` | VARCHAR(100) | - | Status at conclusion of hop |
| `remarks` | TEXT | - | Audit remarks |
| `created_at` | DATETIME | - | Automatic system timestamp |
