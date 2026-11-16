from sqlalchemy import or_, func
from app.models import db, Vehicle, VehicleMovement

def get_vehicle_by_identifier(identifier):
    """
    Search for a vehicle by exact or case-insensitive match on:
    - Bosch VIN
    - OEM Identification No
    - Chassis No
    - Numeric primary key ID
    """
    if not identifier:
        return None
    
    clean_id = str(identifier).strip()
    
    # Check by Bosch VIN
    v = Vehicle.query.filter(func.lower(Vehicle.bosch_vin) == clean_id.lower()).first()
    if v:
        return v
    
    # Check by OEM ID
    v = Vehicle.query.filter(func.lower(Vehicle.oem_id) == clean_id.lower()).first()
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

def search_vehicles(query=None, oem=None, location=None, status=None,
                    oems=None, locations=None, statuses=None):
    """Search vehicles with multiple optional criteria and multi-select support."""
    q = Vehicle.query
    
    if query:
        term = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Vehicle.bosch_vin.ilike(term),
                Vehicle.oem_id.ilike(term),
                Vehicle.vehicle_name.ilike(term),
                Vehicle.chassis_no.ilike(term),
                Vehicle.owner.ilike(term),
                Vehicle.oem.ilike(term),
                Vehicle.current_location.ilike(term),
                Vehicle.current_status.ilike(term)
            )
        )
    
    # Process OEM filters (multi or single)
    selected_oems = set()
    if oem and oem != 'ALL':
        selected_oems.add(oem)
    if oems:
        for o in oems:
            if o and o != 'ALL':
                selected_oems.add(o)
    if selected_oems:
        q = q.filter(Vehicle.oem.in_(list(selected_oems)))
        
    # Process Location filters (locations considered strictly from current_status column)
    selected_locations = set()
    if location and location != 'ALL':
        selected_locations.add(location)
    if locations:
        for l in locations:
            if l and l != 'ALL':
                selected_locations.add(l)
    if selected_locations:
        q = q.filter(Vehicle.current_status.in_(list(selected_locations)))
        
    # Process Status filters
    selected_statuses = set()
    if status and status != 'ALL':
        selected_statuses.add(status)
    if statuses:
        for s in statuses:
            if s and s != 'ALL':
                selected_statuses.add(s)
    if selected_statuses:
        q = q.filter(Vehicle.current_status.in_(list(selected_statuses)))
        
    return q.order_by(Vehicle.id.asc()).all()

def add_movement_hop(vehicle_id, source_location, destination_location, 
                     dispatch_date=None, arrival_date=None, 
                     movement_purpose=None, work_done=None, 
                     dc_number=None, status='At Location', remarks=None):
    """
    Records a new hop in the vehicle's journey (e.g. Location A -> Location B -> OEM -> Location A).
    Updates current_location, current_status, total_hops, and updated_at on the vehicle.
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
        remarks=remarks.strip() if remarks else (work_done.strip() if work_done else None)
    )
    db.session.add(hop)
    db.session.flush()

    # Synchronize vehicle location and status from latest hop
    vehicle.update_from_latest_hop()
    db.session.commit()
    return hop

def get_location_counts():
    """Return dictionary of {location_name: vehicle_count} considered strictly from current_status column."""
    results = db.session.query(
        Vehicle.current_status,
        func.count(Vehicle.id)
    ).filter(
        Vehicle.current_status.isnot(None),
        Vehicle.current_status != '',
        Vehicle.current_status != 'NA'
    ).group_by(Vehicle.current_status).all()
    
    counts = {}
    for loc, count in results:
        key = str(loc).strip()
        if key:
            counts[key] = count
    return counts

def get_distinct_locations():
    """Returns a sorted list of all unique locations recorded strictly in Vehicle.current_status."""
    results = db.session.query(Vehicle.current_status).distinct().all()
    locs = set()
    for r in results:
        val = r[0]
        if val and str(val).strip() and str(val).strip().upper() != 'NA':
            locs.add(str(val).strip())
            
    return sorted(list(locs))

def get_distinct_oems():
    """Returns sorted list of distinct OEMs."""
    results = db.session.query(Vehicle.oem).distinct().all()
    oems = [r[0] for r in results if r[0]]
    defaults = ['TATA', 'MARUTI SUZUKI', 'MG MOTOR', 'ASHOK LEYLAND', 'MAHINDRA', 'HYUNDAI']
    return sorted(list(set(oems + defaults)))
