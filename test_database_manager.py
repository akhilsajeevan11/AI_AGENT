import unittest
import sqlite3
import os
import json
from datetime import datetime
import database_manager as db_manager

# Define the test database file name
TEST_DB_FILE = 'test_hospital_management.db' 
# Or use TEST_DB_FILE = ":memory:" for in-memory database, 
# but then create_connection needs to handle schema path correctly if it assumes schema is in same dir as a file DB.
# For simplicity with current create_connection, a file-based test DB is easier if schema path is relative.
# Let's ensure hospital_schema.sql is found by create_connection.
# The create_connection in db_manager.py uses open('hospital_schema.sql', 'r').
# This implies hospital_schema.sql must be in the current working directory when tests are run.

class TestDatabaseManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # This method is called once before any tests in the class are run.
        # We can use it to ensure the schema file is accessible if needed,
        # or to set up a common test database if not using :memory: for every test.
        # For now, each test will manage its own connection to :memory: for max isolation.
        pass

    def setUp(self):
        # This method is called before each test method.
        # Use an in-memory database for each test for isolation.
        # The schema is applied by create_connection.
        # The print statement from create_connection will appear once per test, which is acceptable.
        self.conn = db_manager.create_connection(":memory:")
        self.assertIsNotNone(self.conn, "Database connection should be established.")

        # Pre-populate with some common data needed for many tests
        self.patient1_data = {'first_name': 'Test', 'last_name': 'PatientA', 'date_of_birth': '1990-01-01', 'gender': 'Male', 'phone_number': '111000111', 'email': 'patientA@test.com', 'address': '1 Test St'}
        self.patient1_id = db_manager.add_patient(self.conn, self.patient1_data)
        
        self.doctor1_data = {'first_name': 'Dr.Test', 'last_name': 'DoctorA', 'specialization': 'UnitTestology', 'phone_number': '222000222', 'email': 'doctorA@test.com'}
        self.doctor1_id = db_manager.add_doctor(self.conn, self.doctor1_data)

        self.availability1_data = {'doctor_id': self.doctor1_id, 'start_time': '2024-09-01 10:00:00', 'end_time': '2024-09-01 10:30:00', 'is_booked': False}
        self.availability1_id = db_manager.add_doctor_availability(self.conn, self.availability1_data)


    def tearDown(self):
        # This method is called after each test method.
        if self.conn:
            self.conn.close()

    # --- Patient Tests ---
    def test_add_and_get_patient(self):
        patient_data = {'first_name': 'John', 'last_name': 'Doe', 'date_of_birth': '1985-05-15', 'gender': 'Male', 'phone_number': '1234567890', 'email': 'john.doe@example.com', 'address': '123 Main St'}
        patient_id = db_manager.add_patient(self.conn, patient_data)
        self.assertIsNotNone(patient_id, "Should return a patient ID.")
        
        retrieved_patient = db_manager.get_patient(self.conn, patient_id)
        self.assertIsNotNone(retrieved_patient)
        self.assertEqual(retrieved_patient['first_name'], 'John')
        self.assertEqual(retrieved_patient['phone_number'], '1234567890')

    def test_get_patient_by_phone(self):
        retrieved_patient = db_manager.get_patient_by_phone(self.conn, self.patient1_data['phone_number'])
        self.assertIsNotNone(retrieved_patient)
        self.assertEqual(retrieved_patient['patient_id'], self.patient1_id)

    def test_update_patient(self):
        update_data = {'email': 'patientA_new@test.com', 'address': '1 New Test St'}
        success = db_manager.update_patient(self.conn, self.patient1_id, update_data)
        self.assertTrue(success)
        
        updated_patient = db_manager.get_patient(self.conn, self.patient1_id)
        self.assertEqual(updated_patient['email'], 'patientA_new@test.com')
        self.assertEqual(updated_patient['address'], '1 New Test St')

    # --- Doctor Tests ---
    def test_add_and_get_doctor(self):
        doctor_data = {'first_name': 'Alice', 'last_name': 'Wonder', 'specialization': 'Cardiology', 'phone_number': '9876543210', 'email': 'alice.wonder@example.com'}
        doctor_id = db_manager.add_doctor(self.conn, doctor_data)
        self.assertIsNotNone(doctor_id)
        
        retrieved_doctor = db_manager.get_doctor(self.conn, doctor_id)
        self.assertIsNotNone(retrieved_doctor)
        self.assertEqual(retrieved_doctor['first_name'], 'Alice')
        self.assertEqual(retrieved_doctor['specialization'], 'Cardiology')

    def test_get_all_doctors(self):
        doctors = db_manager.get_all_doctors(self.conn)
        self.assertTrue(len(doctors) >= 1) # At least doctor1_id from setUp

    def test_get_doctors_by_specialization(self):
        # Add another doctor with same specialization
        db_manager.add_doctor(self.conn, {'first_name': 'Dr.TestB', 'last_name': 'DoctorB', 'specialization': 'UnitTestology', 'phone_number': '333000333', 'email': 'doctorB@test.com'})
        specialized_doctors = db_manager.get_doctors_by_specialization(self.conn, 'UnitTestology')
        self.assertEqual(len(specialized_doctors), 2)
        self.assertEqual(specialized_doctors[0]['specialization'], 'UnitTestology')

    def test_get_all_specializations(self):
        db_manager.add_doctor(self.conn, {'first_name': 'Dr.TestC', 'last_name': 'DoctorC', 'specialization': 'Pediatrics', 'phone_number': '444000444', 'email': 'doctorC@test.com'})
        specializations = db_manager.get_all_specializations(self.conn)
        self.assertIn('UnitTestology', specializations)
        self.assertIn('Pediatrics', specializations)

    # --- DoctorAvailability Tests ---
    def test_add_and_get_doctor_availability(self):
        avail_data = {'doctor_id': self.doctor1_id, 'start_time': '2024-09-02 10:00:00', 'end_time': '2024-09-02 11:00:00'}
        avail_id = db_manager.add_doctor_availability(self.conn, avail_data)
        self.assertIsNotNone(avail_id)
        
        # Query for this specific slot - get_doctor_availability needs a range
        slots = db_manager.get_doctor_availability(self.conn, self.doctor1_id, '2024-09-02 00:00:00', '2024-09-02 23:59:59')
        found = any(s['availability_id'] == avail_id for s in slots)
        self.assertTrue(found)

    def test_update_availability_slot_booked_status(self):
        success = db_manager.update_availability_slot_booked_status(self.conn, self.availability1_id, True)
        self.assertTrue(success)
        
        slots = db_manager.get_doctor_availability(self.conn, self.doctor1_id, '2024-09-01 00:00:00', '2024-09-01 23:59:59')
        slot = next((s for s in slots if s['availability_id'] == self.availability1_id), None)
        self.assertIsNotNone(slot)
        self.assertEqual(slot['is_booked'], 1) # SQLite BOOLEAN is 0 or 1

        success_unbook = db_manager.update_availability_slot_booked_status(self.conn, self.availability1_id, False)
        self.assertTrue(success_unbook)
        slots_after_unbook = db_manager.get_doctor_availability(self.conn, self.doctor1_id, '2024-09-01 00:00:00', '2024-09-01 23:59:59')
        slot_after_unbook = next((s for s in slots_after_unbook if s['availability_id'] == self.availability1_id), None)
        self.assertIsNotNone(slot_after_unbook)
        self.assertEqual(slot_after_unbook['is_booked'], 0)

    # --- Appointment Tests ---
    def test_add_and_get_appointment(self):
        appointment_data = {
            'patient_id': self.patient1_id, 
            'doctor_id': self.doctor1_id, 
            'appointment_datetime': self.availability1_data['start_time'],
            'duration_minutes': 30,
            'reason_for_visit': 'Test Checkup',
            'status': 'Scheduled',
            'availability_id': self.availability1_id
        }
        appt_id = db_manager.add_appointment(self.conn, appointment_data)
        self.assertIsNotNone(appt_id)
        
        retrieved_appt = db_manager.get_appointment(self.conn, appt_id)
        self.assertIsNotNone(retrieved_appt)
        self.assertEqual(retrieved_appt['patient_id'], self.patient1_id)
        self.assertEqual(retrieved_appt['doctor_id'], self.doctor1_id)
        self.assertEqual(retrieved_appt['reason_for_visit'], 'Test Checkup')
        self.assertEqual(retrieved_appt['availability_id'], self.availability1_id)

    def test_get_appointments_for_patient(self):
        # patient1_id already has an appointment from test_add_and_get_appointment if it runs before,
        # but tests should be independent. Add one here.
        appt_data = {'patient_id': self.patient1_id, 'doctor_id': self.doctor1_id, 'appointment_datetime': '2024-09-03 10:00:00', 'availability_id': self.availability1_id}
        db_manager.add_appointment(self.conn, appt_data)
        
        patient_appts = db_manager.get_appointments_for_patient(self.conn, self.patient1_id)
        self.assertTrue(len(patient_appts) >= 1)

    def test_get_appointments_for_doctor(self):
        appt_data = {'patient_id': self.patient1_id, 'doctor_id': self.doctor1_id, 'appointment_datetime': '2024-09-04 10:00:00', 'availability_id': self.availability1_id}
        db_manager.add_appointment(self.conn, appt_data)
        
        doctor_appts = db_manager.get_appointments_for_doctor(self.conn, self.doctor1_id, date_filter='2024-09-04')
        self.assertTrue(len(doctor_appts) >= 1)
        self.assertEqual(doctor_appts[0]['doctor_id'], self.doctor1_id)

    def test_update_appointment_status(self):
        appt_data = {'patient_id': self.patient1_id, 'doctor_id': self.doctor1_id, 'appointment_datetime': '2024-09-05 10:00:00', 'availability_id': self.availability1_id}
        appt_id = db_manager.add_appointment(self.conn, appt_data)
        
        success = db_manager.update_appointment_status(self.conn, appt_id, 'Completed')
        self.assertTrue(success)
        
        updated_appt = db_manager.get_appointment(self.conn, appt_id)
        self.assertEqual(updated_appt['status'], 'Completed')

    # --- ConversationLogs Tests ---
    def test_add_and_get_conversation_log(self):
        log_data = {
            'patient_id': self.patient1_id,
            'session_id': 'test_session_123',
            'message_text': 'User asked to schedule appointment.',
            'intent_detected': 'request_schedule_appointment',
            'entities_extracted': {'doctor_pref': 'Dr. DoctorA', 'date_pref': 'tomorrow'}
        }
        log_id = db_manager.add_conversation_log(self.conn, log_data)
        self.assertIsNotNone(log_id)

        # Test get_conversation_logs_for_patient
        patient_logs = db_manager.get_conversation_logs_for_patient(self.conn, self.patient1_id)
        self.assertTrue(any(log['log_id'] == log_id for log in patient_logs))
        
        # Test get_conversation_logs_by_session
        session_logs = db_manager.get_conversation_logs_by_session(self.conn, 'test_session_123')
        self.assertTrue(any(log['log_id'] == log_id for log in session_logs))
        retrieved_log = next((log for log in session_logs if log['log_id'] == log_id), None)
        self.assertIsNotNone(retrieved_log)
        self.assertEqual(retrieved_log['message_text'], 'User asked to schedule appointment.')
        # Check entities - they are stored as JSON string
        self.assertIsInstance(retrieved_log['entities_extracted'], str) 
        extracted_entities = json.loads(retrieved_log['entities_extracted'])
        self.assertEqual(extracted_entities['doctor_pref'], 'Dr. DoctorA')

if __name__ == '__main__':
    unittest.main()
