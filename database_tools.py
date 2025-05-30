import sqlite3
import json
from typing import Type, Optional, List, Dict, Any
from langchain.tools import Tool, StructuredTool # Import StructuredTool
from pydantic import BaseModel, Field

import database_manager as db_manager # Local module

# --- Database Connection Handling ---
# In a more complex setup, this might involve a connection pool or a shared connection.
# For simplicity, each tool func will get a new connection for now.
# This also ensures thread safety if tools were run in parallel, though SQLite itself has limitations there.
DB_FILE = "hospital_management.db"

def _get_db_connection():
    """Establishes and returns a new database connection."""
    # Suppress print from create_connection during tool use for cleaner LLM interactions
    # This is a bit of a hack; ideally, db_manager.create_connection wouldn't print directly
    # or would have a verbosity setting.
    original_print = None
    if hasattr(db_manager, 'print') and callable(db_manager.print): # Should not exist, print is a builtin
        pass # db_manager.print does not exist.
    
    # The print is from the builtin, so we'd have to patch sys.stdout to fully suppress it from tests/tools
    # For now, we accept that the db_manager's create_connection WILL print.
    # In a real scenario, we'd refactor db_manager.create_connection.
    conn = db_manager.create_connection(DB_FILE)
    if conn is None:
        raise ConnectionError(f"Failed to connect to database: {DB_FILE}")
    return conn

def _execute_db_operation(func, *args, **kwargs):
    """A wrapper to handle DB connection and closing for each tool operation."""
    conn = None
    try:
        conn = _get_db_connection()
        result = func(conn, *args, **kwargs)
        # For functions that return complex sqlite3.Row objects, convert them to dicts
        if isinstance(result, sqlite3.Row):
            return dict(result)
        if isinstance(result, list) and result and isinstance(result[0], sqlite3.Row):
            return [dict(row) for row in result]
        return result
    except Exception as e:
        # Log the exception or return a user-friendly error message
        return f"Database operation failed: {str(e)}"
    finally:
        if conn:
            conn.close()

# --- Pydantic Schemas for Tool Arguments ---

class PatientIdArgs(BaseModel):
    patient_id: int = Field(description="The unique identifier for the patient.")

class PatientPhoneNumberArgs(BaseModel):
    phone_number: str = Field(description="The patient's phone number.")

class AddPatientArgs(BaseModel):
    first_name: str = Field(description="Patient's first name.")
    last_name: str = Field(description="Patient's last name.")
    date_of_birth: str = Field(description="Patient's date of birth (YYYY-MM-DD).")
    gender: str = Field(description="Patient's gender.")
    phone_number: str = Field(description="Patient's phone number (must be unique).")
    email: str = Field(description="Patient's email address (must be unique).")
    address: str = Field(description="Patient's full address.")

class UpdatePatientArgs(BaseModel):
    patient_id: int = Field(description="The ID of the patient to update.")
    updated_data: Dict[str, Any] = Field(description="A dictionary containing the fields to update and their new values. Valid fields are: first_name, last_name, date_of_birth, gender, phone_number, email, address.")

class DoctorIdArgs(BaseModel):
    doctor_id: int = Field(description="The unique identifier for the doctor.")

class DoctorSpecializationArgs(BaseModel):
    specialization: str = Field(description="The medical specialization of the doctor(s) to search for.")

class AddDoctorArgs(BaseModel):
    first_name: str = Field(description="Doctor's first name.")
    last_name: str = Field(description="Doctor's last name.")
    specialization: str = Field(description="Doctor's medical specialization.")
    phone_number: str = Field(description="Doctor's phone number (must be unique).")
    email: str = Field(description="Doctor's email address (must be unique).")
    
class GetDoctorAvailabilityArgs(BaseModel):
    doctor_id: int = Field(description="The ID of the doctor.")
    start_date: str = Field(description="The start date of the range to check for availability (YYYY-MM-DD HH:MM:SS or YYYY-MM-DD). If only date, time will be assumed as 00:00:00.")
    end_date: str = Field(description="The end date of the range to check for availability (YYYY-MM-DD HH:MM:SS or YYYY-MM-DD). If only date, time will be assumed as 23:59:59.")

