INSERT INTO Divisions (division_name) VALUES
('Rasthapeth Division'),
('Shivajinagar Division'),
('Kothrud Division'),
('Hadapsar Division'),
('Pimpri Division'),
('Chinchwad Division'),
('Bhosari Division'),
('Baramati Division'),
('Indapur Division'),
('Daund Division'),
('Shirur Division'),
('Junnar Division'),
('Rajgurunagar Division'),
('Mulshi Division');
select *from Divisions;

INSERT INTO Division_Heads (division_id, name, email, phone, password) VALUES
(1, 'Ramesh Patil', 'ramesh.rasthapeth@egs.com', '9123456701', 'Ramesh@123'),
(2, 'Sunita Deshmukh', 'sunita.shivajinagar@egs.com', '9123456702', 'Sunita@456'),
(3, 'Vikram Joshi', 'vikram.kothrud@egs.com', '9123456703', 'Vikram@789'),
(4, 'Anjali Kulkarni', 'anjali.hadapsar@egs.com', '9123456704', 'Anjali@101'),
(5, 'Rajesh More', 'rajesh.pimpri@egs.com', '9123456705', 'Rajesh@202'),
(6, 'Priya Pawar', 'priya.chinchwad@egs.com', '9123456706', 'Priya@303'),
(7, 'Sandeep Gaikwad', 'sandeep.bhosari@egs.com', '9123456707', 'Sandeep@404'),
(8, 'Meera Sathe', 'meera.baramati@egs.com', '9123456708', 'Meera@505'),
(9, 'Arun Jadhav', 'arun.indapur@egs.com', '9123456709', 'Arun@606'),
(10, 'Neha Sharma', 'neha.daund@egs.com', '9123456710', 'Neha@707'),
(11, 'Prakash Reddy', 'prakash.shirur@egs.com', '9123456711', 'Prakash@808'),
(12, 'Kavita Nair', 'kavita.junnar@egs.com', '9123456712', 'Kavita@909'),
(13, 'Dinesh Kumar', 'dinesh.rajgurunagar@egs.com', '9123456713', 'Dinesh@110'),
(14, 'Lata Mishra', 'lata.mulshi@egs.com', '9123456714', 'Lata@121');

select *from Division_Heads;
select *from users;
INSERT INTO Users (name, phone, email, password, address_line1, address_line2, city, pincode, division_id) VALUES
('Aarav Sharma', '9876500001', 'aarav.sharma@email.com', 'Aarav@123', '123 Main Road', 'Near Temple', 'Pune', '411001', 1),
('Priya Patel', '9876500002', 'priya.patel@email.com', 'Priya@456', '456 Shivaji Road', 'First Floor', 'Pune', '411002', 2),
('Rohan Deshmukh', '9876500003', 'rohan.deshmukh@email.com', 'Rohan@789', '789 MG Road', 'Apartment 3B', 'Pune', '411003', 3),
('Ananya Joshi', '9876500004', 'ananya.joshi@email.com', 'Ananya@101', '321 Kothrud Road', 'Building A', 'Pune', '411038', 3),
('Vikram Singh', '9876500005', 'vikram.singh@email.com', 'Vikram@202', '654 Hadapsar Road', 'Near Market', 'Pune', '411028', 4),
('Sneha Kulkarni', '9876500006', 'sneha.kulkarni@email.com', 'Sneha@303', '987 Pimpri Road', 'Staff Quarters', 'Pune', '411017', 5),
('Raj More', '9876500007', 'raj.more@email.com', 'Raj@404', '159 Chinchwad Road', 'Phase 2', 'Pune', '411033', 6),
('Pooja Gaikwad', '9876500008', 'pooja.gaikwad@email.com', 'Pooja@505', '753 Bhosari Road', 'Industrial Area', 'Pune', '411039', 7),
('Amit Sathe', '9876500009', 'amit.sathe@email.com', 'Amit@606', '246 Baramati Road', 'Near Bus Stand', 'Baramati', '413102', 8),
('Neha Jadhav', '9876500010', 'neha.jadhav@email.com', 'Neha@707', '852 Indapur Road', 'Village Area', 'Indapur', '413132', 9);
select *from Users;

