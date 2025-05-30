import os
import json
import threading 
import uuid 

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

# CrewAI specific imports
from crewai import Agent, Task, Crew, Process

# Langchain LLM imports
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI


# Project specific imports
# Attempt to import initialize_llm from main_crew.py, but provide a fallback
# to ensure app.py can define its own if main_crew.py is not structured for this import
# or to avoid circular dependencies.
try:
    from main_crew import initialize_llm as main_crew_initialize_llm
    # If main_crew.py's version is also updated with Gemini, this would be ideal.
    # For this subtask, we ensure app.py's fallback is updated.
    print("Successfully imported initialize_llm from main_crew.py")
    initialize_llm_source = main_crew_initialize_llm
except ImportError: 
    print("Warning: Could not import initialize_llm from main_crew.py. Using fallback LLM initialization within app.py.")
    def fallback_initialize_llm():
        load_dotenv()
        llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        openai_api_key = os.getenv("OPENAI_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY") # Added for Gemini

        openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")
        groq_model_name = os.getenv("GROQ_MODEL_NAME", "mixtral-8x7b-32768")
        google_gemini_model_name = os.getenv("GOOGLE_GEMINI_MODEL_NAME", "gemini-1.5-pro-latest") # Added for Gemini
        
        llm = None
        current_provider_info = "None"

        if llm_provider == "openai":
            if openai_api_key:
                llm = ChatOpenAI(model_name=openai_model_name, api_key=openai_api_key, temperature=0.0)
                current_provider_info = f"OpenAI model: {openai_model_name}"
            else:
                app.logger.error("OpenAI provider selected, but OPENAI_API_KEY not found.")
        elif llm_provider == "groq":
            if groq_api_key:
                llm = ChatGroq(model_name=groq_model_name, groq_api_key=groq_api_key, temperature=0.0)
                current_provider_info = f"Groq model: {groq_model_name}"
            else:
                app.logger.error("Groq provider selected, but GROQ_API_KEY not found.")
        elif llm_provider == "gemini": # New Gemini condition
            if google_api_key:
                llm = ChatGoogleGenerativeAI(model=google_gemini_model_name, google_api_key=google_api_key, temperature=0.0)
                current_provider_info = f"Google Gemini model: {google_gemini_model_name}"
            else:
                app.logger.error("Gemini provider selected, but GOOGLE_API_KEY not found.")
        
        # Fallback to OpenAI if primary choice failed or was not specific and OpenAI key exists
        if not llm and openai_api_key and llm_provider != "openai": # Avoid re-trying if openai already failed
            app.logger.warn(f"Primary LLM provider '{llm_provider}' failed or key missing. Attempting fallback to OpenAI.")
            llm = ChatOpenAI(model_name=openai_model_name, api_key=openai_api_key, temperature=0.0)
            current_provider_info = f"OpenAI model (fallback): {openai_model_name}"
        elif not llm and openai_api_key and llm_provider == "openai" and not openai_api_key: # Handles case where default is openai but key was missing
             pass # Already logged error for OpenAI

        if llm:
            app.logger.info(f"LLM initialized using: {current_provider_info}")
        else:
            app.logger.error("LLM could not be initialized. Check API keys and LLM_PROVIDER in .env.")
        return llm
    initialize_llm_source = fallback_initialize_llm


import crew_definitions as task_defs
from database_tools import all_database_tools

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Initialize LLM and Agents globally ---
llm = None
patient_onboarding_agent = None
scheduling_agent = None
medical_records_agent = None
ASYNC_TASK_RESULTS = {}

try:
    llm = initialize_llm_source() # Use the determined initializer
    if llm is None:
        # This log might be redundant if initialize_llm_source already logs extensively
        app.logger.error("LLM could not be initialized (returned None). Ensure API keys are set in .env file.")
    else:
        # This log might also be redundant if initialize_llm_source logs success
        # app.logger.info(f"LLM initialized successfully for app agents.") 
        
        patient_onboarding_agent = Agent(
            role=task_defs.patient_onboarding_specialist_def['role'],
            goal=task_defs.patient_onboarding_specialist_def['goal'],
            backstory=task_defs.patient_onboarding_specialist_def['backstory'],
            tools=all_database_tools, llm=llm, verbose=True, allow_delegation=False
        )
        scheduling_agent = Agent(
            role=task_defs.scheduling_coordinator_def['role'],
            goal=task_defs.scheduling_coordinator_def['goal'],
            backstory=task_defs.scheduling_coordinator_def['backstory'],
            tools=all_database_tools, llm=llm, verbose=True, allow_delegation=False
        )
        medical_records_agent = Agent(
            role=task_defs.medical_records_clerk_def['role'],
            goal=task_defs.medical_records_clerk_def['goal'],
            backstory=task_defs.medical_records_clerk_def['backstory'],
            tools=all_database_tools, llm=llm, verbose=True, allow_delegation=False
        )
        app.logger.info("CrewAI Agents initialized (if LLM was available).")
