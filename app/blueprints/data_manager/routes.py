import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from werkzeug.utils import secure_filename
from app.models import db, Vehicle, VehicleMovement
from app.services.excel_service import import_excel_file, export_to_excel
from app.services.tracking_service import get_distinct_locations, get_distinct_oems

data_manager_bp = Blueprint('data_manager', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@data_manager_bp.route('/')
def index():
    vehicles = Vehicle.query.order_by(Vehicle.id.asc()).all()
    return render_template(
        'data_manager/index.html',
        vehicles=vehicles,
        total_count=len(vehicles)
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
                    f"{result['created']} new vehicles added, {result['updated']} existing updated.",
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
    filename = f"Vehicle_Master_Data_Export_{timestamp}.xlsx"
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

        existing = Vehicle.query.filter_by(bosch_vin=bosch_vin).first()
        if existing:
            flash(f'Vehicle with Bosch VIN "{bosch_vin}" already exists.', 'warning')
            return redirect(request.url)

        try:
            sr_no_val = request.form.get('sr_no', '').strip()
            v = Vehicle(
                sr_no=int(sr_no_val) if sr_no_val.isdigit() else None,
                bosch_vin=bosch_vin,
                oem=oem,
                vehicle_name=vehicle_name,
                oem_id_no=request.form.get('oem_id_no', '').strip(),
                vehicle_type=request.form.get('vehicle_type', '').strip(),
                bosch_dc1=request.form.get('bosch_dc1', '').strip(),
                bosch_dc2=request.form.get('bosch_dc2', '').strip(),
                owner=request.form.get('owner', '').strip(),
                incoming_date=request.form.get('incoming_date', '').strip(),
                receiving_location=request.form.get('receiving_location', '').strip() or 'BOSCH PLANT',
                chassis_no=request.form.get('chassis_no', '').strip(),
                material_with_vehicle=request.form.get('material_with_vehicle', '').strip(),
                spare_parts_link=request.form.get('spare_parts_link', '').strip(),
                outgoing_date=request.form.get('outgoing_date', '').strip(),
                outgoing_location=request.form.get('outgoing_location', '').strip(),
                incoming_date2=request.form.get('incoming_date2', '').strip(),
                current_status=request.form.get('current_status', 'Received').strip(),
                current_location=request.form.get('current_location', '').strip() or request.form.get('receiving_location', '').strip() or 'BOSCH PLANT',
                date_sent_to_customer=request.form.get('date_sent_to_customer', '').strip(),
                pdi_status=request.form.get('pdi_status', '').strip(),
                vehicle_problem_issues=request.form.get('vehicle_problem_issues', '').strip(),
                work_order_received_date=request.form.get('work_order_received_date', '').strip(),
                tpm_confirmation=request.form.get('tpm_confirmation', '').strip(),
                remark=request.form.get('remark', '').strip()
            )
            db.session.add(v)
            db.session.flush()

            # Genesis Hop
            hop1 = VehicleMovement(
                vehicle_id=v.id,
                hop_sequence=1,
                source_location=f"{v.oem} Factory",
                destination_location=v.receiving_location,
                arrival_date=v.incoming_date or datetime.now().strftime('%d-%b-%y'),
                movement_purpose="Initial Entry into System",
                work_done="Check-in registration",
                status=v.current_status or "Received",
                remarks="Manual creation genesis hop"
            )
            db.session.add(hop1)
            v.update_from_latest_hop()
            db.session.commit()

            flash(f'Vehicle {v.bosch_vin} successfully created and saved to SQLite database!', 'success')
            return redirect(url_for('data_manager.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating vehicle: {str(e)}', 'danger')

    known_locations = get_distinct_locations()
    known_oems = get_distinct_oems()
    return render_template(
        'data_manager/edit.html',
        vehicle=None,
        is_new=True,
        known_locations=known_locations,
        known_oems=known_oems
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
            vehicle.oem_id_no = request.form.get('oem_id_no', '').strip()
            vehicle.vehicle_type = request.form.get('vehicle_type', '').strip()
            vehicle.bosch_dc1 = request.form.get('bosch_dc1', '').strip()
            vehicle.bosch_dc2 = request.form.get('bosch_dc2', '').strip()
            vehicle.owner = request.form.get('owner', '').strip()
            vehicle.incoming_date = request.form.get('incoming_date', '').strip()
            vehicle.receiving_location = request.form.get('receiving_location', '').strip()
            vehicle.chassis_no = request.form.get('chassis_no', '').strip()
            vehicle.material_with_vehicle = request.form.get('material_with_vehicle', '').strip()
            vehicle.spare_parts_link = request.form.get('spare_parts_link', '').strip()
            vehicle.outgoing_date = request.form.get('outgoing_date', '').strip()
            vehicle.outgoing_location = request.form.get('outgoing_location', '').strip()
            vehicle.incoming_date2 = request.form.get('incoming_date2', '').strip()
            vehicle.current_status = request.form.get('current_status', '').strip()
            vehicle.current_location = request.form.get('current_location', '').strip()
            vehicle.date_sent_to_customer = request.form.get('date_sent_to_customer', '').strip()
            vehicle.pdi_status = request.form.get('pdi_status', '').strip()
            vehicle.vehicle_problem_issues = request.form.get('vehicle_problem_issues', '').strip()
            vehicle.work_order_received_date = request.form.get('work_order_received_date', '').strip()
            vehicle.tpm_confirmation = request.form.get('tpm_confirmation', '').strip()
            vehicle.remark = request.form.get('remark', '').strip()

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
    try:
        db.session.delete(vehicle)
        db.session.commit()
        flash(f'Vehicle {vin} and all its movement history deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vehicle: {str(e)}', 'danger')
    return redirect(url_for('data_manager.index'))
