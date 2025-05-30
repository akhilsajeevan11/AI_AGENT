# crew_definitions.py

"""
This file contains the definitions for CrewAI Agent Roles and Task Outlines
for the Hospital Administration Bot. These definitions serve as a blueprint
for the actual implementation of CrewAI agents and tasks.
"""

# ==========================================
# AGENT ROLE DEFINITIONS
# ==========================================

patient_onboarding_specialist_def = {
    "role": "Patient Onboarding Specialist",
    "goal": "Manage all aspects of patient information, primarily focusing on new patient registration and ensuring data accuracy. Handle patient data with confidentiality and precision.",
    "backstory": (
        "You are an experienced Patient Onboarding Specialist at a modern hospital. "
        "Your primary responsibility is to accurately and efficiently register new patients into the system. "
        "You are meticulous with details, understand the importance of correct patient data for medical care, "
        "and are trained in patient data privacy requirements. You use specialized tools to interact with the patient database."
    ),
    "allow_delegation": False, # Initially, keep simple. Could delegate to a "Data Verification Agent" in a complex setup.
    "tools_placeholder": ["add_new_patient_tool", "get_patient_by_phone_tool", "get_patient_by_email_tool"] # Example tool names
}

scheduling_coordinator_def = {
    "role": "Appointment Scheduling Coordinator",
    "goal": "Efficiently manage doctor appointments, including scheduling new appointments, processing cancellations, and facilitating rescheduling, while optimizing doctor availability and patient convenience.",
    "backstory": (
        "You are a highly organized Scheduling Coordinator for the hospital. You have real-time access to doctor schedules "
        "and patient appointment records. Your expertise lies in finding suitable appointment slots, managing the booking process, "
        "handling cancellations gracefully, and ensuring that doctor availability is always up-to-date. "
        "You use specialized tools for these tasks."
    ),
    "allow_delegation": False, # Could delegate finding availability to another agent if complex.
    "tools_placeholder": [
        "get_doctor_availability_tool", 
        "book_appointment_tool", 
        "update_appointment_status_tool", 
        "update_slot_booked_status_tool",
        "get_patient_appointments_tool" # To check existing appointments before rescheduling/cancelling
    ]
}

medical_records_clerk_def = {
    "role": "Medical Records Clerk",
    "goal": "Provide accurate and timely information regarding patient records and doctor schedules as permitted by hospital policy and privacy regulations.",
    "backstory": (
        "You are a diligent Medical Records Clerk with a strong understanding of the hospital's information systems. "
        "Your main task is to retrieve and present medical information, such as patient appointment lists or doctor specializations and availability, "
        "to authorized requestors or for internal processes. You are careful about data privacy and accuracy. "
        "You use specific query tools to access this information."
    ),
    "allow_delegation": False,
    "tools_placeholder": [
        "get_patient_by_phone_tool", 
        "get_patient_appointments_tool", 
        "get_all_doctors_tool", 
        "get_doctors_by_specialization_tool",
        "get_all_specializations_tool",
        "get_doctor_availability_tool"
    ]
}

# ==========================================
# TASK OUTLINE DEFINITIONS
# ==========================================

register_new_patient_task_def = {
    "description": (
        "Register a new patient in the hospital system. "
        "The user will provide the following patient details: {patient_details_json}. "
        "This JSON string contains: first_name, last_name, date_of_birth (YYYY-MM-DD), "
        "gender, phone_number, email, and address. "
        "Verify that essential details like phone_number and email are provided. "
        "Use the appropriate tool to add this patient to the database."
    ),
    "expected_output": (
        "A confirmation message stating successful registration, including the new patient's ID. "
        "If registration fails (e.g., due to an existing phone number or email, or missing critical information), "
        "return a clear error message explaining the reason for failure."
    ),
    "agent": patient_onboarding_specialist_def["role"] # Assign to the role name
}

schedule_appointment_task_def = {
    "description": (
        "Schedule a new appointment for a patient with a specified doctor. "
        "The required input details are provided in a JSON string: {appointment_details_json}. "
        "This includes: patient_id, doctor_id, desired_availability_slot_id (from previously fetched available slots), "
        "appointment_datetime (confirm this matches the start_time of the chosen availability_slot_id), "
        "duration_minutes (confirm this matches the duration of the chosen availability_slot_id), and reason_for_visit. "
        "Before booking, ensure the chosen availability_slot_id is still marked as not booked. "
        "If available, book the appointment using the tool and then update the chosen availability slot's status to 'booked'."
    ),
    "expected_output": (
        "A confirmation message including the new appointment_id, patient_id, doctor_id, the appointment datetime, "
        "and the reason_for_visit. "
        "If scheduling fails (e.g., slot just became unavailable, invalid IDs), "
        "return a clear error message indicating the failure."
    ),
    "agent": scheduling_coordinator_def["role"]
}

