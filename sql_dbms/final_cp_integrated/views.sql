-- Home page views--

-- View 1: System Statistics Summary
CREATE VIEW System_Stats_View AS
SELECT 
    (SELECT COUNT(*) FROM Workers WHERE is_active = TRUE AND current_task_status = 'Active') as total_workers,
    (SELECT COUNT(*) FROM Issues WHERE status = 'resolved') as resolved_issues,
    (SELECT COUNT(*) FROM Users) as total_users,
    (SELECT COUNT(*) FROM Issues WHERE status = 'pending') as active_issues,
    (SELECT COUNT(*) FROM Issues WHERE status = 'resolved' AND DATE(resolved_at) = CURDATE()) as resolved_today,
    (SELECT COUNT(*) FROM Workers WHERE availability = 'Available' AND is_active = TRUE) as available_workers,
    (SELECT ROUND((
        SELECT COUNT(*) FROM Issues WHERE status = 'resolved'
    ) * 100.0 / NULLIF((
        SELECT COUNT(*) FROM Issues WHERE status IN ('pending', 'resolved')
    ), 0), 2)) as satisfaction_rate;
    
-- View 2: Live Service Status by Division
CREATE VIEW Live_Service_Status_View AS
SELECT 
    d.division_id,
    d.division_name,
    COUNT(DISTINCT w.worker_id) as total_workers,
    COUNT(DISTINCT CASE WHEN w.availability = 'Available' THEN w.worker_id END) as available_workers,
    COUNT(DISTINCT i.issue_id) as total_issues,
    COUNT(DISTINCT CASE WHEN i.status = 'pending' THEN i.issue_id END) as pending_issues,
    COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) as resolved_issues
FROM Divisions d
LEFT JOIN Workers w ON d.division_id = w.division_id AND w.is_active = TRUE
LEFT JOIN Issues i ON d.division_id = i.division_id
GROUP BY d.division_id, d.division_name;

-- View 3: Recent Activity Feed
CREATE VIEW Recent_Activity_View AS
SELECT 
    'issue_raised' as activity_type,
    i.issue_id,
    i.title,
    u.name as user_name,
    i.created_at as timestamp,
    NULL as worker_name
FROM Issues i
JOIN Users u ON i.user_id = u.user_id
WHERE i.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)

UNION ALL

SELECT 
    'issue_resolved' as activity_type,
    i.issue_id,
    i.title,
    u.name as user_name,
    i.resolved_at as timestamp,
    w.name as worker_name
FROM Issues i
JOIN Users u ON i.user_id = u.user_id
LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id
LEFT JOIN Workers w ON iw.worker_id = w.worker_id
WHERE i.status = 'resolved' 
AND i.resolved_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY timestamp DESC
LIMIT 20;

-- HOME PAGE FOR USERS ADDITIONAL VIEWS--
-- View 4: Issue Type Distribution       ****
CREATE VIEW Issue_Type_Distribution_View AS
SELECT 
    issue_type,
    COUNT(*) as issue_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Issues), 2) as percentage
FROM Issues
GROUP BY issue_type
ORDER BY issue_count DESC;

-- ISSUES VIEWS
-- View 5: Top 3 Division Summaries ***********
CREATE VIEW Top_Divisions_Summary_View AS
SELECT 
    d.division_name,
    COUNT(i.issue_id) as total_issues,
    COUNT(CASE WHEN i.status = 'resolved' THEN i.issue_id END) as resolved_issues,
    COUNT(CASE WHEN i.status = 'pending' THEN i.issue_id END) as active_issues,
    ROUND(COUNT(CASE WHEN i.status = 'resolved' THEN i.issue_id END) * 100.0 / 
          NULLIF(COUNT(i.issue_id), 0), 2) as resolution_rate
FROM Divisions d
LEFT JOIN Issues i ON d.division_id = i.division_id
GROUP BY d.division_id, d.division_name
ORDER BY resolution_rate DESC, total_issues DESC
LIMIT 3;
select *from User_Issues_Summary_View;
-- View 6: User Issues Summary (for logged-in users)
CREATE VIEW User_Issues_Summary_View AS
SELECT 
    i.issue_id,
    i.title,
    i.issue_type,
    i.description,
    i.status,
    i.priority,
    i.created_at,
    i.resolved_at,
    d.division_name,
    COUNT(iw.worker_id) as assigned_workers
FROM Issues i
JOIN Divisions d ON i.division_id = d.division_id
LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id
GROUP BY i.issue_id, i.title, i.issue_type, i.description, i.status, i.priority, i.created_at, i.resolved_at, d.division_name;


-- Create a view for user issues summary (if not exists)
CREATE OR REPLACE VIEW User_Issues_Summary_VIEW AS
SELECT 
    i.issue_id,
    i.user_id,
    i.title,
    i.issue_type,
    i.description,
    i.status,
    i.priority,
    i.created_at,
    i.resolved_at,
    d.division_name,
    d.division_id,
    COUNT(iw.worker_id) as assigned_workers_count,
    GROUP_CONCAT(DISTINCT w.name SEPARATOR ', ') as assigned_worker_names
FROM Issues i
JOIN Divisions d ON i.division_id = d.division_id
LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id AND iw.worker_status != 'completed'
LEFT JOIN Workers w ON iw.worker_id = w.worker_id
GROUP BY i.issue_id, i.user_id, i.title, i.issue_type, i.description, i.status, i.priority, i.created_at, i.resolved_at, d.division_name, d.division_id;