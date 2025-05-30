# Manual Testing Guide: Hospital Administration Agent (Web UI & CLI)

This guide provides steps for manually testing the Hospital Administration Agent, primarily focusing on the Flask Web Interface (`app.py`) and also covering the Command-Line Interface (`main_crew.py`).

## I. Testing the Web Interface (`app.py`)

### Prerequisites for Web UI Testing

1.  **Environment:**
    *   Python 3.x installed.
    *   Required Python packages installed. From the project root, run:
        ```bash
        pip install -r requirements.txt
        ```
2.  **API Keys:**
    *   The application uses LLMs via CrewAI, requiring API keys for your chosen LLM provider (e.g., OpenAI, Groq).
    *   Copy `.env.example` to `.env`: `cp .env.example .env`
    *   Edit `.env` to include your API key(s) (e.g., `OPENAI_API_KEY="sk-..."`).
    *   Configure `LLM_PROVIDER` and model names in `.env` if not using defaults.
3.  **Files:** Ensure all project files are present (see `README.md` Directory Structure).
4.  **Initial Database State (Recommended):**
    *   For a clean, predictable database, run `database_manager.py` directly before testing:
        ```bash
        python database_manager.py
        ```
    *   This (re)creates `hospital_management.db` with sample data.
5.  **SQLite Browser (Optional):** Useful for inspecting `hospital_management.db`.

### Running the Web Agent

1.  Open your terminal.
2.  Navigate to the project directory.
3.  Run the Flask development server:
    ```bash
    python app.py
    ```
4.  Open your web browser and go to `http://127.0.0.1:5001` (or `http://0.0.0.0:5001` as configured in `app.py`).
5.  The application will initialize the LLM and display the home page.

### Web UI Test Scenarios

**General Notes for Web UI Testing:**
*   **LLM Output:** Agent responses displayed on the page come from the LLM. Exact wording may vary. Focus on whether the core task was completed and correct information is presented.
*   **Database Verification:** After actions that modify data, always verify changes directly in `hospital_management.db`.
*   **Flashed Messages:** Look for success, error, or info messages displayed at the top of the page after form submissions.
*   **Form Repopulation:** On validation errors or when results are shown, check if form fields are repopulated with your previous input where applicable.
*   **Verbose Output:** Check the Flask server console for verbose output from CrewAI agents (`verbose=True` is set for agents in `app.py`), which shows their thought process and tool usage.

---

**Scenario WEB-1: Navigate to and View Pages**

1.  **Action:** Click navigation links from the header on the Home page: "Register Patient", "Schedule Appointment", "View My Appointments", "View Doctors".
2.  **Expected Outcome:**
    *   The corresponding pages (`register_patient.html`, `schedule_appointment.html`, `view_appointments.html`, `view_doctors.html`) should render correctly.
    *   The active navigation link should be highlighted (if CSS for `.active` is effective).
    *   No errors should appear on page load.

---

**Scenario WEB-2: Patient Registration (Synchronous & Asynchronous)**

1.  **Navigation:** Click "Register Patient" from the navigation menu.
2.  **Synchronous Test:**
    *   **Input:** Fill the form with unique details:
        *   First name: `WebAppTest`
        *   Last name: `UserOne`
        *   DOB: `1993-03-03`
        *   Gender: `Female`
        *   Phone: `5553330001`
        *   Email: `webapp.user1@example.com`
        *   Address: `303 Web Street`
        *   Ensure "Run Asynchronously" checkbox is **unchecked**.
    *   **Action:** Click "Register Patient" button.
    *   **Expected Outcome (Web Page):**
        *   The `register_patient.html` page should reload.
        *   A flashed message (e.g., "Patient registration processed successfully!") should appear.
        *   A "Registration Attempt Result" section should display the outcome from the CrewAI agent (e.g., confirmation message with new Patient ID).
        *   Form fields should retain the submitted values.
    *   **Database Verification:** New patient record in `Patients` table. Relevant entry in `ConversationLogs`.