INSERT INTO Workers (name, password, age, phone_no, address, availability, worker_type, skill_sets, current_task_status, division_id, email, created_by) VALUES
('Amit Deshmukh', 'Amit@123', 28, '9876500101', 'Shivaji Nagar, Pune', 'Available', 'Technician', 'Transformer Repair, Wiring', 'Active', 1, 'amit.tech@egs.com', 1),
('Neha Joshi', 'Neha@456', 32, '9876500102', 'Hinjewadi Phase 1, Pune', 'On Task', 'Inspector', 'Safety Audit, Voltage Monitoring', 'Active', 2, 'neha.insp@egs.com', 2),
('Sanjay Patil', 'Sanjay@789', 35, '9876500103', 'Hadapsar, Pune', 'Available', 'Supervisor', 'Team Management, Billing Ops', 'Active', 3, 'sanjay.sup@egs.com', 3),
('Sneha Kulkarni', 'Sneha@101', 29, '9876500104', 'Nigdi Chowk, Pune', 'Sick Leave', 'Technician', 'Street Light Repair, Cabling', 'Inactive', 4, 'sneha.tech@egs.com', 4),
('Rajesh Shinde', 'Rajesh@202', 31, '9876500105', 'Bhosari, Pune', 'Available', 'Technician', 'Power Restoration, Load Balancing', 'Active', 5, 'rajesh.tech@egs.com', 5),
('Anil Pawar', 'Anil@303', 34, '9876500106', 'Katraj, Pune', 'Available', 'Inspector', 'Transformer Audit, Wiring Checks', 'Active', 6, 'anil.insp@egs.com', 6),
('Deepak Jadhav', 'Deepak@404', 40, '9876500107', 'Pimpri, Pune', 'On Holiday', 'Supervisor', 'Emergency Ops, Coordination', 'Inactive', 7, 'deepak.sup@egs.com', 7),
('Ashwini Rane', 'Ashwini@505', 27, '9876500108', 'Baner Road, Pune', 'Available', 'Technician', 'Appliance Safety, Load Fixes', 'Active', 8, 'ashwini.tech@egs.com', 8),
('Mahesh Kadam', 'Mahesh@606', 33, '9876500109', 'Warje, Pune', 'Available', 'Inspector', 'Voltage Surge Checks, Metering', 'Active', 9, 'mahesh.insp@egs.com', 9),
('Meena Sawant', 'Meena@707', 30, '9876500110', 'Viman Nagar, Pune', 'On Task', 'Technician', 'Smart Meter Installation', 'Active', 10, 'meena.tech@egs.com', 10),
('Prashant Kamble', 'Prashant@808', 38, '9876500111', 'Koregaon Park, Pune', 'Available', 'Supervisor', 'Billing Disputes, Customer Handling', 'Active', 11, 'prashant.sup@egs.com', 11),
('Manoj Gaikwad', 'Manoj@909', 26, '9876500112', 'Sinhagad Road, Pune', 'Other', 'Technician', 'Wiring, Appliance Repair', 'Inactive', 12, 'manoj.tech@egs.com', 12),
('Vikas More', 'Vikas@110', 36, '9876500113', 'Hadapsar Industrial Area, Pune', 'Available', 'Inspector', 'Power Audit, Load Checks', 'Active', 13, 'vikas.insp@egs.com', 13),
('Kiran Salunkhe', 'Kiran@121', 42, '9876500114', 'Chakan, Pune', 'Available', 'Supervisor', 'High Voltage Ops, Team Handling', 'Active', 14, 'kiran.sup@egs.com', 14),
('Rohit Kulkarni', 'Rohit@131', 29, '9876500115', 'Deccan Gymkhana, Pune', 'Available', 'Inspector', 'Inspection, Safety Audit', 'Active', 1, 'rohit.insp@egs.com', 1),
('Ashok Gokhale', 'Ashok@141', 31, '9876500116', 'Hinjewadi Phase 3, Pune', 'Available', 'Technician', 'Transformer Repair, Cabling', 'Active', 2, 'ashok.tech@egs.com', 2),
('Savita Jadhav', 'Savita@151', 28, '9876500117', 'Hadapsar Gaon, Pune', 'On Task', 'Technician', 'Smart Meter, Billing', 'Active', 3, 'savita.tech@egs.com', 3),
('Nitin More', 'Nitin@161', 37, '9876500118', 'Wakad, Pune', 'Available', 'Supervisor', 'Load Distribution, Team Mgmt', 'Active', 4, 'nitin.sup@egs.com', 4),
('Priya Shinde', 'Priya@171', 32, '9876500119', 'Bhosari MIDC, Pune', 'Sick Leave', 'Inspector', 'Voltage Check, Safety Audit', 'Inactive', 5, 'priya.insp@egs.com', 5),
('Ganesh Pawar', 'Ganesh@181', 30, '9876500120', 'Bibvewadi, Pune', 'Available', 'Technician', 'Transformer Repair, Power Supply', 'Active', 6, 'ganesh.tech@egs.com', 6);
select *from workers;
desc users;
select *from Division_Heads;
select * from users;
select * from issues;

