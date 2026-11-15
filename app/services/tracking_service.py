from sqlalchemy import or_, func
from app.models import db, Vehicle, VehicleMovement

def get_vehicle_by_identifier(identifier):
    """
    Search for a vehicle by exact or case-insensitive match on:
    - Bosch VIN
    - OEM Identification No
    - Chassis No
    - ID
    """
    if not identifier:
        return None
    
    clean_id = str(identifier).strip()
    
    # Check by Bosch VIN
    v = Vehicle.query.filter(func.lower(Vehicle.bosch_vin) == clean_id.lower()).first()
    if v:
        return v
    
    # Check by OEM ID
    v = Vehicle.query.filter(func.lower(Vehicle.oem_id_no) == clean_id.lower()).first()
    if v:
        return v
        
    # Check by Chassis NO
    v = Vehicle.query.filter(func.lower(Vehicle.chassis_no) == clean_id.lower()).first()
    if v:
        return v
        
    # Check by numeric primary key
    if clean_id.isdigit():
        return db.session.get(Vehicle, int(clean_id))
        
    return None

def search_vehicles(query=None, oem=None, location=None, status=None):
    """Search vehicles with multiple optional criteria."""
    q = Vehicle.query
    
    if query:
        term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Vehicle.bosch_vin.ilike(term),
                Vehicle.oem_id_no.ilike(term),
                Vehicle.vehicle_name.ilike(term),
                Vehicle.chassis_no.ilike(term),
                Vehicle.owner.ilike(term),
                Vehicle.oem.ilike(term)
            )
        )
    
    if oem and oem != 'ALL':
        q = q.filter(Vehicle.oem == oem)
        
    if location and location != 'ALL':
        q = q.filter(Vehicle.current_location == location)
        
    if status and status != 'ALL':
        q = q.filter(Vehicle.current_status == status)
        
    return q.order_by(Vehicle.id.asc()).all()

def add_movement_hop(vehicle_id, source_location, destination_location, 
                     dispatch_date=None, arrival_date=None, 
                     movement_purpose=None, work_done=None, 
                     dc_number=None, status='At Location', remarks=None):
    """
    Records a new hop in the vehicle's journey (e.g. Location A -> Location B -> OEM -> Location A).
    Updates current_location, current_status, and movement summary on the vehicle.
    """
    vehicle = db.session.get(Vehicle, vehicle_id)
    if not vehicle:
        raise ValueError(f"Vehicle with ID {vehicle_id} not found.")

    # Determine next sequence
    last_movement = VehicleMovement.query.filter_by(vehicle_id=vehicle.id)\
                                        .order_by(VehicleMovement.hop_sequence.desc()).first()
    next_seq = (last_movement.hop_sequence + 1) if last_movement else 1

    hop = VehicleMovement(
        vehicle_id=vehicle.id,
        hop_sequence=next_seq,
        source_location=source_location.strip(),
        destination_location=destination_location.strip(),
        dispatch_date=dispatch_date.strip() if dispatch_date else None,
        arrival_date=arrival_date.strip() if arrival_date else None,
        movement_purpose=movement_purpose.strip() if movement_purpose else None,
        work_done=work_done.strip() if work_done else None,
        dc_number=dc_number.strip() if dc_number else None,
        status=status.strip() if status else 'At Location',
        remarks=remarks.strip() if remarks else None
    )
    db.session.add(hop)
    db.session.flush()

    # Update vehicle's live current location and status
    vehicle.current_location = destination_location.strip()
    if status:
        vehicle.current_status = status.strip()
        
    # If sent to customer/OEM, track customer dispatch date
    if 'OEM' in destination_location.upper() or 'CUSTOMER' in destination_location.upper():
        if dispatch_date:
            vehicle.date_sent_to_customer = dispatch_date
            
    vehicle.update_from_latest_hop()
    db.session.commit()
    return hop

def get_location_counts():
    """Return dictionary of {location_name: vehicle_count}."""
    results = db.session.query(
        Vehicle.current_location,
        func.count(Vehicle.id)
    ).group_by(Vehicle.current_location).all()
    
    counts = {}
    for loc, count in results:
        key = loc if loc else 'UNASSIGNED'
        counts[key] = count
    return counts

def get_distinct_locations():
    """Returns a sorted list of all unique locations recorded across vehicles and movements."""
    locs = set()
    # From vehicle fields
    for v in Vehicle.query.with_entities(Vehicle.receiving_location, Vehicle.outgoing_location, Vehicle.current_location).all():
        for l in v:
            if l and l.strip() and l.strip().upper() != 'NA':
                locs.add(l.strip())
    # From movements
    for m in VehicleMovement.query.with_entities(VehicleMovement.source_location, VehicleMovement.destination_location).all():
        for l in m:
            if l and l.strip():
                locs.add(l.strip())
    
    defaults = ['BOSCH PLANT', 'TATA MOTORS', 'NATRAX', 'MG, GUJRAT', 'MARUTI SUZUKI', 'ASHOK LEYLAND', 'WORKSHOP']
    for d in defaults:
        locs.add(d)
        
    return sorted(list(locs))

def get_distinct_oems():
    """Returns sorted list of distinct OEMs."""
    results = db.session.query(Vehicle.oem).distinct().all()
    oems = [r[0] for r in results if r[0]]
    defaults = ['TATA', 'MARUTI SUZUKI', 'MG MOTOR', 'ASHOK LEYLAND', 'MAHINDRA', 'HYUNDAI']
    return sorted(list(set(oems + defaults)))
