from datetime import datetime, timezone
from . import db

class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sr_no = db.Column(db.Integer, nullable=True)
    bosch_vin = db.Column(db.String(100), unique=True, nullable=False, index=True)
    oem = db.Column(db.String(100), nullable=False, index=True)
    vehicle_name = db.Column(db.String(150), nullable=False)
    oem_id_no = db.Column(db.String(100), nullable=True, index=True)
    vehicle_type = db.Column(db.String(50), nullable=True)  # PP, NON PP
    bosch_dc1 = db.Column(db.String(100), nullable=True)
    bosch_dc2 = db.Column(db.String(100), nullable=True)
    owner = db.Column(db.String(150), nullable=True)
    
    # Start points as specified in requirements
    incoming_date = db.Column(db.String(50), nullable=True, index=True)
    receiving_location = db.Column(db.String(150), nullable=True, index=True)
    
    chassis_no = db.Column(db.String(100), nullable=True, index=True)
    material_with_vehicle = db.Column(db.Text, nullable=True)
    spare_parts_link = db.Column(db.Text, nullable=True)
    outgoing_date = db.Column(db.String(50), nullable=True)
    outgoing_location = db.Column(db.String(150), nullable=True)
    incoming_date2 = db.Column(db.String(50), nullable=True)
    
    current_status = db.Column(db.String(100), nullable=True, default='RECEIVED', index=True)
    current_location = db.Column(db.String(150), nullable=True, index=True)
    
    date_sent_to_customer = db.Column(db.String(50), nullable=True)
    pdi_status = db.Column(db.String(100), nullable=True)
    vehicle_problem_issues = db.Column(db.Text, nullable=True)
    work_order_received_date = db.Column(db.String(50), nullable=True)
    tpm_confirmation = db.Column(db.String(100), nullable=True)
    remark = db.Column(db.Text, nullable=True)
    movement_history_summary = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # 1-to-many relationship with VehicleMovement
    movements = db.relationship(
        'VehicleMovement',
        back_populates='vehicle',
        cascade='all, delete-orphan',
        order_by='VehicleMovement.hop_sequence'
    )

    def __repr__(self):
        return f"<Vehicle {self.bosch_vin} ({self.oem} {self.vehicle_name})>"

    def update_from_latest_hop(self):
        """Re-synchronize current_location, current_status, and movement_history_summary from DB."""
        from .movement import VehicleMovement
        if not self.id:
            return

        latest = VehicleMovement.query.filter_by(vehicle_id=self.id)\
                                      .order_by(VehicleMovement.hop_sequence.desc()).first()
        if latest:
            self.current_location = latest.destination_location or self.receiving_location
            if latest.status:
                self.current_status = latest.status
            
            # Reconstruct sequence history
            all_hops = VehicleMovement.query.filter_by(vehicle_id=self.id)\
                                            .order_by(VehicleMovement.hop_sequence.asc()).all()
            hops = []
            for m in all_hops:
                hop_str = f"Hop {m.hop_sequence}: {m.source_location} -> {m.destination_location}"
                if m.arrival_date or m.dispatch_date:
                    hop_str += f" ({m.arrival_date or m.dispatch_date})"
                if m.movement_purpose:
                    hop_str += f" [{m.movement_purpose}]"
                hops.append(hop_str)
            self.movement_history_summary = " => ".join(hops)
        else:
            if not self.current_location:
                self.current_location = self.receiving_location or 'BOSCH PLANT'

    def to_dict(self, include_movements=False):
        """Serialize vehicle and its hop count for API/DataTables."""
        data = {
            'id': self.id,
            'sr_no': self.sr_no,
            'bosch_vin': self.bosch_vin,
            'oem': self.oem,
            'vehicle_name': self.vehicle_name,
            'oem_id_no': self.oem_id_no or '',
            'vehicle_type': self.vehicle_type or '',
            'bosch_dc1': self.bosch_dc1 or '',
            'bosch_dc2': self.bosch_dc2 or '',
            'owner': self.owner or '',
            'incoming_date': self.incoming_date or '',
            'receiving_location': self.receiving_location or '',
            'chassis_no': self.chassis_no or '',
            'material_with_vehicle': self.material_with_vehicle or '',
            'spare_parts_link': self.spare_parts_link or '',
            'outgoing_date': self.outgoing_date or '',
            'outgoing_location': self.outgoing_location or '',
            'incoming_date2': self.incoming_date2 or '',
            'current_status': self.current_status or 'Active',
            'current_location': self.current_location or self.receiving_location or 'Unknown',
            'date_sent_to_customer': self.date_sent_to_customer or '',
            'pdi_status': self.pdi_status or '',
            'vehicle_problem_issues': self.vehicle_problem_issues or '',
            'work_order_received_date': self.work_order_received_date or '',
            'tpm_confirmation': self.tpm_confirmation or '',
            'remark': self.remark or '',
            'movement_history_summary': self.movement_history_summary or '',
            'total_hops': len(self.movements),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        }
        if include_movements:
            data['movements'] = [m.to_dict() for m in sorted(self.movements, key=lambda x: x.hop_sequence)]
        return data
