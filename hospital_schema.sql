-- Patients Table
CREATE TABLE IF NOT EXISTS Patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(50),
    phone_number VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    address TEXT,
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Doctors Table
CREATE TABLE IF NOT EXISTS Doctors (
    doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255),
    phone_number VARCHAR(20) UNIQUE,
    email VARCHAR(255) UNIQUE,
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments Table
CREATE TABLE IF NOT EXISTS Appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INT,
    doctor_id INT,
    appointment_datetime DATETIME,
    duration_minutes INT DEFAULT 30,
    reason_for_visit TEXT,
    status VARCHAR(50) DEFAULT 'Scheduled', -- Possible values: 'Scheduled', 'Completed', 'Cancelled', 'Rescheduled'
    notes TEXT,
    availability_id INT NULL, -- Link to the specific availability slot booked
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id),
    FOREIGN KEY (availability_id) REFERENCES DoctorAvailability(availability_id)
);

-- DoctorAvailability Table
CREATE TABLE IF NOT EXISTS DoctorAvailability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    creation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id),
    CONSTRAINT chk_time_order CHECK (start_time < end_time)
);

-- ConversationLogs Table
CREATE TABLE IF NOT EXISTS ConversationLogs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INT NULL, -- Can be NULL if patient is not yet registered
    session_id VARCHAR(255),
    message_text TEXT NOT NULL,
    intent_detected VARCHAR(255),
    entities_extracted TEXT, -- Changed JSON to TEXT for broader SQLite compatibility
    log_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id)
);
