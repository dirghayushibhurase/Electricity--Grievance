
-- If action_by_head_id has NOT NULL constraint, we need to modify it
ALTER TABLE Equipment_History MODIFY COLUMN action_by_head_id INT NULL;

-- Create view for equipment requests from workers
CREATE VIEW equipment_requests_view AS
SELECT 
    eh.history_id,
    eh.equipment_id,
    e.name_of_equipment,
    e.serial_no,
    eh.worker_id,
    w.name AS worker_name,
    w.division_id,
    d.division_name,
    eh.action_type,
    eh.purpose,
    eh.expected_return_date,
    eh.action_date,
    eh.action_by_head_id,
    eh.notes
FROM Equipment_History eh
JOIN Electrical_Equipment e ON eh.equipment_id = e.equipment_id
JOIN Workers w ON eh.worker_id = w.worker_id
JOIN Divisions d ON w.division_id = d.division_id
WHERE eh.action_type = 'requested';

-- Create comprehensive equipment view for division heads (without status column)
CREATE VIEW division_equipment_view AS
SELECT 
    e.equipment_id,
    e.serial_no,
    e.name_of_equipment,
    e.model_no,
    e.purchase_date,
    e.equipment_cost,
    e.calibration_date,
    e.is_approved,
    e.division_id,
    d.division_name,
    e.current_worker_id,
    w.name AS worker_name,
    e.issue_date,
    e.expected_return_date,
    e.re_issue_date,
    e.remarks,
    CASE 
        WHEN e.current_worker_id IS NULL THEN 'Available'
        ELSE 'Assigned'
    END AS availability_status
FROM Electrical_Equipment e
LEFT JOIN Workers w ON e.current_worker_id = w.worker_id
LEFT JOIN Divisions d ON e.division_id = d.division_id;

-- Create other views based on your exact schema
CREATE VIEW equipment_status AS 
SELECT equipment_id, name_of_equipment, is_approved, re_issue_date 
FROM Electrical_Equipment;

CREATE VIEW equipment_financials AS 
SELECT equipment_id, name_of_equipment, equipment_cost, purchase_date, issue_date
FROM Electrical_Equipment;

CREATE VIEW worker_equipment_view AS 
SELECT w.worker_id, w.name AS worker_name, e.equipment_id, 
       e.name_of_equipment, e.issue_date, e.is_approved 
FROM Workers w 
JOIN Electrical_Equipment e ON w.worker_id = e.current_worker_id;

CREATE VIEW worker_equipment_count AS
SELECT current_worker_id as worker_id,
       COUNT(*) AS total_equipment,
       SUM(CASE WHEN is_approved = 'Yes' THEN 1 ELSE 0 END) AS approved_equipment
FROM Electrical_Equipment
WHERE current_worker_id IS NOT NULL
GROUP BY current_worker_id;

CREATE VIEW highly_assigned_workers AS
SELECT worker_id, total_equipment
FROM worker_equipment_count
WHERE total_equipment > 2;

CREATE VIEW equipment_history_view AS
SELECT 
    eh.history_id,
    eh.equipment_id,
    e.name_of_equipment,
    e.serial_no,
    eh.worker_id,
    w.name AS worker_name,
    eh.action_type,
    eh.action_date,
    eh.action_by_head_id,
    dh.name AS head_name,
    eh.purpose,
    eh.expected_return_date,
    eh.actual_return_date,
    eh.re_issue_date,
    eh.notes
FROM Equipment_History eh
JOIN Electrical_Equipment e ON eh.equipment_id = e.equipment_id
JOIN Workers w ON eh.worker_id = w.worker_id
LEFT JOIN Division_Heads dh ON eh.action_by_head_id = dh.head_id
ORDER BY eh.action_date DESC;

DELIMITER //
CREATE PROCEDURE AddNewEquipment(
    IN p_serial_no VARCHAR(50),
    IN p_name_of_equipment VARCHAR(150),
    IN p_model_no VARCHAR(100),
    IN p_purchase_date DATE,
    IN p_equipment_cost DECIMAL(10,2),
    IN p_calibration_date DATE,
    IN p_division_id INT,
    IN p_remarks TEXT
)
BEGIN
    INSERT INTO Electrical_Equipment (
        serial_no, 
        name_of_equipment, 
        model_no, 
        purchase_date, 
        equipment_cost, 
        calibration_date, 
        division_id, 
        remarks,
        is_approved
    ) VALUES (
        p_serial_no,
        p_name_of_equipment,
        p_model_no,
        p_purchase_date,
        p_equipment_cost,
        p_calibration_date,
        p_division_id,
        p_remarks,
        'No'
    );
