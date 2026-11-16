from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Vehicle, VehicleMovement
from app.services.tracking_service import (
    search_vehicles, 
    get_vehicle_by_identifier, 
    add_movement_hop,
    get_distinct_locations,
    get_distinct_oems,
    get_location_counts
)

tracking_bp = Blueprint('tracking', __name__)

@tracking_bp.route('/')
def list_vehicles():
    q = request.args.get('q', '').strip()
    
    # Collect multiselect or single filter parameters
    raw_oems = request.args.getlist('oem')
    raw_locations = request.args.getlist('location')
    raw_statuses = request.args.getlist('status')
    
    selected_oems = []
    for item in raw_oems:
        for val in item.split(','):
            v = val.strip()
            if v and v != 'ALL' and v not in selected_oems:
                selected_oems.append(v)
                
    selected_locations = []
    for item in raw_locations:
        for val in item.split(','):
            v = val.strip()
            if v and v != 'ALL' and v not in selected_locations:
                selected_locations.append(v)
                
    selected_statuses = []
    for item in raw_statuses:
        for val in item.split(','):
            v = val.strip()
            if v and v != 'ALL' and v not in selected_statuses:
                selected_statuses.append(v)

    vehicles = search_vehicles(
        query=q,
        oems=selected_oems,
        locations=selected_locations,
        statuses=selected_statuses
    )
    locations = get_distinct_locations()
    oems = get_distinct_oems()
    loc_counts = get_location_counts()

    return render_template(
        'tracking/list.html',
        vehicles=vehicles,
        locations=locations,
        oems=oems,
        loc_counts=loc_counts,
        selected_q=q,
        selected_oems=selected_oems,
        selected_locations=selected_locations,
        selected_statuses=selected_statuses,
        selected_oem=selected_oems[0] if len(selected_oems) == 1 else ('ALL' if not selected_oems else ','.join(selected_oems)),
        selected_location=selected_locations[0] if len(selected_locations) == 1 else ('ALL' if not selected_locations else ','.join(selected_locations)),
        selected_status=selected_statuses[0] if len(selected_statuses) == 1 else ('ALL' if not selected_statuses else ','.join(selected_statuses))
    )

@tracking_bp.route('/lookup')
def lookup():
    identifier = request.args.get('identifier', '').strip()
    if not identifier:
        flash('Please enter a Bosch VIN or OEM Identification Number.', 'warning')
        return redirect(url_for('tracking.list_vehicles'))

    vehicle = get_vehicle_by_identifier(identifier)
    if vehicle:
        return redirect(url_for('tracking.detail', vehicle_id=vehicle.id))
    else:
        flash(f'No vehicle found matching identifier: "{identifier}". Showing search results instead.', 'info')
        return redirect(url_for('tracking.list_vehicles', q=identifier))

@tracking_bp.route('/vehicle/<identifier>')
@tracking_bp.route('/vehicle/<int:vehicle_id>')
def detail(identifier=None, vehicle_id=None):
    clean_id = str(vehicle_id if vehicle_id is not None else identifier).strip()
    if clean_id.isdigit():
        vehicle = db.session.get(Vehicle, int(clean_id))
    else:
        vehicle = Vehicle.query.filter(Vehicle.bosch_vin.ilike(clean_id)).first()

    if not vehicle:
        flash(f'Vehicle "{clean_id}" not found.', 'danger')
        return redirect(url_for('tracking.list_vehicles'))

    known_locations = get_distinct_locations()
    return render_template(
        'tracking/detail.html',
        vehicle=vehicle,
        movements=vehicle.movements,
        known_locations=known_locations
    )

@tracking_bp.route('/vehicle/<identifier>/log-hop', methods=['POST'])
@tracking_bp.route('/vehicle/<int:vehicle_id>/log-hop', methods=['POST'])
def log_hop(identifier=None, vehicle_id=None):
    clean_id = str(vehicle_id if vehicle_id is not None else identifier).strip()
    if clean_id.isdigit():
        vehicle = db.session.get(Vehicle, int(clean_id))
    else:
        vehicle = Vehicle.query.filter(Vehicle.bosch_vin.ilike(clean_id)).first()

    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('tracking.list_vehicles'))
    
    source = request.form.get('source_location', '').strip() or vehicle.current_location or 'BOSCH PLANT'
    destination = request.form.get('destination_location', '').strip()
    dispatch_date = request.form.get('dispatch_date', '').strip()
    arrival_date = request.form.get('arrival_date', '').strip()
    purpose = request.form.get('movement_purpose', '').strip()
    work_done = request.form.get('work_done', '').strip()
    dc_number = request.form.get('dc_number', '').strip()
    status = request.form.get('status', '').strip() or 'At Location'
    remarks = request.form.get('remarks', '').strip()

    if not destination:
        flash('Destination location is required to log a movement hop.', 'danger')
        return redirect(url_for('tracking.detail', identifier=vehicle.bosch_vin))

    try:
        hop = add_movement_hop(
            vehicle_id=vehicle.id,
            source_location=source,
            destination_location=destination,
            dispatch_date=dispatch_date,
            arrival_date=arrival_date,
            movement_purpose=purpose,
            work_done=work_done,
            dc_number=dc_number,
            status=status,
            remarks=remarks
        )
        flash(f'Successfully logged Hop #{hop.hop_sequence}: {source} -> {destination}!', 'success')
    except Exception as e:
        flash(f'Error logging movement hop: {str(e)}', 'danger')

    return redirect(url_for('tracking.detail', vehicle_id=vehicle.id))

@tracking_bp.route('/vehicle/<int:vehicle_id>/delete-hop/<int:hop_id>', methods=['POST'])
def delete_hop(vehicle_id, hop_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    hop = VehicleMovement.query.filter_by(id=hop_id, vehicle_id=vehicle.id).first_or_404()
    
    db.session.delete(hop)
    db.session.flush()
    vehicle.update_from_latest_hop()
    db.session.commit()
    
    flash('Movement hop deleted and vehicle current location updated.', 'info')
    return redirect(url_for('tracking.detail', vehicle_id=vehicle.id))
