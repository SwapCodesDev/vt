import os
import re
from datetime import datetime, timezone
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from app.models import db, Vehicle, VehicleMovement

# Standardized 2-Table Column Schemas (All lowercase with _ as spacebar)
VEHICLES_COLUMNS = [
    "sr_no",
    "bosch_vin",
    "oem_id",
    "oem",
    "vehicle_name",
    "type",
    "owner",
    "chassis_no",
    "vehicle_material",
    "spare_parts_link",
    "pdi_status",
    "vehicle_issues",
    "work_order_received_date",
    "tpm_confirmation",
    "current_status",
    "current_location",
    "remark",
    "total_hops",
    "updated_at"
]

MOVEMENTS_COLUMNS = [
    "id",
    "vehicle_id",
    "bosch_vin",
    "hop_sequence",
    "source_location",
    "destination_location",
    "dispatch_date",
    "arrival_date",
    "dc_number",
    "movement_purpose",
    "status",
    "remarks",
    "created_at"
]

def clean_header(header_str):
    """Normalize headers by removing newlines, extra whitespace, and symbols."""
    if not isinstance(header_str, str):
        return ""
    cleaned = re.sub(r'[\r\n\t]+', ' ', header_str)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def map_column_name(header):
    """
    Map an incoming Excel column string to normalized internal field keys.
    Handles both new lowercase_with_underscore schema and legacy 25-column format.
    """
    raw = clean_header(header)
    h = raw.lower().replace(" ", "_").replace(".", "_").replace("-", "_").replace("/", "_")
    h_upper = raw.upper()

    # Exact lowercase matches
    if h in ("sr_no", "srno", "serial_no"):
        return "sr_no"
    if h in ("bosch_vin", "boschvin", "vin"):
        return "bosch_vin"
    if h in ("oem_id", "oemid", "oem_id_no"):
        return "oem_id"
    if h == "oem":
        return "oem"
    if h in ("vehicle_name", "vehiclename", "model"):
        return "vehicle_name"
    if h in ("type", "vehicle_type"):
        return "type"
    if h == "owner":
        return "owner"
    if h in ("chassis_no", "chassisno", "chassis"):
        return "chassis_no"
    if h in ("vehicle_material", "material_come_with_vehicle", "material"):
        return "vehicle_material"
    if h in ("spare_parts_link", "sparepartslink"):
        return "spare_parts_link"
    if h in ("pdi_status", "pdistatus"):
        return "pdi_status"
    if h in ("vehicle_issues", "vehicle_problem_issues", "issues", "problems"):
        return "vehicle_issues"
    if h in ("work_order_received_date", "work_order_date"):
        return "work_order_received_date"
    if h in ("tpm_confirmation", "tpm"):
        return "tpm_confirmation"
    if h in ("current_status", "status"):
        return "current_status"
    if h in ("current_location", "location"):
        return "current_location"
    if h in ("remark", "remarks"):
        return "remark"
    if h in ("total_hops", "hops"):
        return "total_hops"

    # Movement columns (if imported)
    if h == "vehicle_id":
        return "vehicle_id"
    if h in ("hop_sequence", "hop_seq", "hop"):
        return "hop_sequence"
    if h in ("source_location", "source", "from_location"):
        return "source_location"
    if h in ("destination_location", "destination", "to_location"):
        return "destination_location"
    if h in ("dispatch_date", "dispatch"):
        return "dispatch_date"
    if h in ("arrival_date", "arrival"):
        return "arrival_date"
    if h in ("dc_number", "dc_no"):
        return "dc_number"
    if h in ("movement_purpose", "purpose"):
        return "movement_purpose"

    # Legacy 25-column mapping for auto-conversion
    if "BOSCH" in h_upper and ("IDENTIFICATION" in h_upper or "VIN" in h_upper) and "DC" not in h_upper:
        return "bosch_vin"
    if "OEM IDENTIFICATION" in h_upper or "OEM ID" in h_upper:
        return "oem_id"
    if "MATERIAL COME" in h_upper:
        return "vehicle_material"
    if "PROBLEM" in h_upper or "ISSUES" in h_upper:
        return "vehicle_issues"

    # Legacy hop fields for auto-conversion
    if "RECEIVING LOCATION" in h_upper:
        return "legacy_receiving_location"
    if "INCOMING DATE2" in h_upper:
        return "legacy_incoming_date2"
    if "INCOMING DATE" in h_upper:
        return "legacy_incoming_date"
    if "OUTGOING LOCATION" in h_upper:
        return "legacy_outgoing_location"
    if "OUTGOING DATE" in h_upper:
        return "legacy_outgoing_date"
    if "SENT TO CUSTOMER" in h_upper:
        return "legacy_date_sent_to_customer"
    if "BOSCH" in h_upper and "DC-1" in h_upper:
        return "legacy_bosch_dc1"
    if "BOSCH" in h_upper and "DC-2" in h_upper:
        return "legacy_bosch_dc2"

    return None

