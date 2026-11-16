import os
from flask import Flask
from config import Config
from .models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure storage directories exist
    os.makedirs(app.config['DATA_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from .blueprints.main.routes import main_bp
    from .blueprints.tracking.routes import tracking_bp
    from .blueprints.data_manager.routes import data_manager_bp
    from .blueprints.dashboard.routes import dashboard_bp
    from .blueprints.api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(tracking_bp, url_prefix='/tracking')
    app.register_blueprint(data_manager_bp, url_prefix='/data-manager')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Register Jinja context processors / filters
    def format_short_number(val):
        if val is None:
            return '0'
        try:
            num = float(val)
        except (ValueError, TypeError):
            return str(val)
        
        abs_num = abs(num)
        if abs_num >= 1_000_000_000:
            formatted = f"{num / 1_000_000_000:.1f}B"
            return formatted.replace('.0B', 'B')
        if abs_num >= 1_000_000:
            formatted = f"{num / 1_000_000:.1f}M"
            return formatted.replace('.0M', 'M')
        if abs_num >= 1_000:
            formatted = f"{num / 1_000:.1f}k"
            return formatted.replace('.0k', 'k')
        if num.is_integer():
            return str(int(num))
        return str(num)

    app.jinja_env.filters['short_num'] = format_short_number

    @app.context_processor
    def inject_globals():
        software_theme = 'light'
        dashboard_theme = 'dark'
        try:
            from flask import request
            if request:
                software_theme = request.cookies.get('software_theme', 'light')
                dashboard_theme = request.cookies.get('dashboard_theme', 'dark')
        except Exception:
            pass

        return {
            'app_title': 'Bosch Vehicle Tracking & Live Telemetry',
            'format_short_number': format_short_number,
            'software_theme': software_theme,
            'dashboard_theme': dashboard_theme
        }

    # Auto-create database tables
    with app.app_context():
        db.create_all()

    return app