except Exception as e:
    app.logger.error(f"Critical error during LLM or Agent initialization in app.py: {e}", exc_info=True)

# --- Helper Function to Process CrewAI Results ---
def process_crew_result(result_string):
    if isinstance(result_string, (dict, list)): return result_string
    if not isinstance(result_string, str): return str(result_string)
    try:
        if result_string.startswith("```json"): result_string = result_string[7:-3]
        elif result_string.startswith("```"): result_string = result_string[3:-3]
        data = json.loads(result_string.strip())
        return data
    except (json.JSONDecodeError, TypeError):
        app.logger.warn(f"Could not decode crew result as JSON: {result_string}")
        return result_string

# --- Routes for Rendering Pages (GET requests) ---
@app.route('/')
def home(): 
    return render_template('home.html', active_page='home')

@app.route('/register_patient_page')
def register_patient_page(): 
    return render_template('register_patient.html', active_page='register_patient', patient_data={})

@app.route('/schedule_appointment_page')
def schedule_appointment_page(): 
    return render_template('schedule_appointment.html', active_page='schedule_appointment', schedule_attempt_data={})

@app.route('/view_my_appointments_page')
def view_my_appointments_page(): 
    return render_template('view_appointments.html', active_page='view_my_appointments')

@app.route('/view_doctors_page')
def view_doctors_page(): 
    return render_template('view_doctors.html', active_page='view_doctors')

# --- Routes for Form Submissions & CrewAI Interaction (POST requests) ---

def run_crew_in_thread(crew_instance, task_run_id, app_context=None):
    global ASYNC_TASK_RESULTS
    print(f"Thread started for task ID: {task_run_id}")
    current_app_context = app_context or app.app_context()
    try:
        with current_app_context: 
            result = crew_instance.kickoff()
            ASYNC_TASK_RESULTS[task_run_id] = {"status": "completed", "result": result}
            print(f"Threaded task {task_run_id} completed. Result: {result}")
    except Exception as e:
        ASYNC_TASK_RESULTS[task_run_id] = {"status": "failed", "error": str(e)}
        print(f"Error in threaded task {task_run_id}: {e}")

@app.route('/submit_patient_registration', methods=['POST'])
def submit_patient_registration():
    form_data = request.form.to_dict()
    run_async = request.form.get('run_async_example') == 'on'

    if not llm or not patient_onboarding_agent:
        flash("ERROR: AI components not initialized. Please check server logs and API key configuration.", "danger")
        return render_template('register_patient.html', patient_data=form_data, registration_result=None, active_page='register_patient')

    required_fields = ["first_name", "last_name", "phone_number", "email"] 
    missing_fields = [field for field in required_fields if not form_data.get(field)]
    if missing_fields:
        flash(f"Please fill in all required fields: {', '.join(missing_fields)}.", "warning")
        return render_template('register_patient.html', patient_data=form_data, registration_result=None, active_page='register_patient')

    try:
        task_def = task_defs.register_new_patient_task_def
        registration_task = Task(
            description=task_def['description'].format(patient_details_json=json.dumps(form_data)),
            expected_output=task_def['expected_output'],
            agent=patient_onboarding_agent
        )
        crew = Crew(agents=[patient_onboarding_agent], tasks=[registration_task], verbose=1, process=Process.sequential)

        if run_async:
            # TODO: ASYNCHRONOUS PROCESSING: This is a very basic threading example, NOT for production.
            task_run_id = str(uuid.uuid4())
            ASYNC_TASK_RESULTS[task_run_id] = {"status": "processing"} 
            thread = threading.Thread(target=run_crew_in_thread, args=(crew, task_run_id, app.app_context()))
            thread.start()
            flash(f"Patient registration for {form_data.get('first_name')} has been submitted for processing (Task ID: {task_run_id}). Result will appear on server console.", "info")
            return redirect(url_for('register_patient_page'))
        else:
            # TODO: ASYNCHRONOUS PROCESSING comment
            raw_result = crew.kickoff()
            processed_result = process_crew_result(raw_result)
            if "success" in str(processed_result).lower() or (isinstance(processed_result, dict) and processed_result.get("patient_id")):
                 flash("Patient registration processed successfully!", "success")
            else:
                 flash("Patient registration processed, but outcome might indicate an issue or need review.", "warning")
            return render_template('register_patient.html', registration_result=processed_result, patient_data=form_data, active_page='register_patient')

    except Exception as e:
        app.logger.error(f"Error in patient registration task: {e}", exc_info=True)
        flash(f"An internal error occurred during registration: {str(e)}", "danger")
        return render_template('register_patient.html', patient_data=form_data, registration_result=None, active_page='register_patient')