def import_excel_file(file_path, mode='upsert'):
    """
    Universal importer supporting:
    1. New multi-sheet format ('vehicles' and 'vehicle_movements')
    2. Single-sheet format with normalized lowercase_with_underscore headers
    3. Legacy 25-column format with automatic conversion to 2-table schema
    """
    created_count = 0
    updated_count = 0
    total_processed = 0

    if mode == 'overwrite':
        VehicleMovement.query.delete()
        Vehicle.query.delete()
        db.session.commit()

    if file_path.endswith('.csv'):
        # CSV is single sheet
        df = pd.read_csv(file_path, dtype=str).fillna('')
        res = _import_single_sheet_or_legacy(df)
        created_count += res['created']
        updated_count += res['updated']
        total_processed += res['total_processed']
    else:
        with pd.ExcelFile(file_path) as excel_file:
            sheet_names = [s.strip().lower() for s in excel_file.sheet_names]

            if 'vehicles' in sheet_names:
                # Normalized Multi-Sheet Format
                sheet_map = {s.strip().lower(): s for s in excel_file.sheet_names}
                df_vehicles = pd.read_excel(excel_file, sheet_name=sheet_map['vehicles'], dtype=str).fillna('')
                res_v = _import_vehicles_sheet(df_vehicles)
                created_count += res_v['created']
                updated_count += res_v['updated']
                total_processed += res_v['total_processed']

                if 'vehicle_movements' in sheet_names:
                    df_movements = pd.read_excel(excel_file, sheet_name=sheet_map['vehicle_movements'], dtype=str).fillna('')
                    _import_movements_sheet(df_movements)
            else:
                # First/Active Sheet (Check if legacy or normalized)
                df = pd.read_excel(excel_file, sheet_name=0, dtype=str).fillna('')
                res = _import_single_sheet_or_legacy(df)
                created_count += res['created']
                updated_count += res['updated']
                total_processed += res['total_processed']

    db.session.commit()
    return {
        'created': created_count,
        'updated': updated_count,
        'total_processed': total_processed
    }

def _import_single_sheet_or_legacy(df):
    """Handle a single tabular sheet, auto-converting legacy columns if present."""
    col_mapping = {}
    is_legacy = False

    for col in df.columns:
        mapped = map_column_name(col)
        if mapped:
            col_mapping[col] = mapped
            if mapped.startswith('legacy_'):
                is_legacy = True

    created_count = 0
    updated_count = 0

    for idx, row in df.iterrows():
        data = {col_mapping[c]: str(row[c]).strip() for c in df.columns if c in col_mapping}
        bosch_vin = data.get('bosch_vin')
        if not bosch_vin:
            continue

        vehicle = Vehicle.query.filter_by(bosch_vin=bosch_vin).first()
        is_new = False
        if not vehicle:
            vehicle = Vehicle(bosch_vin=bosch_vin)
            db.session.add(vehicle)
            is_new = True

        # Assign Vehicle Details
        _assign_vehicle_fields(vehicle, data, idx + 1)
        db.session.flush()

        # Handle Hops: If legacy, auto-convert into structured movements
        if is_legacy:
            _auto_convert_legacy_hops(vehicle, data, is_new)
        else:
            # If new normalized sheet without movements sheet, ensure at least Genesis Hop #1
            if is_new or len(vehicle.movements) == 0:
                _ensure_genesis_hop(vehicle, data)

        vehicle.update_from_latest_hop()

        if is_new:
            created_count += 1
        else:
            updated_count += 1

    return {
        'created': created_count,
        'updated': updated_count,
        'total_processed': len(df)
    }

