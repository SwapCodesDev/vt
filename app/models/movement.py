from datetime import datetime, timezone
from . import db

class VehicleMovement(db.Model):
    __tablename__ = 'vehicle_movements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False, index=True)
    hop_sequence = db.Column(db.Integer, nullable=False, default=1)
    
    source_location = db.Column(db.String(150), nullable=False)
    destination_location = db.Column(db.String(150), nullable=False)
    
    dispatch_date = db.Column(db.String(50), nullable=True)
    arrival_date = db.Column(db.String(50), nullable=True)
    
    dc_number = db.Column(db.String(100), nullable=True)
    movement_purpose = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(100), nullable=True, default='At Location')
    remarks = db.Column(db.Text, nullable=True)
    work_done = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship back to Vehicle
    vehicle = db.relationship('Vehicle', back_populates='movements')

    def __repr__(self):
        return f"<Hop #{self.hop_sequence} {self.source_location} -> {self.destination_location}>"

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'bosch_vin': self.vehicle.bosch_vin if self.vehicle else '',
            'hop_sequence': self.hop_sequence,
            'source_location': self.source_location,
            'destination_location': self.destination_location,
            'dispatch_date': self.dispatch_date or '',
            'arrival_date': self.arrival_date or '',
            'dc_number': self.dc_number or '',
            'movement_purpose': self.movement_purpose or '',
            'status': self.status or 'At Location',
            'remarks': self.remarks or self.work_done or '',
            'work_done': self.work_done or self.remarks or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }
