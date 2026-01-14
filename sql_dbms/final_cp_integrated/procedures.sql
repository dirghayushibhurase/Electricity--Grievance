-- procedure to authenticate user
DELIMITER //

CREATE PROCEDURE AuthenticateUser(
    IN p_identifier VARCHAR(100),  -- Can be email or phone
    IN p_password VARCHAR(255)
)
BEGIN
    DECLARE user_count INT;
    DECLARE user_name VARCHAR(100);
    DECLARE user_type ENUM('user', 'worker', 'division_head');
    DECLARE user_id_val INT;
    
    -- Check in Users table (by email or phone)
    SELECT COUNT(*), name, user_id INTO user_count, user_name, user_id_val
    FROM Users 
    WHERE (email = p_identifier OR phone = p_identifier) 
    AND password = p_password;
    
    IF user_count > 0 THEN
        SET user_type = 'user';
    ELSE
        -- Check in Workers table (by email or phone)
        SELECT COUNT(*), name, worker_id INTO user_count, user_name, user_id_val
        FROM Workers 
        WHERE (email = p_identifier OR phone_no = p_identifier) 
        AND password = p_password AND is_active = TRUE;
        
        IF user_count > 0 THEN
            SET user_type = 'worker';
        ELSE
            -- Check in Division_Heads table (by email or phone)
            SELECT COUNT(*), name, head_id INTO user_count, user_name, user_id_val
            FROM Division_Heads 
            WHERE (email = p_identifier OR phone = p_identifier) 
            AND password = p_password AND is_active = TRUE;
            
            IF user_count > 0 THEN
                SET user_type = 'division_head';
            ELSE
                SET user_count = 0;
                SET user_name = NULL;
                SET user_type = NULL;
                SET user_id_val = NULL;
            END IF;
        END IF;
    END IF;
    
    -- Return results
    SELECT user_count as authenticated, user_name, user_type, user_id_val as user_id;
END //

DELIMITER ;


-- welcome notification procedure

DELIMITER //

CREATE PROCEDURE LogUserLogin(
    IN p_user_id INT,
    IN p_user_type VARCHAR(20),
    IN p_user_name VARCHAR(100)
)
BEGIN
    -- This procedure can be extended to log login activities
    -- For now, it just prepares the welcome message
    SELECT CONCAT('Welcome to EGS, ', p_user_name, '!') as welcome_message;
END //

DELIMITER ;


-- Create a test table to verify procedure execution
CREATE TABLE IF NOT EXISTS Issue_Procedure_Log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    issue_id INT,
    procedure_name VARCHAR(100),
    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parameters_used TEXT,
    status VARCHAR(50),
    FOREIGN KEY (issue_id) REFERENCES Issues(issue_id) ON DELETE SET NULL
);

-- Stored procedure for raising issues
DELIMITER //

CREATE PROCEDURE RaiseNewIssue(
    IN p_user_id INT,
    IN p_division_id INT,
    IN p_address_line1 VARCHAR(255),
    IN p_address_line2 VARCHAR(255),
    IN p_latitude DECIMAL(10, 8),
    IN p_longitude DECIMAL(11, 8),
    IN p_issue_type VARCHAR(100),
    IN p_title VARCHAR(255),
    IN p_description TEXT,
    IN p_priority VARCHAR(20)
)
BEGIN
    DECLARE new_issue_id INT;

    -- Insert the new issue
    INSERT INTO Issues (
        user_id, division_id, address_line1, address_line2, 
        latitude, longitude, issue_type, title, description, priority, status
    ) VALUES (
        p_user_id, p_division_id, p_address_line1, p_address_line2,
        p_latitude, p_longitude, p_issue_type, p_title, p_description, p_priority, 'pending'
    );

    -- Get the new issue ID
    SET new_issue_id = LAST_INSERT_ID();

    -- Log successful procedure execution
    INSERT INTO Issue_Procedure_Log (issue_id, procedure_name, parameters_used, status)
    VALUES (new_issue_id, 'RaiseNewIssue', 
            CONCAT('user_id:', p_user_id, ', division_id:', p_division_id, ', title:', LEFT(p_title, 50)),
            'SUCCESS');

    -- Return the new issue ID
    SELECT new_issue_id as issue_id;
END//

DELIMITER ;

select *from issues;