def _import_vehicles_sheet(df):
    """Import records from normalized 'vehicles' sheet."""
    col_mapping = {}
    for col in df.columns:
        mapped = map_column_name(col)
        if mapped:
            col_mapping[col] = mapped

    created_count = 0
    updated_count = 0

    for idx, row in df.iterrows():
        data = {col_mapping[c]: str(row[c]).strip() for c in df.columns if c in col_mapping}
        bosch_vin = data.get('bosch_vin')
        if not bosch_vin:
            continue

        vehicle = Vehicle.query.filter_by(bosch_vin=bosch_vin).first()
        is_new = False
        if not vehicle:
            vehicle = Vehicle(bosch_vin=bosch_vin)
            db.session.add(vehicle)
            is_new = True

        _assign_vehicle_fields(vehicle, data, idx + 1)
        db.session.flush()

        if is_new and len(vehicle.movements) == 0:
            _ensure_genesis_hop(vehicle, data)

        vehicle.update_from_latest_hop()

        if is_new:
            created_count += 1
        else:
            updated_count += 1

    return {
        'created': created_count,
        'updated': updated_count,
        'total_processed': len(df)
    }

def _import_movements_sheet(df):
    """Import and upsert records from normalized 'vehicle_movements' sheet."""
    col_mapping = {}
    for col in df.columns:
        mapped = map_column_name(col)
        if mapped:
            col_mapping[col] = mapped

    for _, row in df.iterrows():
        data = {col_mapping[c]: str(row[c]).strip() for c in df.columns if c in col_mapping}

        vehicle_id = None
        if 'vehicle_id' in data and data['vehicle_id'].isdigit():
            vehicle_id = int(data['vehicle_id'])
        elif 'bosch_vin' in data and data['bosch_vin']:
            v = Vehicle.query.filter_by(bosch_vin=data['bosch_vin']).first()
            if v:
                vehicle_id = v.id

        if not vehicle_id:
            continue

        hop_seq = int(data.get('hop_sequence', 1)) if str(data.get('hop_sequence', '')).isdigit() else 1

        existing_hop = VehicleMovement.query.filter_by(vehicle_id=vehicle_id, hop_sequence=hop_seq).first()
        if not existing_hop:
            existing_hop = VehicleMovement(vehicle_id=vehicle_id, hop_sequence=hop_seq)
            db.session.add(existing_hop)

        existing_hop.source_location = data.get('source_location') or 'BOSCH PLANT'
        existing_hop.destination_location = data.get('destination_location') or 'BOSCH PLANT'
        existing_hop.dispatch_date = data.get('dispatch_date')
        existing_hop.arrival_date = data.get('arrival_date')
        existing_hop.dc_number = data.get('dc_number')
        existing_hop.movement_purpose = data.get('movement_purpose', 'Transit')
        existing_hop.status = data.get('status', 'At Location')
        existing_hop.remarks = data.get('remarks') or data.get('work_done')

        v = db.session.get(Vehicle, vehicle_id)
        if v:
            v.update_from_latest_hop()

def _assign_vehicle_fields(vehicle, data, fallback_sr_no=1):
    """Assign fields from dictionary to Vehicle model using new normalized schema."""
    sr_no_val = data.get('sr_no')
    if sr_no_val and str(sr_no_val).isdigit():
        vehicle.sr_no = int(sr_no_val)
    elif not vehicle.sr_no:
        vehicle.sr_no = fallback_sr_no

    vehicle.oem_id = data.get('oem_id', vehicle.oem_id or '')
    vehicle.oem = data.get('oem', vehicle.oem or 'Unknown')
    vehicle.vehicle_name = data.get('vehicle_name', vehicle.vehicle_name or 'Unknown')
    vehicle.type = data.get('type', vehicle.type or 'PP')
    vehicle.owner = data.get('owner', vehicle.owner or '')
    vehicle.chassis_no = data.get('chassis_no', vehicle.chassis_no or '')
    vehicle.vehicle_material = data.get('vehicle_material', vehicle.vehicle_material or '')
    vehicle.spare_parts_link = data.get('spare_parts_link', vehicle.spare_parts_link or '')
    vehicle.pdi_status = data.get('pdi_status', vehicle.pdi_status or '')
    vehicle.vehicle_issues = data.get('vehicle_issues', vehicle.vehicle_issues or '')
    vehicle.work_order_received_date = data.get('work_order_received_date', vehicle.work_order_received_date or '')
    vehicle.tpm_confirmation = data.get('tpm_confirmation', vehicle.tpm_confirmation or '')
    vehicle.current_status = data.get('current_status', vehicle.current_status or 'Active')
    vehicle.remark = data.get('remark', vehicle.remark or '')

    if 'current_location' in data and data['current_location']:
        vehicle.current_location = data['current_location']
    elif not vehicle.current_location:
        vehicle.current_location = 'BOSCH PLANT'

