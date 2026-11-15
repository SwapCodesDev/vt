from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Vehicle
from app.services.tracking_service import get_vehicle_by_identifier, get_location_counts

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    query = request.args.get('q', '').strip()
    if query:
        # Check if direct match exists
        vehicle = get_vehicle_by_identifier(query)
        if vehicle:
            return redirect(url_for('tracking.detail', vehicle_id=vehicle.id))
        else:
            return redirect(url_for('tracking.list_vehicles', q=query))
            
    total_vehicles = Vehicle.query.count()
    locations = get_location_counts()
    recent_vehicles = Vehicle.query.order_by(Vehicle.updated_at.desc()).limit(6).all()
    
    return render_template(
        'main/index.html',
        total_vehicles=total_vehicles,
        locations=locations,
        recent_vehicles=recent_vehicles
    )
