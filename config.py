import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bosch-vehicle-tracking-secret-key-2026')
    
    # SQLite Database Configuration
    DATA_DIR = os.path.join(basedir, 'data')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(DATA_DIR, 'vehicle_tracking.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Storage Folders
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    EXPORT_FOLDER = os.path.join(DATA_DIR, 'exports')
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB maximum file upload
    
    # Dashboard Streaming Configuration
    DASHBOARD_REFRESH_INTERVAL_SEC = 10
