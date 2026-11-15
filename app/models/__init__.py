from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .vehicle import Vehicle
from .movement import VehicleMovement

__all__ = ['db', 'Vehicle', 'VehicleMovement']