def _auto_convert_legacy_hops(vehicle, data, is_new):
    """
    Auto-converts legacy 25-column format into discrete VehicleMovement records:
    Hop 1: RECEIVING LOCATION + INCOMING DATE (Genesis Hop)
    Hop 2: OUTGOING LOCATION + OUTGOING DATE (with BOSCH DC-1 / DC-2)
    Hop 3: INCOMING DATE2 (Return to facility)
    Hop 4: Date sent to customer (Customer dispatch)
    """
    if not is_new and len(vehicle.movements) > 0:
        return  # Existing movements preserved

    hop_seq = 1
    start_loc = data.get('legacy_receiving_location') or vehicle.current_location or 'BOSCH PLANT'
    start_date = data.get('legacy_incoming_date') or 'N/A'
    dc1 = data.get('legacy_bosch_dc1', '')
    dc2 = data.get('legacy_bosch_dc2', '')

    # Hop 1: Genesis Hop
    hop1 = VehicleMovement(
        vehicle_id=vehicle.id,
        hop_sequence=hop_seq,
        source_location='OEM / Inbound Transit',
        destination_location=start_loc,
        arrival_date=start_date,
        dc_number=dc1,
        movement_purpose='Initial Receipt & Check-in',
        status='Received',
        remarks='Genesis hop synthesized from legacy master data'
    )
    db.session.add(hop1)
    hop_seq += 1
    vehicle.current_location = start_loc

    # Hop 2: Outgoing Transfer (if outgoing location provided)
    out_loc = data.get('legacy_outgoing_location')
    out_date = data.get('legacy_outgoing_date')
    if out_loc and out_loc.upper() not in ('NA', '', 'NONE'):
        hop2 = VehicleMovement(
            vehicle_id=vehicle.id,
            hop_sequence=hop_seq,
            source_location=start_loc,
            destination_location=out_loc,
            dispatch_date=out_date or '',
            arrival_date=out_date or '',
            dc_number=dc2 or dc1,
            movement_purpose='Dispatched for Testing / OEM Return',
            status='Dispatched',
            remarks='Outgoing transfer synthesized from legacy master data'
        )
        db.session.add(hop2)
        hop_seq += 1
        vehicle.current_location = out_loc

    # Hop 3: Return Cycle (if incoming_date2 provided)
    in_date2 = data.get('legacy_incoming_date2')
    if in_date2 and in_date2.upper() not in ('NA', '', 'NONE'):
        hop3 = VehicleMovement(
            vehicle_id=vehicle.id,
            hop_sequence=hop_seq,
            source_location=out_loc or 'External Location',
            destination_location=start_loc,
            arrival_date=in_date2,
            dc_number=dc2,
            movement_purpose='Re-entry for evaluation',
            status='Received Back',
            remarks='Second incoming cycle synthesized from legacy master data'
        )
        db.session.add(hop3)
        hop_seq += 1
        vehicle.current_location = start_loc

    # Hop 4: Customer Return (if date_sent_to_customer provided)
    customer_date = data.get('legacy_date_sent_to_customer')
    if customer_date and customer_date.upper() not in ('NA', '', 'NONE'):
        hop4 = VehicleMovement(
            vehicle_id=vehicle.id,
            hop_sequence=hop_seq,
            source_location=vehicle.current_location,
            destination_location=vehicle.oem or 'Customer / OEM',
            dispatch_date=customer_date,
            arrival_date=customer_date,
            movement_purpose='Dispatched to Customer',
            status='Delivered to Customer',
            remarks='Customer dispatch synthesized from legacy master data'
        )
        db.session.add(hop4)
        vehicle.current_location = vehicle.oem or 'Customer / OEM'

