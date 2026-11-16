import os
from datetime import datetime, timezone
from sqlalchemy import func
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from werkzeug.utils import secure_filename
from app.models import db, Vehicle, VehicleMovement
from app.services.excel_service import import_excel_file, export_to_excel
from app.services.tracking_service import get_distinct_locations, get_distinct_oems, add_movement_hop

data_manager_bp = Blueprint('data_manager', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@data_manager_bp.route('/')
def index():
    tab = request.args.get('tab', 'vehicles').lower()
    vehicles = Vehicle.query.order_by(Vehicle.id.asc()).all()
    movements = VehicleMovement.query.order_by(
        VehicleMovement.vehicle_id.asc(),
        VehicleMovement.hop_sequence.asc()
    ).all()

    return render_template(
        'data_manager/index.html',
        vehicles=vehicles,
        movements=movements,
        total_vehicles=len(vehicles),
        total_movements=len(movements),
        active_tab=tab
    )

@data_manager_bp.route('/import', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part in upload request.', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'warning')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            saved_filename = f"{timestamp}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)
            file.save(upload_path)

            mode = request.form.get('import_mode', 'upsert')
            try:
                result = import_excel_file(upload_path, mode=mode)
                flash(
                    f"Import successful! Processed {result['total_processed']} rows: "
                    f"{result['created']} vehicles created, {result['updated']} updated with multi-hop records.",
                    'success'
                )
                return redirect(url_for('data_manager.index'))
            except Exception as e:
                flash(f"Error parsing file: {str(e)}", 'danger')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload .xlsx, .xls, or .csv.', 'danger')

    return render_template('data_manager/import.html')

@data_manager_bp.route('/export')
def export_data():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Master_Vehicle_Data_{timestamp}.xlsx"
    export_path = os.path.join(current_app.config['EXPORT_FOLDER'], filename)
    
    try:
        export_to_excel(export_path)
        return send_file(
            export_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f"Error generating Excel export: {str(e)}", 'danger')
        return redirect(url_for('data_manager.index'))

@data_manager_bp.route('/add', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        bosch_vin = request.form.get('bosch_vin', '').strip()
        oem = request.form.get('oem', '').strip()
        vehicle_name = request.form.get('vehicle_name', '').strip()

        if not bosch_vin or not oem or not vehicle_name:
            flash('Bosch VIN, OEM, and Vehicle Name are required.', 'danger')
            return redirect(request.url)

        existing = Vehicle.query.filter(Vehicle.bosch_vin.ilike(bosch_vin)).first()
        if existing:
            flash(f'Vehicle with Bosch VIN "{bosch_vin}" already exists.', 'warning')
            return redirect(request.url)

        try:
            # Auto-assign sequence number
            max_sr = db.session.query(func.max(Vehicle.sr_no)).scalar() or 0
            sr_no_val = request.form.get('sr_no', '').strip()
            assigned_sr = int(sr_no_val) if sr_no_val.isdigit() else (max_sr + 1)

            # Genesis Start Point Details (Initial Hop)
            start_location = request.form.get('start_location', '').strip() or \
                             request.form.get('receiving_location', '').strip() or 'BOSCH PLANT'
            start_date = request.form.get('start_date', '').strip() or \
                         request.form.get('incoming_date', '').strip() or datetime.now().strftime('%d-%b-%y')
            initial_dc = request.form.get('initial_dc_number', '').strip() or request.form.get('bosch_dc1', '').strip()
            initial_remarks = request.form.get('initial_remarks', '').strip() or 'Genesis check-in hop'

            v = Vehicle(
                sr_no=assigned_sr,
                bosch_vin=bosch_vin,
                oem_id=request.form.get('oem_id', '').strip() or request.form.get('oem_id_no', '').strip(),
                oem=oem,
                vehicle_name=vehicle_name,
                type=request.form.get('type', '').strip() or request.form.get('vehicle_type', 'PP').strip(),
                owner=request.form.get('owner', '').strip(),
                chassis_no=request.form.get('chassis_no', '').strip(),
                vehicle_material=request.form.get('vehicle_material', '').strip() or request.form.get('material_with_vehicle', '').strip(),
                spare_parts_link=request.form.get('spare_parts_link', '').strip(),
                pdi_status=request.form.get('pdi_status', '').strip(),
                vehicle_issues=request.form.get('vehicle_issues', '').strip() or request.form.get('vehicle_problem_issues', '').strip(),
                work_order_received_date=request.form.get('work_order_received_date', '').strip(),
                tpm_confirmation=request.form.get('tpm_confirmation', '').strip(),
                current_status=request.form.get('current_status', 'RECEIVED').strip(),
                current_location=start_location,
                remark=request.form.get('remark', '').strip()
            )
            db.session.add(v)
            db.session.flush()

            # Automatically log Hop #1 in vehicle_movements (Genesis start point)
            hop1 = VehicleMovement(
                vehicle_id=v.id,
                hop_sequence=1,
                source_location=f"{v.oem} Factory",
                destination_location=start_location,
                arrival_date=start_date,
                dc_number=initial_dc,
                movement_purpose='Genesis Initial Receipt',
                status=v.current_status or 'Received',
                remarks=initial_remarks
            )
            db.session.add(hop1)
            v.update_from_latest_hop()
            db.session.commit()

            flash(f'Vehicle {v.bosch_vin} successfully created with Genesis Hop #1 at {start_location}!', 'success')
            return redirect(url_for('data_manager.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating vehicle: {str(e)}', 'danger')

    known_locations = get_distinct_locations()
    known_oems = get_distinct_oems()
    today_date = datetime.now().strftime('%d-%b-%y')
    return render_template(
        'data_manager/edit.html',
        vehicle=None,
        is_new=True,
        known_locations=known_locations,
        known_oems=known_oems,
        today_date=today_date
    )

@data_manager_bp.route('/edit/<int:vehicle_id>', methods=['GET', 'POST'])
def edit_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if request.method == 'POST':
        try:
            sr_no_val = request.form.get('sr_no', '').strip()
            if sr_no_val.isdigit():
                vehicle.sr_no = int(sr_no_val)

            vehicle.oem = request.form.get('oem', '').strip()
            vehicle.vehicle_name = request.form.get('vehicle_name', '').strip()
            vehicle.oem_id = request.form.get('oem_id', '').strip() or request.form.get('oem_id_no', '').strip()
            vehicle.type = request.form.get('type', '').strip() or request.form.get('vehicle_type', '').strip()
            vehicle.owner = request.form.get('owner', '').strip()
            vehicle.chassis_no = request.form.get('chassis_no', '').strip()
            vehicle.vehicle_material = request.form.get('vehicle_material', '').strip() or request.form.get('material_with_vehicle', '').strip()
            vehicle.spare_parts_link = request.form.get('spare_parts_link', '').strip()
            vehicle.pdi_status = request.form.get('pdi_status', '').strip()
            vehicle.vehicle_issues = request.form.get('vehicle_issues', '').strip() or request.form.get('vehicle_problem_issues', '').strip()
            vehicle.work_order_received_date = request.form.get('work_order_received_date', '').strip()
            vehicle.tpm_confirmation = request.form.get('tpm_confirmation', '').strip()
            vehicle.current_status = request.form.get('current_status', '').strip()
            
            # If current_location passed explicitly, update it
            custom_loc = request.form.get('current_location', '').strip()
            if custom_loc:
                vehicle.current_location = custom_loc

            vehicle.remark = request.form.get('remark', '').strip()
            vehicle.updated_at = datetime.now(timezone.utc)

            db.session.commit()
            flash(f'Vehicle {vehicle.bosch_vin} successfully updated in SQLite database!', 'success')
            return redirect(url_for('data_manager.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating vehicle: {str(e)}', 'danger')

    known_locations = get_distinct_locations()
    known_oems = get_distinct_oems()
    return render_template(
        'data_manager/edit.html',
        vehicle=vehicle,
        is_new=False,
        known_locations=known_locations,
        known_oems=known_oems
    )

@data_manager_bp.route('/delete/<int:vehicle_id>', methods=['POST'])
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    vin = vehicle.bosch_vin
    db.session.delete(vehicle)
    db.session.commit()
    flash(f'Vehicle {vin} and all its associated movement hops have been deleted from SQLite.', 'info')
    return redirect(url_for('data_manager.index'))