END//
DELIMITER ;

-- Verify all assigned equipment now have history
SELECT 
    e.equipment_id,
    e.serial_no,
    e.name_of_equipment,
    COUNT(eh.history_id) as history_count,
    MAX(CASE WHEN eh.action_type = 'issued' THEN 1 ELSE 0 END) as has_issued_record
FROM Electrical_Equipment e
LEFT JOIN Equipment_History eh ON e.equipment_id = eh.equipment_id
WHERE e.current_worker_id IS NOT NULL
GROUP BY e.equipment_id, e.serial_no, e.name_of_equipment
ORDER BY e.equipment_id;

SELECT action_type, COUNT(*) as record_count
FROM equipment_history 
GROUP BY action_type;


-- Fix the equipment_history_view to avoid duplicate entries
DROP VIEW IF EXISTS equipment_history_view;
CREATE VIEW equipment_history_view AS
SELECT DISTINCT
    eh.history_id,
    eh.equipment_id,
    e.name_of_equipment,
    e.serial_no,
    eh.worker_id,
    w.name AS worker_name,
    eh.action_type,
    eh.action_date,
    eh.action_by_head_id,
    dh.name AS head_name,
    eh.purpose,
    eh.expected_return_date,
    eh.actual_return_date,
    eh.re_issue_date,
    eh.notes
FROM Equipment_History eh
JOIN Electrical_Equipment e ON eh.equipment_id = e.equipment_id
JOIN Workers w ON eh.worker_id = w.worker_id
LEFT JOIN Division_Heads dh ON eh.action_by_head_id = dh.head_id
ORDER BY eh.action_date DESC;




-- Add notification system for equipment approval


DELIMITER //
CREATE PROCEDURE CreateEquipmentApprovalNotification(
    IN p_worker_id INT,
    IN p_equipment_name VARCHAR(150),
    IN p_action_type VARCHAR(50)
)
BEGIN
    DECLARE notification_message VARCHAR(255);
    
    IF p_action_type = 'approved' THEN
        SET notification_message = CONCAT('Your equipment request for "', p_equipment_name, '" has been approved and issued.');
    ELSE
        SET notification_message = CONCAT('Your equipment request for "', p_equipment_name, '" has been rejected.');
    END IF;
    
    INSERT INTO Notifications (worker_id, message, created_at)
    VALUES (p_worker_id, notification_message, NOW());
END//
DELIMITER ;


CREATE VIEW equipment_requests_view AS
SELECT 
    eh.history_id,
    eh.equipment_id,
    e.name_of_equipment,
    e.serial_no,
    eh.worker_id,
    w.name AS worker_name,
    w.division_id,
    d.division_name,
    eh.action_type,
    eh.purpose,
    eh.expected_return_date,
    eh.action_date,
    eh.action_by_head_id,
    eh.notes
FROM Equipment_History eh
JOIN Electrical_Equipment e ON eh.equipment_id = e.equipment_id
JOIN Workers w ON eh.worker_id = w.worker_id
JOIN Divisions d ON w.division_id = d.division_id
WHERE eh.action_type = 'requested';


CREATE VIEW equipment_history_view AS
SELECT DISTINCT
    eh.history_id,
    eh.equipment_id,
    e.name_of_equipment,
    e.serial_no,
    eh.worker_id,
    w.name AS worker_name,
    eh.action_type,
    eh.action_date,
    eh.action_by_head_id,
    dh.name AS head_name,
    eh.purpose,
    eh.expected_return_date,
    eh.actual_return_date,
    eh.re_issue_date,
    eh.notes
FROM Equipment_History eh
JOIN Electrical_Equipment e ON eh.equipment_id = e.equipment_id
JOIN Workers w ON eh.worker_id = w.worker_id
LEFT JOIN Division_Heads dh ON eh.action_by_head_id = dh.head_id
ORDER BY eh.action_date DESC;


-- View for all divisions equipment summary
CREATE OR REPLACE VIEW all_divisions_equipment_summary AS
SELECT 
    d.division_id,
    d.division_name,
    COUNT(e.equipment_id) as total_equipment,
    COUNT(CASE WHEN e.current_worker_id IS NULL THEN 1 END) as available_equipment,
    COUNT(CASE WHEN e.current_worker_id IS NOT NULL THEN 1 END) as assigned_equipment,
    ROUND((COUNT(CASE WHEN e.is_approved = 'Yes' THEN 1 END) / COUNT(*)) * 100, 2) as approval_rate,
    AVG(e.equipment_cost) as avg_equipment_cost,
    SUM(e.equipment_cost) as total_equipment_value