class UpdateAvailabilitySlotBookedStatusArgs(BaseModel):
    availability_id: int = Field(description="The ID of the availability slot to update.")
    is_booked: bool = Field(description="Set to true if the slot is booked, false if it's available.")

class AddAppointmentArgs(BaseModel):
    patient_id: int = Field(description="The ID of the patient for the appointment.")
    doctor_id: int = Field(description="The ID of the doctor for the appointment.")
    appointment_datetime: str = Field(description="The date and time for the appointment (YYYY-MM-DD HH:MM:SS). This should match the start_time of the chosen availability slot.")
    duration_minutes: Optional[int] = Field(30, description="Duration of the appointment in minutes. Defaults to 30.")
    reason_for_visit: str = Field(description="The reason for the patient's visit.")
    availability_id: int = Field(description="The ID of the specific doctor availability slot being booked.")

class AppointmentIdArgs(BaseModel):
    appointment_id: int = Field(description="The unique identifier for the appointment.")

class UpdateAppointmentStatusArgs(BaseModel):
    appointment_id: int = Field(description="The ID of the appointment to update.")
    status: str = Field(description="The new status for the appointment (e.g., 'Scheduled', 'Completed', 'Cancelled').")

class AddConversationLogArgs(BaseModel):
    session_id: str = Field(description="The unique identifier for the current user session.")
    message_text: str = Field(description="The text of the message or a description of the event being logged.")
    intent_detected: Optional[str] = Field(None, description="The intent detected by the agent for this interaction.")
    entities_extracted: Optional[Dict[str, Any]] = Field(None, description="A dictionary of entities extracted from the user's message or relevant to the event.")
    patient_id: Optional[int] = Field(None, description="The ID of the patient involved, if applicable.")


# --- Tool Definitions ---

# Wrapper functions for tool execution
def _add_patient_wrapper(first_name: str, last_name: str, date_of_birth: str, gender: str, phone_number: str, email: str, address: str) -> Any:
    patient_data = {
        "first_name": first_name, "last_name": last_name, "date_of_birth": date_of_birth,
        "gender": gender, "phone_number": phone_number, "email": email, "address": address
    }
    return _execute_db_operation(db_manager.add_patient, patient_data=patient_data)

def _get_patient_by_phone_wrapper(phone_number: str) -> Any:
    return _execute_db_operation(db_manager.get_patient_by_phone, phone_number=phone_number)

def _update_patient_wrapper(patient_id: int, updated_data: Dict[str, Any]) -> Any:
    return _execute_db_operation(db_manager.update_patient, patient_id=patient_id, updated_data=updated_data)

def _add_doctor_wrapper(first_name: str, last_name: str, specialization: str, phone_number: str, email: str) -> Any:
    doctor_data = {
        "first_name": first_name, "last_name": last_name, "specialization": specialization,
        "phone_number": phone_number, "email": email
    }
    return _execute_db_operation(db_manager.add_doctor, doctor_data=doctor_data)

def _get_all_doctors_wrapper() -> Any: # No args
    return _execute_db_operation(db_manager.get_all_doctors)

def _get_doctors_by_specialization_wrapper(specialization: str) -> Any:
    return _execute_db_operation(db_manager.get_doctors_by_specialization, specialization=specialization)

def _get_all_specializations_wrapper() -> Any: # No args
    return _execute_db_operation(db_manager.get_all_specializations)

def _get_doctor_availability_wrapper(doctor_id: int, start_date: str, end_date: str) -> Any:
    return _execute_db_operation(db_manager.get_doctor_availability, doctor_id=doctor_id, start_date=start_date, end_date=end_date)

def _update_availability_slot_booked_status_wrapper(availability_id: int, is_booked: bool) -> Any:
    return _execute_db_operation(db_manager.update_availability_slot_booked_status, availability_id=availability_id, is_booked=is_booked)

def _add_appointment_wrapper(patient_id: int, doctor_id: int, appointment_datetime: str, reason_for_visit: str, availability_id: int, duration_minutes: Optional[int] = 30) -> Any:
    appointment_data = {
        "patient_id": patient_id, "doctor_id": doctor_id,
        "appointment_datetime": appointment_datetime, "duration_minutes": duration_minutes,
        "reason_for_visit": reason_for_visit, "availability_id": availability_id
    }
    return _execute_db_operation(db_manager.add_appointment, appointment_data=appointment_data)

