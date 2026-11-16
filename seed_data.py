import os
from app import create_app
from app.models import db, Vehicle, VehicleMovement
from app.services.excel_service import export_to_excel

SEED_RECORDS = [
    {
        "sr_no": 1,
        "bosch_vin": "CVP_2023_001",
        "oem": "TATA",
        "vehicle_name": "ALTROZ CNG",
        "oem_id": "EP07116",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Pankaj Ambatkar (CC/EAS1-IN)",
        "incoming_date": "02-Feb-23",
        "chassis_no": "PP20251032RP07562",
        "vehicle_material": "Jack with handle, wheel spanner, Toe hook, safety, triangle",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "19/Feb/24",
        "outgoing_location": "TATA MOTORS",
        "incoming_date2": "",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "19/Feb/24",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Dispatched to OEM after testing completion"
    },
    {
        "sr_no": 2,
        "bosch_vin": "CVP_2023_002",
        "oem": "TATA",
        "vehicle_name": "SAFARI",
        "oem_id": "EP06999",
        "type": "NON PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Pankaj Ambatkar (CC/EAS1-IN)",
        "incoming_date": "03-Feb-23",
        "chassis_no": "PP30271122RP07411",
        "vehicle_material": "Jack With Handle, Wheel Spanner, Spare Wheel Spanner, Puncture Kit, Screw Driver, Safety Triangle",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "NA",
        "outgoing_location": "NATRAX",
        "incoming_date2": "05/Dec/24",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "",
        "pdi_status": "Pending Verification",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Tested at NATRAX, return cycle completed"
    },
    {
        "sr_no": 3,
        "bosch_vin": "CVP_2023_003",
        "oem": "TATA",
        "vehicle_name": "NEXON",
        "oem_id": "EP05961",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Anbalagan Thangavel (MS/ESI-CC)",
        "incoming_date": "13-Feb-23",
        "chassis_no": "MAT635005MPHS4162",
        "vehicle_material": "Jack With Handle, Wheel Spanner, Safety Triangle, Charging Gun With Cable, Toe Hook, Body Cover",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "04/Sep/23",
        "outgoing_location": "TATA MOTORS",
        "incoming_date2": "",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "04/Sep/23",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Transferred back to TATA Motors"
    },
    {
        "sr_no": 4,
        "bosch_vin": "CVP_2023_004",
        "oem": "TATA",
        "vehicle_name": "XENON TROOP CARRIER",
        "oem_id": "EP07211",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Maheshwari Rahul (CC/EAS1-IN)",
        "incoming_date": "13-Feb-23",
        "chassis_no": "PC30312032RP07603",
        "vehicle_material": "Jack With Handle",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "18/Feb/23",
        "outgoing_location": "NATRAX",
        "incoming_date2": "",
        "current_status": "NATRAX",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "NATRAX proving ground testing program"
    },
    {
        "sr_no": 5,
        "bosch_vin": "CVP_2023_059",
        "oem": "MARUTI SUZUKI",
        "vehicle_name": "BREZZA",
        "oem_id": "NA",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Antony Kamalesh (CC/EAS2.1-IN)",
        "incoming_date": "17/Feb/23",
        "chassis_no": "MA3RYHL1SNM167114",
        "vehicle_material": "Standard OEM Toolkit",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "30/Aug/23",
        "outgoing_location": "MARUTI SUZUKI",
        "incoming_date2": "",
        "current_status": "MARUTI SUZUKI",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "30/Aug/23",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Returned to Maruti Suzuki after verification"
    },
    {
        "sr_no": 6,
        "bosch_vin": "CVP_2023_005",
        "oem": "MG MOTOR",
        "vehicle_name": "ASTOR",
        "oem_id": "NA",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Priteshsingh Rajput (CC/EAS2-IN)",
        "incoming_date": "20-Feb-23",
        "chassis_no": "MZ7ED6HLL3H000016",
        "vehicle_material": "Spare wheel, OEM roadside kit",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "05/Sep/23",
        "outgoing_location": "MG, GUJRAT",
        "incoming_date2": "",
        "current_status": "MG, GUJRAT",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "05/Sep/23",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Delivered to MG Gujarat facility"
    },
    {
        "sr_no": 7,
        "bosch_vin": "CVP_2023_006",
        "oem": "TATA",
        "vehicle_name": "TIAGO EV",
        "oem_id": "EP07138",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Anbalagan Thangavel (MS/ESI-CC)",
        "incoming_date": "27-Feb-23",
        "chassis_no": "MAT568007NKNA6558",
        "vehicle_material": "Jack With Handle, Wheel Spanner, Toe Hook, Puncture Kit, Open Spanner 10, Charging Gun With Cable",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "08/Dec/23",
        "outgoing_location": "TATA MOTORS",
        "incoming_date2": "",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "08/Dec/23",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "EV powertrain validation cycle finished"
    },
    {
        "sr_no": 8,
        "bosch_vin": "CVP_2023_007",
        "oem": "TATA",
        "vehicle_name": "TIAGO EV",
        "oem_id": "EP06782",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Anralagan Thanravel (MS/ESI-CC)",
        "incoming_date": "02-Mar-23",
        "chassis_no": "PP20240122RP07337",
        "vehicle_material": "Jack With Handle, Wheel Spanner, Toe Hook, Puncture Kit, Open Spanner 8/10, Charging Gun With Cable",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "03/May/24",
        "outgoing_location": "TATA MOTORS",
        "incoming_date2": "",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "03/May/24",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Software calibration completed and vehicle returned"
    },
    {
        "sr_no": 9,
        "bosch_vin": "CVP_2023_008",
        "oem": "TATA",
        "vehicle_name": "TIAGO EV XT",
        "oem_id": "HBN",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Anbalagan Thangavel (MS/ESI-CC)",
        "incoming_date": "02-Mar-23",
        "chassis_no": "PP20242122RP07519",
        "vehicle_material": "Jack With Handle, Wheel Spanner, Toe Hook, Puncture Kit, Open Spanner 8/10, Charging Gun With Cable",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "17/May/24",
        "outgoing_location": "TATA MOTORS",
        "incoming_date2": "",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "17/May/24",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Returned to TATA Motors"
    },
    {
        "sr_no": 10,
        "bosch_vin": "CVP_2023_009",
        "oem": "ASHOK LEYLAND",
        "vehicle_name": "SCHOOL BUS",
        "oem_id": "NA",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Maheshwari Rahul (CC/EAS1-IN)",
        "incoming_date": "19/Mar/23",
        "chassis_no": "MB1PH34LOLRBF2929",
        "vehicle_material": "Standard toolkit and emergency triangles",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "12/Apr/23",
        "outgoing_location": "BOSCH WORKSHOP",
        "incoming_date2": "",
        "current_status": "In Workshop",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "",
        "pdi_status": "Under Evaluation",
        "vehicle_issues": "Suspension noise during high payload test",
        "work_order_received_date": "20/Mar/23",
        "tpm_confirmation": "Pending",
        "remark": "Heavy vehicle test program"
    },
    {
        "sr_no": 11,
        "bosch_vin": "CVP_2023_010",
        "oem": "TATA",
        "vehicle_name": "MAGIC",
        "oem_id": "EP06932",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Maheshwari Rahul (CC/EAS1-IN)",
        "incoming_date": "21/Mar/23",
        "chassis_no": "PC20218022RU07221",
        "vehicle_material": "Jack With Handle, Wheel Spanner, Safety Triangle, Toe Hook",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "21/Apr/24",
        "outgoing_location": "TATA MOTORS",
        "incoming_date2": "",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "21/Apr/24",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Commercial vehicle testing cycle"
    },
    {
        "sr_no": 12,
        "bosch_vin": "CVP_2023_011",
        "oem": "TATA",
        "vehicle_name": "TIAGO",
        "oem_id": "EP06229",
        "type": "PP",
        "bosch_dc1": "",
        "bosch_dc2": "",
        "owner": "Maheshwari Rahul (CC/EAS1-IN)",
        "incoming_date": "27/Mar/23",
        "chassis_no": "PP20245022RP06796",
        "vehicle_material": "Jack With Handle, Wheel Spanner, Safety Triangle, Toe Hook",
        "spare_parts_link": "NO SPARE PARTS AVAILABLE",
        "outgoing_date": "13/Jan/24",
        "outgoing_location": "TATA MOTORS",
        "incoming_date2": "",
        "current_status": "TATA MOTORS",
        "receiving_location": "BOSCH PLANT",
        "date_sent_to_customer": "13/Jan/24",
        "pdi_status": "Completed",
        "vehicle_issues": "",
        "work_order_received_date": "",
        "tpm_confirmation": "",
        "remark": "Returned to TATA Motors"
    }
]