3.  **Asynchronous Test (Experimental):**
    *   **Input:** Fill the form with different unique details (e.g., `WebAppAsyncUser`, phone `5553330002`).
        *   Ensure "Run Asynchronously (Experimental)" checkbox is **checked**.
    *   **Action:** Click "Register Patient" button.
    *   **Expected Outcome (Web Page):**
        *   The page should redirect back to the (potentially empty) registration form quickly.
        *   A flashed message like "Patient registration for WebAppAsyncUser has been submitted for processing... Result will appear on server console."
        *   No direct result will be shown on this page for the async submission.
    *   **Console Verification:** Check the Flask server console. After a delay, a message like "Threaded task <task_id> completed with result: ..." should appear.
    *   **Database Verification:** After the console message indicates completion, verify the new patient record in the database.

---

**Scenario WEB-3: List All Doctors**

1.  **Navigation:** Go to "View Doctors" page.
2.  **Action:** Click the "List All Doctors" button.
3.  **Expected Outcome (Web Page):**
    *   The `view_doctors.html` page reloads.
    *   The "Doctor List" section displays a table of all doctors from the seed data (e.g., Dr. Alice Brown, Dr. Bob Green, Dr. Eve White) with their ID, Name, Specialization, Phone, Email.
    *   If no doctors, an appropriate message is shown.
4.  **Database Verification:** Compare displayed list with `SELECT * FROM Doctors;`.

---

**Scenario WEB-4: List Doctors by Specialization**

1.  **Navigation:** Go to "View Doctors" page.
2.  **Input:**
    *   In "Filter by Specialization", enter `Cardiology`.
    *   **Action:** Click "Search Doctors".
3.  **Expected Outcome (Web Page):**
    *   `view_doctors.html` reloads. The "Filter by Specialization" field should still show `Cardiology`.
    *   "Doctor List" section displays only doctors with "Cardiology" specialization.
4.  **Input (No match):**
    *   Enter `NonExistentSpecialization`. Click "Search Doctors".
    *   **Expected Outcome:** "No doctors found matching..." or similar message/empty table.
5.  **Database Verification:** Compare with `SELECT * FROM Doctors WHERE specialization = 'Cardiology';`.

---

**Scenario WEB-5: Find Doctor Availability**

*(Assumes Dr. Alice Brown (ID 1) from seed data)*

1.  **Navigation:** Go to "View Doctors" page.
2.  **Input:** In the "Find Doctor Availability" form:
    *   Doctor ID: `1`
    *   Start Date: `2024-08-20`
    *   End Date: `2024-08-20`
    *   **Action:** Click "Check Availability".
3.  **Expected Outcome (Web Page):**
    *   `view_doctors.html` reloads. Form fields for availability search should retain values.
    *   "Availability Result" section displays a table of slots for Dr. Alice Brown on that date.
    *   Example slots from seed data:
        *   Slot ID 1, Start: 2024-08-20 09:00:00, End: 2024-08-20 12:00:00, Booked: Yes (from `database_manager.py` initial run)
        *   Slot ID 2, Start: 2024-08-20 14:00:00, End: 2024-08-20 17:00:00, Booked: No
4.  **Database Verification:** `SELECT * FROM DoctorAvailability WHERE doctor_id = 1 AND date(start_time) = '2024-08-20';`

---

**Scenario WEB-6: View Patient Appointments**

*(Assumes patient Jane Smith, phone `0987654321`, has appointments from seed data or previous tests like WEB-SCENARIO-APPT-SCHED below if implemented)*

1.  **Navigation:** Go to "View My Appointments" page.
2.  **Input:**
    *   Patient Phone Number: `0987654321`
    *   **Action:** Click "Fetch Appointments".
3.  **Expected Outcome (Web Page):**
    *   `view_appointments.html` reloads. Phone number field should retain value.
    *   "Appointments Found" section displays a table of Jane Smith's appointments with details (Appt. ID, Doctor ID, Date & Time, Reason, Status, Availability ID).
4.  **Database Verification:** Compare with relevant SELECT query on `Appointments` table for Jane Smith's ID.

---

**Scenario WEB-7: Schedule New Appointment (via Web UI)**

*(Requires a known Patient ID (e.g., from WEB-1 or seed data), Doctor ID, and a *valid, unbooked* Availability Slot ID (e.g., from WEB-5 results, Slot ID 2 for Dr. Alice Brown if not booked yet). Let Patient ID be 2 (Jane Smith), Doctor ID 1 (Alice Brown), Availability ID 2.)*

