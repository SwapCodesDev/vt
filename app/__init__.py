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
    @app.context_processor
    def inject_globals():
        return {
            'app_title': 'Bosch Vehicle Tracking & Live Telemetry'
        }

    # Auto-create database tables
    with app.app_context():
        db.create_all()

    return app
