from flask import Blueprint, render_template, current_app
from app.services.dashboard_service import get_dashboard_telemetry

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Standard dashboard inside application shell."""
    telemetry = get_dashboard_telemetry()
    return render_template('dashboard/kiosk.html', telemetry=telemetry, is_kiosk=False)

@dashboard_bp.route('/kiosk')
@dashboard_bp.route('/tv')
def kiosk():
    """Dedicated 24/7 wall-mounted streaming monitor URL."""
    telemetry = get_dashboard_telemetry()
    return render_template(
        'dashboard/kiosk.html', 
        telemetry=telemetry, 
        is_kiosk=True,
        refresh_interval=current_app.config.get('DASHBOARD_REFRESH_INTERVAL_SEC', 10)
    )
