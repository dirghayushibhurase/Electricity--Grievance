create database EGS;
use EGS;
CREATE TABLE Divisions (
    division_id INT AUTO_INCREMENT PRIMARY KEY,
    division_name VARCHAR(100) NOT NULL UNIQUE,
    
    -- All indexes for optimal performance
    INDEX idx_division_name (division_name),
    INDEX idx_division_id_name (division_id, division_name) -- Composite index
);

CREATE TABLE Division_Heads (
    head_id INT AUTO_INCREMENT PRIMARY KEY,
    division_id INT NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE CASCADE,
    
    -- Comprehensive indexes
    INDEX idx_division_head_division (division_id),
    INDEX idx_division_head_active (is_active),
    INDEX idx_head_name (name), -- Additional index for name searches
    INDEX idx_head_email (email), -- Already unique, but explicit
    INDEX idx_head_phone (phone), -- Already unique, but explicit
    INDEX idx_head_active_division (is_active, division_id) -- Composite for common queries
);

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    division_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE SET NULL,
    
    -- Comprehensive indexes for all query patterns
    INDEX idx_user_division (division_id),
    INDEX idx_user_pincode (pincode),
    INDEX idx_user_city (city),
    INDEX idx_user_created (created_at),
    INDEX idx_user_name (name),
    INDEX idx_user_email (email), -- Already unique, but explicit
    INDEX idx_user_phone (phone), -- Already unique, but explicit
    INDEX idx_user_division_city (division_id, city), -- Composite for geographic queries
    INDEX idx_user_pincode_city (pincode, city), -- Composite for location-based queries
    INDEX idx_user_division_created (division_id, created_at) -- Composite for division reports
);


CREATE TABLE Workers (
    worker_id INT AUTO_INCREMENT PRIMARY KEY,  
    name VARCHAR(100) NOT NULL,                
    password VARCHAR(255) NOT NULL,
    age INT,
    phone_no VARCHAR(15) UNIQUE NOT NULL,     
    address TEXT,
    availability ENUM('Available','On Holiday','Sick Leave','On Task','Other') DEFAULT 'Available',
    worker_type ENUM('Technician','Inspector','Supervisor') NOT NULL,
    skill_sets VARCHAR(100),
    current_task_status ENUM('Active','Inactive') DEFAULT 'Active',
    division_id INT NOT NULL,                  -- Worker must belong to a division
    email VARCHAR(100) UNIQUE,                 
    is_active BOOLEAN DEFAULT TRUE,            -- Added for soft deletion
    created_by INT,                            -- Which division head created this worker
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES Division_Heads(head_id) ON DELETE SET NULL,
    
    -- Comprehensive Indexes
    INDEX idx_worker_division (division_id),
    INDEX idx_worker_availability (availability),
    INDEX idx_worker_type (worker_type),
    INDEX idx_worker_task_status (current_task_status),
    INDEX idx_worker_phone (phone_no),
    INDEX idx_worker_email (email),
    INDEX idx_worker_active (is_active),
    INDEX idx_worker_division_availability (division_id, availability),
    INDEX idx_worker_type_availability (worker_type, availability),
    INDEX idx_worker_division_type (division_id, worker_type)
);

CREATE TABLE Issues (
    issue_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    division_id INT NOT NULL,
    
    -- Address and Location
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Issue Details
    issue_type ENUM(
        'power_outage', 
        'voltage_fluctuation',
        'meter_problem', 
        'billing_dispute',
        'safety_hazard', 
        'equipment_damage',
        'street_light_fault',
        'transformer_issue',
        'wire_fault',
        'electric_shock',
        'other'
    ) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Media
    image_url VARCHAR(500),
    
    -- Simplified Status (Only 2 options)
    status ENUM('pending', 'resolved') DEFAULT 'pending',
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,  -- Only set when status = 'resolved'
    
    -- Foreign Keys
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE NO ACTION,
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE RESTRICT,
    
    -- Indexes
    INDEX idx_issue_status (status),
    INDEX idx_issue_division (division_id),
    INDEX idx_issue_user (user_id),
    INDEX idx_issue_type (issue_type),
    INDEX idx_issue_priority (priority),
    INDEX idx_issue_created (created_at),
    INDEX idx_issue_resolved (resolved_at),
    INDEX idx_issue_division_status (division_id, status)
);

CREATE TABLE IssueWorkers (
    issue_id INT NOT NULL,
    worker_id INT NOT NULL,
    assigned_by INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    worker_status ENUM('assigned',  'completed') NOT NULL, -- NO DEFAULT
    worker_notes TEXT,
    completed_at TIMESTAMP NULL,
    
    PRIMARY KEY (issue_id, worker_id),
    FOREIGN KEY (issue_id) REFERENCES Issues(issue_id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES Division_Heads(head_id) ON DELETE NO ACTION,
    
    INDEX idx_issueworker_worker (worker_id),
    INDEX idx_issueworker_status (worker_status)
);

-- ELECTRICAL_EQUIPMENT table
CREATE TABLE Electrical_Equipment (
    equipment_id INT AUTO_INCREMENT PRIMARY KEY,
    serial_no VARCHAR(50) UNIQUE NOT NULL,
    name_of_equipment VARCHAR(150) NOT NULL,
    model_no VARCHAR(100),
    purchase_date DATE NOT NULL,
    equipment_cost DECIMAL(10,2),
    calibration_date DATE,
    is_approved ENUM('Yes', 'No') DEFAULT 'No',
    division_id INT NOT NULL,
    
    -- Current assignment info
    current_worker_id INT NULL,
    issue_date DATE NULL,
    expected_return_date DATE NULL,
    re_issue_date DATE NULL,
    
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE CASCADE,
    FOREIGN KEY (current_worker_id) REFERENCES Workers(worker_id) ON DELETE SET NULL,
    
    INDEX idx_equipment_serial (serial_no),
    INDEX idx_equipment_division (division_id),
    INDEX idx_equipment_worker (current_worker_id),
    INDEX idx_equipment_reissue (re_issue_date)
);

-- EQUIPMENT_HISTORY table (Simplified - only heads can issue)
CREATE TABLE Equipment_History (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT NOT NULL,
    worker_id INT NOT NULL,
    action_type ENUM('requested', 'issued', 'returned', 'rejected') NOT NULL,
    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_by_head_id INT NOT NULL,  -- ALWAYS a division head
    purpose TEXT,
    expected_return_date DATE NULL,
    actual_return_date DATE NULL,
    re_issue_date DATE NULL,
    notes TEXT,
    
    FOREIGN KEY (equipment_id) REFERENCES Electrical_Equipment(equipment_id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id) ON DELETE CASCADE,
    FOREIGN KEY (action_by_head_id) REFERENCES Division_Heads(head_id) ON DELETE NO ACTION,
    
    INDEX idx_history_equipment (equipment_id),
    INDEX idx_history_worker (worker_id),
    INDEX idx_history_head (action_by_head_id),
    INDEX idx_history_date (action_date)
);
ALTER TABLE IssueWorkers 
MODIFY COLUMN worker_status ENUM('assigned', 'in_progress', 'completed') NOT NULL;
