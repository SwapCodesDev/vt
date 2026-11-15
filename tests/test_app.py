import os
import unittest
from app import create_app
from app.models import db, Vehicle, VehicleMovement
from app.services.tracking_service import get_vehicle_by_identifier, add_movement_hop
from app.services.excel_service import export_to_excel
from seed_data import seed_database
import openpyxl

class VehicleTrackingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        seed_database()

    def test_01_home_page_loads(self):
        """Test home page accessibility and title."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Bosch Vehicle Tracking System', response.data)

    def test_02_fleet_list_loads(self):
        """Test tracking fleet list view."""
        response = self.client.get('/tracking/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Fleet Vehicle Tracking', response.data)
        self.assertIn(b'CVP_2023_001', response.data)

    def test_03_lookup_by_vin_and_oem_id(self):
        """Test direct lookup by Bosch VIN and OEM ID."""
        with self.app.app_context():
            v_vin = get_vehicle_by_identifier('CVP_2023_001')
            self.assertIsNotNone(v_vin)
            self.assertEqual(v_vin.vehicle_name, 'ALTROZ CNG')

            v_oem = get_vehicle_by_identifier('EP07116')
            self.assertIsNotNone(v_oem)
            self.assertEqual(v_oem.bosch_vin, 'CVP_2023_001')

    def test_04_vehicle_detail_page(self):
        """Test vehicle 360 degree detail view and start points."""
        with self.app.app_context():
            v = Vehicle.query.filter_by(bosch_vin='CVP_2023_001').first()
            self.assertIsNotNone(v)
            v_id = v.id

        response = self.client.get(f'/tracking/vehicle/{v_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CVP_2023_001', response.data)
        self.assertIn(b'Receiving Location (Start Point)', response.data)
        self.assertIn(b'BOSCH PLANT', response.data)

    def test_05_multi_hop_addition(self):
        """Test logging multi-hop movement and cyclic journey."""
        with self.app.app_context():
            v = Vehicle.query.filter_by(bosch_vin='CVP_2023_001').first()
            initial_hops = len(v.movements)
            
            # Add Hop: Bosch Plant -> NATRAX
            hop1 = add_movement_hop(
                vehicle_id=v.id,
                source_location='BOSCH PLANT',
                destination_location='NATRAX TRACK',
                dispatch_date='15-Nov-26',
                arrival_date='16-Nov-26',
                movement_purpose='Dynamic track testing',
                work_done='Brake testing and sensor telemetry check',
                dc_number='DC-TEST-001',
                status='At Testing Track'
            )
            self.assertEqual(hop1.destination_location, 'NATRAX TRACK')
            
            # Verify vehicle current location updated
            v_updated = db.session.get(Vehicle, v.id)
            self.assertEqual(v_updated.current_location, 'NATRAX TRACK')
            self.assertEqual(v_updated.current_status, 'At Testing Track')
            self.assertEqual(len(v_updated.movements), initial_hops + 1)

            # Add Return Hop: NATRAX -> Return to Bosch Plant (Cyclic test)
            hop2 = add_movement_hop(
                vehicle_id=v.id,
                source_location='NATRAX TRACK',
                destination_location='BOSCH PLANT',
                dispatch_date='18-Nov-26',
                arrival_date='19-Nov-26',
                movement_purpose='Return to plant after testing',
                work_done='Post-test inspection',
                dc_number='DC-RET-001',
                status='Received Back'
            )
            v_updated2 = db.session.get(Vehicle, v.id)
            self.assertEqual(v_updated2.current_location, 'BOSCH PLANT')
            self.assertEqual(v_updated2.current_status, 'Received Back')

    def test_06_data_manager_grid_and_modification(self):
        """Test data manager grid and SQLite record modification."""
        response = self.client.get('/data-manager/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Master Vehicles Data Grid', response.data)

        with self.app.app_context():
            v = Vehicle.query.filter_by(bosch_vin='CVP_2023_001').first()
            v_id = v.id

        # Post edit update
        response_post = self.client.post(f'/data-manager/edit/{v_id}', data={
            'oem': 'TATA',
            'vehicle_name': 'ALTROZ CNG MODIFIED',
            'oem_id_no': 'EP07116',
            'vehicle_type': 'PP',
            'receiving_location': 'BOSCH PLANT',
            'incoming_date': '02-Feb-23',
            'current_location': 'BOSCH PLANT',
            'current_status': 'In Workshop',
            'remark': 'Updated via automated test'
        }, follow_redirects=True)
        self.assertEqual(response_post.status_code, 200)

        with self.app.app_context():
            v_check = db.session.get(Vehicle, v_id)
            self.assertEqual(v_check.vehicle_name, 'ALTROZ CNG MODIFIED')
            self.assertEqual(v_check.remark, 'Updated via automated test')

    def test_07_dashboard_kiosk_stream(self):
        """Test 24/7 TV Streamed Kiosk display route."""
        response = self.client.get('/dashboard/kiosk')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'24/7 STREAMING ACTIVE', response.data)
        self.assertIn(b'LOCATION-WISE VEHICLE QUANTITIES (LIVE)', response.data)
        self.assertIn(b'LIVE MOVEMENT STREAM', response.data)

    def test_08_api_telemetry_json(self):
        """Test JSON telemetry endpoint powering the 24/7 screen."""
        response = self.client.get('/api/telemetry')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_vehicles', data)
        self.assertIn('location_breakdown', data)
        self.assertIn('recent_movements', data)
        self.assertIn('vehicles', data)
        self.assertGreater(data['total_vehicles'], 0)

    def test_09_excel_export(self):
        """Test Excel export generation and structure."""
        with self.app.app_context():
            test_export_path = os.path.join(self.app.config['DATA_DIR'], 'test_export.xlsx')
            export_to_excel(test_export_path)
            self.assertTrue(os.path.exists(test_export_path))

            wb = openpyxl.load_workbook(test_export_path)
            self.assertIn('Vehicle Master Data', wb.sheetnames)
            self.assertIn('Movement Audit Log', wb.sheetnames)

            ws = wb['Vehicle Master Data']
            self.assertEqual(ws.cell(row=1, column=1).value, 'SR.NO')
            self.assertEqual(ws.cell(row=1, column=2).value, 'BOSCHVehicle Identification No')
            self.assertEqual(ws.cell(row=1, column=10).value, 'INCOMING DATE')
            self.assertEqual(ws.cell(row=1, column=18).value, 'RECEIVING LOCATION')
            wb.close()
            if os.path.exists(test_export_path):
                os.remove(test_export_path)

if __name__ == '__main__':
    unittest.main()
