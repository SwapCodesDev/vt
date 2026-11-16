from flask import Blueprint, jsonify, request
from app.models import db, Vehicle, VehicleMovement
from app.services.dashboard_service import get_dashboard_telemetry
from app.services.tracking_service import get_distinct_locations

api_bp = Blueprint('api', __name__)

@api_bp.route('/telemetry')
def telemetry():
    """Live streaming endpoint providing real-time fleet data for the 24/7 dashboard."""
    data = get_dashboard_telemetry()
    return jsonify(data)

@api_bp.route('/suggest')
def suggest():
    """Autocomplete search for Bosch VIN, OEM ID, or vehicle name."""
    query = request.args.get('term', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
        
    term = f"%{query}%"
    vehicles = Vehicle.query.filter(
        (Vehicle.bosch_vin.ilike(term)) |
        (Vehicle.oem_id_no.ilike(term)) |
        (Vehicle.vehicle_name.ilike(term)) |
        (Vehicle.chassis_no.ilike(term))
    ).limit(10).all()
    
    results = []
    for v in vehicles:
        results.append({
            'id': v.id,
            'bosch_vin': v.bosch_vin,
            'oem_id_no': v.oem_id_no or '',
            'vehicle_name': v.vehicle_name,
            'oem': v.oem,
            'location': v.current_location,
            'label': f"{v.bosch_vin} - {v.oem} {v.vehicle_name} ({v.current_location})"
        })
    return jsonify(results)

@api_bp.route('/vehicle/<int:vehicle_id>/quick-edit', methods=['POST'])
def quick_edit(vehicle_id):
    """Allows rapid inline status or location updates from dashboard or data manager."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    payload = request.get_json(silent=True) or request.form
    
    if 'current_status' in payload:
        vehicle.current_status = payload['current_status'].strip()
    if 'current_location' in payload:
        new_loc = payload['current_location'].strip()
        if new_loc and new_loc != vehicle.current_location:
            # Also record this as a quick hop
            last_hop = VehicleMovement.query.filter_by(vehicle_id=vehicle.id).order_by(VehicleMovement.hop_sequence.desc()).first()
            next_seq = (last_hop.hop_sequence + 1) if last_hop else 1
            hop = VehicleMovement(
                vehicle_id=vehicle.id,
                hop_sequence=next_seq,
                source_location=vehicle.current_location or 'BOSCH PLANT',
                destination_location=new_loc,
                status=vehicle.current_status or 'At Location',
                movement_purpose='Quick Transfer',
                remarks='Inline update via dashboard'
            )
            db.session.add(hop)
            vehicle.current_location = new_loc
            vehicle.update_from_latest_hop()
            
    if 'remark' in payload:
        vehicle.remark = payload['remark'].strip()
        
    db.session.commit()
    return jsonify({'success': True, 'vehicle': vehicle.to_dict()})

@api_bp.route('/theme', methods=['POST'])
def set_theme():
    """Allows client-side instant theme synchronization and cookie persistence."""
    payload = request.get_json(silent=True) or request.form
    software_theme = payload.get('software_theme')
    dashboard_theme = payload.get('dashboard_theme')
    
    resp = jsonify({
        'status': 'ok',
        'software_theme': software_theme,
        'dashboard_theme': dashboard_theme
    })
    
    if software_theme in ('light', 'dark'):
        resp.set_cookie('software_theme', software_theme, max_age=60*60*24*365, samesite='Lax')
    if dashboard_theme in ('light', 'dark'):
        resp.set_cookie('dashboard_theme', dashboard_theme, max_age=60*60*24*365, samesite='Lax')
        
    return resp
