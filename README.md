# Hospital Administration Agent (CrewAI Edition)

## Project Overview

The Hospital Administration Agent is a Python application demonstrating how CrewAI and Langchain can be used to create AI-powered agents capable of managing basic hospital administration tasks. Users interact with the system via a command-line interface to register patients, schedule/cancel/reschedule appointments, and query doctor information. The system leverages Large Language Models (LLMs) to understand and process requests, using a predefined set of tools to interact with an SQLite database where all hospital data is stored.

This project showcases a multi-agent approach where different agents (e.g., Patient Onboarding Specialist, Scheduling Coordinator, Medical Records Clerk) are responsible for specific areas of functionality, coordinated by CrewAI.

## Features

*   **AI-Powered Task Execution:** Uses CrewAI agents and an LLM (configurable, e.g., OpenAI GPT, Groq Mixtral) to interpret user needs and perform tasks.
*   **Patient Management:**
    *   Register new patients into the system.
    *   Retrieve existing patient details (e.g., by phone number for appointment viewing).
*   **Appointment Management:**
    *   Schedule new appointments, considering doctor availability.
    *   View a patient's upcoming and past appointments.
    *   Cancel existing 'Scheduled' appointments (releasing the time slot).
    *   Reschedule appointments (guided as a cancel-then-book-new process).
*   **Doctor Information & Availability:**
    *   List all registered doctors and their details.
    *   List doctors by their medical specialization.
    *   List all available specializations.
    *   Query and display doctor availability for specific dates.
*   **Database Interaction:** All data is stored in a local SQLite database. Agents use specialized Langchain tools to perform CRUD operations.
*   **Audit Logging:** Key interactions, agent actions, and tool usage can be (and are partially) logged to the `ConversationLogs` table for transparency and debugging.

## Architecture

The application is structured around the CrewAI framework:

1.  **`main_crew.py`**: This is the main entry point of the application. It handles:
    *   Loading environment variables (like API keys).
    *   Initializing the chosen Large Language Model (LLM).
    *   Instantiating CrewAI `Agent` objects based on definitions.
    *   Defining and preparing CrewAI `Task` objects based on user input from a CLI menu.
    *   Assembling and running the `Crew` to execute tasks.
    *   Presenting results back to the user.

2.  **`crew_definitions.py`**: This file defines the blueprints for the agents and tasks:
    *   **Agent Roles:** Specifies the `role`, `goal`, `backstory`, and default toolset for each agent (e.g., Patient Onboarding Specialist, Scheduling Coordinator, Medical Records Clerk).
    *   **Task Outlines:** Provides structured `description` and `expected_output` templates for common hospital administration tasks. These descriptions guide the LLM-powered agents.

3.  **`database_tools.py`**: This module creates Langchain `Tool` (specifically `StructuredTool`) objects.
    *   Each tool wraps a specific function from `database_manager.py`, enabling agents to interact with the database in a structured and natural language-compatible way.
    *   Tools have clear names, descriptions, and Pydantic-defined argument schemas (`args_schema`) for robust input handling.

4.  **`database_manager.py`**: This is the core data access layer.
    *   It contains Python functions for all direct SQLite database operations (CRUD actions for Patients, Doctors, Appointments, etc.).
    *   It is responsible for executing SQL queries defined in `hospital_schema.sql` to set up the database tables.

5.  **LLM Integration:**
    *   Agents within CrewAI are powered by an LLM (e.g., OpenAI's GPT models, Groq's Mixtral).
    *   The LLM interprets task descriptions, plans steps, decides which tools to use (from its assigned set), and formulates responses.
    *   Configuration of the LLM provider and API keys is done via a `.env` file.

## Directory Structure

*   `main_crew.py`: Main application script using CrewAI.
*   `crew_definitions.py`: Definitions for CrewAI agent roles and task outlines.
*   `database_tools.py`: Langchain tools for database interaction.
*   `database_manager.py`: Core Python functions for SQLite database operations.
*   `test_database_manager.py`: Unit tests for `database_manager.py`.
*   `hospital_schema.sql`: SQL DDL statements for database schema creation.
*   `requirements.txt`: Lists project Python dependencies.
*   `.gitignore`: Specifies intentionally untracked files for Git.
*   `.env.example`: Example file for configuring environment variables (API keys, LLM provider).
*   `hospital_management.db`: The SQLite database file, automatically created/updated during runtime. (Note: `*.db` is in `.gitignore`).
*   `README.md`: This file.
*   `SECURITY_CONSIDERATIONS.md`: Security notes and recommendations.
*   `MANUAL_TESTING_GUIDE.md`: Guide for manually testing `main_crew.py`.
*   `conversational_agent.py`: The previous, non-CrewAI CLI application (superseded by `main_crew.py`, kept for reference).

