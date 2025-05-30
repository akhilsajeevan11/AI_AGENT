import sqlite3
import json
from datetime import datetime

def create_connection(db_file):
    """Create a database connection to an SQLite database and create tables if they don't exist."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row  # Access columns by name

        # Read and execute schema
        with open('hospital_schema.sql', 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print(f"SQLite DB created and schema applied from hospital_schema.sql")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database or executing schema: {e}")
        if conn:
            conn.close()
        return None
    except FileNotFoundError:
        print(f"Error: hospital_schema.sql not found. Make sure the schema file is in the same directory.")
        if conn:
            conn.close()
        return None

# --- Patients CRUD ---
def add_patient(conn, patient_data):
    """Inserts a new patient."""
    sql = '''INSERT INTO Patients(first_name, last_name, date_of_birth, gender, phone_number, email, address)
             VALUES(?,?,?,?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            patient_data.get('first_name'),
            patient_data.get('last_name'),
            patient_data.get('date_of_birth'),
            patient_data.get('gender'),
            patient_data.get('phone_number'),
            patient_data.get('email'),
            patient_data.get('address')
        ))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"Error adding patient (likely duplicate phone/email or missing required field): {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding patient: {e}")
        return None

def get_patient(conn, patient_id):
    """Retrieves a patient by ID."""
    sql = "SELECT * FROM Patients WHERE patient_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (patient_id,))
        return cur.fetchone()
    except sqlite3.Error as e:
        print(f"Database error getting patient: {e}")
        return None

def get_patient_by_phone(conn, phone_number):
    """Retrieves a patient by phone number."""
    sql = "SELECT * FROM Patients WHERE phone_number = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (phone_number,))
        return cur.fetchone()
    except sqlite3.Error as e:
        print(f"Database error getting patient by phone: {e}")
        return None

def update_patient(conn, patient_id, updated_data):
    """Updates patient details. updated_data is a dictionary."""
    fields = []
    values = []
    for key, value in updated_data.items():
        # Ensure only valid columns are updated
        if key in ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone_number', 'email', 'address']:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        print("No valid fields provided for update.")
        return False

    sql = f"UPDATE Patients SET {', '.join(fields)}, last_updated_timestamp = CURRENT_TIMESTAMP WHERE patient_id = ?"
    values.append(patient_id)
    try:
        cur = conn.cursor()
        cur.execute(sql, tuple(values))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.IntegrityError as e:
        print(f"Error updating patient (likely duplicate phone/email): {e}")
        return False
    except sqlite3.Error as e:
        print(f"Database error updating patient: {e}")
        return False

def delete_patient(conn, patient_id):
    """Deletes a patient. Consider related records (appointments, logs) and how to handle them (e.g., cascade, set null, prevent)."""
    # For now, direct delete. In a real system, you might want to archive or handle foreign key constraints carefully.
    sql = "DELETE FROM Patients WHERE patient_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (patient_id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error deleting patient: {e}")
        return False

# --- Doctors CRUD ---
def add_doctor(conn, doctor_data):
    """Inserts a new doctor."""
    sql = '''INSERT INTO Doctors(first_name, last_name, specialization, phone_number, email)
             VALUES(?,?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            doctor_data.get('first_name'),
            doctor_data.get('last_name'),
            doctor_data.get('specialization'),
            doctor_data.get('phone_number'),
            doctor_data.get('email')
        ))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError as e:
        print(f"Error adding doctor (likely duplicate phone/email or missing required field): {e}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding doctor: {e}")
        return None

def get_doctor(conn, doctor_id):
    """Retrieves a doctor by ID."""
    sql = "SELECT * FROM Doctors WHERE doctor_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (doctor_id,))
        return cur.fetchone()
    except sqlite3.Error as e:
        print(f"Database error getting doctor: {e}")
        return None

def get_all_doctors(conn):
    """Retrieves all doctors."""
    sql = "SELECT * FROM Doctors"
    try:
        cur = conn.cursor()
        cur.execute(sql)
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error getting all doctors: {e}")
        return []

def get_doctors_by_specialization(conn, specialization):
    """Retrieves doctors by specialization."""
    sql = "SELECT * FROM Doctors WHERE lower(specialization) = lower(?)"
    try:
        cur = conn.cursor()
        cur.execute(sql, (specialization,))
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error getting doctors by specialization: {e}")
        return []

def get_all_specializations(conn):
    """Retrieves a list of unique doctor specializations."""
    sql = "SELECT DISTINCT specialization FROM Doctors ORDER BY specialization"
    try:
        cur = conn.cursor()
        cur.execute(sql)
        return [row['specialization'] for row in cur.fetchall() if row['specialization']] # Filter out None/empty
    except sqlite3.Error as e:
        print(f"Database error getting all specializations: {e}")
        return []

def update_doctor(conn, doctor_id, updated_data):
    """Updates doctor details."""
    fields = []
    values = []
    for key, value in updated_data.items():
        if key in ['first_name', 'last_name', 'specialization', 'phone_number', 'email']:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        print("No valid fields provided for update.")
        return False

    sql = f"UPDATE Doctors SET {', '.join(fields)}, last_updated_timestamp = CURRENT_TIMESTAMP WHERE doctor_id = ?"
    values.append(doctor_id)
    try:
        cur = conn.cursor()
        cur.execute(sql, tuple(values))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.IntegrityError as e:
        print(f"Error updating doctor (likely duplicate phone/email): {e}")
        return False
    except sqlite3.Error as e:
        print(f"Database error updating doctor: {e}")
        return False

# --- Appointments CRUD ---
def add_appointment(conn, appointment_data):
    """Schedules a new appointment."""
    sql = '''INSERT INTO Appointments(patient_id, doctor_id, appointment_datetime, duration_minutes, reason_for_visit, status, notes, availability_id)
             VALUES(?,?,?,?,?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            appointment_data.get('patient_id'),
            appointment_data.get('doctor_id'),
            appointment_data.get('appointment_datetime'),
            appointment_data.get('duration_minutes', 30),
            appointment_data.get('reason_for_visit'),
            appointment_data.get('status', 'Scheduled'),
            appointment_data.get('notes'),
            appointment_data.get('availability_id') # New field
        ))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Database error adding appointment: {e}")
        return None

def get_appointment(conn, appointment_id):
    """Retrieves an appointment by ID."""
    sql = "SELECT * FROM Appointments WHERE appointment_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (appointment_id,))
        return cur.fetchone()
    except sqlite3.Error as e:
        print(f"Database error getting appointment: {e}")
        return None

def get_appointments_for_patient(conn, patient_id):
    """Retrieves all appointments for a patient."""
    sql = "SELECT * FROM Appointments WHERE patient_id = ? ORDER BY appointment_datetime"
    try:
        cur = conn.cursor()
        cur.execute(sql, (patient_id,))
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error getting patient appointments: {e}")
        return []

def get_appointments_for_doctor(conn, doctor_id, date_filter=None):
    """Retrieves appointments for a doctor, optionally filtered by date (YYYY-MM-DD)."""
    if date_filter:
        sql = "SELECT * FROM Appointments WHERE doctor_id = ? AND date(appointment_datetime) = ? ORDER BY appointment_datetime"
        params = (doctor_id, date_filter)
    else:
        sql = "SELECT * FROM Appointments WHERE doctor_id = ? ORDER BY appointment_datetime"
        params = (doctor_id,)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error getting doctor appointments: {e}")
        return []

def update_appointment_status(conn, appointment_id, status):
    """Updates the status of an appointment."""
    sql = "UPDATE Appointments SET status = ?, last_updated_timestamp = CURRENT_TIMESTAMP WHERE appointment_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (status, appointment_id))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error updating appointment status: {e}")
        return False

def update_appointment_notes(conn, appointment_id, notes):
    """Updates the notes for an appointment."""
    sql = "UPDATE Appointments SET notes = ?, last_updated_timestamp = CURRENT_TIMESTAMP WHERE appointment_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (notes, appointment_id))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error updating appointment notes: {e}")
        return False

def delete_appointment(conn, appointment_id):
    """Cancels/deletes an appointment."""
    # In a real system, changing status to 'Cancelled' might be preferred over deletion.
    sql = "DELETE FROM Appointments WHERE appointment_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (appointment_id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error deleting appointment: {e}")
        return False

# --- DoctorAvailability CRUD ---
def add_doctor_availability(conn, availability_data):
    """Adds a doctor's availability slot."""
    sql = '''INSERT INTO DoctorAvailability(doctor_id, start_time, end_time, is_booked)
             VALUES(?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            availability_data.get('doctor_id'),
            availability_data.get('start_time'), # Expected format: YYYY-MM-DD HH:MM:SS
            availability_data.get('end_time'),   # Expected format: YYYY-MM-DD HH:MM:SS
            availability_data.get('is_booked', False)
        ))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Database error adding doctor availability: {e}")
        return None

def get_doctor_availability(conn, doctor_id, start_date, end_date):
    """Retrieves a doctor's availability within a date range."""
    # Ensure start_date and end_date cover the entire day if only date is provided
    sql = """SELECT * FROM DoctorAvailability 
             WHERE doctor_id = ? 
             AND start_time >= ? 
             AND end_time <= ? 
             ORDER BY start_time"""
    try:
        cur = conn.cursor()
        # Assuming start_date and end_date are strings in 'YYYY-MM-DD' format
        # For DATETIME comparisons, you might need to append time parts if not already included
        # For simplicity, this example assumes full DATETIME strings or compatible date strings.
        cur.execute(sql, (doctor_id, start_date, end_date))
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error getting doctor availability: {e}")
        return []

def update_availability_slot_booked_status(conn, availability_id, is_booked):
    """Marks an availability slot as booked or not booked."""
    sql = "UPDATE DoctorAvailability SET is_booked = ?, last_updated_timestamp = CURRENT_TIMESTAMP WHERE availability_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (is_booked, availability_id))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error updating availability slot: {e}")
        return False

def delete_doctor_availability(conn, availability_id):
    """Deletes a doctor availability slot."""
    sql = "DELETE FROM DoctorAvailability WHERE availability_id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (availability_id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error deleting doctor availability: {e}")
        return False


# --- ConversationLogs CRUD ---
def add_conversation_log(conn, log_data):
    """Adds a new conversation log."""
    sql = '''INSERT INTO ConversationLogs(patient_id, session_id, message_text, intent_detected, entities_extracted)
             VALUES(?,?,?,?,?)'''
    try:
        cur = conn.cursor()
        entities = log_data.get('entities_extracted')
        if isinstance(entities, dict) or isinstance(entities, list):
            entities_json = json.dumps(entities)
        else:
            entities_json = entities # Assume it's already a JSON string or None

        cur.execute(sql, (
            log_data.get('patient_id'), # Can be None
            log_data.get('session_id'),
            log_data.get('message_text'),
            log_data.get('intent_detected'),
            entities_json
        ))
        conn.commit()
        return cur.lastrowid
    except sqlite3.Error as e:
        print(f"Database error adding conversation log: {e}")
        return None

def get_conversation_logs_for_patient(conn, patient_id):
    """Retrieves conversation logs for a patient."""
    sql = "SELECT * FROM ConversationLogs WHERE patient_id = ? ORDER BY log_timestamp"
    try:
        cur = conn.cursor()
        cur.execute(sql, (patient_id,))
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error getting patient conversation logs: {e}")
        return []

def get_conversation_logs_by_session(conn, session_id):
    """Retrieves logs for a specific session."""
    sql = "SELECT * FROM ConversationLogs WHERE session_id = ? ORDER BY log_timestamp"
    try:
        cur = conn.cursor()
        cur.execute(sql, (session_id,))
        return cur.fetchall()
    except sqlite3.Error as e:
        print(f"Database error getting session conversation logs: {e}")
        return []


if __name__ == '__main__':
    # Example Usage (for testing purposes)
    DB_FILE = 'hospital_management.db'

    # Clean up old DB file if it exists for fresh testing
    import os
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = create_connection(DB_FILE)

    if conn:
        # Test Patients
        patient1_id = add_patient(conn, {'first_name': 'John', 'last_name': 'Doe', 'date_of_birth': '1990-01-15', 'gender': 'Male', 'phone_number': '1234567890', 'email': 'john.doe@example.com', 'address': '123 Main St'})
        print(f"Added patient John Doe with ID: {patient1_id}")
        patient2_id = add_patient(conn, {'first_name': 'Jane', 'last_name': 'Smith', 'date_of_birth': '1985-05-20', 'gender': 'Female', 'phone_number': '0987654321', 'email': 'jane.smith@example.com', 'address': '456 Oak Ave'})
        print(f"Added patient Jane Smith with ID: {patient2_id}")

        retrieved_patient = get_patient(conn, patient1_id)
        if retrieved_patient:
            print(f"Retrieved patient: {dict(retrieved_patient)}")

        retrieved_patient_phone = get_patient_by_phone(conn, '0987654321')
        if retrieved_patient_phone:
            print(f"Retrieved patient by phone (Jane): {dict(retrieved_patient_phone)}")

        update_patient(conn, patient1_id, {'email': 'john.doe.new@example.com', 'address': '125 Main St Ext'})
        retrieved_patient_updated = get_patient(conn, patient1_id)
        if retrieved_patient_updated:
            print(f"Updated patient John: {dict(retrieved_patient_updated)}")

        # Test Doctors
        doctor1_id = add_doctor(conn, {'first_name': 'Alice', 'last_name': 'Brown', 'specialization': 'Cardiology', 'phone_number': '1112223333', 'email': 'alice.brown@hospital.com'})
        print(f"Added doctor Alice Brown with ID: {doctor1_id}")
        doctor2_id = add_doctor(conn, {'first_name': 'Bob', 'last_name': 'Green', 'specialization': 'Neurology', 'phone_number': '4445556666', 'email': 'bob.green@hospital.com'})
        print(f"Added doctor Bob Green with ID: {doctor2_id}")
        add_doctor(conn, {'first_name': 'Eve', 'last_name': 'White', 'specialization': 'Cardiology', 'phone_number': '7778889999', 'email': 'eve.white@hospital.com'})


        all_docs = get_all_doctors(conn)
        print(f"All doctors: {[dict(doc) for doc in all_docs]}")
        cardio_docs = get_doctors_by_specialization(conn, 'Cardiology')
        print(f"Cardiologists: {[dict(doc) for doc in cardio_docs]}")

        all_specializations = get_all_specializations(conn)
        print(f"All specializations: {all_specializations}")

        # Test Appointments
        # Note: These test appointments won't have a real availability_id from the DoctorAvailability table setup here.
        # In the agent flow, this would be a valid ID from a selected slot.
        appt1_id = add_appointment(conn, {'patient_id': patient1_id, 'doctor_id': doctor1_id, 'appointment_datetime': '2024-08-15 10:00:00', 'reason_for_visit': 'Chest pain', 'availability_id': None})
        print(f"Scheduled appointment {appt1_id}")
        appt2_id = add_appointment(conn, {'patient_id': patient2_id, 'doctor_id': doctor1_id, 'appointment_datetime': '2024-08-15 11:00:00', 'reason_for_visit': 'Regular checkup', 'availability_id': None})
        print(f"Scheduled appointment {appt2_id}")


        update_appointment_status(conn, appt1_id, 'Completed')
        updated_appt = get_appointment(conn, appt1_id)
        if updated_appt:
            print(f"Updated appointment 1: {dict(updated_appt)}")

        patient1_appts = get_appointments_for_patient(conn, patient1_id)
        print(f"John Doe's appointments: {[dict(appt) for appt in patient1_appts]}")

        doctor1_appts_today = get_appointments_for_doctor(conn, doctor1_id, date_filter='2024-08-15')
        print(f"Dr. Brown's appointments on 2024-08-15: {[dict(appt) for appt in doctor1_appts_today]}")

        # Test Doctor Availability
        avail1_id = add_doctor_availability(conn, {'doctor_id': doctor1_id, 'start_time': '2024-08-20 09:00:00', 'end_time': '2024-08-20 12:00:00'})
        print(f"Added availability slot {avail1_id} for Dr. Brown")
        avail2_id = add_doctor_availability(conn, {'doctor_id': doctor1_id, 'start_time': '2024-08-20 14:00:00', 'end_time': '2024-08-20 17:00:00'})
        print(f"Added availability slot {avail2_id} for Dr. Brown")

        dr1_avail = get_doctor_availability(conn, doctor1_id, '2024-08-20 00:00:00', '2024-08-20 23:59:59')
        print(f"Dr. Brown's availability on 2024-08-20: {[dict(av) for av in dr1_avail]}")
        update_availability_slot_booked_status(conn, avail1_id, True)
        print(f"Marked slot {avail1_id} as booked.")
        dr1_avail_updated = get_doctor_availability(conn, doctor1_id, '2024-08-20 00:00:00', '2024-08-20 23:59:59')
        print(f"Dr. Brown's updated availability: {[dict(av) for av in dr1_avail_updated]}")


        # Test Conversation Logs
        log1_id = add_conversation_log(conn, {'patient_id': patient1_id, 'session_id': 'session123', 'message_text': 'Hello, I want to book an appointment.', 'intent_detected': 'schedule_appointment', 'entities_extracted': {'symptom': 'headache'}})
        print(f"Added conversation log {log1_id}")
        log2_id = add_conversation_log(conn, {'session_id': 'session456', 'message_text': 'What are the hospital visiting hours?', 'intent_detected': 'query_visiting_hours', 'entities_extracted': None}) # Patient not yet identified
        print(f"Added conversation log {log2_id}")


        patient1_logs = get_conversation_logs_for_patient(conn, patient1_id)
        print(f"John Doe's conversation logs: {[dict(log) for log in patient1_logs]}")
        session_logs = get_conversation_logs_by_session(conn, 'session123')
        print(f"Session 'session123' logs: {[dict(log) for log in session_logs]}")

        # Test Deletions (optional, to check if functions run)
        # delete_appointment(conn, appt2_id)
        # print(f"Deleted appointment {appt2_id}")
        # delete_doctor_availability(conn, avail2_id)
        # print(f"Deleted availability {avail2_id}")
        # delete_patient(conn, patient2_id) # This might fail if patient has appointments, depending on FK constraints (not set to cascade in schema)
        # print(f"Attempted to delete patient {patient2_id}")


        conn.close()
        print("DB connection closed.")
    else:
        print("Failed to create database connection.")

    # To run this file directly: python database_manager.py
    # This will create 'hospital_management.db' in the same directory.
    # The example usage block will populate it with some test data.
    # You can then use an SQLite browser to inspect the database.
