-- Create an issue audit log table to track changes
CREATE TABLE IF NOT EXISTS Issue_Audit_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT NOT NULL,
    action_type ENUM('CREATED', 'UPDATED', 'VIEWED', 'STATUS_CHANGED') NOT NULL,
    old_values JSON,
    new_values JSON,
    changed_by INT, -- user_id who made the change
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    INDEX idx_issue_id (issue_id),
    INDEX idx_changed_at (changed_at),
    INDEX idx_action_type (action_type),
    FOREIGN KEY (issue_id) REFERENCES Issues(issue_id) ON DELETE CASCADE
);

-- Trigger for logging issue creation
DELIMITER $$
CREATE TRIGGER after_issue_insert
AFTER INSERT ON Issues
FOR EACH ROW
BEGIN
    INSERT INTO Issue_Audit_Log (issue_id, action_type, new_values, changed_by)
    VALUES (
        NEW.issue_id, 
        'CREATED',
        JSON_OBJECT(
            'title', NEW.title,
            'issue_type', NEW.issue_type,
            'priority', NEW.priority,
            'status', NEW.status,
            'division_id', NEW.division_id
        ),
        NEW.user_id
    );
END$$
DELIMITER ;

-- Trigger for logging issue updates
DELIMITER $$
CREATE TRIGGER after_issue_update
AFTER UPDATE ON Issues
FOR EACH ROW
BEGIN
    IF OLD.title != NEW.title OR OLD.description != NEW.description OR OLD.priority != NEW.priority OR OLD.issue_type != NEW.issue_type THEN
        INSERT INTO Issue_Audit_Log (issue_id, action_type, old_values, new_values, changed_by)
        VALUES (
            NEW.issue_id, 
            'UPDATED',
            JSON_OBJECT(
                'title', OLD.title,
                'issue_type', OLD.issue_type,
                'priority', OLD.priority,
                'description', OLD.description
            ),
            JSON_OBJECT(
                'title', NEW.title,
                'issue_type', NEW.issue_type,
                'priority', NEW.priority,
                'description', NEW.description
            ),
            NEW.user_id
        );
    END IF;
    
    IF OLD.status != NEW.status THEN
        INSERT INTO Issue_Audit_Log (issue_id, action_type, old_values, new_values, changed_by)
        VALUES (
            NEW.issue_id, 
            'STATUS_CHANGED',
            JSON_OBJECT('status', OLD.status),
            JSON_OBJECT('status', NEW.status),
            NEW.user_id
        );
    END IF;
END$$
DELIMITER ;

select *from Issue_Audit_Log;

-- Create user audit log table
CREATE TABLE IF NOT EXISTS User_Audit_Log (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action_type ENUM('PROFILE_UPDATED', 'PASSWORD_CHANGED', 'EMAIL_CHANGED') NOT NULL,
    old_values JSON,
    new_values JSON,
    changed_by INT, -- Usually the same user_id for self-updates
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    INDEX idx_user_audit_user (user_id),
    INDEX idx_user_audit_date (changed_at),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- Trigger for logging user profile updates
DELIMITER $$
CREATE TRIGGER after_user_update
AFTER UPDATE ON Users
FOR EACH ROW
BEGIN
    DECLARE changes_made BOOLEAN DEFAULT FALSE;
    DECLARE old_data JSON DEFAULT NULL;
    DECLARE new_data JSON DEFAULT NULL;
    
    -- Check if any profile information changed (excluding password)
    IF OLD.name != NEW.name OR OLD.phone != NEW.phone OR OLD.email != NEW.email OR 
       OLD.address_line1 != NEW.address_line1 OR OLD.address_line2 != NEW.address_line2 OR 
       OLD.city != NEW.city OR OLD.pincode != NEW.pincode OR OLD.division_id != NEW.division_id THEN
        
        SET changes_made = TRUE;
        SET old_data = JSON_OBJECT(
            'name', OLD.name,
            'phone', OLD.phone,
            'email', OLD.email,
            'address_line1', OLD.address_line1,
            'address_line2', OLD.address_line2,
            'city', OLD.city,
            'pincode', OLD.pincode,
            'division_id', OLD.division_id
        );
        SET new_data = JSON_OBJECT(
            'name', NEW.name,
            'phone', NEW.phone,
            'email', NEW.email,
            'address_line1', NEW.address_line1,
            'address_line2', NEW.address_line2,
            'city', NEW.city,
            'pincode', NEW.pincode,
            'division_id', NEW.division_id
        );
    END IF;
    
    -- Check if password changed
    IF OLD.password != NEW.password THEN
        INSERT INTO User_Audit_Log (user_id, action_type, changed_by, ip_address, user_agent)
        VALUES (NEW.user_id, 'PASSWORD_CHANGED', NEW.user_id, NULL, NULL);
    END IF;
    
    -- Check if email changed specifically
    IF OLD.email != NEW.email THEN
        INSERT INTO User_Audit_Log (user_id, action_type, old_values, new_values, changed_by)
        VALUES (NEW.user_id, 'EMAIL_CHANGED', 
                JSON_OBJECT('old_email', OLD.email),
                JSON_OBJECT('new_email', NEW.email),
                NEW.user_id);
    END IF;
    
    -- Log general profile updates
    IF changes_made THEN
        INSERT INTO User_Audit_Log (user_id, action_type, old_values, new_values, changed_by)
        VALUES (NEW.user_id, 'PROFILE_UPDATED', old_data, new_data, NEW.user_id);
    END IF;
END$$
DELIMITER ;


-- Create table for signup logs if it doesn't exist
CREATE TABLE IF NOT EXISTS User_Signup_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    signup_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    division_id INT,
    city VARCHAR(100),
    pincode VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE SET NULL
);

-- Trigger for logging user signups
DELIMITER //
CREATE TRIGGER after_user_signup
    AFTER INSERT ON Users
    FOR EACH ROW
BEGIN
    INSERT INTO User_Signup_Log (user_id, ip_address, user_agent, division_id, city, pincode)
    VALUES (NEW.user_id, @signup_ip, @signup_agent, NEW.division_id, NEW.city, NEW.pincode);
END//
DELIMITER ;

-- Create table for signup logs if it doesn't exist
CREATE TABLE IF NOT EXISTS User_Signup_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    signup_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    division_id INT,
    city VARCHAR(100),
    pincode VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS User_Signup_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    signup_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    division_id INT,
    city VARCHAR(100),
    pincode VARCHAR(20),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE SET NULL
);

select *from User_Signup_Log;