def _get_appointments_for_patient_wrapper(patient_id: int) -> Any:
    return _execute_db_operation(db_manager.get_appointments_for_patient, patient_id=patient_id)

def _update_appointment_status_wrapper(appointment_id: int, status: str) -> Any:
    return _execute_db_operation(db_manager.update_appointment_status, appointment_id=appointment_id, status=status)

def _add_conversation_log_wrapper(session_id: str, message_text: str, intent_detected: Optional[str] = None, entities_extracted: Optional[Dict[str, Any]] = None, patient_id: Optional[int] = None) -> Any:
    log_data = {
        "session_id": session_id, "message_text": message_text,
        "intent_detected": intent_detected, "entities_extracted": entities_extracted,
        "patient_id": patient_id
    }
    return _execute_db_operation(db_manager.add_conversation_log, log_data=log_data)


# Patient Tools
add_patient_tool = StructuredTool.from_function(
    func=_add_patient_wrapper,
    name="add_new_patient",
    description="Adds a new patient to the hospital system. Use this when a user explicitly requests to register as a new patient and provides all necessary details. All fields in the arguments are required.",
    args_schema=AddPatientArgs
)

get_patient_by_phone_tool = StructuredTool.from_function(
    func=_get_patient_by_phone_wrapper,
    name="get_patient_by_phone_number",
    description="Retrieves patient details from the database using their unique phone number. Use this to check if a patient exists or to fetch their details for other operations.",
    args_schema=PatientPhoneNumberArgs
)

update_patient_tool = StructuredTool.from_function(
    func=_update_patient_wrapper,
    name="update_patient_details",
    description="Updates specified details for an existing patient identified by their patient_id. Only include fields to be updated in the updated_data dictionary.",
    args_schema=UpdatePatientArgs
)

# Doctor Tools
add_doctor_tool = StructuredTool.from_function(
    func=_add_doctor_wrapper,
    name="add_new_doctor",
    description="Adds a new doctor to the hospital system. All fields are required.",
    args_schema=AddDoctorArgs
)

get_all_doctors_tool = StructuredTool.from_function(
    func=_get_all_doctors_wrapper,
    name="get_all_doctors",
    description="Retrieves a list of all doctors registered in the hospital system, including their details like ID, name, specialization, phone, and email.",
    args_schema=None # Explicitly no args
)

get_doctors_by_specialization_tool = StructuredTool.from_function(
    func=_get_doctors_by_specialization_wrapper, # Signature now matches schema fields
    name="get_doctors_by_specialization",
    description="Retrieves a list of doctors who match a specific medical specialization. Useful for finding appropriate doctors for a patient's needs.",
    args_schema=DoctorSpecializationArgs
)

get_all_specializations_tool = StructuredTool.from_function(
    func=_get_all_specializations_wrapper,
    name="get_all_doctor_specializations",
    description="Retrieves a list of all unique medical specializations available from the doctors in the hospital system.",
    args_schema=None # Explicitly no args
)

# Doctor Availability Tools
get_doctor_availability_tool = StructuredTool.from_function(
    func=_get_doctor_availability_wrapper,
    name="get_doctor_availability",
    description="Retrieves the available (booked or unbooked) time slots for a specific doctor within a given date range. Dates should be in 'YYYY-MM-DD HH:MM:SS' format for full specificity, or 'YYYY-MM-DD' (time will be assumed 00:00:00 for start and 23:59:59 for end).",
    args_schema=GetDoctorAvailabilityArgs
)

update_availability_slot_booked_status_tool = StructuredTool.from_function(
    func=_update_availability_slot_booked_status_wrapper,
    name="update_doctor_availability_slot_status",
    description="Updates the booking status of a specific doctor availability slot (e.g., marks it as booked or available). This is critical after scheduling or cancelling an appointment linked to a slot.",
    args_schema=UpdateAvailabilitySlotBookedStatusArgs
)

# Appointment Tools
add_appointment_tool = StructuredTool.from_function(
    func=_add_appointment_wrapper,
    name="schedule_new_appointment",
    description="Schedules a new appointment for a patient with a doctor, linking it to a specific availability slot. All arguments are required.",
    args_schema=AddAppointmentArgs
)

