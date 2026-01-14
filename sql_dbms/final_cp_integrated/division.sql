
-- Create Failed Login Attempts table if not exists ***************
CREATE TABLE IF NOT EXISTS Failed_Login_Attempts (
    attempt_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    division_id INT NULL,
    
    INDEX idx_failed_email (email),
    INDEX idx_failed_time (attempted_at),
    INDEX idx_failed_division (division_id),
    FOREIGN KEY (division_id) REFERENCES Divisions(division_id) ON DELETE SET NULL
);

-- Create trigger for failed login attempts ********************
DELIMITER $$
CREATE TRIGGER after_failed_login
AFTER INSERT ON Failed_Login_Attempts
FOR EACH ROW
BEGIN
    -- This trigger can be used for additional logging or notifications
    -- Currently just logging the attempt in the table
END$$
DELIMITER ;


-- View for Division Issue Summary
CREATE VIEW Division_Issue_Summary AS
SELECT 
    d.division_id,
    d.division_name,
    COUNT(i.issue_id) as total_issues,
    SUM(CASE WHEN i.status = 'pending' THEN 1 ELSE 0 END) as pending_issues,
    SUM(CASE WHEN i.status = 'resolved' THEN 1 ELSE 0 END) as resolved_issues,
    SUM(CASE WHEN iw.worker_id IS NOT NULL THEN 1 ELSE 0 END) as assigned_issues,
    ROUND((SUM(CASE WHEN i.status = 'resolved' THEN 1 ELSE 0 END) / COUNT(i.issue_id)) * 100, 2) as resolution_rate
FROM Divisions d
LEFT JOIN Issues i ON d.division_id = i.division_id
LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id AND iw.worker_status != 'completed'
GROUP BY d.division_id, d.division_name;

-- View for Worker Performance ********
CREATE VIEW Worker_Performance AS
SELECT 
    w.worker_id,
    w.name,
    w.worker_type,
    w.division_id,
    COUNT(iw.issue_id) as total_tasks,
    SUM(CASE WHEN iw.worker_status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
    ROUND((SUM(CASE WHEN iw.worker_status = 'completed' THEN 1 ELSE 0 END) / COUNT(iw.issue_id)) * 100, 2) as completion_rate,
    AVG(TIMESTAMPDIFF(HOUR, iw.assigned_at, iw.completed_at)) as avg_completion_hours
FROM Workers w
LEFT JOIN IssueWorkers iw ON w.worker_id = iw.worker_id
WHERE w.is_active = TRUE
GROUP BY w.worker_id, w.name, w.worker_type, w.division_id;

-- View for Division Live Status
CREATE VIEW Division_Live_Status AS
SELECT 
    d.division_id,
    d.division_name,
    COUNT(DISTINCT w.worker_id) as total_workers,
    SUM(CASE WHEN w.availability = 'Available' THEN 1 ELSE 0 END) as available_workers,
    COUNT(DISTINCT i.issue_id) as pending_issues,
    SUM(CASE WHEN i.status = 'resolved' AND DATE(i.resolved_at) = CURDATE() THEN 1 ELSE 0 END) as resolved_today,
    ROUND((SUM(CASE WHEN i.status = 'resolved' THEN 1 ELSE 0 END) / NULLIF(COUNT(i.issue_id), 0)) * 100, 2) as resolution_rate
FROM Divisions d
LEFT JOIN Workers w ON d.division_id = w.division_id AND w.is_active = TRUE
LEFT JOIN Issues i ON d.division_id = i.division_id
GROUP BY d.division_id, d.division_name;

-- View for Security Logs  -- ***********
CREATE VIEW Security_Logs_View AS
SELECT 
    f.attempt_id,
    f.email,
    f.attempted_at,
    f.ip_address,
    f.division_id,
    d.division_name,
    CASE 
        WHEN dh.head_id IS NOT NULL THEN 'Division Head'
        WHEN w.worker_id IS NOT NULL THEN 'Worker'
        WHEN u.user_id IS NOT NULL THEN 'User'
        ELSE 'Unknown'
    END as user_type
FROM Failed_Login_Attempts f
LEFT JOIN Divisions d ON f.division_id = d.division_id
LEFT JOIN Division_Heads dh ON f.email = dh.email
LEFT JOIN Workers w ON f.email = w.email
LEFT JOIN Users u ON f.email = u.email;

-- View for User Activity Logs ********************8error
CREATE VIEW User_Activity_Logs AS
SELECT 
    ual.audit_id,
    ual.user_id,
    u.name as user_name,
    ual.action_type,
    ual.old_values,
    ual.new_values,
    ual.changed_at,
    u.division_id
FROM User_Audit_Log ual
JOIN Users u ON ual.user_id = u.user_id;

-- View for Issue Audit Logs---*********888error
CREATE VIEW Issue_Audit_Logs_View AS
SELECT 
    ial.log_id,
    ial.issue_id,
    i.title as issue_title,
    ial.action_type,
    ial.old_values,
    ial.new_values,
    u.name as changed_by_name,
    ial.changed_at,
    i.division_id
FROM Issue_Audit_Log ial
JOIN Issues i ON ial.issue_id = i.issue_id
LEFT JOIN Users u ON ial.changed_by = u.user_id;


-- Drop and recreate the problematic view 
DROP VIEW IF EXISTS Division_Live_Status;

CREATE VIEW Division_Live_Status AS -- ***************
SELECT 
    d.division_id,
    d.division_name,
    COUNT(DISTINCT w.worker_id) as total_workers,
    COUNT(DISTINCT CASE WHEN w.availability = 'Available' THEN w.worker_id END) as available_workers,
    COUNT(DISTINCT i.issue_id) as total_issues,
    COUNT(DISTINCT CASE WHEN i.status = 'pending' THEN i.issue_id END) as pending_issues,
    COUNT(DISTINCT CASE WHEN i.status = 'resolved' AND DATE(i.resolved_at) = CURDATE() THEN i.issue_id END) as resolved_today,
    ROUND(
        (COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) / 
        NULLIF(COUNT(DISTINCT i.issue_id), 0)) * 100, 2
    ) as resolution_rate
