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
            
            # Verify vehicle current location and current status updated from latest hop
            v_updated = db.session.get(Vehicle, v.id)
            self.assertEqual(v_updated.current_location, 'NATRAX TRACK')
            self.assertEqual(v_updated.current_status, 'NATRAX TRACK')
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
            self.assertEqual(v_updated2.current_status, 'BOSCH PLANT')

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
        """Test Kiosk Dashboard display route."""
        response = self.client.get('/dashboard/kiosk')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LOCATION-WISE VEHICLE QUANTITIES', response.data)
        self.assertIn(b'LIVE MOVEMENT STREAM', response.data)
        self.assertIn(b'LIVE UPDATES', response.data)
        self.assertNotIn(b'24/7 STREAMING ACTIVE', response.data)

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
        """Test normalized 2-sheet Excel export generation and structure."""
        with self.app.app_context():
            test_export_path = os.path.join(self.app.config['DATA_DIR'], 'test_export.xlsx')
            export_to_excel(test_export_path)
            self.assertTrue(os.path.exists(test_export_path))

            wb = openpyxl.load_workbook(test_export_path)
            self.assertIn('vehicles', wb.sheetnames)
            self.assertIn('vehicle_movements', wb.sheetnames)

            ws_v = wb['vehicles']
            self.assertEqual(ws_v.cell(row=1, column=1).value, 'sr_no')
            self.assertEqual(ws_v.cell(row=1, column=2).value, 'bosch_vin')
            self.assertEqual(ws_v.cell(row=1, column=3).value, 'oem_id')
            self.assertEqual(ws_v.cell(row=1, column=9).value, 'vehicle_material')
            self.assertEqual(ws_v.cell(row=1, column=12).value, 'vehicle_issues')
            self.assertEqual(ws_v.cell(row=1, column=16).value, 'current_location')

            ws_m = wb['vehicle_movements']
            self.assertEqual(ws_m.cell(row=1, column=1).value, 'id')
            self.assertEqual(ws_m.cell(row=1, column=2).value, 'vehicle_id')
            self.assertEqual(ws_m.cell(row=1, column=5).value, 'source_location')
            self.assertEqual(ws_m.cell(row=1, column=6).value, 'destination_location')
            wb.close()
            if os.path.exists(test_export_path):
                os.remove(test_export_path)

    def test_10_vin_url_routing(self):
        """Test accessing vehicle detail page by Bosch VIN string directly."""
        response = self.client.get('/tracking/vehicle/CVP_2023_001')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CVP_2023_001', response.data)
        self.assertIn(b'ALTROZ CNG', response.data)

    def test_11_universal_importer_legacy_auto_conversion(self):
        """Test universal importer auto-converting legacy 25-column format into normalized 2 tables."""
        from app.services.excel_service import import_excel_file
        import pandas as pd

        test_legacy_path = os.path.join(self.app.config['DATA_DIR'], 'test_legacy.xlsx')
        legacy_data = [{
            "SR.NO": "99",
            "BOSCHVehicle Identification No": "CVP_LEGACY_099",
            "OEM": "TATA",
            "VEHICLE NAME ": "HARRIER EV",
            "OEM Identification No": "EP99999",
            "Type": "PP",
            "BOSCH DC-1": "DC-LEG-01",
            "BOSCH DC-2": "DC-LEG-02",
            "Owner": "Test Engineer",
            "INCOMING DATE": "01-Jan-24",
            "CHASSIS NO": "CHASSIS99999",
            "MATERIAL COME WITH VEHICLE": "Charging Gun, Spanner",
            "Spare Parts Link": "NO SPARE PARTS",
            "OUTGOING DATE": "15-Feb-24",
            "OUTGOING LOCATION": "NATRAX",
            "INCOMING DATE2": "20-Mar-24",
            "CURRENT STATUS": "Received Back",
            "RECEIVING LOCATION": "BOSCH PLANT",
            "Date sent to customer": "",
            "PDI STATUS": "Pass",
            "VEHICLE PROBLEM/ISSUES": "None",
            "WORK ORDER RECEIVED DATE": "05-Jan-24",
            "TPM COMFIRMATION": "Confirmed",
            "REMARK ": "Legacy format test upload",
            "Movement_History": "Legacy history text to be dropped"
        }]

        df_legacy = pd.DataFrame(legacy_data)
        df_legacy.to_excel(test_legacy_path, index=False)

        with self.app.app_context():
            res = import_excel_file(test_legacy_path, mode='upsert')
            self.assertGreater(res['created'] + res['updated'], 0)

            v = Vehicle.query.filter_by(bosch_vin='CVP_LEGACY_099').first()
            self.assertIsNotNone(v)
            self.assertEqual(v.vehicle_name, 'HARRIER EV')
            self.assertEqual(v.oem_id, 'EP99999')
            self.assertEqual(v.vehicle_material, 'Charging Gun, Spanner')
            # Verify legacy hops were auto-converted into discrete movements
            self.assertGreaterEqual(len(v.movements), 2)
            self.assertEqual(v.movements[0].destination_location, 'BOSCH PLANT')
            self.assertEqual(v.movements[1].destination_location, 'NATRAX')

        if os.path.exists(test_legacy_path):
            os.remove(test_legacy_path)

    def test_12_shortform_number_and_status_locations(self):
        """Test shortform number formatter and locations from current_status."""
        with self.app.app_context():
            from app.services.tracking_service import get_location_counts
            filter_fn = self.app.jinja_env.filters.get('short_num')
            self.assertIsNotNone(filter_fn)
            self.assertEqual(filter_fn(1100), '1.1k')
            self.assertEqual(filter_fn(1000), '1k')
            self.assertEqual(filter_fn(25400), '25.4k')
            self.assertEqual(filter_fn(1500000), '1.5M')
            self.assertEqual(filter_fn(2000000000), '2B')
            self.assertEqual(filter_fn(42), '42')

            # Verify locations are strictly from current_status
            counts = get_location_counts()
            self.assertIn('TATA MOTORS', counts)

    def test_13_tracking_multiselect_filters(self):
        """Test multi-select filter query on tracking endpoint."""
        response = self.client.get('/tracking/?location=TATA+MOTORS&location=NATRAX')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Location: TATA MOTORS', response.data)
        self.assertIn(b'Location: NATRAX', response.data)

        # Test home page has clean placeholder and no Quick Lookup
        resp_home = self.client.get('/')
        self.assertEqual(resp_home.status_code, 200)
        self.assertIn(b'Enter Bosch VIN (e.g. CVP_2023_001) or OEM ID (e.g. EP07116)', resp_home.data)
        self.assertNotIn(b'Quick lookup:', resp_home.data)
        self.assertIn(b'Operating Locations', resp_home.data)
        self.assertIn(b'Quality &amp; TPM Alerts', resp_home.data)

    def test_14_settings_page_and_theme_cookies(self):
        """Test separate software and dashboard theme configuration and cookie persistence."""
        # 1. Test GET /settings
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Display & Theme Settings', response.data)
        self.assertIn(b'Main Software Theme', response.data)
        self.assertIn(b'Dashboard Theme (24/7 Kiosk)', response.data)
        self.assertIn(b'software_theme', response.data)
        self.assertIn(b'dashboard_theme', response.data)

        # 2. Test POST /settings with custom themes
        post_resp = self.client.post('/settings', data={
            'software_theme': 'dark',
            'dashboard_theme': 'light'
        }, follow_redirects=False)
        self.assertEqual(post_resp.status_code, 302)
        
        # Verify cookies set on response
        cookies = post_resp.headers.getlist('Set-Cookie')
        cookie_str = ' '.join(cookies)
        self.assertIn('software_theme=dark', cookie_str)
        self.assertIn('dashboard_theme=light', cookie_str)

        # 3. Test that base template respects software_theme cookie
        self.client.set_cookie('software_theme', 'dark')
        home_resp = self.client.get('/')
        self.assertEqual(home_resp.status_code, 200)
        self.assertIn(b'data-bs-theme="dark"', home_resp.data)

        # 4. Test that kiosk template respects dashboard_theme cookie
        self.client.set_cookie('dashboard_theme', 'light')
        kiosk_resp = self.client.get('/dashboard/kiosk')
        self.assertEqual(kiosk_resp.status_code, 200)
        self.assertIn(b'data-bs-theme="light"', kiosk_resp.data)

        # 5. Test AJAX /api/theme endpoint
        api_resp = self.client.post('/api/theme', json={
            'software_theme': 'light',
            'dashboard_theme': 'dark'
        })
        self.assertEqual(api_resp.status_code, 200)
        api_data = api_resp.get_json()
        self.assertEqual(api_data['software_theme'], 'light')
        self.assertEqual(api_data['dashboard_theme'], 'dark')

if __name__ == '__main__':
    unittest.main()