get_appointments_for_patient_tool = StructuredTool.from_function(
    func=_get_appointments_for_patient_wrapper,
    name="get_patient_appointments",
    description="Retrieves a list of all appointments (past and future, with their status) for a specific patient using their patient ID.",
    args_schema=PatientIdArgs
)

# get_appointments_for_doctor_tool # Could be added if an agent needs it. For now, focusing on patient-centric tools for Crew.

update_appointment_status_tool = StructuredTool.from_function(
    func=_update_appointment_status_wrapper,
    name="update_appointment_status",
    description="Updates the status of an existing appointment (e.g., to 'Scheduled', 'Completed', 'Cancelled').",
    args_schema=UpdateAppointmentStatusArgs
)

# ConversationLog Tool
add_conversation_log_tool = StructuredTool.from_function(
    func=_add_conversation_log_wrapper,
    name="add_conversation_log_entry",
    description="Adds an entry to the conversation log. Useful for auditing agent actions, decisions, or important user interactions. All fields are optional but session_id and message_text are highly recommended.",
    args_schema=AddConversationLogArgs
)


# --- List of all tools for easy import by agents/crew ---
all_database_tools = [
    add_patient_tool,
    get_patient_by_phone_tool,
    update_patient_tool, # Added
    add_doctor_tool,    # Added
    get_all_doctors_tool,
    get_doctors_by_specialization_tool,
    get_all_specializations_tool,
    get_doctor_availability_tool,
    update_availability_slot_booked_status_tool,
    add_appointment_tool,
    get_appointments_for_patient_tool,
    update_appointment_status_tool,
    add_conversation_log_tool,
]

# --- Basic Sanity Check ---
if __name__ == '__main__':
    print("Performing basic sanity checks for database tools...")

    # Test: Add a new patient
    print("\nTesting add_new_patient tool...")
    new_patient_data = AddPatientArgs(
        first_name="ToolTest", last_name="User", date_of_birth="1999-01-01",
        gender="Other", phone_number="0001112223", email="tooltest.user@example.com",
        address="123 Tool Test Lane"
    )
    # For StructuredTool, the input to tool.run() should be a dictionary where keys match the Pydantic model fields.
    patient_id_result = add_patient_tool.run(new_patient_data.model_dump())
    print(f"Add Patient Result: {patient_id_result}")

    test_patient_id = None
    if isinstance(patient_id_result, int):
        test_patient_id = patient_id_result
    elif isinstance(patient_id_result, str) and "operation failed" not in patient_id_result.lower(): # Check for failure message
        try:
            test_patient_id = int(patient_id_result) # If it returns ID as string
        except ValueError:
            print(f"Could not parse patient_id from result: {patient_id_result}")

    if test_patient_id:
        # Test: Get patient by phone
        print("\nTesting get_patient_by_phone_number tool...")
        # For StructuredTool where func directly takes args from schema, pass dict directly
        patient_details_result = get_patient_by_phone_tool.run({"phone_number": "0001112223"})
        print(f"Get Patient by Phone Result: {patient_details_result}")

        # Test: Get all specializations (relies on db_manager.py populating some doctors)
        print("\nTesting get_all_doctor_specializations tool...")
        specs_result = get_all_specializations_tool.run({}) # No args needed
        print(f"Get All Specializations Result: {specs_result}")

        # Test: Add a conversation log
        print("\nTesting add_conversation_log_entry tool...")
        log_entry_data_dict = AddConversationLogArgs(
            session_id="sanity_check_session_001",
            message_text="Sanity check for add_conversation_log_tool.",
            intent_detected="tool_sanity_check",
            entities_extracted={"tool_name": "add_conversation_log_tool"},
            patient_id=test_patient_id
        ).model_dump()
        # Filter out None values for optional fields if the wrapper expects them to be absent not None
        log_entry_data_dict_cleaned = {k: v for k, v in log_entry_data_dict.items() if v is not None}
        log_id_result = add_conversation_log_tool.run(log_entry_data_dict_cleaned)
        print(f"Add Conversation Log Result: {log_id_result}")
    else:
        print("Patient ID not retrieved from add_new_patient tool, skipping further dependent tests.")
    
    print("\nBasic sanity checks complete. Review output for success/failure messages.")
