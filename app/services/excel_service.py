import os
import re
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from app.models import db, Vehicle, VehicleMovement

EXCEL_COLUMNS = [
    "SR.NO",
    "BOSCHVehicle Identification No",
    "OEM",
    "VEHICLE NAME",
    "OEM Identification No",
    "Type",
    "BOSCH DC-1",
    "BOSCH DC-2",
    "Owner",
    "INCOMING DATE",
    "CHASSIS NO",
    "MATERIAL COME WITH VEHICLE",
    "Spare Parts Link",
    "OUTGOING DATE",
    "OUTGOING LOCATION",
    "INCOMING DATE2",
    "CURRENT STATUS",
    "RECEIVING LOCATION",
    "Date sent to customer",
    "PDI STATUS",
    "VEHICLE PROBLEM/ISSUES",
    "WORK ORDER RECEIVED DATE",
    "TPM COMFIRMATION",
    "REMARK",
    "Movement_History"
]

def clean_header(header_str):
    """Normalize headers by removing newlines, multiple spaces, quotes, and case."""
    if not isinstance(header_str, str):
        return ""
    cleaned = re.sub(r'[\r\n\t]+', ' ', header_str)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def map_column_name(header):
    """Map cleaned Excel column string to standardized internal field key."""
    h = clean_header(header).upper()
    if "SR.NO" in h or "SR NO" in h or "SERIAL" in h:
        return "sr_no"
    if "BOSCH" in h and ("IDENTIFICATION" in h or "VIN" in h or "VEHICLE" in h) and "DC" not in h:
        return "bosch_vin"
    if h == "OEM":
        return "oem"
    if "VEHICLE NAME" in h or "MODEL" in h:
        return "vehicle_name"
    if "OEM IDENTIFICATION" in h or "OEM ID" in h or "OEM NO" in h:
        return "oem_id_no"
    if h == "TYPE":
        return "vehicle_type"
    if "BOSCH" in h and "DC-1" in h:
        return "bosch_dc1"
    if "BOSCH" in h and "DC-2" in h:
        return "bosch_dc2"
    if "OWNER" in h:
        return "owner"
    if "INCOMING DATE2" in h:
        return "incoming_date2"
    if "INCOMING DATE" in h:
        return "incoming_date"
    if "CHASSIS" in h:
        return "chassis_no"
    if "MATERIAL" in h:
        return "material_with_vehicle"
    if "SPARE" in h:
        return "spare_parts_link"
    if "OUTGOING DATE" in h:
        return "outgoing_date"
    if "OUTGOING LOCATION" in h:
        return "outgoing_location"
    if "CURRENT STATUS" in h or "STATUS" in h:
        return "current_status"
    if "RECEIVING LOCATION" in h:
        return "receiving_location"
    if "SENT TO CUSTOMER" in h:
        return "date_sent_to_customer"
    if "PDI" in h:
        return "pdi_status"
    if "PROBLEM" in h or "ISSUE" in h:
        return "vehicle_problem_issues"
    if "WORK ORDER" in h:
        return "work_order_received_date"
    if "TPM" in h:
        return "tpm_confirmation"
    if "REMARK" in h:
        return "remark"
    if "MOVEMENT" in h:
        return "movement_history"
    return None

