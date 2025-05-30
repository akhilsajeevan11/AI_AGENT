import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from crewai import Agent, Task, Crew, Process

# Import agent and task definitions
from crew_definitions import (
    patient_onboarding_specialist_def,
    scheduling_coordinator_def,
    medical_records_clerk_def,
    register_new_patient_task_def,
    schedule_appointment_task_def,
    view_patient_appointments_task_def,
    cancel_appointment_task_def,
    find_doctor_availability_task_def,
    get_doctor_specializations_task_def,
    get_doctors_by_specialization_task_def,
    identify_patient_by_phone_task_def
)

# Import database tools
from database_tools import (
    add_patient_tool,
    get_patient_by_phone_tool,
    update_patient_tool,
    add_doctor_tool,
    get_all_doctors_tool,
    get_doctors_by_specialization_tool,
    get_all_specializations_tool,
    get_doctor_availability_tool,
    update_availability_slot_booked_status_tool,
    add_appointment_tool,
    get_appointments_for_patient_tool,
    update_appointment_status_tool,
    add_conversation_log_tool,
    all_database_tools # For assigning all tools if needed, or pick specific ones
)

def initialize_llm():
    """Initializes and returns the LLM based on environment variables."""
    load_dotenv()
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
    groq_model_name = os.getenv("GROQ_MODEL_NAME", "mixtral-8x7b-32768") # Example, ensure it's available

    llm = None
    if llm_provider == "openai":
        if not openai_api_key:
            print("Error: OpenAI API key (OPENAI_API_KEY) not found in .env file.")
            return None
        try:
            llm = ChatOpenAI(model_name=openai_model_name, api_key=openai_api_key, temperature=0.0)
            print(f"Using OpenAI model: {openai_model_name}")
        except Exception as e:
            print(f"Error initializing OpenAI LLM: {e}")
            return None
    elif llm_provider == "groq":
        if not groq_api_key:
            print("Error: Groq API key (GROQ_API_KEY) not found in .env file.")
            return None
        try:
            llm = ChatGroq(model_name=groq_model_name, groq_api_key=groq_api_key, temperature=0.0)
            print(f"Using Groq model: {groq_model_name}")
        except Exception as e:
            print(f"Error initializing Groq LLM: {e}")
            return None
    else:
        print(f"Warning: LLM_PROVIDER '{llm_provider}' is not recognized or API key missing. Defaulting to OpenAI if key is available.")
        if openai_api_key:
            try:
                llm = ChatOpenAI(model_name=openai_model_name, api_key=openai_api_key, temperature=0.0)
                print(f"Using default OpenAI model: {openai_model_name}")
            except Exception as e:
                print(f"Error initializing default OpenAI LLM: {e}")
                return None
        else:
            print("Error: No API key provided for default OpenAI. Please set OPENAI_API_KEY or configure LLM_PROVIDER and its key in .env file.")
            return None

    if llm is None:
        print("LLM could not be initialized.")
    return llm

# --- Instantiate Agents ---
llm = initialize_llm()

