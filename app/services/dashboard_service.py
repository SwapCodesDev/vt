from datetime import datetime
from sqlalchemy import func
from app.models import db, Vehicle, VehicleMovement
from .tracking_service import get_location_counts

def get_dashboard_telemetry():
    """
    Assembles comprehensive live telemetry data for the 24/7 Kiosk & Streamed Dashboard.
    """
    total_vehicles = Vehicle.query.count()
    total_hops = VehicleMovement.query.count()
    
    # Location Breakdown
    location_counts = get_location_counts()
    sorted_locations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)
    
    # OEM Breakdown
    oem_results = db.session.query(
        Vehicle.oem, 
        func.count(Vehicle.id)
    ).group_by(Vehicle.oem).all()
    oem_distribution = [{'oem': r[0], 'count': r[1]} for r in oem_results if r[0]]
    
    # Status Breakdown
    status_results = db.session.query(
        Vehicle.current_status,
        func.count(Vehicle.id)
    ).group_by(Vehicle.current_status).all()
    status_distribution = [{'status': r[0] or 'Active', 'count': r[1]} for r in status_results]
    
    # Vehicles with Problems or Issues
    problem_vehicles = Vehicle.query.filter(
        Vehicle.vehicle_problem_issues != None,
        Vehicle.vehicle_problem_issues != '',
        Vehicle.vehicle_problem_issues != 'NA',
        Vehicle.vehicle_problem_issues != 'None'
    ).all()
    
    # Recent Movement Hops (latest 20 across fleet)
    recent_hops = VehicleMovement.query.order_by(
        VehicleMovement.id.desc()
    ).limit(20).all()
    
    # Vehicles summary for the live display table & roadmap
    vehicles = Vehicle.query.order_by(Vehicle.id.asc()).all()
    vehicle_rows = [v.to_dict(include_movements=True) for v in vehicles]
    
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_vehicles': total_vehicles,
        'total_hops': total_hops,
        'location_breakdown': [{'location': k, 'count': v} for k, v in sorted_locations],
        'oem_distribution': oem_distribution,
        'status_distribution': status_distribution,
        'problem_count': len(problem_vehicles),
        'problem_vehicles': [
            {
                'id': v.id,
                'bosch_vin': v.bosch_vin,
                'vehicle_name': v.vehicle_name,
                'location': v.current_location,
                'issue': v.vehicle_problem_issues,
                'tpm': v.tpm_confirmation or 'Pending'
            } for v in problem_vehicles
        ],
        'recent_movements': [
            {
                'id': m.id,
                'vehicle_id': m.vehicle_id,
                'vin': m.vehicle.bosch_vin if m.vehicle else 'N/A',
                'name': m.vehicle.vehicle_name if m.vehicle else '',
                'oem': m.vehicle.oem if m.vehicle else '',
                'hop': m.hop_sequence,
                'from': m.source_location,
                'to': m.destination_location,
                'date': m.arrival_date or m.dispatch_date or '',
                'purpose': m.movement_purpose or 'Transit',
                'work_done': m.work_done or '',
                'dc_number': m.dc_number or '',
                'status': m.status or 'Completed'
            } for m in recent_hops
        ],
        'vehicles': vehicle_rows
    }