INSERT INTO Issues (user_id, division_id, address_line1, address_line2, latitude, longitude, issue_type, title, description, image_url, status, priority, created_at, resolved_at) VALUES
(1, 1, 'MG Road', 'Near Commercial Complex', 18.520300, 73.855800, 'power_outage', 'Short Circuit Reported', 'Short circuit reported near MG Road commercial complex.', 'short_circuit.jpg', 'pending', 'high', '2025-09-06 10:30:00', NULL),
(2, 2, 'Kalyani Nagar', 'Building A', 18.523000, 73.876000, 'meter_problem', 'Smart Meter Delay', 'Delay in smart meter reading updates.', 'meter_delay.png', 'pending', 'medium', '2025-09-06 12:45:00', NULL),
(3, 4, 'Nigdi Pradhikaran', 'Sector 5', 18.650500, 73.770300, 'power_outage', 'Frequent Evening Outages', 'Daily power outages in evening hours in Nigdi.', 'frequent_outage.jpg', 'pending', 'high', '2025-09-07 19:20:00', NULL),
(4, 3, 'Kharadi', 'IT Park Road', 18.530500, 73.870500, 'billing_dispute', 'September Bill Missing', 'Bill for September not generated in portal.', 'bill_missing.jpg', 'pending', 'medium', '2025-09-07 08:00:00', NULL),
(5, 3, 'Hadapsar Industrial Area', 'Near Factory Gate', 18.540600, 73.880400, 'transformer_issue', 'Transformer Noise Complaint', 'Transformer making loud buzzing noise.', 'transformer_noise.jpg', 'pending', 'critical', '2025-09-07 15:00:00', NULL),
(6, 2, 'Warje Malwadi', 'Housing Society', 18.490400, 73.810600, 'voltage_fluctuation', 'Over Voltage Incidents', 'Over voltage incidents noticed in Warje.', 'over_voltage.jpg', 'pending', 'high', '2025-09-06 21:00:00', NULL),
(7, 2, 'Magarpatta City', 'Building C', 18.550700, 73.870900, 'meter_problem', 'Damaged Meter', 'Meter physically damaged due to rains.', 'broken_meter.jpg', 'pending', 'medium', '2025-09-08 09:30:00', NULL),
(8, 1, 'Karve Nagar', 'Near School', 18.510600, 73.820700, 'wire_fault', 'Underground Cable Fault', 'Underground cable fault affecting supply.', 'underground_cable.jpg', 'pending', 'high', '2025-09-08 18:30:00', NULL),
(9, 1, 'Bibwewadi', 'Apartment 302', 18.520800, 73.830800, 'billing_dispute', 'Wrong Tenant Billed', 'Wrong tenant billed despite complaint.', 'tenant_bill.png', 'pending', 'medium', '2025-09-09 08:20:00', NULL),
(10, 2, 'Nagar Road', 'Street Light Pole 45', 18.560900, 73.890200, 'street_light_fault', 'Dim Street Lights', 'Street lights dim and flickering near Nagar Road.', 'street_dim.jpg', 'pending', 'low', '2025-09-09 20:30:00', NULL);

select *from issues;
select *from users;
update issues set status="resolved" where issue_id=1;
UPDATE Issues
SET status = 'resolved'
WHERE issue_id = 5;

INSERT INTO IssueWorkers (issue_id, worker_id, assigned_by, worker_status, assigned_at) VALUES
(1, 1, 1, 'assigned', '2025-01-15 09:00:00'),  -- Amit Deshmukh assigned to Short Circuit issue
(2, 2, 2, 'in_progress', '2025-01-15 10:30:00'), -- Neha Joshi working on Smart Meter Delay
(3, 5, 4, 'completed', '2025-01-14 14:00:00'),   -- Rajesh Shinde completed Frequent Outages
(4, 6, 3, 'assigned', '2025-01-15 11:15:00'),    -- Anil Pawar assigned to Bill Missing
(5, 8, 3, 'in_progress', '2025-01-15 08:45:00'); -- Ashwini Rane working on Transformer Noise