@app.route('/fetch_doctors', methods=['POST'])
def fetch_doctors():
    specialization = request.form.get('specialization', "").strip()
    if not llm or not medical_records_agent:
        flash("ERROR: AI components not initialized.", "danger")
        return render_template('view_doctors.html', specialization=specialization, active_page='view_doctors')
    try:
        if specialization:
            task_def = task_defs.get_doctors_by_specialization_task_def
            task_description = task_def['description'].format(specialization=specialization)
        else: 
            task_def = task_defs.get_all_doctors_task_def
            task_description = task_def['description']
        doctors_task = Task(description=task_description, expected_output=task_def['expected_output'], agent=medical_records_agent)
        # TODO: ASYNCHRONOUS PROCESSING comment
        crew = Crew(agents=[medical_records_agent], tasks=[doctors_task], verbose=1, process=Process.sequential)
        raw_result = crew.kickoff()
        processed_result = process_crew_result(raw_result)
        return render_template('view_doctors.html', doctors_data=processed_result, specialization=specialization, active_page='view_doctors')
    except Exception as e:
        app.logger.error(f"Error in fetching doctors task: {e}", exc_info=True)
        flash(f"An internal error occurred: {str(e)}", "danger")
        return render_template('view_doctors.html', specialization=specialization, active_page='view_doctors')

@app.route('/fetch_doctor_availability', methods=['POST'])
def fetch_doctor_availability():
    doctor_id_str = request.form.get('doctor_id')
    start_date = request.form.get('start_date') 
    end_date = request.form.get('end_date')
    active_page_val = 'view_doctors'
    
    if not llm or not medical_records_agent:
        flash("ERROR: AI components not initialized.", "danger")
        return render_template('view_doctors.html', doctor_id_for_avail=doctor_id_str, start_date_for_avail=start_date, end_date_for_avail=end_date, active_page=active_page_val)

    if not all([doctor_id_str, start_date, end_date]):
        flash("Doctor ID, start date, and end date are required for availability.", "warning")
        return render_template('view_doctors.html', doctor_id_for_avail=doctor_id_str, start_date_for_avail=start_date, end_date_for_avail=end_date, active_page=active_page_val)
    
    try:
        doctor_id = int(doctor_id_str)
        start_datetime_str = start_date + " 00:00:00" if len(start_date) == 10 else start_date
        end_datetime_str = end_date + " 23:59:59" if len(end_date) == 10 else end_date

        task_def = task_defs.find_doctor_availability_task_def
        availability_task = Task(
            description=task_def['description'].format(doctor_id=doctor_id, start_date=start_datetime_str, end_date=end_datetime_str),
            expected_output=task_def['expected_output'], agent=medical_records_agent 
        )
        # TODO: ASYNCHRONOUS PROCESSING comment
        crew = Crew(agents=[medical_records_agent], tasks=[availability_task], verbose=1, process=Process.sequential)
        raw_result = crew.kickoff()
        processed_result = process_crew_result(raw_result)
        return render_template('view_doctors.html', availability_data=processed_result, doctor_id_for_avail=doctor_id_str, start_date_for_avail=start_date, end_date_for_avail=end_date, active_page=active_page_val)
    except ValueError:
        flash("Invalid Doctor ID format. It must be a number.", "danger")
        return render_template('view_doctors.html', doctor_id_for_avail=doctor_id_str, start_date_for_avail=start_date, end_date_for_avail=end_date, active_page=active_page_val)
    except Exception as e:
        app.logger.error(f"Error in fetching doctor availability task: {e}", exc_info=True)
        flash(f"An internal error occurred: {str(e)}", "danger")
        return render_template('view_doctors.html', doctor_id_for_avail=doctor_id_str, start_date_for_avail=start_date, end_date_for_avail=end_date, active_page=active_page_val)

