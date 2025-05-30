import database_manager as db_manager
import uuid
from datetime import datetime, timedelta

DB_FILE = 'hospital_management.db'
# Global connection object
conn = None 
current_session_id = None

def log_conversation(patient_id, intent, message, entities=None):
    """Logs a message to the ConversationLogs table."""
    global current_session_id
    if not conn or not current_session_id:
        return
    
    # Basic sanitization/check for entities
    final_entities = {}
    if isinstance(entities, dict):
        for key, value in entities.items():
            if isinstance(key, str) and (isinstance(value, (str, int, float, bool)) or value is None):
                final_entities[key] = value
            # else:
                # print(f"Warning: Entity '{key}' with complex value type '{type(value)}' not logged in detail.")
    
    log_data = {
        'patient_id': patient_id,
        'session_id': current_session_id,
        'message_text': str(message)[:1000], # Limit message length
        'intent_detected': str(intent)[:255], # Limit intent length
        'entities_extracted': final_entities # Use sanitized entities
    }
    db_manager.add_conversation_log(conn, log_data)

def get_input(prompt, patient_id_for_log=None, intent_for_input_log=None): # Simplified logging from get_input
    """Gets user input and optionally logs the act of asking for this input."""
    # Avoid logging the actual user's raw input here directly to prevent over-logging sensitive data.
    # Specific important inputs can be logged by the calling function after validation/use.
    # if intent_for_input_log and patient_id_for_log: # Decided against this level of verbosity for now
    #     log_conversation(patient_id_for_log, intent_for_input_log, f"Prompted user: {prompt}", {})
    user_input = input(prompt).strip()
    return user_input

def handle_patient_registration():
    """Handles the patient registration flow."""
    # TODO: Add authentication/authorization check here in a production system (e.g., is an admin doing this?)
    print("\n--- Patient Registration ---")
    first_name = get_input("Enter your first name: ")
    last_name = get_input("Enter your last name: ")
    dob_str = get_input("Enter your date of birth (YYYY-MM-DD): ")
    gender = get_input("Enter your gender: ")
    phone_number = get_input("Enter your phone number: ")
    email = get_input("Enter your email: ")
    address = get_input("Enter your address: ")

    patient_data_for_db = {
        'first_name': first_name, 'last_name': last_name, 'date_of_birth': dob_str,
        'gender': gender, 'phone_number': phone_number, 'email': email, 'address': address
    }
    
    log_conversation(None, "audit_attempt_patient_registration", f"Attempting patient registration for phone: {phone_number}, email: {email}.", {'phone': phone_number, 'email': email})

    patient_id = db_manager.add_patient(conn, patient_data_for_db)

    if patient_id:
        print(f"\nPatient {first_name} {last_name} registered successfully with ID: {patient_id}!")
        log_conversation(patient_id, "audit_patient_registered", f"Patient registered successfully.", {'patient_id': patient_id})
    else:
        print("\nRegistration failed. Phone number or email might already exist. Please check your details.")
        log_conversation(None, "audit_patient_registration_failed", f"Patient registration failed for phone: {phone_number}, email: {email}.", {'phone': phone_number, 'email': email})