INSERT INTO Electrical_Equipment (serial_no, name_of_equipment, model_no, purchase_date, equipment_cost, calibration_date, is_approved, division_id, current_worker_id, issue_date, expected_return_date, re_issue_date, remarks) VALUES
('EQ-1001', 'Multimeter', 'MT-2024X', '2024-01-10', 4500.00, '2024-07-01', 'Yes', 1, 1, '2024-08-12', '2024-08-26', '2024-09-01', 'Issued for Voltage Testing'),
('EQ-1002', 'Transformer Analyzer', 'TA-550', '2024-03-15', 12500.00, '2024-08-01', 'Yes', 2, 2, '2024-08-15', '2024-08-29', NULL, 'Used for transformer maintenance'),
('EQ-1003', 'Cable Fault Locator', 'CFL-880', '2024-02-12', 9800.00, '2024-06-15', 'No', 3, 3, '2024-09-01', '2024-09-08', '2024-09-15', 'Awaiting re-approval'),
('EQ-1004', 'Insulation Tester', 'IT-400', '2024-04-10', 5500.00, '2024-08-10', 'Yes', 4, 4, '2024-09-05', '2024-09-12', NULL, 'Issued to Hadapsar division'),
('EQ-1005', 'Power Quality Analyzer', 'PQA-880', '2024-05-05', 14500.00, '2024-07-20', 'Yes', 5, 5, '2024-08-10', '2024-08-20', '2024-08-25', 'Approved and functional'),
('EQ-1006', 'Current Clamp Meter', 'CCM-303', '2024-03-22', 3500.00, '2024-05-22', 'No', 6, NULL, NULL, NULL, NULL, 'Stored in central office'),
('EQ-1007', 'Earth Resistance Tester', 'ERT-550', '2024-02-28', 7000.00, '2024-07-10', 'Yes', 7, 7, '2024-08-14', '2024-08-28', NULL, 'Issued to Bhosari team'),
('EQ-1008', 'Energy Meter Test Kit', 'EMT-700', '2024-01-05', 8800.00, '2024-08-02', 'No', 8, NULL, NULL, NULL, NULL, 'Calibration required'),
('EQ-1009', 'Thermal Imaging Camera', 'TIC-900', '2024-03-19', 16500.00, '2024-09-01', 'Yes', 9, 9, '2024-08-30', '2024-09-13', '2024-09-18', 'For fault detection'),
('EQ-1010', 'Line Tester', 'LT-101', '2024-04-25', 2500.00, '2024-07-12', 'No', 10, 10, '2024-09-02', '2024-09-09', NULL, 'Newly issued to technician');
show tables;
select *from workers;
select *from issueworkers;
select *from equipment_history;
select *from attendance; --  error******************************888
select *from issues;
INSERT INTO Equipment_History (equipment_id, worker_id, action_type, action_by_head_id, purpose, expected_return_date, re_issue_date, notes) VALUES
(1, 1, 'requested', 1, 'Need multimeter for voltage testing in Rasthapeth area', '2024-08-26', '2024-09-01', 'Worker requested equipment for field work'),
(1, 1, 'issued', 1, 'Voltage fluctuation testing assignment', '2024-08-26', '2024-09-01', 'Approved for voltage testing project'),

(2, 2, 'requested', 2, 'Transformer maintenance in Shivajinagar division', '2024-08-29', NULL, 'Required for scheduled transformer inspection'),
(2, 2, 'issued', 2, 'Transformer analysis and maintenance', '2024-08-29', NULL, 'Issued for critical transformer work'),

(3, 3, 'requested', 3, 'Cable fault detection in Kothrud underground lines', '2024-09-08', '2024-09-15', 'Multiple cable fault reports received'),
(3, 3, 'issued', 3, 'Underground cable fault location', '2024-09-08', '2024-09-15', 'Approved with re-issue constraint'),

(5, 5, 'requested', 5, 'Power quality analysis in Pimpri industrial area', '2024-08-20', '2024-08-25', 'Industrial clients reporting power quality issues'),
(5, 5, 'issued', 5, 'Industrial power quality assessment', '2024-08-20', '2024-08-25', 'Approved for industrial zone inspection'),