## Database Schema

The database schema is defined in `hospital_schema.sql`. Key tables include: Patients, Doctors, Appointments, DoctorAvailability, and ConversationLogs. For detailed structure, refer to `hospital_schema.sql`.

## Conversational Flows (via CrewAI)

The `main_crew.py` script provides a menu-driven interface. When a user selects an option:
1.  The script collects necessary input from the user.
2.  This input is used to format a specific task description (from `crew_definitions.py`).
3.  A CrewAI `Task` is created and assigned to an appropriate agent (e.g., patient registration to the "Patient Onboarding Specialist").
4.  A `Crew` is assembled and launched (`crew.kickoff()`).
5.  The assigned agent processes the task, using its LLM capabilities and assigned database tools to achieve the task's goal.
6.  The final result from the crew's work is printed to the user.

Detailed scenarios for each menu option are available in `MANUAL_TESTING_GUIDE.md`.

## Setup and Running the Agent

**Prerequisites:**

*   Python 3.x (preferably 3.9 or higher).
*   Git (for cloning, optional).
*   Access to an LLM API (e.g., OpenAI, Groq) and the corresponding API key.

**Installation & Setup:**

1.  **Clone the repository (optional):**
    ```bash
    # git clone <repository_url>
    # cd <repository_directory>
    ```
2.  **Install Dependencies:**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Configure API Keys:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your API key(s) and preferred provider/model if not using defaults:
        ```
        LLM_PROVIDER="openai" # or "groq"
        OPENAI_API_KEY="your_openai_api_key_here"
        # GROQ_API_KEY="your_groq_api_key_here"
        # OPENAI_MODEL_NAME="gpt-4" 
        # GROQ_MODEL_NAME="mixtral-8x7b-32768"
        ```
    *   **Important:** The `.env` file contains sensitive keys and is ignored by Git. Do not commit it.

**Running the Agent:**

1.  **Initialize Database (Optional but Recommended for First Run / Reset):**
    To ensure a consistent starting state with some sample data (doctors, availability), run:
    ```bash
    python database_manager.py
    ```
    This script (re)creates `hospital_management.db` and populates it.
2.  **Run the Main Application:**
    ```bash
    python main_crew.py
    ```
    The application will start, attempt to initialize the LLM (displaying provider information or errors if keys are misconfigured), and if successful, show the main menu.

## Key Dependencies

*   **CrewAI:** For orchestrating AI agents and tasks. (`crewai`, `crewai[tools]`)
*   **Langchain:** Core framework for LLM interactions, tools, and Pydantic models. (`langchain`, `langchain-community`, `langchain-openai`, `langchain-groq`)
*   **Python-Dotenv:** For managing environment variables (API keys).
*   **SQLite:** The `sqlite3` module is part of the Python standard library.

## Testing

### Unit Tests

Unit tests cover the foundational database logic in `database_manager.py`. They ensure the core data manipulation functions work correctly and do not test LLM or CrewAI components.

1.  Ensure you are in the project directory.
2.  Run the tests:
    ```bash
    python -m unittest test_database_manager.py
    ```

### Manual Testing (CrewAI Application)

For testing the complete CrewAI application flows via `main_crew.py`:
*   Refer to **`MANUAL_TESTING_GUIDE.md`**.
*   This guide provides detailed scenarios for each menu option.
*   **API Key Required:** Manual testing of `main_crew.py` **requires** a valid, configured LLM API key in your `.env` file.
*   The verbose output from agents (enabled in `main_crew.py`) is crucial for observing their decision-making and tool usage during tests.

## Important Considerations

*   **Security:** This application is a prototype. For production use, refer to `SECURITY_CONSIDERATIONS.md` for critical security enhancements needed.
*   **LLM Output Variability:** LLM responses can vary. Testing should focus on whether the task's objective was met (e.g., data correctly written to DB) rather than exact string matches in responses.
*   **Error Handling:** Current error handling is basic. Production systems require more robust error management.

This README provides a guide to understanding, setting up, and using the CrewAI-based Hospital Administration Agent.