def handle_appointment_scheduling():
    """Handles the appointment scheduling flow."""
    # TODO: Add authentication/authorization check here in a production system.
    global current_session_id
    print("\n--- Schedule Appointment ---")
    
    patient_id = None
    # Log the prompt for phone number, but not the actual number here
    log_conversation(None, "schedule_appt_prompt_patient_phone", "Prompted for patient phone or 'new'.")
    patient_phone = get_input("Enter your phone number to find your record, or type 'new' if you are a new patient: ")

    if patient_phone.lower() == 'new':
        log_conversation(None, "schedule_appt_new_patient_flow_selected", "User indicated they are a new patient.")
        print("Please register first.")
        handle_patient_registration() # This function has its own logging
        
        # After registration, try to get patient_id again
        log_conversation(None, "schedule_appt_prompt_confirm_phone_after_reg", "Prompting for phone number again post-registration.")
        new_phone = get_input("Enter your phone number again to confirm: ")
        # Log the attempt to find the newly registered patient by the confirmed phone
        log_conversation(None, "schedule_appt_find_patient_by_confirmed_phone", f"Attempting to find patient by confirmed phone: {new_phone}.")

        patient_record = db_manager.get_patient_by_phone(conn, new_phone)
        if patient_record:
            patient_id = patient_record['patient_id']
            log_conversation(patient_id, "schedule_appt_found_patient_after_reg", "Successfully found patient after registration.", {'patient_id': patient_id})
        else:
            print("Could not find your record after registration. Please try scheduling again.")
            log_conversation(None, "schedule_appt_fail_after_reg", f"Failed to find patient by phone {new_phone} after registration flow.")
            return
    else:
        # Log the attempt to find an existing patient by the provided phone number
        log_conversation(None, "schedule_appt_find_existing_patient_by_phone", f"Attempting to find existing patient by phone: {patient_phone}.")
        patient_record = db_manager.get_patient_by_phone(conn, patient_phone)
        if patient_record:
            patient_id = patient_record['patient_id']
            print(f"Welcome back, {patient_record['first_name']} {patient_record['last_name']} (ID: {patient_id}).")
            log_conversation(patient_id, "schedule_appt_existing_patient_found", "Found existing patient.", {'patient_id': patient_id})
        else:
            log_conversation(None, "schedule_appt_existing_patient_not_found", f"Patient not found for phone: {patient_phone}.")
            print("Patient record not found. Would you like to register?")
            choice = get_input("(yes/no): ")
            log_conversation(None, "schedule_appt_prompt_register_after_not_found", f"Prompted for registration, user choice: {choice}.")
            if choice.lower() == 'yes':
                handle_patient_registration() # This function has its own logging
                log_conversation(None, "schedule_appt_prompt_confirm_phone_after_reg_option", "Prompting for phone number again post-registration (option path).")
                new_phone = get_input("Enter your phone number again to confirm: ") # Assume they use the same phone
                log_conversation(None, "schedule_appt_find_patient_by_confirmed_phone_option", f"Attempting to find patient by confirmed phone: {new_phone} (option path).")
                patient_record = db_manager.get_patient_by_phone(conn, new_phone)
                if patient_record:
                    patient_id = patient_record['patient_id']
                    log_conversation(patient_id, "schedule_appt_found_patient_after_reg_option", "Successfully found patient after registration (option path).", {'patient_id': patient_id})
                else:
                    print("Could not find your record after registration. Please try scheduling again.")
                    log_conversation(None, "schedule_appt_fail_after_reg_option", f"Failed to find patient by phone {new_phone} after registration flow (option path).")
                    return
            else:
                print("Cannot schedule appointment without a patient record.")
                log_conversation(None, "schedule_appt_declined_registration", "User declined registration, cannot schedule appointment.")
                return

    if not patient_id:
        print("Failed to identify patient. Cannot schedule appointment.")
        return

    # List specializations
    specializations = db_manager.get_all_specializations(conn)
    if not specializations:
        print("No doctor specializations available at the moment.")
        log_conversation(patient_id, "schedule_appt_no_specializations_found", "No doctor specializations available in DB.", {'patient_id': patient_id})
        return

    print("\nAvailable Specializations:")
    for i, spec in enumerate(specializations):
        print(f"{i + 1}. {spec}")
    
    selected_specialization = None
    while not selected_specialization:
        try:
            spec_choice_input = get_input(f"Choose a specialization number (1-{len(specializations)}): ", patient_id)
            spec_choice = int(spec_choice_input)
            if 1 <= spec_choice <= len(specializations):
                selected_specialization = specializations[spec_choice - 1]
                log_conversation(patient_id, "schedule_appt_specialization_selected", f"User selected specialization: {selected_specialization}.", {'patient_id': patient_id, 'specialization': selected_specialization})
            else:
                print("Invalid choice. Please enter a number from the list.")
                log_conversation(patient_id, "schedule_appt_invalid_specialization_choice_oor", "User specialization choice out of range.", {'patient_id': patient_id, 'input': spec_choice_input})
        except ValueError:
            print("Invalid input. Please enter a number.")
            log_conversation(patient_id, "schedule_appt_invalid_specialization_choice_nan", "User specialization choice not a number.", {'patient_id': patient_id, 'input': spec_choice_input})

    # List doctors for that specialization
    doctors = db_manager.get_doctors_by_specialization(conn, selected_specialization)
    if not doctors:
        print(f"No doctors found for {selected_specialization}.")
        log_conversation(patient_id, "schedule_appt_no_doctors_for_specialization", f"No doctors found for specialization: {selected_specialization}.", {'patient_id': patient_id, 'specialization': selected_specialization})
        return

    print(f"\nAvailable Doctors for {selected_specialization}:")
    for i, doc in enumerate(doctors):
        print(f"{i + 1}. Dr. {doc['first_name']} {doc['last_name']}")

    selected_doctor = None
    while not selected_doctor:
        try:
            doc_choice_input = get_input(f"Choose a doctor number (1-{len(doctors)}): ", patient_id)
            doc_choice_idx = int(doc_choice_input) -1
            if 0 <= doc_choice_idx < len(doctors):
                selected_doctor = doctors[doc_choice_idx]
                log_conversation(patient_id, "schedule_appt_doctor_selected", f"User selected doctor ID: {selected_doctor['doctor_id']}.", {'patient_id': patient_id, 'doctor_id': selected_doctor['doctor_id']})
            else:
                print("Invalid choice. Please enter a number from the list.")
                log_conversation(patient_id, "schedule_appt_invalid_doctor_choice_oor", "User doctor choice out of range.", {'patient_id': patient_id, 'input': doc_choice_input})
        except ValueError:
            print("Invalid input. Please enter a number.")
            log_conversation(patient_id, "schedule_appt_invalid_doctor_choice_nan", "User doctor choice not a number.", {'patient_id': patient_id, 'input': doc_choice_input})
    
    doctor_id = selected_doctor['doctor_id']

    # Get availability
    date_str = get_input("Enter desired date for appointment (YYYY-MM-DD): ", patient_id)
    log_conversation(patient_id, "schedule_appt_date_provided", f"User provided date: {date_str}.", {'patient_id': patient_id, 'date_str': date_str})
    try:
        # Validate date format somewhat
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
        log_conversation(patient_id, "schedule_appt_invalid_date_format", f"User entered invalid date format: {date_str}.", {'patient_id': patient_id, 'date_str': date_str})
        return

    # For SQLite, DATETIME comparisons require full datetime strings.
    # We'll query for the whole day.
    start_datetime_str = f"{date_str} 00:00:00"
    end_datetime_str = f"{date_str} 23:59:59"
    
    log_conversation(patient_id, "schedule_appt_querying_availability", f"Querying availability for Dr. {doctor_id} between {start_datetime_str} and {end_datetime_str}.", {'patient_id': patient_id, 'doctor_id': doctor_id, 'start_time': start_datetime_str, 'end_time': end_datetime_str})
    availability_slots = db_manager.get_doctor_availability(conn, doctor_id, start_datetime_str, end_datetime_str)
    
    available_slots_for_booking = [slot for slot in availability_slots if not slot['is_booked']]

    if not available_slots_for_booking:
        print(f"Sorry, Dr. {selected_doctor['first_name']} {selected_doctor['last_name']} has no available slots on {date_str}.")
        log_conversation(patient_id, "schedule_appt_no_slots_found_for_doctor_date", f"No available slots found for Dr. {doctor_id} on {date_str}.", {'patient_id': patient_id, 'doctor_id': doctor_id, 'date': date_str})
        return

    print("\nAvailable Slots:")
    for i, slot in enumerate(available_slots_for_booking):
        slot_start_dt = datetime.strptime(slot['start_time'], '%Y-%m-%d %H:%M:%S')
        slot_end_dt = datetime.strptime(slot['end_time'], '%Y-%m-%d %H:%M:%S')
        print(f"{i + 1}. {slot_start_dt.strftime('%H:%M')} - {slot_end_dt.strftime('%H:%M')} (ID: {slot['availability_id']})")

    selected_slot = None
    while not selected_slot:
        try:
            slot_choice_input = get_input(f"Choose a slot number (1-{len(available_slots_for_booking)}): ", patient_id)
            slot_choice_idx = int(slot_choice_input) - 1
            if 0 <= slot_choice_idx < len(available_slots_for_booking):
                selected_slot = available_slots_for_booking[slot_choice_idx]
                log_conversation(patient_id, "schedule_appt_slot_selected", f"User selected slot ID: {selected_slot['availability_id']}.", {'patient_id': patient_id, 'availability_id': selected_slot['availability_id']})
            else:
                print("Invalid choice. Please enter a number from the list.")
                log_conversation(patient_id, "schedule_appt_invalid_slot_choice_oor", "User slot choice out of range.", {'patient_id': patient_id, 'input': slot_choice_input})
        except ValueError:
            print("Invalid input. Please enter a number.")
            log_conversation(patient_id, "schedule_appt_invalid_slot_choice_nan", "User slot choice not a number.", {'patient_id': patient_id, 'input': slot_choice_input})
            
    reason_for_visit = get_input("Reason for visit: ", patient_id)
    # Log the reason separately if it's considered sensitive and needs specific handling or if it's okay for message_text
    log_conversation(patient_id, "schedule_appt_reason_provided", f"Reason for visit provided by user (length: {len(reason_for_visit)}).", {'patient_id': patient_id, 'reason_length': len(reason_for_visit)})

    appointment_data_for_db = {
        'patient_id': patient_id,
        'doctor_id': doctor_id,
        'appointment_datetime': selected_slot['start_time'], 
        'duration_minutes': int((datetime.strptime(selected_slot['end_time'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(selected_slot['start_time'], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60),
        'reason_for_visit': reason_for_visit, # This is sensitive, but part of the appointment
        'status': 'Scheduled',
        'availability_id': selected_slot['availability_id']
    }
    
    log_entities_for_sched = {
        'patient_id': patient_id, 
        'doctor_id': doctor_id, 
        'availability_id': selected_slot['availability_id'], 
        'appointment_time': selected_slot['start_time']
    }
    log_conversation(patient_id, "audit_attempt_schedule_appointment", f"Attempting to schedule appointment for patient {patient_id}, doctor {doctor_id}, slot {selected_slot['availability_id']}.", log_entities_for_sched)
    appointment_id = db_manager.add_appointment(conn, appointment_data_for_db)

    if appointment_id:
        booked_success = db_manager.update_availability_slot_booked_status(conn, selected_slot['availability_id'], True)
        if booked_success:
            print(f"\nAppointment scheduled successfully with Dr. {selected_doctor['first_name']} {selected_doctor['last_name']} on {selected_slot['start_time']}.")
            print(f"Appointment ID: {appointment_id}. Slot ID: {selected_slot['availability_id']} marked as booked.")
            log_conversation(patient_id, "audit_appointment_scheduled", "Appointment scheduled and slot marked as booked.", 
                             {'patient_id': patient_id, 'appointment_id': appointment_id, 'doctor_id': doctor_id, 'availability_id': selected_slot['availability_id']})
        else:
            print(f"\nAppointment scheduled (ID: {appointment_id}), but failed to mark the time slot as booked. Please contact administration.")
            log_conversation(patient_id, "audit_appointment_scheduled_slot_update_failed", "Appointment scheduled but slot update failed.", 
                             {'patient_id': patient_id, 'appointment_id': appointment_id, 'availability_id': selected_slot['availability_id']})
    else:
        print("\nFailed to schedule appointment. The slot might have just been taken or there was a database error.")
        log_conversation(patient_id, "audit_schedule_appointment_failed", "Failed to add appointment to DB.", log_entities_for_sched)


def handle_view_appointments():
    """Handles viewing patient appointments."""
    # TODO: Add authentication/authorization check here in a production system.
    print("\n--- View Appointments ---")
    log_conversation(None, "view_appts_prompt_phone", "Prompted for phone to view appointments.")
    phone_number = get_input("Enter your phone number: ")
    
    patient = db_manager.get_patient_by_phone(conn, phone_number)
    if not patient:
        print("No patient found with this phone number.")
        log_conversation(None, "view_appts_patient_not_found", f"Patient not found for phone: {phone_number}.", {'phone_number': phone_number})
        return

    patient_id = patient['patient_id']
    print(f"Appointments for {patient['first_name']} {patient['last_name']}:")
    # Log the successful retrieval and intention to view
    log_conversation(patient_id, "audit_viewed_appointments", f"Patient {patient_id} viewed their appointments.", {'patient_id': patient_id})

    appointments = db_manager.get_appointments_for_patient(conn, patient_id)
    if not appointments:
        print("No appointments found.")
        # log_conversation(patient_id, "view_appts_none_found_for_patient", "No appointments found for patient.", {'patient_id': patient_id}) # Covered by audit_viewed_appointments
        return

    for appt in appointments:
        doctor = db_manager.get_doctor(conn, appt['doctor_id'])
        doc_name = f"Dr. {doctor['first_name']} {doctor['last_name']}" if doctor else "Unknown Doctor"
        # Reason for visit is sensitive, so not printing here by default in a list.
        # For a real system, what to display needs careful consideration.
        print(f"  ID: {appt['appointment_id']}, Date: {appt['appointment_datetime']}, Doctor: {doc_name}, Status: {appt['status']}")
    # log_conversation(patient_id, "view_appts_displayed_count", f"Displayed {len(appointments)} appointments.", {'patient_id': patient_id, 'count': len(appointments)}) # Covered by audit_viewed_appointments


def handle_appointment_cancellation():
    """Handles cancelling an appointment."""
    # TODO: Add authentication/authorization check here in a production system.
    global current_session_id
    print("\n--- Cancel Appointment ---")
    log_conversation(None, "cancel_appt_prompt_phone", "Prompted for phone to cancel appointment.")
    patient_phone = get_input("Enter your phone number to find your record: ")
    patient_record = db_manager.get_patient_by_phone(conn, patient_phone)

    if not patient_record:
        print("Patient record not found.")
        log_conversation(None, "cancel_appt_patient_not_found", f"Patient not found for phone: {patient_phone}.", {'phone_number': patient_phone})
        return

    patient_id = patient_record['patient_id']
    print(f"Welcome, {patient_record['first_name']} {patient_record['last_name']}.")
    log_conversation(patient_id, "cancel_appt_patient_identified", "Patient identified for appointment cancellation.", {'patient_id': patient_id})

    appointments = db_manager.get_appointments_for_patient(conn, patient_id)
    scheduled_appointments = [appt for appt in appointments if appt['status'] == 'Scheduled']

    if not scheduled_appointments:
        print("You have no scheduled appointments to cancel.")
        log_conversation(patient_id, "cancel_appt_no_scheduled_appointments", "No scheduled appointments found for patient to cancel.", {'patient_id': patient_id})
        return

    print("\nYour Scheduled Appointments:")
    for i, appt in enumerate(scheduled_appointments):
        doctor = db_manager.get_doctor(conn, appt['doctor_id'])
        doc_name = f"Dr. {doctor['first_name']} {doctor['last_name']}" if doctor else "Unknown Doctor"
        print(f"{i + 1}. ID: {appt['appointment_id']}, Date: {appt['appointment_datetime']}, Doctor: {doc_name}, SlotID: {appt['availability_id']}")

    selected_appointment_to_cancel = None
    while not selected_appointment_to_cancel:
        try:
            choice_input = get_input(f"Choose appointment number to cancel (1-{len(scheduled_appointments)}): ", patient_id)
            choice_idx = int(choice_input) - 1
            if 0 <= choice_idx < len(scheduled_appointments):
                selected_appointment_to_cancel = scheduled_appointments[choice_idx]
                log_conversation(patient_id, "cancel_appt_appointment_selected", f"User selected appointment ID {selected_appointment_to_cancel['appointment_id']} to cancel.", 
                                 {'patient_id': patient_id, 'appointment_id': selected_appointment_to_cancel['appointment_id']})
            else:
                print("Invalid choice. Please enter a number from the list.")
                log_conversation(patient_id, "cancel_appt_invalid_choice_oor", "User cancellation choice out of range.", {'patient_id': patient_id, 'input': choice_input})
        except ValueError:
            print("Invalid input. Please enter a number.")
            log_conversation(patient_id, "cancel_appt_invalid_choice_nan", "User cancellation choice not a number.", {'patient_id': patient_id, 'input': choice_input})

    appointment_id_to_cancel = selected_appointment_to_cancel['appointment_id']
    availability_id_to_release = selected_appointment_to_cancel['availability_id']

    confirm = get_input(f"Are you sure you want to cancel appointment ID {appointment_id_to_cancel}? (yes/no): ", patient_id).lower()
    log_conversation(patient_id, "cancel_appt_confirmation_response", f"User confirmation response for cancelling appt {appointment_id_to_cancel}: {confirm}.", 
                     {'patient_id': patient_id, 'appointment_id': appointment_id_to_cancel, 'response': confirm})

    if confirm == 'yes':
        status_updated = db_manager.update_appointment_status(conn, appointment_id_to_cancel, 'Cancelled')
        
        if status_updated:
            print(f"Appointment ID {appointment_id_to_cancel} has been cancelled.")
            log_conversation(patient_id, "audit_appointment_cancelled", "Appointment status set to Cancelled.", 
                             {'patient_id': patient_id, 'appointment_id': appointment_id_to_cancel})

            if availability_id_to_release is not None:
                slot_released = db_manager.update_availability_slot_booked_status(conn, availability_id_to_release, False)
                if slot_released:
                    print(f"Availability slot ID {availability_id_to_release} has been made available again.")
                    log_conversation(patient_id, "audit_availability_slot_released", "Availability slot marked as not booked.", 
                                     {'patient_id': patient_id, 'availability_id': availability_id_to_release, 'appointment_id': appointment_id_to_cancel})
                else:
                    print(f"Failed to update availability slot ID {availability_id_to_release}. Please contact administration.")
                    log_conversation(patient_id, "audit_slot_release_failed", "Failed to update availability slot after cancellation.", 
                                     {'patient_id': patient_id, 'availability_id': availability_id_to_release, 'appointment_id': appointment_id_to_cancel})
            else: # Should ideally not happen if appt was made via new flow
                log_conversation(patient_id, "audit_cancel_appt_no_slot_linked", f"No availability_id linked to cancelled appt {appointment_id_to_cancel}.",
                                 {'patient_id': patient_id, 'appointment_id': appointment_id_to_cancel})
        else:
            print("Failed to cancel the appointment. Please try again.")
            log_conversation(patient_id, "audit_appointment_cancellation_failed", "Failed to update appointment status to Cancelled in DB.", 
                             {'patient_id': patient_id, 'appointment_id': appointment_id_to_cancel})
    else:
        print("Appointment cancellation aborted.")
        log_conversation(patient_id, "cancel_appt_aborted_by_user", "User aborted appointment cancellation.", 
                         {'patient_id': patient_id, 'appointment_id': appointment_id_to_cancel})

def handle_appointment_rescheduling():
    """Handles rescheduling an appointment (simplified as cancel then book new)."""
    # TODO: Add authentication/authorization check here in a production system.
    global current_session_id
    print("\n--- Reschedule Appointment ---")
    print("Rescheduling involves cancelling your existing appointment and then booking a new one.")
    
    log_conversation(None, "reschedule_appt_prompt_phone", "Prompted for phone to reschedule appointment.")
    patient_phone = get_input("First, let's find your existing appointment. Enter your phone number: ")
    
    patient_record = db_manager.get_patient_by_phone(conn, patient_phone)
    if not patient_record:
        print("Patient record not found. Cannot proceed with rescheduling.")
        log_conversation(None, "reschedule_appt_patient_not_found", f"Patient not found for phone: {patient_phone}.", {'phone_number': patient_phone})
        return
        
    patient_id = patient_record['patient_id']
    log_conversation(patient_id, "reschedule_appt_patient_identified", "Patient identified for rescheduling process.", {'patient_id': patient_id})

    print("\nStep 1: Cancel existing appointment.")
    handle_appointment_cancellation() # This function has its own detailed logging

    proceed = get_input("\nWould you like to schedule a new appointment now? (yes/no): ", patient_id).lower()
    log_conversation(patient_id, "reschedule_appt_prompt_proceed_to_new_schedule", f"User response to proceed with new booking: {proceed}.", {'patient_id': patient_id, 'response': proceed})
    if proceed == 'yes':
        print("\nStep 2: Schedule new appointment.")
        handle_appointment_scheduling() # This function has its own detailed logging
    else:
        print("Rescheduling process aborted after cancellation step.")
        log_conversation(patient_id, "reschedule_appt_aborted_after_cancellation", "User aborted rescheduling after cancellation part.", {'patient_id': patient_id})


def main_menu():
    """Displays the main menu and handles user choices."""
    global current_session_id
    current_session_id = str(uuid.uuid4()) 
    log_conversation(None, "audit_app_session_started", f"New user session started.", {'session_id': current_session_id})

    print("\nWelcome to Hospital Administration Bot!")
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Register as a new patient")
        print("2. Schedule an appointment")
        print("3. View your appointments")
        print("4. Cancel an appointment")
        print("5. Reschedule an appointment")
        print("6. Exit")

        choice = get_input("Enter choice (1-6): ") # Removed main_menu_choice log from here

        if choice == '1':
            log_conversation(None, "menu_choice_register_patient", "User selected menu option: Register Patient")
            handle_patient_registration()
        elif choice == '2':
            log_conversation(None, "menu_choice_schedule_appointment", "User selected menu option: Schedule Appointment")
            handle_appointment_scheduling()
        elif choice == '3':
            log_conversation(None, "menu_choice_view_appointments", "User selected menu option: View Appointments")
            handle_view_appointments()
        elif choice == '4':
            log_conversation(None, "menu_choice_cancel_appointment", "User selected menu option: Cancel Appointment")
            handle_appointment_cancellation()
        elif choice == '5':
            log_conversation(None, "menu_choice_reschedule_appointment", "User selected menu option: Reschedule Appointment")
            handle_appointment_rescheduling()
        elif choice == '6':
            log_conversation(None, "menu_choice_exit", "User selected menu option: Exit")
            print("Thank you for using Hospital Administration Bot. Goodbye!")
            log_conversation(None, "audit_app_session_ended", "User exited application.", {'session_id': current_session_id})
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")
            log_conversation(None, "menu_choice_invalid", f"User entered invalid menu choice: {choice}", {'choice': choice})
        
        
        # current_session_id remains the same for the whole run of main_menu after initial assignment


if __name__ == '__main__':
    conn = db_manager.create_connection(DB_FILE)
    if conn:
        # Optional: Run initial setup/tests from database_manager if needed,
        # but typically the agent just uses the DB.
        # For a clean run, we might want to ensure the db is pristine or has test data.
        # The `database_manager.py` already has a self-test part that cleans and populates
        # if run directly. Here we assume the DB exists and is set up.
        # If not, running `python database_manager.py` first is a prerequisite.
        
        # For testing the agent, it's good if some data exists.
        # Let's check if doctors exist, if not, maybe prompt to run db_manager.py
        if not db_manager.get_all_doctors(conn):
            print("NOTICE: No doctors found in the database. Some features might not work as expected.")
            print("Please consider running 'python database_manager.py' once to populate initial test data.")
            log_conversation(None, "app_start_warn_no_doctors", "Warning: No doctors in DB.")


        main_menu()
        conn.close()
        print("Database connection closed.")
    else:
        print("CRITICAL: Could not connect to the database. The agent cannot start.")
