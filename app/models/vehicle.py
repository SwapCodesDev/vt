from datetime import datetime, timezone
from . import db

class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    # Primary key & sequence
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sr_no = db.Column(db.Integer, nullable=True)

    # Identifiers
    bosch_vin = db.Column(db.String(100), unique=True, nullable=False, index=True)
    oem_id = db.Column(db.String(100), nullable=True, index=True)

    # Vehicle Specifications
    oem = db.Column(db.String(100), nullable=False, index=True)
    vehicle_name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), nullable=True)  # PP, NON PP
    owner = db.Column(db.String(150), nullable=True)
    chassis_no = db.Column(db.String(100), nullable=True, index=True)

    # Equipment & Documentation
    vehicle_material = db.Column(db.Text, nullable=True)
    spare_parts_link = db.Column(db.Text, nullable=True)
    pdi_status = db.Column(db.String(100), nullable=True)
    vehicle_issues = db.Column(db.Text, nullable=True)
    work_order_received_date = db.Column(db.String(50), nullable=True)
    tpm_confirmation = db.Column(db.String(100), nullable=True)

    # Operational Status & Derived Current Location
    current_status = db.Column(db.String(100), nullable=True, default='RECEIVED', index=True)
    current_location = db.Column(db.String(150), nullable=False, default='BOSCH PLANT', index=True)
    remark = db.Column(db.Text, nullable=True)

    # Metrics & Timestamps
    total_hops = db.Column(db.Integer, nullable=False, default=0)
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

    # Backward-compatibility property getters and setters
    @property
    def oem_id_no(self):
        return self.oem_id

    @oem_id_no.setter
    def oem_id_no(self, val):
        self.oem_id = val

    @property
    def vehicle_type(self):
        return self.type

    @vehicle_type.setter
    def vehicle_type(self, val):
        self.type = val

    @property
    def material_with_vehicle(self):
        return self.vehicle_material

    @material_with_vehicle.setter
    def material_with_vehicle(self, val):
        self.vehicle_material = val

    @property
    def vehicle_problem_issues(self):
        return self.vehicle_issues

    @vehicle_problem_issues.setter
    def vehicle_problem_issues(self, val):
        self.vehicle_issues = val

    @property
    def receiving_location(self):
        if self.movements:
            return self.movements[0].destination_location or self.movements[0].source_location
        return self.current_location or 'BOSCH PLANT'

    @property
    def incoming_date(self):
        if self.movements:
            return self.movements[0].arrival_date or self.movements[0].dispatch_date or ''
        return ''

    def update_from_latest_hop(self):
        """Re-synchronize current_location, current_status, total_hops, and updated_at from vehicle_movements."""
        from .movement import VehicleMovement
        if not self.id:
            return

        all_hops = VehicleMovement.query.filter_by(vehicle_id=self.id)\
                                        .order_by(VehicleMovement.hop_sequence.asc()).all()
        self.total_hops = len(all_hops)
        if all_hops:
            latest = all_hops[-1]
            latest_loc = latest.destination_location or self.current_location or 'BOSCH PLANT'
            self.current_location = latest_loc
            # current_status automatically reflects the latest/current location of the vehicle from vehicle_movements
            self.current_status = latest_loc
        else:
            if not self.current_location:
                self.current_location = 'BOSCH PLANT'
            if not self.current_status:
                self.current_status = self.current_location

        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self, include_movements=False):
        """Serialize vehicle with standardized lowercase_with_underscore schema."""
        data = {
            'id': self.id,
            'sr_no': self.sr_no or self.id,
            'bosch_vin': self.bosch_vin,
            'oem_id': self.oem_id or '',
            'oem': self.oem,
            'vehicle_name': self.vehicle_name,
            'type': self.type or '',
            'owner': self.owner or '',
            'chassis_no': self.chassis_no or '',
            'vehicle_material': self.vehicle_material or '',
            'spare_parts_link': self.spare_parts_link or '',
            'pdi_status': self.pdi_status or '',
            'vehicle_issues': self.vehicle_issues or '',
            'work_order_received_date': self.work_order_received_date or '',
            'tpm_confirmation': self.tpm_confirmation or '',
            'current_status': self.current_status or 'Active',
            'current_location': self.current_location or 'BOSCH PLANT',
            'remark': self.remark or '',
            'total_hops': self.total_hops if self.total_hops is not None else len(self.movements),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

        # Legacy compatibility aliases for existing templates/APIs
        data['oem_id_no'] = data['oem_id']
        data['vehicle_type'] = data['type']
        data['material_with_vehicle'] = data['vehicle_material']
        data['vehicle_problem_issues'] = data['vehicle_issues']
        data['receiving_location'] = self.receiving_location
        data['incoming_date'] = self.incoming_date

        if include_movements:
            data['movements'] = [m.to_dict() for m in sorted(self.movements, key=lambda x: x.hop_sequence)]
        return data