(6, 6, 'requested', 6, 'Current measurement for load balancing', NULL, NULL, 'Need clamp meter for load analysis'),
(6, 6, 'rejected', 6, 'Equipment requires calibration', NULL, NULL, 'Rejected - equipment needs recalibration'),

(9, 9, 'requested', 9, 'Thermal scanning for fault detection in Indapur', '2024-09-13', '2024-09-18', 'Suspected hot spots in distribution lines'),
(9, 9, 'issued', 9, 'Thermal imaging for preventive maintenance', '2024-09-13', '2024-09-18', 'Approved for preventive maintenance work');

select *from equipment_history;

-- Add more available equipment (not assigned to any worker)
INSERT INTO Electrical_Equipment (serial_no, name_of_equipment, model_no, purchase_date, equipment_cost, calibration_date, is_approved, division_id, current_worker_id, issue_date, expected_return_date, re_issue_date, remarks) VALUES
-- Available Equipment (current_worker_id IS NULL)
('EQ-1011', 'Digital Multimeter', 'DM-5000', '2024-06-10', 5200.00, '2024-12-10', 'Yes', 1, NULL, NULL, NULL, NULL, 'High precision multimeter'),
('EQ-1012', 'Voltage Tester', 'VT-300', '2024-05-15', 2800.00, '2024-11-15', 'Yes', 1, NULL, NULL, NULL, NULL, 'Basic voltage detection'),
('EQ-1013', 'Clamp Meter', 'CM-450', '2024-04-20', 6800.00, '2024-10-20', 'Yes', 2, NULL, NULL, NULL, NULL, 'AC/DC current measurement'),
('EQ-1014', 'Insulation Tester', 'IT-550', '2024-03-25', 7500.00, '2024-09-25', 'Yes', 2, NULL, NULL, NULL, NULL, 'Megohmmeter for insulation testing'),
('EQ-1015', 'Power Quality Analyzer', 'PQA-1000', '2024-07-05', 18500.00, '2025-01-05', 'Yes', 3, NULL, NULL, NULL, NULL, 'Advanced power analysis'),
('EQ-1016', 'Thermal Imaging Camera', 'TIC-850', '2024-02-18', 14500.00, '2024-08-18', 'Yes', 3, NULL, NULL, NULL, NULL, 'Medium range thermal camera'),
('EQ-1017', 'Cable Fault Locator', 'CFL-750', '2024-01-30', 8200.00, '2024-07-30', 'No', 4, NULL, NULL, NULL, NULL, 'Needs calibration'),
('EQ-1018', 'Earth Ground Tester', 'EGT-400', '2024-06-22', 6200.00, '2024-12-22', 'Yes', 4, NULL, NULL, NULL, NULL, 'Ground resistance testing'),
('EQ-1019', 'Phase Sequence Tester', 'PST-200', '2024-05-08', 3200.00, '2024-11-08', 'Yes', 5, NULL, NULL, NULL, NULL, 'Phase rotation detection'),
('EQ-1020', 'Digital Hygrometer', 'DH-150', '2024-04-12', 1800.00, '2024-10-12', 'Yes', 5, NULL, NULL, NULL, NULL, 'Humidity and temperature'),
('EQ-1021', 'Lux Meter', 'LM-300', '2024-03-15', 4200.00, '2024-09-15', 'Yes', 6, NULL, NULL, NULL, NULL, 'Light intensity measurement'),
('EQ-1022', 'Sound Level Meter', 'SLM-250', '2024-02-28', 5800.00, '2024-08-28', 'Yes', 6, NULL, NULL, NULL, NULL, 'Noise level monitoring'),
('EQ-1023', 'Vibration Analyzer', 'VA-600', '2024-07-18', 12500.00, '2025-01-18', 'No', 7, NULL, NULL, NULL, NULL, 'Awaiting parts'),
('EQ-1024', 'Gas Detector', 'GD-350', '2024-06-05', 8900.00, '2024-12-05', 'Yes', 7, NULL, NULL, NULL, NULL, 'Multi-gas detection'),
('EQ-1025', 'Network Analyzer', 'NA-880', '2024-05-20', 22500.00, '2024-11-20', 'Yes', 8, NULL, NULL, NULL, NULL, 'Network troubleshooting');