def seed_database():
    app = create_app()
    with app.app_context():
        print("Clearing old data and reseeding with master data...")
        # Drop all and recreate to ensure schema table updates
        db.drop_all()
        db.create_all()

        for rec in SEED_RECORDS:
            v = Vehicle(
                sr_no=rec["sr_no"],
                bosch_vin=rec["bosch_vin"],
                oem=rec["oem"],
                vehicle_name=rec["vehicle_name"],
                oem_id=rec["oem_id"],
                type=rec["type"],
                owner=rec["owner"],
                chassis_no=rec["chassis_no"],
                vehicle_material=rec["vehicle_material"],
                spare_parts_link=rec["spare_parts_link"],
                pdi_status=rec["pdi_status"],
                vehicle_issues=rec["vehicle_issues"],
                work_order_received_date=rec["work_order_received_date"],
                tpm_confirmation=rec["tpm_confirmation"],
                current_status=rec["current_status"],
                current_location=rec["outgoing_location"] if rec["outgoing_location"] and rec["outgoing_location"] != "NA" else rec["receiving_location"],
                remark=rec["remark"]
            )
            db.session.add(v)
            db.session.flush()

            # Genesis Hop (Hop 1): RECEIVING LOCATION & INCOMING DATE as start points
            hop1 = VehicleMovement(
                vehicle_id=v.id,
                hop_sequence=1,
                source_location=f"{v.oem} Manufacturing Plant",
                destination_location=rec["receiving_location"],
                arrival_date=rec["incoming_date"],
                movement_purpose="Initial Vehicle Receipt & Check-in",
                work_done="Vehicle gate-in, inventory check of materials and tools",
                dc_number=rec["bosch_dc1"] or f"IN-{v.bosch_vin}",
                status="Received",
                remarks=f"Initial check-in at {rec['receiving_location']} on {rec['incoming_date']}"
            )
            db.session.add(hop1)
            next_hop = 2

            # Hop 2: Intermediate testing / Transfer (if outgoing exists)
            out_loc = rec["outgoing_location"]
            if out_loc and out_loc.upper() not in ('NA', '', 'NONE'):
                hop2 = VehicleMovement(
                    vehicle_id=v.id,
                    hop_sequence=next_hop,
                    source_location=rec["receiving_location"],
                    destination_location=out_loc,
                    dispatch_date=rec["outgoing_date"] if rec["outgoing_date"] != 'NA' else rec["incoming_date"],
                    arrival_date=rec["outgoing_date"] if rec["outgoing_date"] != 'NA' else '',
                    movement_purpose="Track Testing / OEM Dispatch",
                    work_done=f"Vehicle dispatched to {out_loc}",
                    dc_number=rec["bosch_dc2"] or f"DC-{v.bosch_vin}",
                    status="Dispatched",
                    remarks=f"Moved to {out_loc}"
                )
                db.session.add(hop2)
                next_hop += 1

            # Hop 3: Incoming Date 2 (Vehicle returned back to start location)
            in_date2 = rec["incoming_date2"]
            if in_date2 and in_date2.upper() not in ('NA', '', 'NONE'):
                hop3 = VehicleMovement(
                    vehicle_id=v.id,
                    hop_sequence=next_hop,
                    source_location=out_loc or "External Track",
                    destination_location=rec["receiving_location"],
                    arrival_date=in_date2,
                    movement_purpose="Re-entry after external testing",
                    work_done="Second receiving and inspection after field/track test",
                    dc_number=f"RET-{v.bosch_vin}",
                    status="Received Back",
                    remarks="Vehicle returned to Bosch facility for next development stage"
                )
                db.session.add(hop3)

            db.session.flush()
            v.update_from_latest_hop()

        db.session.commit()
        print(f"Successfully seeded {len(SEED_RECORDS)} vehicles with complete multi-hop histories into normalized schema!")

        # Also generate the initial 2-sheet Excel master file
        export_file = os.path.join(app.config['DATA_DIR'], 'Master_Vehicle_Data.xlsx')
        export_to_excel(export_file)
        print(f"Master 2-sheet Excel file generated at: {export_file}")

if __name__ == '__main__':
    seed_database()