1.  **Navigation:** Go to "Schedule Appointment" page.
2.  **Input:**
    *   Patient ID: `2`
    *   Doctor ID: `1`
    *   Doctor Availability Slot ID: `2`
    *   Appointment Date and Time: `2024-08-20 14:00:00` (must match slot start)
    *   Duration: `30` (or actual duration of slot 2)
    *   Reason for Visit: `Web UI Scheduled Checkup`
    *   **Action:** Click "Schedule Appointment".
3.  **Expected Outcome (Web Page):**
    *   `schedule_appointment.html` reloads.
    *   Flashed message indicating processing.
    *   "Scheduling Attempt Result" section shows confirmation from agent, including new Appointment ID.
    *   Form fields should retain values.
4.  **Database Verification:**
    *   New record in `Appointments` table for Patient ID 2, Doctor ID 1, Availability ID 2. Status "Scheduled".
    *   `DoctorAvailability` table: Slot ID 2 should now have `is_booked = 1`.

---
**Scenario WEB-8: Test Invalid Form Submissions**
1.  **Patient Registration:**
    *   Submit the form with some required fields empty (e.g., First Name, Phone).
    *   **Expected:** Page reloads, flashed warning message listing missing fields. Form data for filled fields should persist.
2.  **Doctor Availability Search:**
    *   Submit with Doctor ID empty.
    *   **Expected:** Page reloads, flashed warning "Doctor ID, start date, and end date are required...". Form data persists.
    *   Submit with an invalid Doctor ID format (e.g., "abc").
    *   **Expected:** Page reloads, flashed error "Invalid Doctor ID format...". Form data persists.

---
**Scenario WEB-9: Test Error Pages**
1.  **404 Error:** Manually navigate to a non-existent URL (e.g., `http://127.0.0.1:5001/invalidpage`).
    *   **Expected:** The custom `404.html` page is displayed.
2.  **500 Error (Harder to simulate without breaking code):** If an unhandled exception occurs during a request, the custom `500.html` should appear. This is more for observing if it happens during other tests due to unexpected issues.

---

## II. Testing the Command-Line Interface (`main_crew.py`)

The `MANUAL_TESTING_GUIDE.md` (this file, in its previous state or if updated separately for CLI) already contains detailed scenarios for `main_crew.py`. The general principles are the same:
*   Run `python main_crew.py`.
*   Select options from the CLI menu.
*   Provide input as prompted.
*   Observe CLI output (including verbose agent logs).
*   Verify database changes.

Key scenarios from `main_crew.py` to re-verify if changes were made to it or underlying logic:
*   Patient Registration (Menu Option 1)
*   View Patient Appointments (Menu Option 2)
*   Schedule New Appointment (Menu Option 3) - *Note: CLI scheduling prompts might differ from Web UI form.*
*   Cancel Appointment (Menu Option 4)
*   Reschedule Appointment (Menu Option 5)
*   Find Doctor Availability (Menu Option 6)
*   List All Doctors (Menu Option 7)
*   List Doctors by Specialization (Menu Option 8)
*   List All Doctor Specializations (Menu Option 9)

---

## General Troubleshooting / Observation Notes (Applicable to both UI and CLI)

*   **Verbose Output:** CrewAI's verbose output in the console is invaluable. It shows:
    *   Which agent is working.
    *   The thought process and planning steps of the LLM.
    *   Which tool is selected by the agent.
    *   The exact parameters passed to the tool.
    *   The result received from the tool.
    *   The agent's final response.
*   **LLM Responses & Task Definitions:** If agents are not behaving as expected (e.g., not using tools correctly, not parsing information), review and refine:
    *   Task descriptions in `crew_definitions.py` (ensure they are clear, specific, and guide the LLM well).
    *   Tool descriptions in `database_tools.py` (ensure they accurately reflect tool functionality and arguments).
*   **Database State:** Always be mindful of the data in `hospital_management.db`. Reset with `python database_manager.py` for a clean slate.
*   **API Keys & LLM Configuration:** Ensure `.env` is correct and the selected LLM provider/model is accessible.
*   **Loading Indicators (Web UI):** The HTML templates (`register_patient.html`, `schedule_appointment.html`) include commented-out placeholders for loading indicators. These are not functional without client-side JavaScript but serve as reminders for UI improvement for long-running (synchronous) tasks. The experimental async registration path in `register_patient.html` will not update the UI with the result directly.

This guide should help in manually testing the core functionalities of the Hospital Administration Agent.