FROM Divisions d
LEFT JOIN Electrical_Equipment e ON d.division_id = e.division_id
GROUP BY d.division_id, d.division_name
ORDER BY total_equipment DESC;

-- View for high value equipment
CREATE OR REPLACE VIEW high_value_equipment_view AS
SELECT 
    e.*,
    d.division_name,
    w.name as assigned_worker_name,
    CASE 
        WHEN e.equipment_cost > 15000 THEN 'Very High'
        WHEN e.equipment_cost > 10000 THEN 'High' 
        WHEN e.equipment_cost > 5000 THEN 'Medium'
        ELSE 'Low'
    END as value_category
FROM Electrical_Equipment e
LEFT JOIN Divisions d ON e.division_id = d.division_id
LEFT JOIN Workers w ON e.current_worker_id = w.worker_id
WHERE e.equipment_cost > 8000
ORDER BY e.equipment_cost DESC;


-- Create Equipment_Logs table for comprehensive logging
CREATE TABLE IF NOT EXISTS Equipment_Logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT NOT NULL,
    worker_id INT NULL,
    action_type ENUM('requested', 'issued', 'returned', 'rejected', 'added', 'updated') NOT NULL,
    action_by_head_id INT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (equipment_id) REFERENCES Electrical_Equipment(equipment_id) ON DELETE CASCADE,
    FOREIGN KEY (worker_id) REFERENCES Workers(worker_id) ON DELETE SET NULL,
    FOREIGN KEY (action_by_head_id) REFERENCES Division_Heads(head_id) ON DELETE SET NULL,
    
    INDEX idx_equipment_logs_equipment (equipment_id),
    INDEX idx_equipment_logs_worker (worker_id),
    INDEX idx_equipment_logs_action (action_type),
    INDEX idx_equipment_logs_date (created_at)
);

-- Trigger to log equipment requests
DELIMITER //
CREATE TRIGGER after_equipment_request_insert
AFTER INSERT ON Equipment_History
FOR EACH ROW
BEGIN
    IF NEW.action_type = 'requested' THEN
        INSERT INTO Equipment_Logs (equipment_id, worker_id, action_type, action_by_head_id, notes)
        VALUES (NEW.equipment_id, NEW.worker_id, 'requested', NEW.action_by_head_id, 
                CONCAT('Equipment requested: ', COALESCE(NEW.purpose, 'No purpose specified')));
    END IF;
END//
DELIMITER ;

-- Trigger to log equipment approval/issuance
DELIMITER //
CREATE TRIGGER after_equipment_issue
AFTER UPDATE ON Electrical_Equipment
FOR EACH ROW
BEGIN
    -- Log when equipment is assigned to a worker
    IF OLD.current_worker_id IS NULL AND NEW.current_worker_id IS NOT NULL THEN
        INSERT INTO Equipment_Logs (equipment_id, worker_id, action_type, action_by_head_id, notes)
        VALUES (NEW.equipment_id, NEW.current_worker_id, 'issued', 
                (SELECT action_by_head_id FROM Equipment_History 
                 WHERE equipment_id = NEW.equipment_id AND action_type = 'issued' 
                 ORDER BY action_date DESC LIMIT 1),
                CONCAT('Equipment issued - Expected return: ', COALESCE(NEW.expected_return_date, 'Not specified')));
    END IF;
END//
DELIMITER ;

-- Trigger to log equipment returns
DELIMITER //
CREATE TRIGGER after_equipment_return
AFTER UPDATE ON Electrical_Equipment
FOR EACH ROW
BEGIN
    -- Log when equipment is returned (worker assignment removed)
    IF OLD.current_worker_id IS NOT NULL AND NEW.current_worker_id IS NULL THEN
        INSERT INTO Equipment_Logs (equipment_id, worker_id, action_type, action_by_head_id, notes)
        VALUES (NEW.equipment_id, OLD.current_worker_id, 'returned', 
                (SELECT action_by_head_id FROM Equipment_History 
                 WHERE equipment_id = NEW.equipment_id AND action_type = 'returned' 
                 ORDER BY action_date DESC LIMIT 1),
                'Equipment returned to inventory');
    END IF;
