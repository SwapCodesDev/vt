from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from app.models import db, Vehicle, VehicleMovement
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
    total_hops = VehicleMovement.query.count()
    problem_count = Vehicle.query.filter(
        Vehicle.vehicle_issues.isnot(None),
        Vehicle.vehicle_issues != '',
        Vehicle.vehicle_issues != 'NA',
        Vehicle.vehicle_issues != 'None'
    ).count()
    recent_vehicles = Vehicle.query.order_by(Vehicle.updated_at.desc()).limit(6).all()
    
    return render_template(
        'main/index.html',
        total_vehicles=total_vehicles,
        locations=locations,
        total_hops=total_hops,
        problem_count=problem_count,
        recent_vehicles=recent_vehicles
    )

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        software_theme = request.form.get('software_theme', 'light').strip()
        dashboard_theme = request.form.get('dashboard_theme', 'dark').strip()
        
        if software_theme not in ('light', 'dark'):
            software_theme = 'light'
        if dashboard_theme not in ('light', 'dark'):
            dashboard_theme = 'dark'
            
        flash('Theme preferences saved successfully!', 'success')
        resp = make_response(redirect(url_for('main.settings')))
        resp.set_cookie('software_theme', software_theme, max_age=60*60*24*365, samesite='Lax')
        resp.set_cookie('dashboard_theme', dashboard_theme, max_age=60*60*24*365, samesite='Lax')
        return resp
        
    software_theme = request.cookies.get('software_theme', 'light')
    dashboard_theme = request.cookies.get('dashboard_theme', 'dark')
    return render_template(
        'main/settings.html',
        software_theme=software_theme,
        dashboard_theme=dashboard_theme
    )