def import_excel_file(file_path, mode='upsert'):
    """
    Import vehicle records from an Excel or CSV file.
    mode: 'upsert' (update existing VIN or insert new) or 'overwrite' (wipe existing and reload)
    """
    # Load with pandas to support csv, xlsx, xls
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, dtype=str)
    else:
        df = pd.read_excel(file_path, dtype=str)

    # Fill NaN with empty string
    df = df.fillna('')

    # Map dataframe columns to model attributes
    col_mapping = {}
    for col in df.columns:
        mapped_key = map_column_name(col)
        if mapped_key:
            col_mapping[col] = mapped_key

    if mode == 'overwrite':
        VehicleMovement.query.delete()
        Vehicle.query.delete()
        db.session.commit()

    created_count = 0
    updated_count = 0

    for _, row in df.iterrows():
        data = {col_mapping[c]: str(row[c]).strip() for c in df.columns if c in col_mapping}
        
        bosch_vin = data.get('bosch_vin')
        if not bosch_vin:
            continue  # Skip rows without Bosch VIN

        vehicle = Vehicle.query.filter_by(bosch_vin=bosch_vin).first()
        is_new = False
        if not vehicle:
            vehicle = Vehicle(bosch_vin=bosch_vin)
            db.session.add(vehicle)
            is_new = True

        # Assign fields
        if 'sr_no' in data and data['sr_no']:
            try:
                vehicle.sr_no = int(float(data['sr_no']))
            except (ValueError, TypeError):
                pass
        
        vehicle.oem = data.get('oem', vehicle.oem or 'Unknown')
        vehicle.vehicle_name = data.get('vehicle_name', vehicle.vehicle_name or 'Unknown')
        vehicle.oem_id_no = data.get('oem_id_no', vehicle.oem_id_no)
        vehicle.vehicle_type = data.get('vehicle_type', vehicle.vehicle_type)
        vehicle.bosch_dc1 = data.get('bosch_dc1', vehicle.bosch_dc1)
        vehicle.bosch_dc2 = data.get('bosch_dc2', vehicle.bosch_dc2)
        vehicle.owner = data.get('owner', vehicle.owner)
        
        # Start points as specified in requirements
        vehicle.incoming_date = data.get('incoming_date', vehicle.incoming_date)
        vehicle.receiving_location = data.get('receiving_location', vehicle.receiving_location)
        
        vehicle.chassis_no = data.get('chassis_no', vehicle.chassis_no)
        vehicle.material_with_vehicle = data.get('material_with_vehicle', vehicle.material_with_vehicle)
        vehicle.spare_parts_link = data.get('spare_parts_link', vehicle.spare_parts_link)
        vehicle.outgoing_date = data.get('outgoing_date', vehicle.outgoing_date)
        vehicle.outgoing_location = data.get('outgoing_location', vehicle.outgoing_location)
        vehicle.incoming_date2 = data.get('incoming_date2', vehicle.incoming_date2)
        vehicle.current_status = data.get('current_status', vehicle.current_status) or 'Active'
        vehicle.date_sent_to_customer = data.get('date_sent_to_customer', vehicle.date_sent_to_customer)
        vehicle.pdi_status = data.get('pdi_status', vehicle.pdi_status)
        vehicle.vehicle_problem_issues = data.get('vehicle_problem_issues', vehicle.vehicle_problem_issues)
        vehicle.work_order_received_date = data.get('work_order_received_date', vehicle.work_order_received_date)
        vehicle.tpm_confirmation = data.get('tpm_confirmation', vehicle.tpm_confirmation)
        vehicle.remark = data.get('remark', vehicle.remark)
        
        # Resolve initial current_location
        if vehicle.outgoing_location and vehicle.outgoing_location != 'NA':
            vehicle.current_location = vehicle.outgoing_location
        elif vehicle.receiving_location:
            vehicle.current_location = vehicle.receiving_location
        else:
            vehicle.current_location = 'BOSCH PLANT'

        db.session.flush()

        # Build initial multi-hop movement logs if none exist
        if is_new or len(vehicle.movements) == 0:
            hop_seq = 1
            start_loc = vehicle.receiving_location or 'BOSCH WORKSHOP'
            start_date = vehicle.incoming_date or 'N/A'
            
            # Hop 1: Genesis Hop (Receiving location + incoming date)
            hop1 = VehicleMovement(
                vehicle_id=vehicle.id,
                hop_sequence=hop_seq,
                source_location='OEM / Inbound Transit',
                destination_location=start_loc,
                arrival_date=start_date,
                movement_purpose='Initial Receipt at Facility',
                work_done='Initial inspection & check-in',
                dc_number=vehicle.bosch_dc1 or '',
                status='Received',
                remarks='Genesis hop from incoming master data'
            )
            db.session.add(hop1)
            hop_seq += 1

            # Hop 2: Outgoing Hop (if outgoing date/location provided)
            if vehicle.outgoing_location and vehicle.outgoing_location.upper() not in ('NA', '', 'NONE'):
                hop2 = VehicleMovement(
                    vehicle_id=vehicle.id,
                    hop_sequence=hop_seq,
                    source_location=start_loc,
                    destination_location=vehicle.outgoing_location,
                    dispatch_date=vehicle.outgoing_date or '',
                    arrival_date=vehicle.outgoing_date or '',
                    movement_purpose='Dispatched for Testing / OEM Return',
                    work_done='Dispatched from facility',
                    dc_number=vehicle.bosch_dc2 or vehicle.bosch_dc1 or '',
                    status='Dispatched',
                    remarks='Outgoing transfer recorded from master data'
                )
                db.session.add(hop2)
                hop_seq += 1
                vehicle.current_location = vehicle.outgoing_location

            # Hop 3: Incoming Date 2 (if re-entered)
            if vehicle.incoming_date2 and vehicle.incoming_date2.upper() not in ('NA', '', 'NONE'):
                hop3 = VehicleMovement(
                    vehicle_id=vehicle.id,
                    hop_sequence=hop_seq,
                    source_location=vehicle.outgoing_location or 'External Location',
                    destination_location=vehicle.receiving_location or 'BOSCH PLANT',
                    arrival_date=vehicle.incoming_date2,
                    movement_purpose='Re-entry for subsequent work/evaluation',
                    work_done='Vehicle returned from external location',
                    status='Received Back',
                    remarks='Second incoming cycle from master data'
                )
                db.session.add(hop3)
                vehicle.current_location = vehicle.receiving_location or 'BOSCH PLANT'

            db.session.flush()
            vehicle.update_from_latest_hop()

        if is_new:
            created_count += 1
        else:
            updated_count += 1

    db.session.commit()
    return {'created': created_count, 'updated': updated_count, 'total_processed': len(df)}