if llm:
    patient_onboarding_agent = Agent(
        role=patient_onboarding_specialist_def["role"],
        goal=patient_onboarding_specialist_def["goal"],
        backstory=patient_onboarding_specialist_def["backstory"],
        tools=[
            add_patient_tool, 
            get_patient_by_phone_tool
            # In a real scenario, might also need update_patient_tool
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    scheduling_agent = Agent(
        role=scheduling_coordinator_def["role"],
        goal=scheduling_coordinator_def["goal"],
        backstory=scheduling_coordinator_def["backstory"],
        tools=[
            get_doctor_availability_tool,
            add_appointment_tool,
            update_appointment_status_tool,
            update_availability_slot_booked_status_tool,
            get_patient_appointments_tool, # To check existing appointments
            get_patient_by_phone_tool, # To confirm patient ID if only phone is given initially for scheduling
            get_all_specializations_tool, # To list specializations
            get_doctors_by_specialization_tool # To list doctors
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False # Could delegate finding patient_id to patient_onboarding_agent if needed
    )

    medical_records_agent = Agent(
        role=medical_records_clerk_def["role"],
        goal=medical_records_clerk_def["goal"],
        backstory=medical_records_clerk_def["backstory"],
        tools=[
            get_patient_by_phone_tool,
            get_patient_appointments_tool,
            get_all_doctors_tool,
            get_doctors_by_specialization_tool,
            get_all_specializations_tool,
            get_doctor_availability_tool
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
else:
    print("Exiting: LLM not initialized. Agents cannot be created.")
    # In a real app, you might exit or raise an error.
    # For this script, we'll allow it to proceed but crew creation will fail or be skipped.
    patient_onboarding_agent = None
    scheduling_agent = None
    medical_records_agent = None


def handle_patient_registration_flow():
    if not patient_onboarding_agent:
        print("Patient Onboarding Agent not available.")
        return

    print("\n--- New Patient Registration ---")
    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()
    dob = input("Enter date of birth (YYYY-MM-DD): ").strip()
    gender = input("Enter gender: ").strip()
    phone = input("Enter phone number: ").strip()
    email = input("Enter email: ").strip()
    address = input("Enter address: ").strip()

    patient_details = {
        "first_name": first_name, "last_name": last_name, "date_of_birth": dob,
        "gender": gender, "phone_number": phone, "email": email, "address": address
    }
    patient_details_json = json.dumps(patient_details)

    # Create the task
    registration_task_description = register_new_patient_task_def["description"].format(
        patient_details_json=patient_details_json
    )
    
    task_register_patient = Task(
        description=registration_task_description,
        expected_output=register_new_patient_task_def["expected_output"],
        agent=patient_onboarding_agent
    )

    # Assemble and run the crew
    crew = Crew(
        agents=[patient_onboarding_agent],
        tasks=[task_register_patient],
        process=Process.sequential,
        verbose=2 # Enables detailed logging of the crew's execution
    )
    
    print("\nKicking off patient registration crew...")
    result = crew.kickoff()
    print("\n--- Patient Registration Result ---")
    print(result)
    print("---------------------------------")

def handle_view_patient_appointments_flow():
    if not medical_records_agent:
        print("Medical Records Agent not available.")
        return

    print("\n--- View Patient Appointments ---")
    phone_number = input("Enter patient's phone number: ").strip()

    # First, we need the patient_id. We can use a tool directly or make it part of the task.
    # For CrewAI, it's better if the agent can figure this out.
    # We can have an initial task to get patient_id from phone.
    
    # Task 1: Identify patient by phone
    # This task could be implicitly handled by the medical_records_agent if it's smart enough,
    # or we can define it explicitly. Let's assume the agent can use get_patient_by_phone_tool.

    task_description = view_patient_appointments_task_def["description"].format(
        patient_id=f"the patient ID associated with phone number {phone_number}" # Let the agent find the ID
    )
    # A more robust way would be to have a preliminary step or tool to get patient_id first,
    # then pass that ID to the task. For now, we'll see if the agent can infer this.
    # If this proves too complex for the LLM, we'd make a separate task/tool call for ID first.

    # A better approach: The task description should guide the agent to first find the patient_id using the phone number.
    task_description_refined = (
        f"A patient wants to view their appointments. Their phone number is {phone_number}. "
        "First, use the 'get_patient_by_phone_number' tool to find their patient_id. "
        "If the patient is found, then use their patient_id to retrieve and list all their appointments "
        "using the 'get_patient_appointments' tool. "
        "If the patient is not found, state that no patient was found with that phone number."
    )


    task_view_appointments = Task(
        description=task_description_refined,
        expected_output=view_patient_appointments_task_def["expected_output"],
        agent=medical_records_agent # This agent has both tools
    )

    crew = Crew(
        agents=[medical_records_agent],
        tasks=[task_view_appointments],
        process=Process.sequential,
        verbose=2
    )

    print("\nKicking off view patient appointments crew...")
    result = crew.kickoff()
    print("\n--- View Patient Appointments Result ---")
    print(result)
    print("------------------------------------")

# --- New Flow Handlers ---

def handle_schedule_appointment_flow():
    if not scheduling_agent:
        print("Scheduling Agent not available.")
        return

    print("\n--- Schedule New Appointment ---")
    print("INFO: You should first find doctor availability to get a valid 'Doctor Availability Slot ID'.")
    patient_id = input("Enter Patient ID: ").strip()
    doctor_id = input("Enter Doctor ID: ").strip()
    availability_id = input("Enter Doctor Availability Slot ID to book: ").strip()
    appointment_datetime = input("Enter desired appointment date and time (YYYY-MM-DD HH:MM:SS, must match slot start time): ").strip()
    # Duration can be derived from the slot, but task def expects it. For now, let's assume 30 or ask.
    duration_minutes = input("Enter appointment duration in minutes (e.g., 30): ").strip()
    reason = input("Reason for visit: ").strip()

    try:
        appointment_details = {
            "patient_id": int(patient_id),
            "doctor_id": int(doctor_id),
            "availability_id": int(availability_id),
            "appointment_datetime": appointment_datetime,
            "duration_minutes": int(duration_minutes),
            "reason_for_visit": reason,
        }
    except ValueError:
        print("Error: Patient ID, Doctor ID, Availability Slot ID, and Duration must be integers.")
        return
        
    task_description = schedule_appointment_task_def["description"].format(
        appointment_details_json=json.dumps(appointment_details)
    )
    
    task = Task(
        description=task_description,
        expected_output=schedule_appointment_task_def["expected_output"],
        agent=scheduling_agent
    )
    
    crew = Crew(agents=[scheduling_agent], tasks=[task], verbose=1, process=Process.sequential)
    print("\nKicking off schedule appointment crew...")
    result = crew.kickoff()
    print("\n--- Schedule Appointment Result ---")
    print(result)
    print("---------------------------------")


def handle_cancel_appointment_flow():
    if not scheduling_agent:
        print("Scheduling Agent not available.")
        return

    print("\n--- Cancel Appointment ---")
    patient_id_str = input("Enter Patient ID (optional, for verification): ").strip()
    appointment_id_str = input("Enter Appointment ID to cancel: ").strip()
    # The task also expects availability_id to release the slot.
    # This implies the user/agent should know it, or the agent needs to fetch the appointment first to get it.
    # Let's refine the task description in crew_definitions if agent needs to fetch it.
    # For now, assume it might be provided or agent infers. The current cancel_appointment_task_def implies it's given.
    availability_id_str = input("Enter the Availability Slot ID associated with this appointment (if known, otherwise leave blank): ").strip()


    try:
        appointment_id = int(appointment_id_str)
        patient_id = int(patient_id_str) if patient_id_str else None
        availability_id = int(availability_id_str) if availability_id_str else None
    except ValueError:
        print("Error: Appointment ID, Patient ID (if provided), and Availability ID (if provided) must be integers.")
        return

    # Refined description to guide the agent better if availability_id is not directly provided by user
    # For now, sticking to the original task def which implies availability_id might be part of the input to the task.
    task_description = cancel_appointment_task_def["description"].format(
        appointment_id=appointment_id,
        patient_id=patient_id, # Used for verification in the task description
        availability_id=availability_id # If None, agent might need to find it or skip unbooking slot
    )
    
    task = Task(
        description=task_description,
        expected_output=cancel_appointment_task_def["expected_output"],
        agent=scheduling_agent 
    )
    
    crew = Crew(agents=[scheduling_agent], tasks=[task], verbose=1, process=Process.sequential)
    print("\nKicking off cancel appointment crew...")
    result = crew.kickoff()
    print("\n--- Cancel Appointment Result ---")
    print(result)
    print("-------------------------------")

def handle_reschedule_appointment_flow():
    # This will be a guided flow for the user, using existing cancel + schedule logic
    # The Reschedule Task in crew_definitions is a high-level description for an agent.
    # For the CLI, we make it more direct.
    print("\n--- Reschedule Appointment ---")
    print("Rescheduling involves cancelling your existing appointment and then scheduling a new one.")
    
    print("\nStep 1: Cancel your existing appointment.")
    handle_cancel_appointment_flow() # User goes through cancellation
    
    print("\nStep 2: Schedule your new appointment.")
    # User can choose to proceed or not.
    proceed = input("Do you want to proceed to schedule a new appointment now? (yes/no): ").strip().lower()
    if proceed == 'yes':
        handle_schedule_appointment_flow()
    else:
        print("New appointment scheduling skipped.")


def handle_find_doctor_availability_flow():
    if not medical_records_agent: # Or scheduling_agent if it has the tool
        print("Relevant agent not available.")
        return

    print("\n--- Find Doctor Availability ---")
    doctor_id_str = input("Enter Doctor ID: ").strip()
    start_date_str = input("Enter start date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS): ").strip()
    end_date_str = input("Enter end date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS): ").strip()

    try:
        doctor_id = int(doctor_id_str)
    except ValueError:
        print("Error: Doctor ID must be an integer.")
        return

    # Pad dates if only date part is provided
    if len(start_date_str) == 10: start_date_str += " 00:00:00"
    if len(end_date_str) == 10: end_date_str += " 23:59:59"
        
    task_description = find_doctor_availability_task_def["description"].format(
        doctor_id=doctor_id,
        start_date=start_date_str,
        end_date=end_date_str
    )
    
    task = Task(
        description=task_description,
        expected_output=find_doctor_availability_task_def["expected_output"],
        agent=medical_records_agent # This agent has get_doctor_availability_tool
    )
    
    crew = Crew(agents=[medical_records_agent], tasks=[task], verbose=1, process=Process.sequential)
    print("\nKicking off find doctor availability crew...")
    result = crew.kickoff()
    print("\n--- Doctor Availability Result ---")
    print(result) # This might be a list of dicts, could format it better
    print("----------------------------------")

def handle_list_all_doctors_flow():
    if not medical_records_agent:
        print("Medical Records Agent not available.")
        return
    
    task = Task(
        description="List all doctors registered in the system with their details.",
        expected_output="A list of all doctors, including their ID, name, specialization, phone, and email.",
        agent=medical_records_agent
    )
    crew = Crew(agents=[medical_records_agent], tasks=[task], verbose=1, process=Process.sequential)
    print("\nKicking off list all doctors crew...")
    result = crew.kickoff()
    print("\n--- All Doctors ---")
    # Result might be a list of dicts.
    try:
        doctors = json.loads(result) if isinstance(result, str) else result
        if isinstance(doctors, list) and all(isinstance(doc, dict) for doc in doctors):
            for doc in doctors:
                print(f"  ID: {doc.get('doctor_id')}, Name: Dr. {doc.get('first_name')} {doc.get('last_name')}, Spec: {doc.get('specialization')}, Phone: {doc.get('phone_number')}, Email: {doc.get('email')}")
        else:
            print(result)
    except: # Catch JSON decode error or if result is not as expected
        print(result)
    print("-------------------")


def handle_list_doctors_by_specialization_flow():
    if not medical_records_agent:
        print("Medical Records Agent not available.")
        return

    print("\n--- List Doctors by Specialization ---")
    specialization = input("Enter specialization: ").strip()
    
    task_description = get_doctors_by_specialization_task_def["description"].format(
        specialization=specialization
    )
    task = Task(
        description=task_description,
        expected_output=get_doctors_by_specialization_task_def["expected_output"],
        agent=medical_records_agent
    )
    crew = Crew(agents=[medical_records_agent], tasks=[task], verbose=1, process=Process.sequential)
    print("\nKicking off list doctors by specialization crew...")
    result = crew.kickoff()
    print(f"\n--- Doctors with Specialization: {specialization} ---")
    try:
        doctors = json.loads(result) if isinstance(result, str) else result
        if isinstance(doctors, list) and all(isinstance(doc, dict) for doc in doctors):
            if not doctors: print("  No doctors found with this specialization.")
            for doc in doctors:
                print(f"  ID: {doc.get('doctor_id')}, Name: Dr. {doc.get('first_name')} {doc.get('last_name')}, Phone: {doc.get('phone_number')}, Email: {doc.get('email')}")
        else:
            print(result)
    except:
         print(result)
    print("---------------------------------------------")

def handle_list_all_specializations_flow():
    if not medical_records_agent:
        print("Medical Records Agent not available.")
        return

    task = Task(
        description=get_doctor_specializations_task_def["description"],
        expected_output=get_doctor_specializations_task_def["expected_output"],
        agent=medical_records_agent
    )
    crew = Crew(agents=[medical_records_agent], tasks=[task], verbose=1, process=Process.sequential)
    print("\nKicking off list all specializations crew...")
    result = crew.kickoff()
    print("\n--- All Doctor Specializations ---")
    print(result) # Expected to be a list of strings
    print("----------------------------------")


def main():
    if not llm:
        print("LLM not initialized. Cannot run full agentic flows. Some database direct operations might still work if agents are bypassed.")
        # Fallback to a simpler CLI if needed, or just exit. For now, exiting.
        return 

    while True:
        print("\n--- Hospital Administration Menu ---")
        print("1. Register New Patient")
        print("2. View Patient Appointments")
        print("3. Schedule New Appointment")
        print("4. Cancel Appointment")
        print("5. Reschedule Appointment")
        print("6. Find Doctor Availability")
        print("7. List All Doctors")
        print("8. List Doctors by Specialization")
        print("9. List All Doctor Specializations")
        print("0. Exit")
        
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            handle_patient_registration_flow()
        elif choice == '2':
            handle_view_patient_appointments_flow()
        elif choice == '3':
            handle_schedule_appointment_flow()
        elif choice == '4':
            handle_cancel_appointment_flow()
        elif choice == '5':
            handle_reschedule_appointment_flow()
        elif choice == '6':
            handle_find_doctor_availability_flow()
        elif choice == '7':
            handle_list_all_doctors_flow()
        elif choice == '8':
            handle_list_doctors_by_specialization_flow()
        elif choice == '9':
            handle_list_all_specializations_flow()
        elif choice == '0':
            print("Exiting application.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