END//
DELIMITER ;

-- Trigger to log equipment rejection
DELIMITER //
CREATE TRIGGER after_equipment_rejection
AFTER UPDATE ON Equipment_History
FOR EACH ROW
BEGIN
    IF NEW.action_type = 'rejected' AND OLD.action_type = 'requested' THEN
        INSERT INTO Equipment_Logs (equipment_id, worker_id, action_type, action_by_head_id, notes)
        VALUES (NEW.equipment_id, NEW.worker_id, 'rejected', NEW.action_by_head_id, 
                CONCAT('Request rejected: ', COALESCE(NEW.notes, 'No reason specified')));
    END IF;
END//
DELIMITER ;

-- Create views for all divisions equipment summary
DROP VIEW IF EXISTS all_divisions_equipment_summary;
CREATE VIEW all_divisions_equipment_summary AS
SELECT 
    d.division_id,
    d.division_name,
    COUNT(e.equipment_id) as total_equipment,
    COUNT(CASE WHEN e.current_worker_id IS NULL THEN 1 END) as available_equipment,
    COUNT(CASE WHEN e.current_worker_id IS NOT NULL THEN 1 END) as assigned_equipment,
    COUNT(CASE WHEN e.is_approved = 'Yes' THEN 1 END) as approved_equipment,
    COUNT(CASE WHEN e.is_approved = 'No' THEN 1 END) as pending_approval_equipment,
    ROUND((COUNT(CASE WHEN e.is_approved = 'Yes' THEN 1 END) / COUNT(*)) * 100, 2) as approval_rate,
    AVG(e.equipment_cost) as avg_equipment_cost,
    SUM(e.equipment_cost) as total_equipment_value,
    COUNT(CASE WHEN e.calibration_date < CURDATE() THEN 1 END) as calibration_due_equipment
FROM Divisions d
LEFT JOIN Electrical_Equipment e ON d.division_id = e.division_id
GROUP BY d.division_id, d.division_name
ORDER BY total_equipment DESC;

-- View for all divisions available equipment
DROP VIEW IF EXISTS all_divisions_available_equipment;
CREATE VIEW all_divisions_available_equipment AS
SELECT 
    e.*,
    d.division_name,
    'Available' as status
FROM Electrical_Equipment e
JOIN Divisions d ON e.division_id = d.division_id
WHERE e.current_worker_id IS NULL AND e.is_approved = 'Yes'
ORDER BY d.division_name, e.name_of_equipment;

-- View for all divisions assigned equipment
DROP VIEW IF EXISTS all_divisions_assigned_equipment;
CREATE VIEW all_divisions_assigned_equipment AS
SELECT 
    e.*,
    d.division_name,
    w.name as worker_name,
    w.worker_type,
    w.email as worker_email,
    'Assigned' as status
FROM Electrical_Equipment e
JOIN Divisions d ON e.division_id = d.division_id
JOIN Workers w ON e.current_worker_id = w.worker_id
WHERE e.current_worker_id IS NOT NULL
ORDER BY d.division_name, e.name_of_equipment;

-- Enhanced equipment history view with more details
DROP VIEW IF EXISTS enhanced_equipment_history_view;
CREATE VIEW enhanced_equipment_history_view AS
SELECT 
    eh.history_id,
    eh.equipment_id,
    e.serial_no,
    e.name_of_equipment,
    e.model_no,
    eh.worker_id,
    w.name AS worker_name,
    w.worker_type,
    d.division_name,
    eh.action_type,
    eh.action_date,
    eh.action_by_head_id,
    dh.name AS head_name,
    eh.purpose,
    eh.expected_return_date,
    eh.actual_return_date,
    eh.re_issue_date,
    eh.notes,
    CASE 
        WHEN eh.action_type = 'requested' THEN 'primary'
        WHEN eh.action_type = 'issued' THEN 'success'
        WHEN eh.action_type = 'returned' THEN 'info'
        WHEN eh.action_type = 'rejected' THEN 'danger'
        ELSE 'secondary'
    END as badge_color
FROM Equipment_History eh
JOIN Electrical_Equipment e ON eh.equipment_id = e.equipment_id
JOIN Workers w ON eh.worker_id = w.worker_id
JOIN Divisions d ON w.division_id = d.division_id
LEFT JOIN Division_Heads dh ON eh.action_by_head_id = dh.head_id
ORDER BY eh.action_date DESC;