def export_to_excel(export_filepath):
    """
    Exports all vehicle records and movement histories to a beautifully styled Excel workbook.
    """
    wb = openpyxl.Workbook()
    ws_main = wb.active
    ws_main.title = "Vehicle Master Data"

    # Styling constants
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    cell_font = Font(name="Calibri", size=10)
    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Write Master Headers
    for col_idx, col_name in enumerate(EXCEL_COLUMNS, 1):
        cell = ws_main.cell(row=1, column=col_idx, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    vehicles = Vehicle.query.order_by(Vehicle.id.asc()).all()

    for row_idx, v in enumerate(vehicles, 2):
        row_data = [
            v.sr_no or (row_idx - 1),
            v.bosch_vin or '',
            v.oem or '',
            v.vehicle_name or '',
            v.oem_id_no or '',
            v.vehicle_type or '',
            v.bosch_dc1 or '',
            v.bosch_dc2 or '',
            v.owner or '',
            v.incoming_date or '',
            v.chassis_no or '',
            v.material_with_vehicle or '',
            v.spare_parts_link or '',
            v.outgoing_date or '',
            v.outgoing_location or '',
            v.incoming_date2 or '',
            v.current_status or '',
            v.receiving_location or '',
            v.date_sent_to_customer or '',
            v.pdi_status or '',
            v.vehicle_problem_issues or '',
            v.work_order_received_date or '',
            v.tpm_confirmation or '',
            v.remark or '',
            v.movement_history_summary or ''
        ]
        for col_idx, val in enumerate(row_data, 1):
            c = ws_main.cell(row=row_idx, column=col_idx, value=val)
            c.font = cell_font
            c.border = border_thin
            if col_idx in [1, 2, 5, 6, 10, 14, 16, 17, 19, 20]:
                c.alignment = center_align
            else:
                c.alignment = left_align

    # Auto-adjust column widths
    for col in ws_main.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if '\n' in val_str:
                val_str = max(val_str.split('\n'), key=len)
            max_len = max(max_len, len(val_str))
        ws_main.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

    # Add second sheet for Detailed Movement Logs
    ws_hops = wb.create_sheet(title="Movement Audit Log")
    hop_headers = [
        "Vehicle ID", "Bosch VIN", "OEM", "Vehicle Name", "Hop #",
        "Source Location", "Destination Location", "Dispatch Date",
        "Arrival Date", "Purpose", "Work Done", "DC / Gate Pass", "Status", "Remarks"
    ]
    for col_idx, col_name in enumerate(hop_headers, 1):
        cell = ws_hops.cell(row=1, column=col_idx, value=col_name)
        cell.fill = PatternFill(start_color="203764", end_color="203764", fill_type="solid")
        cell.font = header_font
        cell.alignment = center_align

    movements = VehicleMovement.query.join(Vehicle).order_by(Vehicle.id.asc(), VehicleMovement.hop_sequence.asc()).all()
    for row_idx, m in enumerate(movements, 2):
        hop_row = [
            m.vehicle_id,
            m.vehicle.bosch_vin if m.vehicle else '',
            m.vehicle.oem if m.vehicle else '',
            m.vehicle.vehicle_name if m.vehicle else '',
            m.hop_sequence,
            m.source_location,
            m.destination_location,
            m.dispatch_date or '',
            m.arrival_date or '',
            m.movement_purpose or '',
            m.work_done or '',
            m.dc_number or '',
            m.status or '',
            m.remarks or ''
        ]
        for col_idx, val in enumerate(hop_row, 1):
            c = ws_hops.cell(row=row_idx, column=col_idx, value=val)
            c.font = cell_font
            c.border = border_thin
            c.alignment = center_align if col_idx in [1, 2, 5, 8, 9, 13] else left_align

    for col in ws_hops.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            max_len = max(max_len, len(val_str))
        ws_hops.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    # Save to file
    os.makedirs(os.path.dirname(export_filepath), exist_ok=True)
    wb.save(export_filepath)
    return export_filepath
