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
    oem = request.args.get('oem', 'ALL')
    location = request.args.get('location', 'ALL')
    status = request.args.get('status', 'ALL')

    vehicles = search_vehicles(query=q, oem=oem, location=location, status=status)
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
        selected_oem=oem,
        selected_location=location,
        selected_status=status
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

@tracking_bp.route('/vehicle/<int:vehicle_id>')
def detail(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    known_locations = get_distinct_locations()
    return render_template(
        'tracking/detail.html',
        vehicle=vehicle,
        movements=vehicle.movements,
        known_locations=known_locations
    )

@tracking_bp.route('/vehicle/<int:vehicle_id>/log-hop', methods=['POST'])
def log_hop(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
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
        return redirect(url_for('tracking.detail', vehicle_id=vehicle.id))

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