view_patient_appointments_task_def = {
    "description": (
        "Retrieve and list all appointments for a given patient. "
        "The patient will be identified by their patient_id: {patient_id}. "
        "Use the appropriate tool to fetch the appointment data."
    ),
    "expected_output": (
        "A list of the patient's appointments, including appointment ID, doctor's name, specialization, date, time, and status for each. "
        "If the patient has no appointments, return a message stating so. "
        "If the patient ID is invalid or not found, return an appropriate error message."
    ),
    "agent": medical_records_clerk_def["role"]
}

cancel_appointment_task_def = {
    "description": (
        "Cancel a specific 'Scheduled' appointment for a patient. "
        "The appointment to be cancelled is identified by its appointment_id: {appointment_id}. "
        "The patient is identified by patient_id: {patient_id} (for verification, optional). "
        "The task involves updating the appointment's status to 'Cancelled'. "
        "Crucially, if the appointment was linked to a specific doctor availability slot (identified by {availability_id} associated with the appointment), "
        "that availability slot must be marked as 'is_booked = False' to make it available again."
    ),
    "expected_output": (
        "A confirmation message stating that the appointment (ID: {appointment_id}) has been successfully cancelled. "
        "If an associated availability slot was released, this should also be confirmed. "
        "If cancellation fails (e.g., appointment not found, already cancelled/completed, or database error), "
        "return a clear error message."
    ),
    "agent": scheduling_coordinator_def["role"]
}

reschedule_appointment_task_def = {
    "description": (
        "Reschedule an existing 'Scheduled' appointment for a patient. "
        "This is a multi-step process: "
        "1. Identify the appointment to be rescheduled using its appointment_id: {old_appointment_id}. "
        "   Also note its associated {old_availability_id}. "
        "2. Guide the user through cancelling this old appointment (effectively performing the 'cancel_appointment_task_def' logic for it, "
        "   which includes making the old_availability_id slot available again). "
        "3. Guide the user through scheduling a new appointment using the details provided in {new_appointment_details_json} "
        "   (similar to 'schedule_appointment_task_def', including selecting a new doctor, date, time, and a new {new_availability_id}). "
        "The patient is identified by patient_id: {patient_id}."
    ),
    "expected_output": (
        "A confirmation message detailing the cancellation of the old appointment and the confirmation of the new appointment "
        "(including new appointment ID, doctor, date, time). "
        "If any step fails (e.g., old appointment not found, new slot unavailable), provide clear error messages for that step. "
        "The final output should summarize the outcome of both cancellation and new booking attempts."
    ),
    "agent": scheduling_coordinator_def["role"] # This agent coordinates both cancellation and new scheduling
}

find_doctor_availability_task_def = {
    "description": (
        "Find all available (not booked) time slots for a specific doctor within a given date range. "
        "Required input: doctor_id: {doctor_id}, start_date (YYYY-MM-DD): {start_date}, end_date (YYYY-MM-DD): {end_date}. "
        "Use the appropriate tool to query the DoctorAvailability table."
    ),
    "expected_output": (
        "A list of available time slots, each including availability_id, start_time, and end_time. "
        "If no slots are available for the doctor in the given range, return an empty list or a message stating so. "
        "If the doctor_id is invalid, return an error message."
    ),
    "agent": medical_records_clerk_def["role"] # Or SchedulingCoordinator, depending on workflow. Medical Records seems fit for just querying.
}

# Placeholder for a task to get doctor specializations
get_doctor_specializations_task_def = {
    "description": "Retrieve a list of all unique doctor specializations available in the hospital.",
    "expected_output": "A list of strings, where each string is a unique doctor specialization. Returns an empty list if no specializations are found.",
    "agent": medical_records_clerk_def["role"]
}

# Placeholder for a task to get doctors by specialization
get_doctors_by_specialization_task_def = {
    "description": "Retrieve a list of doctors practicing a specific specialization: {specialization}.",
    "expected_output": "A list of doctor objects/dictionaries matching the specialization, including their ID, first name, and last name. Returns an empty list if no doctors match.",
    "agent": medical_records_clerk_def["role"]
}

# Placeholder for a task to identify patient by phone
identify_patient_by_phone_task_def = {
    "description": "Identify and retrieve patient details using their phone number: {phone_number}.",
    "expected_output": "A patient object/dictionary including patient_id, first_name, last_name, and other details if found. Returns null or an error message if no patient is found with that phone number.",
    "agent": patient_onboarding_specialist_def["role"] # Could also be Medical Records Clerk
}
