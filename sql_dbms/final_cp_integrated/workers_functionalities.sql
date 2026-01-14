-- Add new tables for Worker functionality
CREATE TABLE IF NOT EXISTS Attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    date DATE NOT NULL,
    status ENUM('Present', 'Absent', 'Leave') DEFAULT 'Present',
    in_time TIME,
    out_time TIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id) ON DELETE CASCADE,
    UNIQUE KEY unique_worker_date (worker_id, date),
    
    INDEX idx_attendance_worker (worker_id),
    INDEX idx_attendance_date (date),
    INDEX idx_attendance_status (status)
);

CREATE TABLE IF NOT EXISTS Notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    message VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id) ON DELETE CASCADE,
    
    INDEX idx_notifications_worker (worker_id),
    INDEX idx_notifications_read (is_read),
    INDEX idx_notifications_created (created_at)
);
INSERT INTO Notifications (worker_id, message) VALUES
(1, 'New task assigned: Power outage in Sector 5'),
(1, 'Your leave application for 2024-01-15 to 2024-01-17 has been approved'),
(1, 'Equipment request for Multimeter has been rejected'),
(1, 'Your attendance for today has been recorded');

select *from notifications;
CREATE TABLE IF NOT EXISTS Worker_Audit_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    action_type ENUM('Profile Update', 'Equipment Request', 'Attendance Marked', 'Leave Applied', 'Issue Status Updated') NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id) ON DELETE CASCADE,
    
    INDEX idx_worker_audit_worker (worker_id),
    INDEX idx_worker_audit_type (action_type),
    INDEX idx_worker_audit_created (created_at)
);

CREATE TABLE IF NOT EXISTS Leave_Applications (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT NULL,
    reviewed_at TIMESTAMP NULL,
    
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES Division_Heads(head_id) ON DELETE SET NULL,
    
    INDEX idx_leave_worker (worker_id),
    INDEX idx_leave_status (status),
    INDEX idx_leave_dates (start_date, end_date)
);

-- Create views for worker dashboard
CREATE OR REPLACE VIEW worker_assigned_issues AS
SELECT 
    iw.issue_id,
    iw.worker_id,
    iw.worker_status,
    iw.assigned_at,
    iw.worker_notes,
    iw.completed_at,
    i.title,
    i.issue_type,
    i.description,
    i.priority,
    i.status as issue_status,
    i.created_at as issue_created_at,
    u.name as user_name,
    u.phone as user_phone,
    d.division_name
FROM IssueWorkers iw
JOIN Issues i ON iw.issue_id = i.issue_id
JOIN Users u ON i.user_id = u.user_id
JOIN Divisions d ON i.division_id = d.division_id;

CREATE OR REPLACE VIEW worker_equipment_assignments AS
SELECT 
    e.equipment_id,
    e.serial_no,
    e.name_of_equipment,
    e.model_no,
    e.purchase_date,
    e.calibration_date,
    e.is_approved,
    e.current_worker_id,
    e.issue_date,
    e.expected_return_date,
    e.re_issue_date,
    e.remarks,
    w.name as worker_name
FROM Electrical_Equipment e
JOIN Workers w ON e.current_worker_id = w.worker_id;

CREATE OR REPLACE VIEW worker_monthly_attendance AS
SELECT 
    worker_id,
    MONTH(date) as month,
    YEAR(date) as year,
    COUNT(*) as total_days,
    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
    SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
    SUM(CASE WHEN status = 'Leave' THEN 1 ELSE 0 END) as leave_days
FROM Attendance
GROUP BY worker_id, MONTH(date), YEAR(date);

-- Create stored procedures
DELIMITER $$

CREATE PROCEDURE get_worker_stats(IN p_worker_id INT)
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM worker_assigned_issues WHERE worker_id = p_worker_id) as total_tasks,
        (SELECT COUNT(*) FROM worker_assigned_issues WHERE worker_id = p_worker_id AND worker_status = 'assigned') as ongoing_tasks,
        (SELECT COUNT(*) FROM worker_assigned_issues WHERE worker_id = p_worker_id AND worker_status = 'completed') as completed_tasks,
        (SELECT COUNT(*) FROM Notifications WHERE worker_id = p_worker_id AND is_read = FALSE) as unread_notifications,
        (SELECT COUNT(*) FROM worker_equipment_assignments WHERE current_worker_id = p_worker_id) as assigned_equipment;