@app.route('/fetch_patient_appointments', methods=['POST'])
def fetch_patient_appointments():
    phone_number = request.form.get('phone_number', "").strip()
    active_page_val = 'view_my_appointments'
    if not llm or not medical_records_agent:
        flash("ERROR: AI components not initialized.", "danger")
        return render_template('view_appointments.html', patient_phone=phone_number, active_page=active_page_val)

    if not phone_number:
        flash("Patient phone number is required.", "warning")
        return render_template('view_appointments.html', patient_phone=phone_number, active_page=active_page_val)
    
    try:
        task_description = (
            f"A patient wants to view their appointments. Their phone number is {phone_number}. "
            "First, use the 'get_patient_by_phone_number' tool to find their patient_id. "
            "If the patient is found, then use their patient_id to retrieve and list all their appointments "
            "using the 'get_patient_appointments' tool. "
            "If the patient is not found, state that no patient was found with that phone number."
        )
        task_def = task_defs.view_patient_appointments_task_def
        appointments_task = Task(description=task_description, expected_output=task_def['expected_output'], agent=medical_records_agent)
        # TODO: ASYNCHRONOUS PROCESSING comment
        crew = Crew(agents=[medical_records_agent], tasks=[appointments_task], verbose=1, process=Process.sequential)
        raw_result = crew.kickoff()
        processed_result = process_crew_result(raw_result)
        return render_template('view_appointments.html', appointments_data=processed_result, patient_phone=phone_number, active_page=active_page_val)
    except Exception as e:
        app.logger.error(f"Error in fetching patient appointments task: {e}", exc_info=True)
        flash(f"An internal error occurred: {str(e)}", "danger")
        return render_template('view_appointments.html', patient_phone=phone_number, active_page=active_page_val)

@app.route('/submit_schedule_appointment', methods=['POST'])
def submit_schedule_appointment():
    form_data = request.form.to_dict()
    active_page_val = 'schedule_appointment'
    if not llm or not scheduling_agent:
        flash("ERROR: AI components not initialized.", "danger")
        return render_template('schedule_appointment.html', schedule_attempt_data=form_data, active_page=active_page_val)

    required_fields = ['patient_id', 'doctor_id', 'availability_id', 'appointment_datetime', 'duration_minutes', 'reason_for_visit']
    if not all(form_data.get(field) for field in required_fields):
        flash("All appointment details are required.", "warning")
        return render_template('schedule_appointment.html', schedule_attempt_data=form_data, active_page=active_page_val)
    
    try:
        form_data['patient_id'] = int(form_data['patient_id'])
        form_data['doctor_id'] = int(form_data['doctor_id'])
        form_data['availability_id'] = int(form_data['availability_id'])
        form_data['duration_minutes'] = int(form_data['duration_minutes'])

        task_def = task_defs.schedule_appointment_task_def
        task = Task(description=task_def['description'].format(appointment_details_json=json.dumps(form_data)), expected_output=task_def['expected_output'], agent=scheduling_agent)
        # TODO: ASYNCHRONOUS PROCESSING comment
        crew = Crew(agents=[scheduling_agent], tasks=[task], verbose=1, process=Process.sequential)
        raw_result = crew.kickoff()
        processed_result = process_crew_result(raw_result)
        flash("Appointment scheduling processed. See result below.", "info") 
        return render_template('schedule_appointment.html', schedule_result=processed_result, schedule_attempt_data=form_data, active_page=active_page_val)
    except ValueError:
        flash("Invalid format for one of the ID fields or duration. They must be numbers.", "danger")
        return render_template('schedule_appointment.html', schedule_attempt_data=form_data, active_page=active_page_val)
    except Exception as e:
        app.logger.error(f"Error in scheduling appointment task: {e}", exc_info=True)
        flash(f"An internal error occurred: {str(e)}", "danger")
        return render_template('schedule_appointment.html', schedule_attempt_data=form_data, active_page=active_page_val)

# --- Custom Error Handlers ---
@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(f"Page not found: {request.url} - {e}")
    return render_template('404.html', active_page='error'), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Internal server error: {e}", exc_info=True)
    return render_template('500.html', active_page='error'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
```
