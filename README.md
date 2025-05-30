# Hospital Administration Agent (CrewAI Edition with Flask UI)

## Project Overview

The Hospital Administration Agent is a Python application demonstrating how CrewAI and Langchain can be used to create AI-powered agents capable of managing basic hospital administration tasks. The system now features a **Flask-based web interface** for user interaction, alongside the original command-line interface (`main_crew.py`) for backend logic and alternative interaction.

Users can register patients, schedule/cancel/reschedule appointments, and query doctor information through the web UI or CLI. The system leverages Large Language Models (LLMs) to understand and process requests, using a predefined set of tools to interact with an SQLite database where all hospital data is stored. This project showcases a multi-agent approach where different agents are responsible for specific areas of functionality, coordinated by CrewAI.

## Features

*   **Web Interface:** A Flask-based frontend for user-friendly interaction:
    *   Web-based patient registration.
    *   Browser-based views for doctor listings and availability.
    *   Forms for scheduling, viewing, and managing appointments (partially implemented for submission, full display of results on page).
*   **AI-Powered Task Execution:** Uses CrewAI agents and an LLM (configurable, e.g., OpenAI GPT, Groq Mixtral) to interpret user needs and perform tasks via both web UI and CLI.
*   **Patient Management:**
    *   Register new patients.
    *   Retrieve existing patient details.
*   **Appointment Management:**
    *   Schedule new appointments, considering doctor availability.
    *   View a patient's upcoming and past appointments.
    *   Cancel existing 'Scheduled' appointments (releasing the time slot) - (CLI implemented, Web UI form submission to be completed).
    *   Reschedule appointments (CLI implemented as guided flow, Web UI to follow similar logic).
*   **Doctor Information & Availability:**
    *   List all registered doctors and their details.
    *   List doctors by their medical specialization.
    *   List all available specializations.
    *   Query and display doctor availability for specific dates.
*   **Database Interaction:** All data is stored in a local SQLite database. Agents use specialized Langchain tools for CRUD operations.
*   **Audit Logging:** Key interactions are partially logged to the `ConversationLogs` table.

## Architecture

The application comprises a backend (CrewAI agents and database logic) and a new Flask web frontend:

1.  **Flask Web Frontend (`app.py`):**
    *   The main web application entry point using Flask.
    *   Handles HTTP requests, serves HTML pages, and processes form submissions.
    *   Interacts with the CrewAI backend by preparing and dispatching tasks to the appropriate agents based on user actions in the web UI.
    *   Renders results returned by the CrewAI agents back into HTML templates.
    *   `templates/` directory: Contains all HTML templates (e.g., `base.html`, `home.html`, `register_patient.html`) using Jinja2 templating.
    *   `static/` directory: Contains static files like `style.css`.

2.  **CrewAI Backend (Orchestrated by `app.py` or `main_crew.py`):**
    *   **LLM Initialization:** Loads API keys (from `.env`) and configures the chosen LLM (e.g., `ChatOpenAI`, `ChatGroq`). This is done globally in `app.py` and `main_crew.py`.
    *   **`crew_definitions.py`**: Defines blueprints for agent roles (Patient Onboarding Specialist, Scheduling Coordinator, Medical Records Clerk) and task outlines, guiding LLM behavior.
    *   **`database_tools.py`**: Provides Langchain `StructuredTool` objects wrapping database functions, enabling agents to interact with the database.
    *   **CrewAI Agents:** Instances of `Agent` (from `crewai`) are created based on `crew_definitions.py`, equipped with tools and the LLM.
    *   **CrewAI Tasks & Crew:** User requests (from web UI forms or CLI) are translated into CrewAI `Task` objects. A `Crew` is assembled with the relevant agent(s) and task(s) and then `kickoff()` is called to execute.

3.  **Database Layer:**
    *   **`database_manager.py`**: Core data access layer with Python functions for SQLite operations.
    *   **`hospital_schema.sql`**: Defines the database structure.

## Directory Structure

*   `app.py`: Main Flask web application file.
*   `main_crew.py`: Original CLI entry point for CrewAI logic (can be used for backend testing/interaction).
*   `crew_definitions.py`: Definitions for CrewAI agent roles and task outlines.
*   `database_tools.py`: Langchain tools for database interaction.
*   `database_manager.py`: Core Python functions for SQLite database operations.
*   `test_database_manager.py`: Unit tests for `database_manager.py`.
*   `hospital_schema.sql`: SQL DDL statements for database schema creation.
*   `requirements.txt`: Lists project Python dependencies.
*   `.gitignore`: Specifies intentionally untracked files for Git.
*   `.env.example`: Example file for configuring environment variables.
*   `templates/`: Directory for HTML templates.
    *   `base.html`: Base template for common page structure.
    *   `home.html`: Landing page.
    *   `register_patient.html`: Patient registration form.
    *   `schedule_appointment.html`: Appointment scheduling form.
    *   `view_appointments.html`: Page to view patient appointments.
    *   `view_doctors.html`: Page to view doctors and their availability.
    *   `404.html`, `500.html`: Custom error pages.