FROM Divisions d
LEFT JOIN Workers w ON d.division_id = w.division_id AND w.is_active = TRUE
LEFT JOIN Issues i ON d.division_id = i.division_id
GROUP BY d.division_id, d.division_name;

DROP VIEW IF EXISTS Division_Issue_Summary;

CREATE VIEW Division_Issue_Summary AS
SELECT 
    d.division_id,
    d.division_name,
    COUNT(DISTINCT i.issue_id) as total_issues,
    COUNT(DISTINCT CASE WHEN i.status = 'pending' THEN i.issue_id END) as pending_issues,
    COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) as resolved_issues,
    COUNT(DISTINCT CASE WHEN iw.worker_id IS NOT NULL AND i.status != 'resolved' THEN i.issue_id END) as assigned_issues,
    ROUND(
        (COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) / 
        NULLIF(COUNT(DISTINCT i.issue_id), 0)) * 100, 2
    ) as resolution_rate
FROM Divisions d
LEFT JOIN Issues i ON d.division_id = i.division_id
LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id AND iw.worker_status != 'completed'
GROUP BY d.division_id, d.division_name;



-- just for chekcing not implemented
UPDATE Issues i
JOIN IssueWorkers iw ON i.issue_id = iw.issue_id
SET i.status = 'resolved', i.resolved_at = iw.completed_at
WHERE iw.worker_status = 'completed' AND i.status = 'pending';

UPDATE Workers w
JOIN IssueWorkers iw ON w.worker_id = iw.worker_id
SET w.availability = 'Available'
WHERE iw.worker_status = 'completed' AND w.availability = 'On Task';

drop procedure AddDivisionWorker;  -- **************
DELIMITER //

CREATE PROCEDURE AddDivisionWorker( -- *******************
    IN p_name VARCHAR(100),
    IN p_email VARCHAR(100),
    IN p_phone_no VARCHAR(15),
    IN p_age INT,
    IN p_address TEXT,
    IN p_worker_type ENUM('Technician','Inspector','Supervisor'),
    IN p_skill_sets VARCHAR(100),
    IN p_password VARCHAR(255),
    IN p_division_id INT,
    IN p_created_by INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Insert the new worker
    INSERT INTO Workers (
        name, email, phone_no, age, address, worker_type, 
        skill_sets, password, division_id, created_by
    ) VALUES (
        p_name, p_email, p_phone_no, p_age, p_address, p_worker_type,
        p_skill_sets, p_password, p_division_id, p_created_by
    );
    
    COMMIT;
END //

DELIMITER ;

DELIMITER //  -- ******************

CREATE TRIGGER before_worker_soft_delete -- ************
BEFORE UPDATE ON Workers
FOR EACH ROW
BEGIN
    IF NEW.is_active = FALSE AND OLD.is_active = TRUE THEN
        -- Log the deletion in audit log (you'll need to create this table)
        INSERT INTO Worker_Deletion_Log (worker_id, worker_name, deleted_by, deleted_at)
        VALUES (OLD.worker_id, OLD.name, @current_user_id, NOW());
        
        -- Set worker as inactive and update availability
        SET NEW.availability = 'Other';
        SET NEW.current_task_status = 'Inactive';
    END IF;
END //

DELIMITER ;

CREATE TABLE IF NOT EXISTS Worker_Deletion_Log ( -- **********
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    worker_id INT NOT NULL,
    worker_name VARCHAR(100) NOT NULL,
    deleted_by INT NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deleted_by) REFERENCES Division_Heads(head_id)
);

-- Drop the previous trigger if exists
DROP TRIGGER IF EXISTS before_worker_soft_delete;

-- Create new trigger for soft delete ***********
DELIMITER //

CREATE TRIGGER before_worker_soft_delete
BEFORE UPDATE ON Workers
FOR EACH ROW
BEGIN
    IF NEW.is_active = FALSE AND OLD.is_active = TRUE THEN
        -- Log the deletion
        INSERT INTO Worker_Deletion_Log (worker_id, worker_name, deleted_by, deleted_at)
        VALUES (OLD.worker_id, OLD.name, @current_user_id, NOW());
        
        -- Set worker as inactive and update availability
        SET NEW.availability = 'Other';
        SET NEW.current_task_status = 'Inactive';
    END IF;
END //

DELIMITER ;