END$$

CREATE PROCEDURE mark_attendance(
    IN p_worker_id INT,
    IN p_date DATE,
    IN p_status ENUM('Present', 'Absent', 'Leave'),
    IN p_in_time TIME,
    IN p_out_time TIME
)
BEGIN
    INSERT INTO Attendance (worker_id, date, status, in_time, out_time)
    VALUES (p_worker_id, p_date, p_status, p_in_time, p_out_time)
    ON DUPLICATE KEY UPDATE
        status = p_status,
        in_time = p_in_time,
        out_time = p_out_time;
        
    INSERT INTO Worker_Audit_Log (worker_id, action_type, description)
    VALUES (p_worker_id, 'Attendance Marked', 
            CONCAT('Date: ', p_date, ', Status: ', p_status, ', In: ', COALESCE(p_in_time, 'N/A'), ', Out: ', COALESCE(p_out_time, 'N/A')));
END$$

CREATE PROCEDURE apply_for_leave(
    IN p_worker_id INT,
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_reason TEXT
)
BEGIN
    INSERT INTO Leave_Applications (worker_id, start_date, end_date, reason)
    VALUES (p_worker_id, p_start_date, p_end_date, p_reason);
    
    INSERT INTO Worker_Audit_Log (worker_id, action_type, description)
    VALUES (p_worker_id, 'Leave Applied', 
            CONCAT('Leave from ', p_start_date, ' to ', p_end_date, '. Reason: ', p_reason));
END$$

CREATE PROCEDURE update_worker_profile(
    IN p_worker_id INT,
    IN p_name VARCHAR(100),
    IN p_age INT,
    IN p_phone_no VARCHAR(15),
    IN p_address TEXT,
    IN p_skill_sets VARCHAR(100)
)
BEGIN
    -- Validate age
    IF p_age IS NOT NULL AND p_age <= 18 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Age must be greater than 18';
    END IF;

    -- Validate phone number
    IF p_phone_no IS NOT NULL AND NOT (CHAR_LENGTH(p_phone_no) = 10 AND p_phone_no REGEXP '^[0-9]{10}$') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Phone number must be exactly 10 digits';
    END IF;

    UPDATE Workers
    SET name = p_name, 
        age = p_age, 
        phone_no = p_phone_no, 
        address = p_address,
        skill_sets = p_skill_sets
    WHERE worker_id = p_worker_id;

    INSERT INTO Worker_Audit_Log (worker_id, action_type, description)
    VALUES (p_worker_id, 'Profile Update', 
            CONCAT('Updated profile: Name=', p_name, ', Age=', p_age, ', Phone=', p_phone_no));
END$$

DELIMITER ;

-- Create triggers
DELIMITER $$

CREATE TRIGGER after_worker_attendance_insert
AFTER INSERT ON Attendance
FOR EACH ROW
BEGIN
    INSERT INTO Worker_Audit_Log (worker_id, action_type, description)
    VALUES (NEW.worker_id, 'Attendance Marked', 
            CONCAT('Date: ', NEW.date, ', Status: ', NEW.status));
END$$

CREATE TRIGGER after_worker_attendance_update
AFTER UPDATE ON Attendance
FOR EACH ROW
BEGIN
    INSERT INTO Worker_Audit_Log (worker_id, action_type, description)
    VALUES (NEW.worker_id, 'Attendance Marked', 
            CONCAT('Updated attendance for ', NEW.date, ' to ', NEW.status));
END$$

CREATE TRIGGER after_issue_status_update
AFTER UPDATE ON IssueWorkers
FOR EACH ROW
BEGIN
    IF NEW.worker_status != OLD.worker_status THEN
        INSERT INTO Worker_Audit_Log (worker_id, action_type, description)
        VALUES (NEW.worker_id, 'Issue Status Updated', 
                CONCAT('Issue ', NEW.issue_id, ' status changed to ', NEW.worker_status));
    END IF;
END$$

DELIMITER ;