*   `static/`: Directory for static files.
    *   `style.css`: Main stylesheet.
*   `hospital_management.db`: The SQLite database file. (Note: `*.db` is in `.gitignore`).
*   `README.md`: This file.
*   `SECURITY_CONSIDERATIONS.md`: Security notes and recommendations.
*   `MANUAL_TESTING_GUIDE.md`: Guide for manually testing web and CLI interfaces.
*   `conversational_agent.py`: Previous CLI application (superseded, for reference).


## Setup and Running the Application

**Prerequisites:**

*   Python 3.x (preferably 3.9 or higher).
*   Git (for cloning, optional).
*   Access to an LLM API (e.g., OpenAI, Groq) and the corresponding API key.

**Installation & Setup:**

1.  **Clone the repository (optional).**
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure API Keys:**
    *   Copy the example environment file: `cp .env.example .env`
    *   Edit `.env` to add your API key(s) (e.g., `OPENAI_API_KEY="your_key_here"`) and set `LLM_PROVIDER` if not using OpenAI.

**Running the Application:**

There are two main ways to run the application:

1.  **Web Interface (Recommended for User Interaction):**
    *   **Initialize Database (Optional but Recommended for First Run / Reset):**
        ```bash
        python database_manager.py
        ```
        This (re)creates `hospital_management.db` with sample data.
    *   **Run the Flask Development Server:**
        ```bash
        python app.py
        ```
    *   Open your web browser and go to `http://127.0.0.1:5001` (or `http://0.0.0.0:5001`).
    *   The web application will attempt to initialize the LLM and then display the home page. Interact with features via the web UI.

2.  **Command-Line Interface (CLI - for backend logic testing/alternative interaction):**
    *   Ensure the database is initialized as above.
    *   Ensure API keys are set in `.env`.
    *   Run:
        ```bash
        python main_crew.py
        ```
    *   Interact with the agent via the command-line menu.

## Key Dependencies

*   **Flask:** For the web framework.
*   **CrewAI:** For orchestrating AI agents and tasks.
<<<<<<< HEAD
*   **Langchain (Core, Community, OpenAI, Groq):** For LLM interactions, tools, Pydantic models.
=======
*   **Langchain (Core, Community, OpenAI, Groq):** For LLM interactions, tools, and Pydantic model integration.
*   **Pydantic (v2.x):** Explicitly used for data validation and settings management, ensuring compatibility with the latest Langchain and CrewAI versions. Included in `requirements.txt`.
>>>>>>> origin/hospital-agent-crewai-refactor-v1
*   **Python-Dotenv:** For managing environment variables.
*   **SQLite:** The `sqlite3` module is part of the Python standard library.

## Testing

### Unit Tests (Database Layer)

Unit tests cover `database_manager.py` to ensure core data functions are correct. They do not test LLM/CrewAI components or the Flask UI.

1.  Ensure you are in the project directory.
2.  Run: `python -m unittest test_database_manager.py`

### Manual Testing

Comprehensive manual testing is crucial for both the Web UI and the CLI (if used).
*   Refer to **`MANUAL_TESTING_GUIDE.md`** for detailed scenarios.
*   **API Key Required:** Manual testing of `app.py` (web UI) or `main_crew.py` (CLI) **requires** a valid, configured LLM API key in `.env`.
*   Observe verbose agent output in the console for debugging.

## Important Considerations

*   **Security:** This is a prototype. Refer to `SECURITY_CONSIDERATIONS.md` for essential production enhancements.
*   **LLM Output Variability:** LLM responses vary. Test objectives, not exact string matches.
*   **Error Handling:** Basic; production needs more robustness.
*   **Asynchronous Task Processing (Web UI):** Current Flask routes execute CrewAI tasks synchronously. For production, use task queues (Celery, RQ) as detailed in the "Important Considerations -> Asynchronous Task Processing" section of this README. `app.py` includes `TODO` comments and an experimental threading example for patient registration.

This README provides a guide to understanding, setting up, and using the CrewAI-based Hospital Administration Agent with its Flask web interface.