def _ensure_genesis_hop(vehicle, data):
    """Creates a basic Hop #1 for new vehicles without existing movements."""
    start_loc = vehicle.current_location or 'BOSCH PLANT'
    hop1 = VehicleMovement(
        vehicle_id=vehicle.id,
        hop_sequence=1,
        source_location='OEM / Factory',
        destination_location=start_loc,
        arrival_date=datetime.now().strftime('%d-%b-%y'),
        movement_purpose='Genesis Initial Receipt',
        status='Received',
        remarks='Initial check-in hop'
    )
    db.session.add(hop1)
    vehicle.current_location = start_loc

def export_to_excel(export_filepath):
    """
    Exports both tables into separate sheets in an Excel workbook:
    Sheet 1: 'vehicles' (All vehicle specifications in lowercase_with_underscore)
    Sheet 2: 'vehicle_movements' (All hop entries in lowercase_with_underscore)
    """
    wb = openpyxl.Workbook()

    # Sheet 1: vehicles
    ws_v = wb.active
    ws_v.title = "vehicles"

    # Styling definitions
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    cell_font = Font(name="Calibri", size=10)
    v_header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    m_header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    
    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Write vehicles header
    for col_idx, col_name in enumerate(VEHICLES_COLUMNS, 1):
        cell = ws_v.cell(row=1, column=col_idx, value=col_name)
        cell.fill = v_header_fill
        cell.font = header_font
        cell.alignment = center_align

    vehicles = Vehicle.query.order_by(Vehicle.id.asc()).all()

    for row_idx, v in enumerate(vehicles, 2):
        row_data = [
            v.sr_no or (row_idx - 1),
            v.bosch_vin or '',
            v.oem_id or '',
            v.oem or '',
            v.vehicle_name or '',
            v.type or '',
            v.owner or '',
            v.chassis_no or '',
            v.vehicle_material or '',
            v.spare_parts_link or '',
            v.pdi_status or '',
            v.vehicle_issues or '',
            v.work_order_received_date or '',
            v.tpm_confirmation or '',
            v.current_status or 'Active',
            v.current_location or 'BOSCH PLANT',
            v.remark or '',
            v.total_hops or len(v.movements),
            v.updated_at.strftime('%Y-%m-%d %H:%M:%S') if v.updated_at else ''
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws_v.cell(row=row_idx, column=col_idx, value=val)
            cell.font = cell_font
            cell.border = border_thin
            cell.alignment = center_align if col_idx in (1, 2, 3, 4, 6, 8, 11, 14, 15, 18, 19) else left_align

    # Sheet 2: vehicle_movements
    ws_m = wb.create_sheet(title="vehicle_movements")

    for col_idx, col_name in enumerate(MOVEMENTS_COLUMNS, 1):
        cell = ws_m.cell(row=1, column=col_idx, value=col_name)
        cell.fill = m_header_fill
        cell.font = header_font
        cell.alignment = center_align

    movements = VehicleMovement.query.order_by(
        VehicleMovement.vehicle_id.asc(),
        VehicleMovement.hop_sequence.asc()
    ).all()

    for row_idx, m in enumerate(movements, 2):
        row_data = [
            m.id,
            m.vehicle_id,
            m.vehicle.bosch_vin if m.vehicle else '',
            m.hop_sequence,
            m.source_location or '',
            m.destination_location or '',
            m.dispatch_date or '',
            m.arrival_date or '',
            m.dc_number or '',
            m.movement_purpose or '',
            m.status or '',
            m.remarks or m.work_done or '',
            m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else ''
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws_m.cell(row=row_idx, column=col_idx, value=val)
            cell.font = cell_font
            cell.border = border_thin
            cell.alignment = center_align if col_idx in (1, 2, 3, 4, 7, 8, 9, 11, 13) else left_align

    # Auto-fit column widths
    for sheet in (ws_v, ws_m):
        for col in sheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    os.makedirs(os.path.dirname(export_filepath), exist_ok=True)
    wb.save(export_filepath)
    return export_filepath
