from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
import os
import re  
import csv
import io
from flask import Response
app = Flask(__name__)
app.secret_key = 'msedcl_secret_key_2024'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'dirgha@123',
    'database': 'EGS'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

# ========== AUTHENTICATION ROUTES ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['email']  # Can be email or phone
        password = request.form['password']
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent')
        
        conn = get_db_connection()
        if not conn:
            return render_template('login.html', error='Database connection failed')

        cursor = conn.cursor(dictionary=True)
        try:
            user = None
            division_id = None
            
            # Check in Users table
            cursor.execute("""
                SELECT user_id, name, 'user' as user_type, division_id
                FROM Users 
                WHERE (email = %s OR phone = %s) AND password = %s
            """, (identifier, identifier, password))
            user = cursor.fetchone()
            
            if not user:
                # Check in Workers table
                cursor.execute("""
                    SELECT worker_id as user_id, name, 'worker' as user_type, division_id
                    FROM Workers 
                    WHERE (email = %s OR phone_no = %s) AND password = %s AND is_active = TRUE
                """, (identifier, identifier, password))
                user = cursor.fetchone()
            
            if not user:
                # Check in Division_Heads table
                cursor.execute("""
                    SELECT head_id as user_id, name, 'division_head' as user_type, division_id
                    FROM Division_Heads 
                    WHERE (email = %s OR phone = %s) AND password = %s AND is_active = TRUE
                """, (identifier, identifier, password))
                user = cursor.fetchone()

            if user:
                # Login successful - redirect based on user type
                session['user_id'] = user['user_id']
                session['user_name'] = user['name']
                session['user_type'] = user['user_type']
                session['logged_in'] = True
                
                # Store division_id for division heads and workers
                if user['user_type'] in ['division_head', 'worker']:
                    session['division_id'] = user['division_id']
                    # Get division name for division heads
                    if user['user_type'] == 'division_head':
                        cursor.execute("SELECT division_name FROM Divisions WHERE division_id = %s", (user['division_id'],))
                        division = cursor.fetchone()
                        session['division_name'] = division['division_name'] if division else 'Division'
                
                flash(f'Welcome back, {user["name"]}!', 'success')
                
                # Redirect based on user type
                if user['user_type'] == 'user':
                    return redirect(url_for('dashboard'))
                elif user['user_type'] == 'worker':
                    return redirect(url_for('worker_dashboard'))
                elif user['user_type'] == 'division_head':
                    return redirect(url_for('division_dashboard'))
                
            else:
                # Failed login - log the attempt
                try:
                    # Check if the identifier belongs to any division-related user
                    division_id = None
                    
                    # Check Division Heads
                    cursor.execute("SELECT division_id FROM Division_Heads WHERE email = %s OR phone = %s", (identifier, identifier))
                    division_head = cursor.fetchone()
                    if division_head:
                        division_id = division_head['division_id']
                    else:
                        # Check Workers
                        cursor.execute("SELECT division_id FROM Workers WHERE email = %s OR phone_no = %s", (identifier, identifier))
                        worker = cursor.fetchone()
                        if worker:
                            division_id = worker['division_id']
                        else:
                            # Check Users
                            cursor.execute("SELECT division_id FROM Users WHERE email = %s OR phone = %s", (identifier, identifier))
                            regular_user = cursor.fetchone()
                            if regular_user:
                                division_id = regular_user['division_id']
                    
                    # Log the failed attempt
                    cursor.execute("""
                        INSERT INTO Failed_Login_Attempts (email, ip_address, user_agent, division_id)
                        VALUES (%s, %s, %s, %s)
                    """, (identifier, ip_address, user_agent, division_id))
                    conn.commit()
                    
                except Exception as log_error:
                    print(f"Failed to log login attempt: {log_error}")
                    # Continue even if logging fails
                
                return render_template('login.html', error='Invalid email/phone or password')
                
        except Exception as e:
            print(f"Login error: {e}")
            return render_template('login.html', error='Login failed. Please try again.')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        address_line1 = request.form['address_line1']
        address_line2 = request.form.get('address_line2', '')
        city = request.form['city']
        pincode = request.form['pincode']
        division_id = request.form.get('division_id')
        
        if division_id == '':
            division_id = None
        
        # Server-side validation
        import re
        
        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            # Get divisions again for the template
            conn = get_db_connection()
            divisions = []
            if conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT division_id, division_name FROM Divisions")
                    divisions = cursor.fetchall()
                except Exception as e:
                    print(f"Could not fetch divisions: {e}")
                finally:
                    cursor.close()
                    conn.close()
            return render_template('signup.html', error='Please enter a valid email address', divisions=divisions)
        
        # Phone validation
        if not re.match(r'^[0-9]{10}$', phone):
            # Get divisions again for the template
            conn = get_db_connection()
            divisions = []
            if conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT division_id, division_name FROM Divisions")
                    divisions = cursor.fetchall()
                except Exception as e:
                    print(f"Could not fetch divisions: {e}")
                finally:
                    cursor.close()
                    conn.close()
            return render_template('signup.html', error='Phone number must be exactly 10 digits', divisions=divisions)
        
        # Password length validation
        if len(password) < 6:
            # Get divisions again for the template
            conn = get_db_connection()
            divisions = []
            if conn:
                cursor = conn.cursor(dictionary=True)
                try:
                    cursor.execute("SELECT division_id, division_name FROM Divisions")
                    divisions = cursor.fetchall()
                except Exception as e:
                    print(f"Could not fetch divisions: {e}")
                finally:
                    cursor.close()
                    conn.close()
            return render_template('signup.html', error='Password must be at least 6 characters long', divisions=divisions)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Check if email already exists
                cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return render_template('signup.html', error='An account with this email already exists', divisions=divisions)

                # Check if phone already exists
                cursor.execute("SELECT user_id FROM Users WHERE phone = %s", (phone,))
                if cursor.fetchone():
                    return render_template('signup.html', error='An account with this phone number already exists', divisions=divisions)

                # Set session variables for IP and User Agent for the trigger
                cursor.execute("SET @signup_ip = %s", (request.remote_addr,))
                cursor.execute("SET @signup_agent = %s", (request.headers.get('User-Agent'),))

                # Insert new user
                insert_cursor = conn.cursor()
                insert_cursor.execute("""
                    INSERT INTO Users (name, phone, email, password, address_line1, address_line2, city, pincode, division_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, phone, email, password, address_line1, address_line2, city, pincode, division_id))
                
                user_id = insert_cursor.lastrowid
                conn.commit()
                insert_cursor.close()
                
                # Log the successful signup (trigger will handle the actual logging)
                print(f"New user registered: {name} (ID: {user_id}) from IP: {request.remote_addr}")
                
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
                
            except mysql.connector.Error as e:
                # Get divisions again for the template in case of error
                conn_fallback = get_db_connection()
                divisions_fallback = []
                if conn_fallback:
                    cursor_fallback = conn_fallback.cursor(dictionary=True)
                    try:
                        cursor_fallback.execute("SELECT division_id, division_name FROM Divisions")
                        divisions_fallback = cursor_fallback.fetchall()
                    except Exception as ex:
                        print(f"Could not fetch divisions: {ex}")
                    finally:
                        cursor_fallback.close()
                        conn_fallback.close()
                return render_template('signup.html', error=f'Registration failed: {e}', divisions=divisions_fallback)
            finally:
                cursor.close()
                conn.close()
        else:
            # Get divisions again for the template in case of connection error
            conn_fallback = get_db_connection()
            divisions_fallback = []
            if conn_fallback:
                cursor_fallback = conn_fallback.cursor(dictionary=True)
                try:
                    cursor_fallback.execute("SELECT division_id, division_name FROM Divisions")
                    divisions_fallback = cursor_fallback.fetchall()
                except Exception as ex:
                    print(f"Could not fetch divisions: {ex}")
                finally:
                    cursor_fallback.close()
                    conn_fallback.close()
            return render_template('signup.html', error='Database connection failed', divisions=divisions_fallback)
    
    # GET request - Get divisions for dropdown
    conn = get_db_connection()
    divisions = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT division_id, division_name FROM Divisions")
            divisions = cursor.fetchall()
        except Exception as e:
            print(f"Could not fetch divisions: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('signup.html', divisions=divisions)

## ========== PUBLIC ROUTES ==========
# ========== PUBLIC ROUTES ==========
@app.route('/')
def index():
    """Public homepage - visible to all"""
    conn = get_db_connection()
    stats = {}
    top_divisions = []
    issue_types = []
    live_status = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get system stats from view
            cursor.execute("SELECT * FROM System_Stats_View")
            stats = cursor.fetchone()
            
            # Get top divisions from view (already ordered by resolution rate)
            cursor.execute("SELECT * FROM Top_Divisions_Summary_View")
            top_divisions = cursor.fetchall()
            
            # Get issue type distribution
            cursor.execute("SELECT * FROM Issue_Type_Distribution_View")
            issue_types = cursor.fetchall()
            
            # Get live service status for all divisions - ORDER BY resolved_issues DESC
            cursor.execute("""
                SELECT 
                    d.division_id,
                    d.division_name,
                    COUNT(DISTINCT w.worker_id) as total_workers,
                    COUNT(DISTINCT CASE WHEN w.availability = 'Available' THEN w.worker_id END) as available_workers,
                    COUNT(DISTINCT CASE WHEN i.status = 'pending' THEN i.issue_id END) as pending_issues,
                    COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) as resolved_issues,
                    ROUND(
                        (COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) / 
                         NULLIF(COUNT(DISTINCT i.issue_id), 0)) * 100, 2
                    ) as resolution_rate
                FROM Divisions d
                LEFT JOIN Workers w ON d.division_id = w.division_id AND w.is_active = TRUE
                LEFT JOIN Issues i ON d.division_id = i.division_id
                GROUP BY d.division_id, d.division_name
                ORDER BY resolved_issues DESC, resolution_rate DESC
            """)
            live_status = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching homepage data: {e}")
            # Provide fallback data if views don't exist
            stats = {'total_workers': 25, 'resolved_issues': 150, 'total_users': 300, 'satisfaction_rate': 92}
            # Fallback live status data - ordered by resolved issues
            live_status = [
                {'division_name': 'Mumbai Division', 'total_workers': 10, 'available_workers': 7, 'pending_issues': 8, 'resolved_issues': 152, 'resolution_rate': 95.0},
                {'division_name': 'Pune Division', 'total_workers': 8, 'available_workers': 5, 'pending_issues': 12, 'resolved_issues': 145, 'resolution_rate': 92.4},
                {'division_name': 'Nashik Division', 'total_workers': 7, 'available_workers': 3, 'pending_issues': 10, 'resolved_issues': 142, 'resolution_rate': 93.4},
                {'division_name': 'Nagpur Division', 'total_workers': 6, 'available_workers': 4, 'pending_issues': 15, 'resolved_issues': 138, 'resolution_rate': 90.2},
                {'division_name': 'Thane Division', 'total_workers': 9, 'available_workers': 6, 'pending_issues': 7, 'resolved_issues': 135, 'resolution_rate': 95.1},
                {'division_name': 'Aurangabad Division', 'total_workers': 5, 'available_workers': 2, 'pending_issues': 18, 'resolved_issues': 128, 'resolution_rate': 87.7}
            ]
        finally:
            cursor.close()
            conn.close()
    
    return render_template('index.html', 
                         stats=stats, 
                         top_divisions=top_divisions, 
                         issue_types=issue_types,
                         live_status=live_status)


# ========== USER ROUTES ==========
@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    stats = {}
    live_status = []
    recent_activity = []
    user_issues = []
    top_divisions = []
    issue_types = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get user's division_id first
            cursor.execute("SELECT division_id FROM Users WHERE user_id = %s", (session.get('user_id'),))
            user_division = cursor.fetchone()
            user_division_id = user_division['division_id'] if user_division else None
            
            # Get system stats from view
            cursor.execute("SELECT * FROM System_Stats_View")
            stats = cursor.fetchone()

            # Get live service status - ONLY user's division
            if user_division_id:
                cursor.execute("""
                    SELECT * FROM Live_Service_Status_View 
                    WHERE division_id = %s
                """, (user_division_id,))
            else:
                cursor.execute("SELECT * FROM Live_Service_Status_View LIMIT 1")
            live_status = cursor.fetchall()

            # Get recent activity
            cursor.execute("SELECT * FROM Recent_Activity_View")
            recent_activity = cursor.fetchall()

            # Get top divisions
            cursor.execute("SELECT * FROM Top_Divisions_Summary_View")
            top_divisions = cursor.fetchall()

            # Get issue type distribution
            cursor.execute("SELECT * FROM Issue_Type_Distribution_View")
            issue_types = cursor.fetchall()

            # Get user's issues
            print(f"DEBUG: Fetching issues for user_id: {session.get('user_id')}")
            
            # Try the view first
            try:
                cursor.execute("SELECT * FROM User_Issues_Summary_VIEW WHERE user_id = %s", (session.get('user_id'),))
                user_issues = cursor.fetchall()
                print(f"DEBUG: Found {len(user_issues)} issues from view")
            except Exception as view_error:
                print(f"DEBUG: View failed, using direct query: {view_error}")
                # Fallback direct query
                cursor.execute("""
                    SELECT 
                        i.issue_id, i.title, i.issue_type, i.description, i.status, i.priority,
                        i.created_at, i.resolved_at, d.division_name
                    FROM Issues i
                    JOIN Divisions d ON i.division_id = d.division_id
                    WHERE i.user_id = %s
                    ORDER BY i.created_at DESC
                """, (session.get('user_id'),))
                user_issues = cursor.fetchall()
                print(f"DEBUG: Found {len(user_issues)} issues from direct query")
            
        except Exception as e:
            print(f"Error in user dashboard: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cursor.close()
            conn.close()
    
    print(f"DEBUG: Rendering dashboard with {len(user_issues)} user issues")
    return render_template('dashboard.html',
                         stats=stats,
                         live_status=live_status,
                         recent_activity=recent_activity,
                         user_issues=user_issues,
                         top_divisions=top_divisions,
                         issue_types=issue_types,
                         user_name=session.get('user_name'))

@app.route('/raise-issue')
def raise_issue_page():
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    # Get divisions for dropdown
    conn = get_db_connection()
    divisions = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT division_id, division_name FROM Divisions ORDER BY division_name")
            divisions = cursor.fetchall()
        except Exception as e:
            print(f"Error fetching divisions: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('raise_issue.html', 
                         divisions=divisions,
                         user_name=session.get('user_name'))
@app.route('/track-issues')
def track_issues():
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    issue_type_filter = request.args.get('issue_type', '')
    division_filter = request.args.get('division', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    date_type = request.args.get('date_type', 'created')
    
    conn = get_db_connection()
    user_issues = []
    divisions = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Build the query with filters
            query = """
                SELECT 
                    i.issue_id, i.title, i.issue_type, i.description, i.status, i.priority,
                    i.created_at, i.resolved_at, d.division_name, d.division_id,
                    COUNT(iw.worker_id) as assigned_workers_count,
                    GROUP_CONCAT(DISTINCT w.name SEPARATOR ', ') as assigned_worker_names
                FROM Issues i
                JOIN Divisions d ON i.division_id = d.division_id
                LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id AND iw.worker_status != 'completed'
                LEFT JOIN Workers w ON iw.worker_id = w.worker_id
                WHERE i.user_id = %s
            """
            params = [session.get('user_id')]
            
            # Add filters if provided
            if status_filter:
                query += " AND i.status = %s"
                params.append(status_filter)
            
            if priority_filter:
                query += " AND i.priority = %s"
                params.append(priority_filter)
            
            if issue_type_filter:
                query += " AND i.issue_type = %s"
                params.append(issue_type_filter)
            
            if division_filter:
                query += " AND i.division_id = %s"
                params.append(division_filter)
            
            # Add date filters
            if from_date:
                if date_type == 'created':
                    query += " AND DATE(i.created_at) >= %s"
                elif date_type == 'resolved':
                    query += " AND DATE(i.resolved_at) >= %s"
                else:  # both
                    query += " AND (DATE(i.created_at) >= %s OR DATE(i.resolved_at) >= %s)"
                params.append(from_date)
            
            if to_date:
                if date_type == 'created':
                    query += " AND DATE(i.created_at) <= %s"
                elif date_type == 'resolved':
                    query += " AND DATE(i.resolved_at) <= %s"
                else:  # both
                    query += " AND (DATE(i.created_at) <= %s OR DATE(i.resolved_at) <= %s)"
                params.append(to_date)
            
            query += " GROUP BY i.issue_id, i.title, i.issue_type, i.description, i.status, i.priority, i.created_at, i.resolved_at, d.division_name, d.division_id"
            query += " ORDER BY i.created_at DESC"
            
            cursor.execute(query, params)
            user_issues = cursor.fetchall()
            
            # Get divisions for filter dropdown
            cursor.execute("SELECT division_id, division_name FROM Divisions ORDER BY division_name")
            divisions = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching user issues: {e}")
            flash('Error loading issues. Please try again.', 'error')
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Database connection failed. Please try again.', 'error')
    
    # Get today's date for date filter max values
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('track_issues.html', 
                         user_issues=user_issues,
                         divisions=divisions,
                         user_name=session.get('user_name'),
                         today=today)
@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user_data = {}
    divisions = []
    stats = {}
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get user data
            cursor.execute("""
                SELECT u.*, d.division_name 
                FROM Users u 
                LEFT JOIN Divisions d ON u.division_id = d.division_id 
                WHERE u.user_id = %s
            """, (session.get('user_id'),))
            user_data = cursor.fetchone()
            
            # Get divisions for dropdown
            cursor.execute("SELECT division_id, division_name FROM Divisions")
            divisions = cursor.fetchall()
            
            # Get user stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_issues,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_issues,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_issues
                FROM Issues 
                WHERE user_id = %s
            """, (session.get('user_id'),))
            
            stats = cursor.fetchone() or {'total_issues': 0, 'pending_issues': 0, 'resolved_issues': 0}
            
        except Exception as e:
            print(f"Error fetching user profile: {e}")
            # Set default stats if there's an error
            stats = {'total_issues': 0, 'pending_issues': 0, 'resolved_issues': 0}
        finally:
            cursor.close()
            conn.close()
    
    return render_template('profile.html', 
                         user_data=user_data,
                         divisions=divisions,
                         stats=stats,
                         user_name=session.get('user_name'))

# ========== PROFILE MANAGEMENT ROUTES ==========

@app.route('/api/update-profile', methods=['POST'])
def update_profile():
    """API endpoint to update user profile"""
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get form data
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address_line1 = request.form['address_line1']
        address_line2 = request.form.get('address_line2', '')
        city = request.form['city']
        pincode = request.form['pincode']
        division_id = request.form.get('division_id')
        
        # Convert empty division_id to None
        if division_id == '':
            division_id = None
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Update user profile
            cursor.execute("""
                UPDATE Users 
                SET name = %s, email = %s, phone = %s, address_line1 = %s, 
                    address_line2 = %s, city = %s, pincode = %s, division_id = %s
                WHERE user_id = %s
            """, (name, email, phone, address_line1, address_line2, city, pincode, division_id, session.get('user_id')))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update session name if changed
            if session.get('user_name') != name:
                session['user_name'] = name
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except mysql.connector.Error as e:
        print(f"Error updating profile: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/change-password', methods=['POST'])
def change_password():
    """API endpoint to change user password"""
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Validate passwords match
        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'New passwords do not match'}), 400
        
        # Validate password length
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Verify current password
            cursor.execute("""
                SELECT user_id FROM Users 
                WHERE user_id = %s AND password = %s
            """, (session.get('user_id'), current_password))
            
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
            
            # Update password
            update_cursor = conn.cursor()
            update_cursor.execute("""
                UPDATE Users 
                SET password = %s 
                WHERE user_id = %s
            """, (new_password, session.get('user_id')))
            
            conn.commit()
            cursor.close()
            update_cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except mysql.connector.Error as e:
        print(f"Error changing password: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    except Exception as e:
        print(f"Error changing password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user-audit-log')
def get_user_audit_log():
    """API endpoint to get user audit log for profile page"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT action_type, changed_at, old_values, new_values
                FROM User_Audit_Log
                WHERE user_id = %s
                ORDER BY changed_at DESC
                LIMIT 10
            """, (session.get('user_id'),))
            
            logs = cursor.fetchall()
            return jsonify({'success': True, 'logs': logs})
                
        except Exception as e:
            print(f"Error fetching user audit log: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    


@app.route('/api/user-stats')
def get_user_stats():
    """API endpoint to get user statistics for profile page"""
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            user_id = session.get('user_id')
            
            # Get issue statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_issues,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_issues,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_issues
                FROM Issues 
                WHERE user_id = %s
            """, (user_id,))
            
            stats = cursor.fetchone()
            
            return jsonify({'success': True, 'stats': stats})
                
        except Exception as e:
            print(f"Error fetching user stats: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

@app.route('/api/welcome-message')
def get_welcome_message():
    """API endpoint to get personalized welcome message using existing procedure"""
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    user_id = session.get('user_id')
    user_type = session.get('user_type', 'user')
    user_name = session.get('user_name', 'User')
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Call the existing stored procedure
            cursor.callproc('LogUserLogin', [user_id, user_type, user_name])
            
            # Get the result
            for result in cursor.stored_results():
                welcome_data = result.fetchone()
                break
            
            cursor.close()
            conn.close()
            
            if welcome_data:
                return jsonify({
                    'success': True, 
                    'welcome_message': welcome_data['welcome_message']
                })
            else:
                # Fallback if procedure returns no data
                return jsonify({
                    'success': True,
                    'welcome_message': f'Welcome to EGS, {user_name}!'
                })
                
        except Exception as e:
            print(f"Error getting welcome message: {e}")
            # Fallback if procedure fails
            return jsonify({
                'success': True,
                'welcome_message': f'Welcome to EGS, {user_name}!'
            })
    else:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    

# ========== WORKER ROUTES ==========
@app.route('/worker-dashboard')
def worker_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    worker_id = session.get('user_id')
    conn = get_db_connection()
    
    stats = {}
    assigned_issues = []
    recent_notifications = []
    today_attendance = None
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get worker stats using procedure
            cursor.callproc('get_worker_stats', [worker_id])
            for result in cursor.stored_results():
                stats = result.fetchone()
                break
            
            # Get assigned issues
            cursor.execute("""
                SELECT * FROM worker_assigned_issues 
                WHERE worker_id = %s 
                ORDER BY assigned_at DESC 
                LIMIT 5
            """, (worker_id,))
            assigned_issues = cursor.fetchall()
            
            # Get recent notifications
            cursor.execute("""
                SELECT * FROM Notifications 
                WHERE worker_id = %s 
                ORDER BY created_at DESC 
                LIMIT 5
            """, (worker_id,))
            recent_notifications = cursor.fetchall()
            
            # Get today's attendance
            today = datetime.now().date()
            cursor.execute("""
                SELECT * FROM Attendance 
                WHERE worker_id = %s AND date = %s
            """, (worker_id, today))
            today_attendance = cursor.fetchone()
            
        except Exception as e:
            print(f"Error in worker dashboard: {e}")
            # Set default stats if there's an error
            stats = {'total_tasks': 0, 'ongoing_tasks': 0, 'completed_tasks': 0, 'unread_notifications': 0, 'assigned_equipment': 0}
        finally:
            cursor.close()
            conn.close()
    
    return render_template('worker_dashboard.html',
                         stats=stats,
                         assigned_issues=assigned_issues,
                         recent_notifications=recent_notifications,
                         today_attendance=today_attendance,
                         user_name=session.get('user_name'))

# In your worker_attendance route in app.py
@app.route('/worker-attendance')
def worker_attendance():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    worker_id = session.get('user_id')
    conn = get_db_connection()
    
    attendance_records = []
    monthly_stats = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get current month and year
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Get attendance records for current month
            cursor.execute("""
                SELECT * FROM Attendance 
                WHERE worker_id = %s AND MONTH(date) = %s AND YEAR(date) = %s
                ORDER BY date DESC
            """, (worker_id, current_month, current_year))
            records = cursor.fetchall()
            
            # Process records to calculate working hours
            for record in records:
                if record['in_time'] and record['out_time']:
                    # Calculate working hours from timedelta objects
                    in_seconds = record['in_time'].seconds
                    out_seconds = record['out_time'].seconds
                    total_seconds = out_seconds - in_seconds
                    if total_seconds > 0:
                        record['working_hours'] = round(total_seconds / 3600, 1)
                    else:
                        record['working_hours'] = 0
                else:
                    record['working_hours'] = None
                attendance_records.append(record)
            
            # Get monthly stats - FIXED QUERY
            cursor.execute("""
                SELECT 
                    MONTH(date) as month, 
                    YEAR(date) as year,
                    COUNT(*) as total_days,
                    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
                    SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
                    SUM(CASE WHEN status = 'Leave' THEN 1 ELSE 0 END) as leave_days
                FROM Attendance 
                WHERE worker_id = %s AND MONTH(date) = %s AND YEAR(date) = %s
                GROUP BY YEAR(date), MONTH(date)
                ORDER BY year DESC, month DESC
                LIMIT 6
            """, (worker_id, current_month, current_year))
            monthly_stats = cursor.fetchall()
            
            # If no data for current month, get latest available month
            if not monthly_stats:
                cursor.execute("""
                    SELECT 
                        MONTH(date) as month, 
                        YEAR(date) as year,
                        COUNT(*) as total_days,
                        SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
                        SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
                        SUM(CASE WHEN status = 'Leave' THEN 1 ELSE 0 END) as leave_days
                    FROM Attendance 
                    WHERE worker_id = %s
                    GROUP BY YEAR(date), MONTH(date)
                    ORDER BY year DESC, month DESC
                    LIMIT 1
                """, (worker_id,))
                monthly_stats = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching attendance: {e}")
            flash('Error loading attendance records', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('worker_attendance.html',
                         attendance_records=attendance_records,
                         monthly_stats=monthly_stats,
                         user_name=session.get('user_name'),
                         today=datetime.now().date())

# Enhanced worker tasks route with location data
@app.route('/worker-tasks')
def worker_tasks():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    worker_id = session.get('user_id')
    conn = get_db_connection()
    
    assigned_issues = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get assigned issues with ALL details including location
            cursor.execute("""
                SELECT 
                    iw.issue_id, iw.worker_id, iw.worker_status, iw.assigned_at, 
                    iw.worker_notes, iw.completed_at,
                    i.title, i.issue_type, i.description, i.priority, i.status as issue_status,
                    i.created_at as issue_created_at, i.resolved_at,
                    i.latitude, i.longitude, i.address_line1, i.address_line2,
                    i.image_url,
                    u.name as user_name, u.phone as user_phone, u.email as user_email,
                    d.division_name, d.division_id
                FROM IssueWorkers iw
                JOIN Issues i ON iw.issue_id = i.issue_id
                JOIN Users u ON i.user_id = u.user_id
                JOIN Divisions d ON i.division_id = d.division_id
                WHERE iw.worker_id = %s 
                ORDER BY 
                    CASE WHEN iw.worker_status = 'assigned' THEN 1
                         WHEN iw.worker_status = 'in_progress' THEN 2
                         ELSE 3 END,
                    iw.assigned_at DESC
            """, (worker_id,))
            assigned_issues = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching worker tasks: {e}")
            flash('Error loading tasks', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('worker_tasks.html',
                         assigned_issues=assigned_issues,
                         user_name=session.get('user_name'))

# Enhanced worker equipment route with equipment history
@app.route('/worker-equipment')
def worker_equipment():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    worker_id = session.get('user_id')
    conn = get_db_connection()
    
    assigned_equipment = []
    available_equipment = []
    equipment_history = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get assigned equipment
           # Get assigned equipment
            cursor.execute("""
                SELECT 
                    e.*,
                    w.name as worker_name,
                    d.division_name
                FROM Electrical_Equipment e
                LEFT JOIN Workers w ON e.current_worker_id = w.worker_id
                LEFT JOIN Divisions d ON e.division_id = d.division_id
                WHERE e.current_worker_id = %s
            """, (worker_id,))
            assigned_equipment = cursor.fetchall()
            
            # Get available equipment (not assigned to anyone and approved)
            # Get available equipment - FIXED with division_type
            cursor.execute("""
                SELECT 
                    e.*,
                    d.division_name as equipment_division_name,
                    CASE 
                        WHEN e.division_id = %s THEN 'Your Division'
                        ELSE 'External Division'
                    END as division_type
                FROM Electrical_Equipment e
                LEFT JOIN Divisions d ON e.division_id = d.division_id
                WHERE e.current_worker_id IS NULL AND e.is_approved = 'Yes'
                ORDER BY 
                    CASE WHEN e.division_id = %s THEN 0 ELSE 1 END,  -- Show own division equipment first
                    e.name_of_equipment
            """, (session.get('division_id'), session.get('division_id')))
            available_equipment = cursor.fetchall()
            
            # Get equipment history (requests and rejections)
            # Get equipment history - FIXED with division info
            cursor.execute("""
                SELECT 
                    eh.history_id, eh.equipment_id, eh.action_type, eh.action_date,
                    eh.purpose, eh.expected_return_date, eh.actual_return_date,
                    eh.re_issue_date, eh.notes, eh.action_by_head_id,
                    e.serial_no, e.name_of_equipment, e.model_no, e.equipment_cost,
                    e.division_id as equipment_division_id,
                    d_equip.division_name as equipment_division_name,
                    dh.name as head_name
                FROM Equipment_History eh
                JOIN Electrical_Equipment e ON eh.equipment_id = e.equipment_id
                LEFT JOIN Division_Heads dh ON eh.action_by_head_id = dh.head_id
                LEFT JOIN Divisions d_equip ON e.division_id = d_equip.division_id
                WHERE eh.worker_id = %s
                ORDER BY eh.action_date DESC
            """, (worker_id,))
            equipment_history = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching equipment: {e}")
            flash('Error loading equipment information', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('worker_equipment.html',
                         assigned_equipment=assigned_equipment,
                         available_equipment=available_equipment,
                         equipment_history=equipment_history,
                         user_name=session.get('user_name'))
# API route for equipment requests
@app.route('/api/request-equipment', methods=['POST'])
def request_equipment():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        worker_id = session.get('user_id')
        equipment_id = request.form['equipment_id']
        purpose = request.form['purpose']
        expected_return_date = request.form['expected_return_date']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Insert equipment request into history with NULL action_by_head_id
            cursor.execute("""
                INSERT INTO Equipment_History 
                (equipment_id, worker_id, action_type, action_by_head_id, purpose, expected_return_date)
                VALUES (%s, %s, 'requested', NULL, %s, %s)
            """, (equipment_id, worker_id, purpose, expected_return_date))
            
            # Create notification for the worker
            cursor.execute("""
                INSERT INTO Notifications (worker_id, message)
                VALUES (%s, %s)
            """, (worker_id, f'Equipment request submitted for equipment ID {equipment_id}'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Equipment request submitted successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error requesting equipment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/worker-leave')
def worker_leave():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    worker_id = session.get('user_id')
    conn = get_db_connection()
    
    leave_applications = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM Leave_Applications 
                WHERE worker_id = %s 
                ORDER BY applied_at DESC
            """, (worker_id,))
            leave_applications = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching leave applications: {e}")
            flash('Error loading leave applications', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('worker_leave.html',
                         leave_applications=leave_applications,
                         user_name=session.get('user_name'))

@app.route('/worker-profile')
def worker_profile():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    worker_id = session.get('user_id')
    conn = get_db_connection()
    
    worker_data = {}
    divisions = []
    audit_logs = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get worker data
            cursor.execute("""
                SELECT w.*, d.division_name 
                FROM Workers w 
                LEFT JOIN Divisions d ON w.division_id = d.division_id 
                WHERE w.worker_id = %s
            """, (worker_id,))
            worker_data = cursor.fetchone()
            
            # Get divisions for dropdown (if needed)
            cursor.execute("SELECT division_id, division_name FROM Divisions")
            divisions = cursor.fetchall()
            
            # Get audit logs
            cursor.execute("""
                SELECT * FROM Worker_Audit_Log 
                WHERE worker_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (worker_id,))
            audit_logs = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching worker profile: {e}")
            flash('Error loading profile', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('worker_profile.html',
                         worker_data=worker_data,
                         divisions=divisions,
                         audit_logs=audit_logs,
                         user_name=session.get('user_name'))

# ========== WORKER API ROUTES ==========
@app.route('/api/mark-attendance', methods=['POST'])
def mark_attendance():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        worker_id = session.get('user_id')
        date = request.form['date']
        status = request.form['status']
        in_time = request.form.get('in_time')
        out_time = request.form.get('out_time')
        
        # Convert empty strings to None
        in_time = in_time if in_time else None
        out_time = out_time if out_time else None
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.callproc('mark_attendance', [worker_id, date, status, in_time, out_time])
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Attendance marked successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error marking attendance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/apply-leave', methods=['POST'])
def apply_leave():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        worker_id = session.get('user_id')
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.callproc('apply_for_leave', [worker_id, start_date, end_date, reason])
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Leave application submitted successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error applying for leave: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-issue-status', methods=['POST'])
def update_issue_status():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        worker_id = session.get('user_id')
        issue_id = request.form['issue_id']
        new_status = request.form['status']
        notes = request.form.get('notes', '')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            if new_status == 'completed':
                # Update worker status in IssueWorkers
                cursor.execute("""
                    UPDATE IssueWorkers 
                    SET worker_status = %s, worker_notes = %s, completed_at = NOW()
                    WHERE issue_id = %s AND worker_id = %s
                """, (new_status, notes, issue_id, worker_id))
                
                # AUTO-UPDATE the main issue status in Issues table
                cursor.execute("""
                    UPDATE Issues 
                    SET status = 'resolved', resolved_at = NOW()
                    WHERE issue_id = %s
                """, (issue_id,))
                
                # Mark worker as available again
                cursor.execute("""
                    UPDATE Workers 
                    SET availability = 'Available' 
                    WHERE worker_id = %s
                """, (worker_id,))
                
            else:
                cursor.execute("""
                    UPDATE IssueWorkers 
                    SET worker_status = %s, worker_notes = %s
                    WHERE issue_id = %s AND worker_id = %s
                """, (new_status, notes, issue_id, worker_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Task status updated successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error updating issue status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-worker-profile', methods=['POST'])
def update_worker_profile():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        worker_id = session.get('user_id')
        name = request.form['name']
        age = request.form['age']
        phone_no = request.form['phone_no']
        address = request.form['address']
        skill_sets = request.form.get('skill_sets', '')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.callproc('update_worker_profile', [worker_id, name, age, phone_no, address, skill_sets])
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update session name if changed
            if session.get('user_name') != name:
                session['user_name'] = name
            
            flash('Profile updated successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except mysql.connector.Error as e:
        print(f"Error updating worker profile: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    except Exception as e:
        print(f"Error updating worker profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mark-notification-read', methods=['POST'])
def mark_notification_read():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        notification_id = request.form['notification_id']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Notifications 
                SET is_read = TRUE 
                WHERE notification_id = %s AND worker_id = %s
            """, (notification_id, session.get('user_id')))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/task-details/<int:issue_id>')
def get_task_details(issue_id):
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    iw.issue_id, iw.worker_status, iw.worker_notes,
                    i.title, i.description, i.issue_type, i.priority, 
                    i.latitude, i.longitude, i.address_line1, i.address_line2,
                    u.name as user_name, u.phone as user_phone
                FROM IssueWorkers iw
                JOIN Issues i ON iw.issue_id = i.issue_id
                JOIN Users u ON i.user_id = u.user_id
                WHERE iw.issue_id = %s AND iw.worker_id = %s
            """, (issue_id, session.get('user_id')))
            
            task = cursor.fetchone()
            
            if task:
                return jsonify({'success': True, 'task': task})
            else:
                return jsonify({'success': False, 'error': 'Task not found'}), 404
                
        except Exception as e:
            print(f"Error fetching task details: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    

@app.route('/api/mark-all-notifications-read', methods=['POST'])
def mark_all_notifications_read():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        worker_id = session.get('user_id')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Notifications 
                SET is_read = TRUE 
                WHERE worker_id = %s AND is_read = FALSE
            """, (worker_id,))
            
            affected_rows = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True, 
                'message': f'Marked {affected_rows} notifications as read'
            })
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== DIVISION HEAD ROUTES ==========
# Division Dashboard Route
# Division Head Routes
# Division Dashboard Route - CORRECTED

@app.route('/division/dashboard')
def division_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return redirect(url_for('login'))
    
    division_id = session['division_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get division name
        cursor.execute("SELECT division_name FROM Divisions WHERE division_id = %s", (division_id,))
        division = cursor.fetchone()
        division_name = division['division_name'] if division else 'Division'
        
        # Get division stats with corrected queries
        cursor.execute("""
            SELECT 
                d.division_id,
                d.division_name,
                COUNT(DISTINCT i.issue_id) as total_issues,
                COUNT(DISTINCT CASE WHEN i.status = 'pending' THEN i.issue_id END) as pending_issues,
                COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) as resolved_issues,
                COUNT(DISTINCT CASE WHEN iw.worker_id IS NOT NULL AND i.status != 'resolved' THEN i.issue_id END) as assigned_issues,
                COUNT(DISTINCT w.worker_id) as total_workers,
                COUNT(DISTINCT CASE WHEN w.availability = 'Available' THEN w.worker_id END) as available_workers,
                COUNT(DISTINCT CASE WHEN w.availability = 'On Task' THEN w.worker_id END) as on_task_workers,
                ROUND(
                    (COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) / 
                    NULLIF(COUNT(DISTINCT i.issue_id), 0)) * 100, 2
                ) as resolution_rate
            FROM Divisions d
            LEFT JOIN Workers w ON d.division_id = w.division_id AND w.is_active = TRUE
            LEFT JOIN Issues i ON d.division_id = i.division_id
            LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id AND iw.worker_status != 'completed'
            WHERE d.division_id = %s
            GROUP BY d.division_id, d.division_name
        """, (division_id,))
        division_data = cursor.fetchone()
        
        # Get all divisions status with corrected query
        cursor.execute("""
            SELECT 
                d.division_id,
                d.division_name,
                COUNT(DISTINCT w.worker_id) as total_workers,
                COUNT(DISTINCT CASE WHEN w.availability = 'Available' THEN w.worker_id END) as available_workers,
                COUNT(DISTINCT CASE WHEN i.status = 'pending' THEN i.issue_id END) as pending_issues,
                COUNT(DISTINCT CASE WHEN i.status = 'resolved' AND DATE(i.resolved_at) = CURDATE() THEN i.issue_id END) as resolved_today,
                ROUND(
                    (COUNT(DISTINCT CASE WHEN i.status = 'resolved' THEN i.issue_id END) / 
                    NULLIF(COUNT(DISTINCT i.issue_id), 0)) * 100, 2
                ) as resolution_rate
            FROM Divisions d
            LEFT JOIN Workers w ON d.division_id = w.division_id AND w.is_active = TRUE
            LEFT JOIN Issues i ON d.division_id = i.division_id
            GROUP BY d.division_id, d.division_name
            ORDER BY resolution_rate DESC 
            LIMIT 6
        """)
        all_divisions_status = cursor.fetchall()
        
        # Get issue type distribution
        cursor.execute("""
            SELECT 
                issue_type,
                COUNT(*) as issue_count,
                ROUND((COUNT(*) / NULLIF((SELECT COUNT(*) FROM Issues WHERE division_id = %s), 0)) * 100, 1) as percentage
            FROM Issues 
            WHERE division_id = %s 
            GROUP BY issue_type 
            ORDER BY issue_count DESC
        """, (division_id, division_id))
        issue_types = cursor.fetchall()
        
        # Get recent issues
        cursor.execute("""
            SELECT i.issue_id, i.title, i.issue_type, i.priority, i.status, i.created_at
            FROM Issues i 
            WHERE i.division_id = %s 
            ORDER BY i.created_at DESC 
            LIMIT 10
        """, (division_id,))
        recent_issues = cursor.fetchall()
        
        # Get available workers
        cursor.execute("""
            SELECT name, worker_type, availability 
            FROM Workers 
            WHERE division_id = %s AND is_active = TRUE AND availability = 'Available'
            LIMIT 5
        """, (division_id,))
        available_workers = cursor.fetchall()
        
        # Get security alerts
        cursor.execute("""
            SELECT email, attempted_at, ip_address 
            FROM Failed_Login_Attempts 
            WHERE division_id = %s 
            ORDER BY attempted_at DESC 
            LIMIT 5
        """, (division_id,))
        security_alerts = cursor.fetchall()
        
        # Prepare stats dictionary with corrected data
        stats = {
            'total_issues': division_data['total_issues'] if division_data else 0,
            'pending_issues': division_data['pending_issues'] if division_data else 0,
            'assigned_issues': division_data['assigned_issues'] if division_data else 0,
            'resolved_issues': division_data['resolved_issues'] if division_data else 0,
            'total_workers': division_data['total_workers'] if division_data else 0,
            'available_workers': division_data['available_workers'] if division_data else 0,
            'on_task_workers': division_data['on_task_workers'] if division_data else 0,
            'resolution_rate': division_data['resolution_rate'] if division_data else 0,
            'avg_resolution_time': 2.5,  # Placeholder
            'worker_utilization': round(
                (division_data['on_task_workers'] / division_data['total_workers'] * 100) 
                if division_data and division_data['total_workers'] > 0 else 0, 1
            )
        }
        
        return render_template('division_dashboard.html',
                           user_name=session['user_name'],
                           division_name=division_name,
                           stats=stats,
                           all_divisions_status=all_divisions_status,
                           recent_issues=recent_issues,
                           available_workers=available_workers,
                           security_alerts=security_alerts,
                           issue_types=issue_types,
                           current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                           
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('division_dashboard.html',
                           user_name=session['user_name'],
                           division_name=session.get('division_name', 'Division'),
                           stats={},
                           all_divisions_status=[],
                           recent_issues=[],
                           available_workers=[],
                           security_alerts=[],
                           issue_types=[])
    finally:
        cursor.close()
        conn.close()

@app.route('/division/issues')
def division_issues():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return redirect(url_for('login'))
    
    division_id = session['division_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get division name
        cursor.execute("SELECT division_name FROM Divisions WHERE division_id = %s", (division_id,))
        division = cursor.fetchone()
        division_name = division['division_name'] if division else 'Division'
        
        # Get filter parameters
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        type_filter = request.args.get('type', '')
        
        # Build query with filters
        query = """
            SELECT 
                i.issue_id, i.title, i.description, i.issue_type, i.priority, i.status, i.created_at,
                u.name as user_name,
                w.name as worker_name,
                iw.worker_status,
                iw.worker_notes,
                iw.assigned_at,
                i.address_line1,
                i.address_line2,
                i.latitude,
                i.longitude,
                i.image_url
            FROM Issues i
            LEFT JOIN Users u ON i.user_id = u.user_id
            LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id
            LEFT JOIN Workers w ON iw.worker_id = w.worker_id
            WHERE i.division_id = %s
        """
        params = [division_id]
        
        if status_filter:
            query += " AND i.status = %s"
            params.append(status_filter)
        if priority_filter:
            query += " AND i.priority = %s"
            params.append(priority_filter)
        if type_filter:
            query += " AND i.issue_type = %s"
            params.append(type_filter)
            
        query += " ORDER BY i.created_at DESC"
        
        cursor.execute(query, params)
        issues = cursor.fetchall()
        
        # Get available workers for assignment
        cursor.execute("""
            SELECT worker_id, name, worker_type, availability, skill_sets 
            FROM Workers 
            WHERE division_id = %s AND is_active = TRUE AND availability = 'Available'
        """, (division_id,))
        available_workers = cursor.fetchall()
        
        # Get total issues count
        cursor.execute("SELECT COUNT(*) as total FROM Issues WHERE division_id = %s", (division_id,))
        total_issues = cursor.fetchone()['total']
        
        return render_template('division_issues.html',
                           user_name=session['user_name'],
                           division_name=division_name,
                           issues=issues,
                           available_workers=available_workers,
                           total_issues=total_issues)
                           
    except Exception as e:
        flash(f'Error loading issues: {str(e)}', 'error')
        return render_template('division_issues.html',
                           user_name=session['user_name'],
                           division_name=session.get('division_name', 'Division'),
                           issues=[],
                           available_workers=[],
                           total_issues=0)
    finally:
        cursor.close()
        conn.close()

@app.route('/division/workers')
def division_workers():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return redirect(url_for('login'))
    
    division_id = session['division_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get division name
        cursor.execute("SELECT division_name FROM Divisions WHERE division_id = %s", (division_id,))
        division = cursor.fetchone()
        division_name = division['division_name'] if division else 'Division'
        
        # Get filter parameters
        type_filter = request.args.get('type', '')
        availability_filter = request.args.get('availability', '')
        status_filter = request.args.get('status', 'active')
        
        # Build query with filters
        query = """
            SELECT 
                w.worker_id, w.name, w.worker_type, w.phone_no, w.email, 
                w.age, w.availability, w.skill_sets, w.current_task_status, w.is_active,
                COUNT(iw.issue_id) as total_tasks,
                SUM(CASE WHEN iw.worker_status = 'completed' THEN 1 ELSE 0 END) as completed_tasks_count
            FROM Workers w
            LEFT JOIN IssueWorkers iw ON w.worker_id = iw.worker_id
            WHERE w.division_id = %s
        """
        params = [division_id]
        
        if status_filter == 'active':
            query += " AND w.is_active = TRUE"
        elif status_filter == 'inactive':
            query += " AND w.is_active = FALSE"
        
        if type_filter:
            query += " AND w.worker_type = %s"
            params.append(type_filter)
        if availability_filter:
            query += " AND w.availability = %s"
            params.append(availability_filter)
            
        query += " GROUP BY w.worker_id ORDER BY w.is_active DESC, w.name"
        
        cursor.execute(query, params)
        workers = cursor.fetchall()
        
        # Get worker stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_workers,
                SUM(CASE WHEN availability = 'Available' THEN 1 ELSE 0 END) as available_workers,
                SUM(CASE WHEN availability = 'On Task' THEN 1 ELSE 0 END) as on_task_workers,
                SUM(CASE WHEN worker_type = 'Technician' THEN 1 ELSE 0 END) as technicians,
                SUM(CASE WHEN worker_type = 'Inspector' THEN 1 ELSE 0 END) as inspectors,
                SUM(CASE WHEN worker_type = 'Supervisor' THEN 1 ELSE 0 END) as supervisors,
                SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as inactive_workers
            FROM Workers 
            WHERE division_id = %s
        """, (division_id,))
        stats_result = cursor.fetchone()
        
        stats = {
            'total_workers': stats_result['total_workers'] if stats_result else 0,
            'available_workers': stats_result['available_workers'] if stats_result else 0,
            'on_task_workers': stats_result['on_task_workers'] if stats_result else 0,
            'technicians': stats_result['technicians'] if stats_result else 0,
            'inspectors': stats_result['inspectors'] if stats_result else 0,
            'supervisors': stats_result['supervisors'] if stats_result else 0,
            'inactive_workers': stats_result['inactive_workers'] if stats_result else 0
        }
        
        # Get leave requests for this division
        cursor.execute("""
            SELECT 
                la.leave_id, la.start_date, la.end_date, la.reason, 
                la.status, la.applied_at, la.reviewed_at,
                w.name as worker_name, w.worker_type
            FROM Leave_Applications la
            JOIN Workers w ON la.worker_id = w.worker_id
            WHERE w.division_id = %s
            ORDER BY la.applied_at DESC
        """, (division_id,))
        leave_requests = cursor.fetchall()
        
        # Count pending leaves
        pending_leaves_count = len([l for l in leave_requests if l['status'] == 'Pending'])
        
        return render_template('division_workers.html',
                           user_name=session['user_name'],
                           division_name=division_name,
                           workers=workers,
                           stats=stats,
                           leave_requests=leave_requests,
                           pending_leaves_count=pending_leaves_count)
                           
    except Exception as e:
        flash(f'Error loading workers: {str(e)}', 'error')
        return render_template('division_workers.html',
                           user_name=session['user_name'],
                           division_name=session.get('division_name', 'Division'),
                           workers=[],
                           stats={},
                           leave_requests=[],
                           pending_leaves_count=0)
    finally:
        cursor.close()
        conn.close()

@app.route('/division/logs')
def division_logs():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return redirect(url_for('login'))
    
    division_id = session['division_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get filter parameters
        log_type = request.args.get('log_type', 'security')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        search = request.args.get('search', '')
        
        # Get division name
        cursor.execute("SELECT division_name FROM Divisions WHERE division_id = %s", (division_id,))
        division = cursor.fetchone()
        division_name = division['division_name'] if division else 'Division'
        
        # Build date filter condition
        def build_date_filter(date_column, params):
            conditions = []
            if date_from:
                conditions.append(f"DATE({date_column}) >= %s")
                params.append(date_from)
            if date_to:
                conditions.append(f"DATE({date_column}) <= %s")
                params.append(date_to)
            return " AND " + " AND ".join(conditions) if conditions else ""
        
        # 1. SECURITY LOGS - Only failed login attempts for this division's heads
        security_params = [division_id]
        security_query = f"""
            SELECT email, attempted_at, ip_address, user_agent
            FROM Failed_Login_Attempts 
            WHERE division_id = %s 
            {build_date_filter('attempted_at', security_params)}
            ORDER BY attempted_at DESC 
            LIMIT 100
        """
        cursor.execute(security_query, security_params)
        security_logs = cursor.fetchall()
        
        # 2. USER ACTIVITY LOGS - Only users from this division
        user_params = [division_id]
        user_activity_query = f"""
            SELECT ual.audit_id, ual.user_id, u.name as user_name, ual.action_type, 
                   ual.old_values, ual.new_values, ual.changed_at
            FROM User_Audit_Log ual
            JOIN Users u ON ual.user_id = u.user_id
            WHERE u.division_id = %s 
            {build_date_filter('ual.changed_at', user_params)}
            ORDER BY ual.changed_at DESC 
            LIMIT 100
        """
        cursor.execute(user_activity_query, user_params)
        user_activity_logs = cursor.fetchall()
        
        # 3. USER SIGNUP LOGS - Only users from this division
        user_signup_query = f"""
            SELECT usl.log_id, usl.user_id, usl.signup_time, usl.ip_address, 
                   usl.city, usl.pincode, u.name as user_name
            FROM User_Signup_Log usl
            JOIN Users u ON usl.user_id = u.user_id
            WHERE usl.division_id = %s
            ORDER BY usl.signup_time DESC 
            LIMIT 100
        """
        cursor.execute(user_signup_query, [division_id])
        user_signup_logs = cursor.fetchall()
        
        # 4. ISSUE AUDIT LOGS - Only issues from this division
        issue_params = [division_id]
        issue_audit_query = f"""
            SELECT ial.log_id, ial.issue_id, i.title as issue_title, ial.action_type, 
                   ial.old_values, ial.new_values, u.name as changed_by_name, ial.changed_at
            FROM Issue_Audit_Log ial
            JOIN Issues i ON ial.issue_id = i.issue_id
            LEFT JOIN Users u ON ial.changed_by = u.user_id
            WHERE i.division_id = %s 
            {build_date_filter('ial.changed_at', issue_params)}
            ORDER BY ial.changed_at DESC 
            LIMIT 100
        """
        cursor.execute(issue_audit_query, issue_params)
        issue_audit_logs = cursor.fetchall()
        
        # 5. WORKER ACTIVITY LOGS - Only workers from this division
        worker_params = [division_id]
        worker_activity_query = f"""
            SELECT wal.log_id, wal.worker_id, w.name as worker_name, wal.action_type, 
                   wal.description, wal.created_at
            FROM Worker_Audit_Log wal
            JOIN Workers w ON wal.worker_id = w.worker_id
            WHERE w.division_id = %s 
            {build_date_filter('wal.created_at', worker_params)}
            ORDER BY wal.created_at DESC 
            LIMIT 100
        """
        cursor.execute(worker_activity_query, worker_params)
        worker_activity_logs = cursor.fetchall()
        
        # 6. EQUIPMENT LOGS - Only equipment from this division
        equipment_params = [division_id]
        equipment_query = f"""
            SELECT el.log_id, el.equipment_id, ee.name_of_equipment, ee.serial_no,
                   el.action_type, el.notes, el.created_at,
                   w.name as worker_name, dh.name as head_name
            FROM Equipment_Logs el
            JOIN Electrical_Equipment ee ON el.equipment_id = ee.equipment_id
            LEFT JOIN Workers w ON el.worker_id = w.worker_id
            LEFT JOIN Division_Heads dh ON el.action_by_head_id = dh.head_id
            WHERE ee.division_id = %s 
            {build_date_filter('el.created_at', equipment_params)}
            ORDER BY el.created_at DESC 
            LIMIT 100
        """
        cursor.execute(equipment_query, equipment_params)
        equipment_logs = cursor.fetchall()
        
        # Get log statistics - ALL DIVISION-SPECIFIC
        cursor.execute("SELECT COUNT(*) as count FROM Failed_Login_Attempts WHERE division_id = %s", (division_id,))
        security_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM Issue_Audit_Log ial 
            JOIN Issues i ON ial.issue_id = i.issue_id 
            WHERE i.division_id = %s
        """, (division_id,))
        issue_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM User_Audit_Log ual 
            JOIN Users u ON ual.user_id = u.user_id 
            WHERE u.division_id = %s
        """, (division_id,))
        user_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM Worker_Audit_Log wal 
            JOIN Workers w ON wal.worker_id = w.worker_id 
            WHERE w.division_id = %s
        """, (division_id,))
        worker_count = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM Equipment_Logs el 
            JOIN Electrical_Equipment ee ON el.equipment_id = ee.equipment_id 
            WHERE ee.division_id = %s
        """, (division_id,))
        equipment_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM User_Signup_Log WHERE division_id = %s", (division_id,))
        signup_count = cursor.fetchone()['count']
        
        total_logs = security_count + issue_count + user_count + worker_count + equipment_count
        
        stats = {
            'security_logs': security_count,
            'issue_logs': issue_count,
            'user_logs': user_count,
            'worker_logs': worker_count,
            'equipment_logs': equipment_count,
            'total_logs': total_logs,
            'failed_logins': security_count,
            'new_signups': signup_count
        }
        
        return render_template('division_logs.html',
                           user_name=session['user_name'],
                           division_name=division_name,
                           security_logs=security_logs,
                           user_activity_logs=user_activity_logs,
                           user_signup_logs=user_signup_logs,
                           issue_audit_logs=issue_audit_logs,
                           worker_activity_logs=worker_activity_logs,
                           equipment_logs=equipment_logs,
                           stats=stats)
                           
    except Exception as e:
        print(f"Error loading logs: {str(e)}")
        flash(f'Error loading logs: {str(e)}', 'error')
        return render_template('division_logs.html',
                           user_name=session['user_name'],
                           division_name=session.get('division_name', 'Division'),
                           security_logs=[],
                           user_activity_logs=[],
                           user_signup_logs=[],
                           issue_audit_logs=[],
                           worker_activity_logs=[],
                           equipment_logs=[],
                           stats={})
    finally:
        cursor.close()
        conn.close()
@app.route('/division/equipment')
def division_equipment():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return redirect('/login')
    
    try:
        division_id = session['division_id']
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get equipment requests only from worker's division (DIVISION-SPECIFIC) - FIXED
        cursor.execute("""
            SELECT * FROM equipment_requests_view 
            WHERE worker_division_id = %s  -- Changed from division_id to worker_division_id
            ORDER BY action_date DESC
        """, (division_id,))
        equipment_requests = cursor.fetchall()
        
        # Get ALL equipment from ALL divisions (REMOVED division filter) - FIXED
        cursor.execute("""
            SELECT * FROM division_equipment_view 
            ORDER BY equipment_division_name, availability_status, name_of_equipment
        """)
        all_equipment = cursor.fetchall()
        
        # Get divisions for dropdown (only current division for adding new equipment)
        cursor.execute("SELECT division_id, division_name FROM Divisions WHERE division_id = %s", (division_id,))
        divisions = cursor.fetchall()
        
        # Get available workers from current division only (for issuing equipment)
        cursor.execute("""
            SELECT worker_id, name, worker_type 
            FROM Workers 
            WHERE division_id = %s AND is_active = TRUE AND availability = 'Available'
            ORDER BY name
        """, (division_id,))
        available_workers = cursor.fetchall()
        
        # Get equipment statistics for current division only - FIXED
        cursor.execute("""
            SELECT COUNT(*) as total_equipment 
            FROM Electrical_Equipment 
            WHERE division_id = %s
        """, (division_id,))
        total_equipment = cursor.fetchone()['total_equipment']
        
        cursor.execute("""
            SELECT COUNT(*) as available_equipment 
            FROM Electrical_Equipment 
            WHERE division_id = %s AND current_worker_id IS NULL
        """, (division_id,))
        available_equipment = cursor.fetchone()['available_equipment']
        
        cursor.execute("""
            SELECT COUNT(*) as assigned_equipment 
            FROM Electrical_Equipment 
            WHERE division_id = %s AND current_worker_id IS NOT NULL
        """, (division_id,))
        assigned_equipment = cursor.fetchone()['assigned_equipment']
        
        # Get all divisions summary for the new views
        cursor.execute("SELECT * FROM all_divisions_equipment_summary")
        all_divisions_summary = cursor.fetchall()
        
        # Get total statistics across all divisions
        cursor.execute("""
            SELECT 
                COUNT(*) as total_equipment_all,
                COUNT(CASE WHEN current_worker_id IS NULL THEN 1 END) as available_equipment_all,
                COUNT(CASE WHEN current_worker_id IS NOT NULL THEN 1 END) as assigned_equipment_all
            FROM Electrical_Equipment
        """)
        total_stats = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return render_template('division_equipment.html',
                           all_equipment=all_equipment,
                           equipment_requests=equipment_requests,
                           divisions=divisions,
                           available_workers=available_workers,
                           total_equipment=total_equipment,
                           available_equipment=available_equipment,
                           assigned_equipment=assigned_equipment,
                           all_divisions_summary=all_divisions_summary,
                           total_stats=total_stats,
                           user_name=session.get('user_name'),
                           division_name=session.get('division_name'))
                           
    except Exception as e:
        flash(f'Error loading equipment page: {str(e)}', 'error')
        return redirect(url_for('division_dashboard'))
    
@app.route('/add_equipment', methods=['POST'])
def add_equipment():
    # FIX: Change from 'division_head_id' to 'user_id'
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        data = request.get_json()
        head_id = session['user_id'] 
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Call stored procedure
        cursor.callproc('AddNewEquipment', [
            data['serial_no'],
            data['name_of_equipment'],
            data['model_no'],
            data['purchase_date'],
            float(data['equipment_cost']),
            data['calibration_date'],
            int(data['division_id']),
            data.get('remarks', '')
        ])
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Equipment added successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding equipment: {str(e)}'})
@app.route('/handle_equipment_request', methods=['POST'])
def handle_equipment_request():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        data = request.get_json()
        history_id = data['history_id']
        action = data['action']  # 'approve' or 'reject'
        head_id = session['user_id']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get request details
        cursor.execute("SELECT * FROM equipment_requests_view WHERE history_id = %s", (history_id,))
        request_data = cursor.fetchone()
        
        if not request_data:
            return jsonify({'success': False, 'message': 'Request not found'})
        
        if action == 'approve':
            # Update equipment history with head_id
            cursor.execute("""
                UPDATE Equipment_History 
                SET action_type = 'issued', action_by_head_id = %s 
                WHERE history_id = %s
            """, (head_id, history_id))
            
            # Update equipment assignment
            cursor.execute("""
                UPDATE Electrical_Equipment 
                SET current_worker_id = %s, 
                    issue_date = CURDATE(),
                    expected_return_date = %s
                WHERE equipment_id = %s
            """, (request_data['worker_id'], request_data['expected_return_date'], request_data['equipment_id']))
            
            # Create notification for worker
            cursor.execute("""
                INSERT INTO Notifications (worker_id, message, created_at)
                VALUES (%s, %s, NOW())
            """, (request_data['worker_id'], 
                  f'Your equipment request for "{request_data["name_of_equipment"]}" has been approved and issued.'))
            
            message = 'Equipment request approved successfully'
            
        else:  # reject
            cursor.execute("""
                UPDATE Equipment_History 
                SET action_type = 'rejected', action_by_head_id = %s 
                WHERE history_id = %s
            """, (head_id, history_id))
            
            # Create notification for worker
            cursor.execute("""
                INSERT INTO Notifications (worker_id, message, created_at)
                VALUES (%s, %s, NOW())
            """, (request_data['worker_id'], 
                  f'Your equipment request for "{request_data["name_of_equipment"]}" has been rejected.'))
            
            message = 'Equipment request rejected'
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error handling request: {str(e)}'})
@app.route('/issue_equipment_direct', methods=['POST'])
def issue_equipment_direct():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        data = request.get_json()
        head_id = session['user_id']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Create equipment history record
        cursor.execute("""
            INSERT INTO Equipment_History 
            (equipment_id, worker_id, action_type, action_by_head_id, purpose, expected_return_date, notes)
            VALUES (%s, %s, 'issued', %s, %s, %s, %s)
        """, (
            data['equipment_id'],
            data['worker_id'],
            head_id,
            data.get('purpose', 'Direct assignment by division head'),
            data['expected_return_date'],
            data.get('notes', '')
        ))
        
        # Update equipment assignment (can assign equipment from any division)
        cursor.execute("""
            UPDATE Electrical_Equipment 
            SET current_worker_id = %s, 
                issue_date = CURDATE(),
                expected_return_date = %s
            WHERE equipment_id = %s
        """, (data['worker_id'], data['expected_return_date'], data['equipment_id']))
        
        # Update worker availability
        cursor.execute("""
            UPDATE Workers 
            SET availability = 'On Task' 
            WHERE worker_id = %s
        """, (data['worker_id'],))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Equipment issued successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error issuing equipment: {str(e)}'})
    
@app.route('/return_equipment', methods=['POST'])
def return_equipment():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        # Check if it's JSON data
        if request.is_json:
            data = request.get_json()
        else:
            # Fallback to form data
            data = request.form.to_dict()
        
        head_id = session['user_id']
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get equipment details
        cursor.execute("SELECT * FROM Electrical_Equipment WHERE equipment_id = %s", (data['equipment_id'],))
        equipment = cursor.fetchone()
        
        if not equipment:
            return jsonify({'success': False, 'message': 'Equipment not found'})
        
        # Create return history record
        cursor.execute("""
            INSERT INTO Equipment_History 
            (equipment_id, worker_id, action_type, action_by_head_id, purpose, actual_return_date, notes)
            VALUES (%s, %s, 'returned', %s, %s, CURDATE(), %s)
        """, (
            data['equipment_id'],
            equipment['current_worker_id'],
            head_id,
            'Equipment return',
            data.get('notes', 'Returned by division head')
        ))
        
        # Update equipment to available
        cursor.execute("""
            UPDATE Electrical_Equipment 
            SET current_worker_id = NULL, 
                issue_date = NULL,
                expected_return_date = NULL,
                re_issue_date = NULL
            WHERE equipment_id = %s
        """, (data['equipment_id'],))
        
        # Update worker availability only if worker exists
        if equipment['current_worker_id']:
            cursor.execute("""
                UPDATE Workers 
                SET availability = 'Available' 
                WHERE worker_id = %s
            """, (equipment['current_worker_id'],))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'message': 'Equipment returned successfully'})
        
    except Exception as e:
        print(f"Error returning equipment: {str(e)}")
        # Ensure we return proper JSON even on error
        return jsonify({'success': False, 'message': f'Error returning equipment: {str(e)}'})
    
@app.route('/get_equipment_history/<int:equipment_id>')
def get_equipment_history(equipment_id):
    # FIX: Change from 'division_head_id' to 'user_id'
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM equipment_history_view 
            WHERE equipment_id = %s 
            ORDER BY action_date DESC
        """, (equipment_id,))
        
        history = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'history': history})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching history: {str(e)}'})
    
@app.route('/division/profile')
def division_profile():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return redirect(url_for('login'))
    
    division_id = session['division_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get division name
        cursor.execute("SELECT division_name FROM Divisions WHERE division_id = %s", (division_id,))
        division = cursor.fetchone()
        division_name = division['division_name'] if division else 'Division'
        
        # Get division head info with current email and phone
        cursor.execute("""
            SELECT head_id, division_id, name, email, phone, is_active
            FROM Division_Heads 
            WHERE head_id = %s
        """, (session['user_id'],))
        user_info = cursor.fetchone()
        
        return render_template('division_profile.html',
                           user_name=session['user_name'],
                           division_name=division_name,
                           user_info=user_info or {})
                           
    except Exception as e:
        print(f"Error loading profile: {str(e)}")
        flash(f'Error loading profile: {str(e)}', 'error')
        
        # Provide safe fallback data
        safe_user_info = {
            'head_id': session['user_id'],
            'name': session['user_name'],
            'email': 'Unknown',
            'phone': 'Unknown',
            'is_active': True,
            'division_id': division_id
        }
        
        return render_template('division_profile.html',
                           user_name=session['user_name'],
                           division_name=session.get('division_name', 'Division'),
                           user_info=safe_user_info)
    finally:
        cursor.close()
        conn.close()
@app.route('/api/division/assign-worker', methods=['POST'])
def division_assign_worker():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    issue_id = request.form.get('issue_id')
    worker_id = request.form.get('worker_id')
    worker_notes = request.form.get('worker_notes', '')
    assigned_by = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if issue already has assigned worker
        cursor.execute("SELECT * FROM IssueWorkers WHERE issue_id = %s", (issue_id,))
        existing_assignment = cursor.fetchone()
        
        if existing_assignment:
            # Update existing assignment
            cursor.execute("""
                UPDATE IssueWorkers 
                SET worker_id = %s, assigned_by = %s, worker_notes = %s, 
                    worker_status = 'assigned', assigned_at = CURRENT_TIMESTAMP
                WHERE issue_id = %s
            """, (worker_id, assigned_by, worker_notes, issue_id))
        else:
            # Create new assignment
            cursor.execute("""
                INSERT INTO IssueWorkers (issue_id, worker_id, assigned_by, worker_status, worker_notes)
                VALUES (%s, %s, %s, 'assigned', %s)
            """, (issue_id, worker_id, assigned_by, worker_notes))
        
        # Update worker availability
        cursor.execute("UPDATE Workers SET availability = 'On Task' WHERE worker_id = %s", (worker_id,))
        
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()

# ========== API ROUTES ==========
@app.route('/api/public_stats')
def public_stats():
    """API for public statistics"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM System_Stats_View")
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify(stats)
    return jsonify({})

@app.route('/api/raise-issue', methods=['POST'])
def raise_issue():
    """API endpoint to handle issue submission using stored procedure"""
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get form data
        title = request.form['title']
        issue_type = request.form['issue_type']
        description = request.form['description']
        priority = request.form['priority']
        address_line1 = request.form['address_line1']
        address_line2 = request.form.get('address_line2', '')
        division_id = request.form.get('division_id')
        
        # Get latitude and longitude (optional)
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        
        # Convert to decimal if provided
        latitude = float(latitude) if latitude else None
        longitude = float(longitude) if longitude else None
        
        # Get user's division if not provided
        if not division_id or division_id == '':
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT division_id FROM Users WHERE user_id = %s", (session.get('user_id'),))
                user_data = cursor.fetchone()
                division_id = user_data['division_id'] if user_data and user_data['division_id'] else None
                cursor.close()
                conn.close()
        
        # Convert division_id to int or None
        division_id = int(division_id) if division_id and division_id != '' else None
        
        print(f"DEBUG: Raising issue with user_id: {session.get('user_id')}, division_id: {division_id}")
        
        # Use stored procedure to raise issue
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Call the stored procedure
            cursor.callproc('RaiseNewIssue', [
                session.get('user_id'), 
                division_id, 
                address_line1, 
                address_line2 or '',
                latitude, 
                longitude, 
                issue_type, 
                title, 
                description, 
                priority
            ])
            
            # Get the result from the procedure
            issue_id = None
            for result in cursor.stored_results():
                procedure_result = result.fetchone()
                if procedure_result:
                    issue_id = procedure_result['issue_id']
                break
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if issue_id:
                return jsonify({'success': True, 'issue_id': issue_id})
            else:
                return jsonify({'success': False, 'error': 'Failed to create issue via procedure'}), 500
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error raising issue: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500
    
# API route to get issue details for the modal
@app.route('/api/issue-details/<int:issue_id>')
def get_issue_details(issue_id):
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get detailed issue information with worker assignments
            cursor.execute("""
                SELECT 
                    i.issue_id, i.title, i.issue_type, i.description, i.status, i.priority,
                    i.created_at, i.resolved_at, i.latitude, i.longitude,
                    d.division_name,
                    COUNT(iw.worker_id) as assigned_workers_count,
                    GROUP_CONCAT(DISTINCT w.name SEPARATOR ', ') as assigned_worker_names,
                    GROUP_CONCAT(DISTINCT w.email SEPARATOR ', ') as assigned_worker_emails
                FROM Issues i
                JOIN Divisions d ON i.division_id = d.division_id
                LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id AND iw.worker_status != 'completed'
                LEFT JOIN Workers w ON iw.worker_id = w.worker_id
                WHERE i.issue_id = %s AND i.user_id = %s
                GROUP BY i.issue_id, i.title, i.issue_type, i.description, i.status, i.priority, 
                         i.created_at, i.resolved_at, i.latitude, i.longitude, d.division_name
            """, (issue_id, session.get('user_id')))
            
            issue = cursor.fetchone()
            
            if issue:
                return jsonify({'success': True, 'issue': issue})
            else:
                return jsonify({'success': False, 'error': 'Issue not found'}), 404
                
        except Exception as e:
            print(f"Error fetching issue details: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500

# API route to log issue views
@app.route('/api/log-issue-view', methods=['POST'])
def log_issue_view():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        data = request.get_json()
        issue_id = data.get('issue_id')
        action_type = data.get('action_type', 'VIEWED')
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Issue_Audit_Log (issue_id, action_type, changed_by, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
            """, (issue_id, action_type, session.get('user_id'), 
                  request.remote_addr, request.headers.get('User-Agent')))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error logging issue view: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    

# Route to display edit issue page
@app.route('/edit-issue/<int:issue_id>')
def edit_issue_page(issue_id):
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM Issues 
                WHERE issue_id = %s AND user_id = %s AND status = 'pending'
            """, (issue_id, session.get('user_id')))
            
            issue = cursor.fetchone()
            
            if issue:
                return render_template('edit_issue.html', 
                                     issue=issue, 
                                     user_name=session.get('user_name'))
            else:
                flash('Issue not found or cannot be edited.', 'error')
                return redirect(url_for('track_issues'))
                
        except Exception as e:
            print(f"Error fetching issue for editing: {e}")
            flash('Error loading issue for editing.', 'error')
            return redirect(url_for('track_issues'))
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Database connection failed.', 'error')
        return redirect(url_for('track_issues'))

# API route to update issue
@app.route('/api/update-issue/<int:issue_id>', methods=['POST'])
def update_issue(issue_id):
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        # Get form data
        title = request.form['title']
        issue_type = request.form['issue_type']
        description = request.form['description']
        priority = request.form['priority']
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Issues 
                SET title = %s, issue_type = %s, description = %s, priority = %s
                WHERE issue_id = %s AND user_id = %s AND status = 'pending'
            """, (title, issue_type, description, priority, issue_id, session.get('user_id')))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Issue updated successfully!', 'success')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except Exception as e:
        print(f"Error updating issue: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API route to get audit log
@app.route('/api/issue-audit-log/<int:issue_id>')
def get_issue_audit_log(issue_id):
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT action_type, old_values, new_values, changed_at
                FROM Issue_Audit_Log
                WHERE issue_id = %s
                ORDER BY changed_at DESC
                LIMIT 10
            """, (issue_id,))
            
            logs = cursor.fetchall()
            return jsonify({'success': True, 'logs': logs})
                
        except Exception as e:
            print(f"Error fetching audit log: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cursor.close()
            conn.close()
    else:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

# ========== UTILITY ROUTES ==========
@app.route('/test-data')
def test_data():
    """Test route to check database connection and data"""
    conn = get_db_connection()
    if not conn:
        return "❌ Database connection failed"
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT COUNT(*) as count FROM Users")
        users = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM Workers")
        workers = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM Issues")
        issues = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM Divisions")
        divisions = cursor.fetchone()
        
        result = f"""
        <h1>Database Test Results</h1>
        <p>Users: {users['count']}</p>
        <p>Workers: {workers['count']}</p>
        <p>Issues: {issues['count']}</p>
        <p>Divisions: {divisions['count']}</p>
        <p>Database Connection: ✅ Success</p>
        <p><a href="/">Back to Home</a></p>
        """
        
    except Exception as e:
        result = f"❌ Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()
    
    return result

@app.route('/api/division/update-issue-priority', methods=['POST'])
def division_update_priority():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    issue_id = request.form.get('issue_id')
    priority = request.form.get('priority')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE Issues SET priority = %s WHERE issue_id = %s", (priority, issue_id))
        conn.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()

# API route to get issue details

@app.route('/api/division/issue-details/<int:issue_id>')
def division_issue_details(issue_id):
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                i.*,
                u.name as user_name,
                u.phone as user_phone,
                u.email as user_email,
                w.name as worker_name,
                w.worker_type,
                w.phone_no as worker_phone,
                iw.worker_status,
                iw.worker_notes,
                iw.assigned_at,
                iw.completed_at,
                dh.name as assigned_by_name
            FROM Issues i
            LEFT JOIN Users u ON i.user_id = u.user_id
            LEFT JOIN IssueWorkers iw ON i.issue_id = iw.issue_id
            LEFT JOIN Workers w ON iw.worker_id = w.worker_id
            LEFT JOIN Division_Heads dh ON iw.assigned_by = dh.head_id
            WHERE i.issue_id = %s
        """, (issue_id,))
        
        issue_details = cursor.fetchone()
        
        if issue_details:
            return jsonify({'success': True, 'data': issue_details})
        else:
            return jsonify({'success': False, 'error': 'Issue not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()

# API route to add new worker
@app.route('/api/division/add-worker', methods=['POST'])
def division_add_worker():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        name = request.form['name']
        email = request.form['email']
        phone_no = request.form['phone_no']
        age = request.form.get('age')
        address = request.form.get('address', '')
        worker_type = request.form['worker_type']
        skill_sets = request.form.get('skill_sets', '')
        password = request.form['password']
        division_id = session['division_id']
        created_by = session['user_id']
        
        # Convert age to int if provided
        age = int(age) if age and age.isdigit() else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Call the stored procedure
        cursor.callproc('AddDivisionWorker', [
            name, email, phone_no, age, address, worker_type, 
            skill_sets, password, division_id, created_by
        ])
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Worker added successfully'})
        
    except mysql.connector.Error as e:
        return jsonify({'success': False, 'error': f'Database error: {e}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API route to remove worker (soft delete)
# API route to remove worker (soft delete)
@app.route('/api/division/remove-worker', methods=['POST'])
def division_remove_worker():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    worker_id = request.form.get('worker_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Set session variable for trigger
        cursor.execute("SET @current_user_id = %s", (session['user_id'],))
        
        # Soft delete the worker - set is_active to FALSE
        cursor.execute("""
            UPDATE Workers 
            SET is_active = FALSE, availability = 'Other', current_task_status = 'Inactive'
            WHERE worker_id = %s AND division_id = %s
        """, (worker_id, session['division_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Worker removed successfully'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})

# API route to update worker details
@app.route('/api/division/update-worker', methods=['POST'])
def division_update_worker():
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        worker_id = request.form['worker_id']
        name = request.form['name']
        email = request.form['email']
        phone_no = request.form['phone_no']
        age = request.form.get('age')
        address = request.form.get('address', '')
        worker_type = request.form['worker_type']
        skill_sets = request.form.get('skill_sets', '')
        availability = request.form['availability']
        
        age = int(age) if age and age.isdigit() else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE Workers 
            SET name = %s, email = %s, phone_no = %s, age = %s, address = %s,
                worker_type = %s, skill_sets = %s, availability = %s
            WHERE worker_id = %s AND division_id = %s AND is_active = TRUE
        """, (name, email, phone_no, age, address, worker_type, skill_sets, availability, 
              worker_id, session['division_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Worker updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# API route to get worker details
@app.route('/api/division/worker-details/<int:worker_id>')
def division_worker_details(worker_id):
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get worker details with accurate task counts
        cursor.execute("""
            SELECT 
                w.*,
                d.division_name,
                COUNT(iw.issue_id) as total_tasks,
                SUM(CASE WHEN iw.worker_status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN iw.worker_status IN ('assigned', 'in_progress') THEN 1 ELSE 0 END) as active_tasks,
                ROUND((SUM(CASE WHEN iw.worker_status = 'completed' THEN 1 ELSE 0 END) / 
                      NULLIF(COUNT(iw.issue_id), 0)) * 100, 2) as completion_rate
            FROM Workers w
            LEFT JOIN Divisions d ON w.division_id = d.division_id
            LEFT JOIN IssueWorkers iw ON w.worker_id = iw.worker_id
            WHERE w.worker_id = %s AND w.division_id = %s AND w.is_active = TRUE
            GROUP BY w.worker_id, w.name, w.email, w.phone_no, w.age, w.address, 
                     w.worker_type, w.skill_sets, w.availability, w.current_task_status,
                     w.created_at, d.division_name
        """, (worker_id, session['division_id']))
        
        worker = cursor.fetchone()
        
        if worker:
            # Generate HTML for modal
            html_content = f"""
                <div class="row">
                    <div class="col-md-6">
                        <h6>Personal Information</h6>
                        <p><strong>Name:</strong> {worker['name']}</p>
                        <p><strong>Email:</strong> {worker['email']}</p>
                        <p><strong>Phone:</strong> {worker['phone_no']}</p>
                        <p><strong>Age:</strong> {worker['age'] or 'Not specified'}</p>
                        <p><strong>Address:</strong> {worker['address'] or 'Not specified'}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Work Information</h6>
                        <p><strong>Type:</strong> {worker['worker_type']}</p>
                        <p><strong>Availability:</strong> {worker['availability']}</p>
                        <p><strong>Skill Sets:</strong> {worker['skill_sets'] or 'Not specified'}</p>
                        <p><strong>Division:</strong> {worker['division_name']}</p>
                        <p><strong>Member Since:</strong> {worker['created_at'].strftime('%Y-%m-%d')}</p>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-12">
                        <h6>Task Statistics</h6>
                        <p><strong>Total Tasks:</strong> {worker['total_tasks']}</p>
                        <p><strong>Completed Tasks:</strong> {worker['completed_tasks']}</p>
                        <p><strong>Active Tasks:</strong> {worker['active_tasks']}</p>
                        <p><strong>Completion Rate:</strong> {worker['completion_rate'] or 0}%</p>
                    </div>
                </div>
            """
            return jsonify({'success': True, 'html': html_content})
        else:
            return jsonify({'success': False, 'error': 'Worker not found'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()



# ========== DIVISION HEAD PROFILE ROUTES ==========

# ========== DIVISION HEAD PROFILE ROUTES ==========

@app.route('/api/division/update-profile', methods=['POST'])
def division_update_profile():
    """API endpoint to update division head profile"""
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        
        # Basic validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'error': 'Please enter a valid email address'}), 400
        
        if not re.match(r'^[0-9]{10}$', phone):
            return jsonify({'success': False, 'error': 'Phone number must be exactly 10 digits'}), 400
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Check if email already exists (excluding current user)
            cursor.execute("""
                SELECT head_id FROM Division_Heads 
                WHERE email = %s AND head_id != %s
            """, (email, session['user_id']))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'An account with this email already exists'}), 400
            
            # Check if phone already exists (excluding current user)
            cursor.execute("""
                SELECT head_id FROM Division_Heads 
                WHERE phone = %s AND head_id != %s
            """, (phone, session['user_id']))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'An account with this phone number already exists'}), 400
            
            # Update profile
            cursor.execute("""
                UPDATE Division_Heads 
                SET name = %s, email = %s, phone = %s
                WHERE head_id = %s
            """, (name, email, phone, session['user_id']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Update session name if changed
            if session.get('user_name') != name:
                session['user_name'] = name
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except mysql.connector.Error as e:
        print(f"Error updating division head profile: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    except Exception as e:
        print(f"Error updating division head profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/division/change-password', methods=['POST'])
def division_change_password():
    """API endpoint to change division head password"""
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
    
    try:
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Validate passwords match
        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'New passwords do not match'}), 400
        
        # Validate password length
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Verify current password
            cursor.execute("""
                SELECT head_id FROM Division_Heads 
                WHERE head_id = %s AND password = %s
            """, (session['user_id'], current_password))
            
            user = cursor.fetchone()
            
            if not user:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
            
            # Update password
            update_cursor = conn.cursor()
            update_cursor.execute("""
                UPDATE Division_Heads 
                SET password = %s 
                WHERE head_id = %s
            """, (new_password, session['user_id']))
            
            conn.commit()
            cursor.close()
            update_cursor.close()
            conn.close()
            
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
            
    except mysql.connector.Error as e:
        print(f"Error changing division head password: {e}")
        return jsonify({'success': False, 'error': f'Database error: {e}'}), 500
    except Exception as e:
        print(f"Error changing division head password: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/division/all-equipment-stats')
def division_all_equipment_stats():
    """API endpoint to get equipment statistics for all divisions"""
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all divisions equipment summary
        cursor.execute("SELECT * FROM all_divisions_equipment_summary")
        all_divisions_summary = cursor.fetchall()
        
        # Get total statistics across all divisions
        cursor.execute("""
            SELECT 
                COUNT(*) as total_equipment_all,
                COUNT(CASE WHEN current_worker_id IS NULL THEN 1 END) as available_equipment_all,
                COUNT(CASE WHEN current_worker_id IS NOT NULL THEN 1 END) as assigned_equipment_all,
                SUM(equipment_cost) as total_value_all,
                AVG(equipment_cost) as avg_cost_all
            FROM Electrical_Equipment
        """)
        total_stats = cursor.fetchone()
        
        return jsonify({
            'success': True, 
            'all_divisions_summary': all_divisions_summary,
            'total_stats': total_stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/division/all-available-equipment')
def division_all_available_equipment():
    """API endpoint to get available equipment from all divisions"""
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM all_divisions_available_equipment")
        available_equipment = cursor.fetchall()
        
        return jsonify({'success': True, 'available_equipment': available_equipment})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()
@app.route('/api/division/logs-data')
def division_logs_data():
    """API endpoint to get filtered logs data"""
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    division_id = session['division_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get filter parameters
        log_type = request.args.get('log_type', 'security')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        
        # Build base queries for each log type - ONLY CURRENT DIVISION
        queries = {
            'security': """
                SELECT f.attempt_id, f.email, f.attempted_at, f.ip_address, 
                       CASE 
                           WHEN dh.head_id IS NOT NULL THEN 'Division Head'
                           WHEN w.worker_id IS NOT NULL THEN 'Worker'
                           WHEN u.user_id IS NOT NULL THEN 'User'
                           ELSE 'Unknown'
                       END as user_type
                FROM Failed_Login_Attempts f
                LEFT JOIN Division_Heads dh ON f.email = dh.email AND dh.division_id = %s
                LEFT JOIN Workers w ON f.email = w.email AND w.division_id = %s
                LEFT JOIN Users u ON f.email = u.email AND u.division_id = %s
                WHERE f.division_id = %s
            """,
            'issue': """
                SELECT ial.log_id, ial.issue_id, ial.action_type, 
                       ial.old_values, ial.new_values, ial.changed_at,
                       u.name as changed_by_name
                FROM Issue_Audit_Log ial
                JOIN Issues i ON ial.issue_id = i.issue_id
                LEFT JOIN Users u ON ial.changed_by = u.user_id
                WHERE i.division_id = %s
            """,
            'user': """
                SELECT ual.audit_id, ual.user_id, ual.action_type, 
                       ual.old_values, ual.new_values, ual.changed_at,
                       u.name as user_name
                FROM User_Audit_Log ual
                JOIN Users u ON ual.user_id = u.user_id
                WHERE u.division_id = %s
            """,
            'signup': """
                SELECT usl.log_id, usl.user_id, usl.signup_time, 
                       usl.ip_address, usl.city, usl.pincode,
                       u.name as user_name
                FROM User_Signup_Log usl
                JOIN Users u ON usl.user_id = u.user_id
                WHERE usl.division_id = %s
            """,
            'worker': """
                SELECT wal.log_id, wal.worker_id, wal.action_type, 
                       wal.description, wal.created_at,
                       w.name as worker_name
                FROM Worker_Audit_Log wal
                JOIN Workers w ON wal.worker_id = w.worker_id
                WHERE w.division_id = %s
            """,
            'equipment': """
                SELECT el.log_id, el.equipment_id, el.action_type, 
                       el.notes, el.created_at,
                       ee.name_of_equipment, ee.serial_no,
                       w.name as worker_name, dh.name as head_name
                FROM Equipment_Logs el
                JOIN Electrical_Equipment ee ON el.equipment_id = ee.equipment_id
                LEFT JOIN Workers w ON el.worker_id = w.worker_id
                LEFT JOIN Division_Heads dh ON el.action_by_head_id = dh.head_id
                WHERE ee.division_id = %s
            """
        }
        
        if log_type not in queries:
            return jsonify({'success': False, 'error': 'Invalid log type'})
        
        query = queries[log_type]
        
        # Set parameters based on log type
        if log_type == 'security':
            params = [division_id, division_id, division_id, division_id]
        else:
            params = [division_id]
        
        # Add date filter
        date_column = 'attempted_at' if log_type == 'security' else 'changed_at' if log_type in ['issue', 'user'] else 'signup_time' if log_type == 'signup' else 'created_at'
        
        if date_from:
            query += f" AND DATE({date_column}) >= %s"
            params.append(date_from)
        if date_to:
            query += f" AND DATE({date_column}) <= %s"
            params.append(date_to)
        
        # Add search filter
        if search:
            if log_type == 'security':
                query += " AND (f.email LIKE %s OR f.ip_address LIKE %s)"
            elif log_type == 'issue':
                query += " AND (ial.action_type LIKE %s OR u.name LIKE %s)"
            elif log_type == 'user':
                query += " AND (ual.action_type LIKE %s OR u.name LIKE %s)"
            elif log_type == 'signup':
                query += " AND (u.name LIKE %s OR usl.city LIKE %s OR usl.pincode LIKE %s)"
            elif log_type == 'worker':
                query += " AND (wal.action_type LIKE %s OR w.name LIKE %s OR wal.description LIKE %s)"
            elif log_type == 'equipment':
                query += " AND (el.action_type LIKE %s OR ee.name_of_equipment LIKE %s OR w.name LIKE %s OR dh.name LIKE %s)"
            
            search_term = f"%{search}%"
            if log_type in ['security', 'issue', 'user']:
                params.extend([search_term, search_term])
            elif log_type == 'signup':
                params.extend([search_term, search_term, search_term])
            elif log_type == 'worker':
                params.extend([search_term, search_term, search_term])
            elif log_type == 'equipment':
                params.extend([search_term, search_term, search_term, search_term])
        
        # Add column-specific filters
        for key, value in request.args.items():
            if key not in ['log_type', 'date_from', 'date_to', 'search', 'limit', 'export'] and value:
                if log_type == 'security' and key in ['email', 'ip_address', 'user_type']:
                    query += f" AND f.{key} LIKE %s"
                    params.append(f"%{value}%")
                elif log_type == 'issue' and key in ['issue_id', 'action_type', 'changed_by_name']:
                    if key == 'issue_id':
                        query += f" AND ial.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'user' and key in ['user_id', 'user_name', 'action_type']:
                    if key == 'user_id':
                        query += f" AND ual.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'signup' and key in ['user_id', 'user_name', 'city', 'pincode']:
                    if key == 'user_id':
                        query += f" AND usl.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'worker' and key in ['worker_id', 'worker_name', 'action_type']:
                    if key == 'worker_id':
                        query += f" AND wal.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'equipment' and key in ['equipment_id', 'name_of_equipment', 'worker_name', 'action_type']:
                    if key == 'equipment_id':
                        query += f" AND el.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
        
        # Add ordering and limit
        query += f" ORDER BY {date_column} DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        # Convert datetime objects to strings for JSON serialization
        for row in data:
            for key, value in row.items():
                if isinstance(value, datetime):
                    row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    row[key] = ''
        
        return jsonify({'success': True, 'data': data})
        
    except Exception as e:
        print(f"Error fetching logs data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()



@app.route('/api/division/export-logs')
def export_logs():
    """Export logs to CSV"""
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    division_id = session['division_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get filter parameters
        log_type = request.args.get('log_type', 'security')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        search = request.args.get('search', '')
        
        # Build base queries for each log type - ONLY CURRENT DIVISION
        queries = {
            'security': """
                SELECT f.attempt_id, f.email, f.attempted_at, f.ip_address, 
                       CASE 
                           WHEN dh.head_id IS NOT NULL THEN 'Division Head'
                           WHEN w.worker_id IS NOT NULL THEN 'Worker'
                           WHEN u.user_id IS NOT NULL THEN 'User'
                           ELSE 'Unknown'
                       END as user_type
                FROM Failed_Login_Attempts f
                LEFT JOIN Division_Heads dh ON f.email = dh.email AND dh.division_id = %s
                LEFT JOIN Workers w ON f.email = w.email AND w.division_id = %s
                LEFT JOIN Users u ON f.email = u.email AND u.division_id = %s
                WHERE f.division_id = %s
            """,
            'issue': """
                SELECT ial.log_id, ial.issue_id, ial.action_type, 
                       ial.old_values, ial.new_values, ial.changed_at,
                       u.name as changed_by_name
                FROM Issue_Audit_Log ial
                JOIN Issues i ON ial.issue_id = i.issue_id
                LEFT JOIN Users u ON ial.changed_by = u.user_id
                WHERE i.division_id = %s
            """,
            'user': """
                SELECT ual.audit_id, ual.user_id, ual.action_type, 
                       ual.old_values, ual.new_values, ual.changed_at,
                       u.name as user_name
                FROM User_Audit_Log ual
                JOIN Users u ON ual.user_id = u.user_id
                WHERE u.division_id = %s
            """,
            'signup': """
                SELECT usl.log_id, usl.user_id, usl.signup_time, 
                       usl.ip_address, usl.city, usl.pincode,
                       u.name as user_name
                FROM User_Signup_Log usl
                JOIN Users u ON usl.user_id = u.user_id
                WHERE usl.division_id = %s
            """,
            'worker': """
                SELECT wal.log_id, wal.worker_id, wal.action_type, 
                       wal.description, wal.created_at,
                       w.name as worker_name
                FROM Worker_Audit_Log wal
                JOIN Workers w ON wal.worker_id = w.worker_id
                WHERE w.division_id = %s
            """,
            'equipment': """
                SELECT el.log_id, el.equipment_id, el.action_type, 
                       el.notes, el.created_at,
                       ee.name_of_equipment, ee.serial_no,
                       w.name as worker_name, dh.name as head_name
                FROM Equipment_Logs el
                JOIN Electrical_Equipment ee ON el.equipment_id = ee.equipment_id
                LEFT JOIN Workers w ON el.worker_id = w.worker_id
                LEFT JOIN Division_Heads dh ON el.action_by_head_id = dh.head_id
                WHERE ee.division_id = %s
            """
        }
        
        if log_type not in queries:
            return jsonify({'success': False, 'error': 'Invalid log type'})
        
        query = queries[log_type]
        
        # Set parameters based on log type
        if log_type == 'security':
            params = [division_id, division_id, division_id, division_id]
        else:
            params = [division_id]
        
        # Add date filter
        date_column = 'attempted_at' if log_type == 'security' else 'changed_at' if log_type in ['issue', 'user'] else 'signup_time' if log_type == 'signup' else 'created_at'
        
        if date_from:
            query += f" AND DATE({date_column}) >= %s"
            params.append(date_from)
        if date_to:
            query += f" AND DATE({date_column}) <= %s"
            params.append(date_to)
        
        # Add search filter
        if search:
            if log_type == 'security':
                query += " AND (f.email LIKE %s OR f.ip_address LIKE %s)"
            elif log_type == 'issue':
                query += " AND (ial.action_type LIKE %s OR u.name LIKE %s)"
            elif log_type == 'user':
                query += " AND (ual.action_type LIKE %s OR u.name LIKE %s)"
            elif log_type == 'signup':
                query += " AND (u.name LIKE %s OR usl.city LIKE %s OR usl.pincode LIKE %s)"
            elif log_type == 'worker':
                query += " AND (wal.action_type LIKE %s OR w.name LIKE %s OR wal.description LIKE %s)"
            elif log_type == 'equipment':
                query += " AND (el.action_type LIKE %s OR ee.name_of_equipment LIKE %s OR w.name LIKE %s OR dh.name LIKE %s)"
            
            search_term = f"%{search}%"
            if log_type in ['security', 'issue', 'user']:
                params.extend([search_term, search_term])
            elif log_type == 'signup':
                params.extend([search_term, search_term, search_term])
            elif log_type == 'worker':
                params.extend([search_term, search_term, search_term])
            elif log_type == 'equipment':
                params.extend([search_term, search_term, search_term, search_term])
        
        # Add column-specific filters
        for key, value in request.args.items():
            if key not in ['log_type', 'date_from', 'date_to', 'search', 'limit', 'export'] and value:
                if log_type == 'security' and key in ['email', 'ip_address', 'user_type']:
                    query += f" AND f.{key} LIKE %s"
                    params.append(f"%{value}%")
                elif log_type == 'issue' and key in ['issue_id', 'action_type', 'changed_by_name']:
                    if key == 'issue_id':
                        query += f" AND ial.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'user' and key in ['user_id', 'user_name', 'action_type']:
                    if key == 'user_id':
                        query += f" AND ual.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'signup' and key in ['user_id', 'user_name', 'city', 'pincode']:
                    if key == 'user_id':
                        query += f" AND usl.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'worker' and key in ['worker_id', 'worker_name', 'action_type']:
                    if key == 'worker_id':
                        query += f" AND wal.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
                elif log_type == 'equipment' and key in ['equipment_id', 'name_of_equipment', 'worker_name', 'action_type']:
                    if key == 'equipment_id':
                        query += f" AND el.{key} = %s"
                        params.append(int(value))
                    else:
                        query += f" AND {key} LIKE %s"
                        params.append(f"%{value}%")
        
        # Add ordering - no limit for export
        query += f" ORDER BY {date_column} DESC"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        # Define CSV headers for each log type
        csv_headers = {
            'security': ['Attempt ID', 'Email', 'Attempt Time', 'IP Address', 'User Type'],
            'issue': ['Log ID', 'Issue ID', 'Action Type', 'Old Values', 'New Values', 'Changed At', 'Changed By'],
            'user': ['Audit ID', 'User ID', 'Action Type', 'Old Values', 'New Values', 'Changed At', 'User Name'],
            'signup': ['Log ID', 'User ID', 'Signup Time', 'IP Address', 'City', 'Pincode', 'User Name'],
            'worker': ['Log ID', 'Worker ID', 'Action Type', 'Description', 'Created At', 'Worker Name'],
            'equipment': ['Log ID', 'Equipment ID', 'Action Type', 'Notes', 'Created At', 'Equipment Name', 'Serial No', 'Worker Name', 'Head Name']
        }
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = csv_headers.get(log_type, [])
        writer.writerow(headers)
        
        # Write data rows
        for row in data:
            csv_row = []
            if log_type == 'security':
                csv_row = [
                    row['attempt_id'],
                    row['email'],
                    row['attempted_at'].strftime('%Y-%m-%d %H:%M:%S') if row['attempted_at'] else '',
                    row['ip_address'],
                    row['user_type']
                ]
            elif log_type == 'issue':
                csv_row = [
                    row['log_id'],
                    row['issue_id'],
                    row['action_type'],
                    str(row['old_values'])[:100] if row['old_values'] else '',
                    str(row['new_values'])[:100] if row['new_values'] else '',
                    row['changed_at'].strftime('%Y-%m-%d %H:%M:%S') if row['changed_at'] else '',
                    row['changed_by_name'] or ''
                ]
            elif log_type == 'user':
                csv_row = [
                    row['audit_id'],
                    row['user_id'],
                    row['action_type'],
                    str(row['old_values'])[:100] if row['old_values'] else '',
                    str(row['new_values'])[:100] if row['new_values'] else '',
                    row['changed_at'].strftime('%Y-%m-%d %H:%M:%S') if row['changed_at'] else '',
                    row['user_name']
                ]
            elif log_type == 'signup':
                csv_row = [
                    row['log_id'],
                    row['user_id'],
                    row['signup_time'].strftime('%Y-%m-%d %H:%M:%S') if row['signup_time'] else '',
                    row['ip_address'],
                    row['city'],
                    row['pincode'],
                    row['user_name']
                ]
            elif log_type == 'worker':
                csv_row = [
                    row['log_id'],
                    row['worker_id'],
                    row['action_type'],
                    row['description'][:100] if row['description'] else '',
                    row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
                    row['worker_name']
                ]
            elif log_type == 'equipment':
                csv_row = [
                    row['log_id'],
                    row['equipment_id'],
                    row['action_type'],
                    row['notes'][:100] if row['notes'] else '',
                    row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
                    row['name_of_equipment'],
                    row['serial_no'],
                    row['worker_name'] or '',
                    row['head_name'] or ''
                ]
            
            writer.writerow(csv_row)
        
        # Prepare response
        output.seek(0)
        
        # Create filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{log_type}_logs_{timestamp}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-type": "text/csv"
            }
        )
        
    except Exception as e:
        print(f"Error exporting logs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/division/handle-leave', methods=['POST'])
def handle_leave_request():
    """API endpoint to approve/reject leave requests - ULTRA SIMPLE VERSION"""
    if 'user_id' not in session or session.get('user_type') != 'division_head':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        leave_id = request.form['leave_id']
        action = request.form['action']
        head_id = session['user_id']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get leave details without any date functions
        cursor.execute("""
            SELECT la.*, w.name, w.worker_id, w.availability
            FROM Leave_Applications la
            JOIN Workers w ON la.worker_id = w.worker_id
            WHERE la.leave_id = %s AND w.division_id = %s
        """, (leave_id, session['division_id']))
        
        leave = cursor.fetchone()
        
        if not leave:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Leave request not found'})
        
        # Update status
        new_status = 'Approved' if action == 'approve' else 'Rejected'
        cursor.execute("""
            UPDATE Leave_Applications 
            SET status = %s, reviewed_by = %s, reviewed_at = NOW()
            WHERE leave_id = %s
        """, (new_status, head_id, leave_id))
        
        # For approve action, always set availability to 'On Holiday'
        if action == 'approve':
            cursor.execute("""
                UPDATE Workers 
                SET availability = 'On Holiday' 
                WHERE worker_id = %s
            """, (leave['worker_id'],))
            
            # Notification for approval
            cursor.execute("""
                INSERT INTO Notifications (worker_id, message, created_at)
                VALUES (%s, %s, NOW())
            """, (leave['worker_id'], 
                  f'Your leave request from {leave["start_date"]} to {leave["end_date"]} has been approved. (Availability set to On Holiday)'))
        else:
            # Notification for rejection
            cursor.execute("""
                INSERT INTO Notifications (worker_id, message, created_at)
                VALUES (%s, %s, NOW())
            """, (leave['worker_id'], 
                  f'Your leave request from {leave["start_date"]} to {leave["end_date"]} has been rejected.'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        message = f'Leave request {action}ed successfully'
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    

@app.route('/api/auto-mark-attendance', methods=['POST'])
def auto_mark_attendance():
    """Automatically mark attendance based on leave status and check-in"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        worker_id = session['user_id']
        today = datetime.now().date()
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if attendance already marked for today
        cursor.execute("""
            SELECT * FROM Attendance 
            WHERE worker_id = %s AND date = %s
        """, (worker_id, today))
        
        existing_record = cursor.fetchone()
        
        if existing_record:
            return jsonify({'success': False, 'error': 'Attendance already marked for today'})
        
        # Check if worker is on approved leave today
        cursor.execute("""
            SELECT * FROM Leave_Applications 
            WHERE worker_id = %s 
            AND status = 'Approved'
            AND %s BETWEEN start_date AND end_date
        """, (worker_id, today))
        
        leave_record = cursor.fetchone()
        
        if leave_record:
            # Auto-mark as Leave
            cursor.execute("""
                INSERT INTO Attendance (worker_id, date, status, auto_marked)
                VALUES (%s, %s, 'Leave', 1)
            """, (worker_id, today))
            message = 'Auto-marked as Leave (Approved leave)'
        else:
            # Default to Absent (worker needs to check-in to change to Present)
            cursor.execute("""
                INSERT INTO Attendance (worker_id, date, status, auto_marked)
                VALUES (%s, %s, 'Absent', 1)
            """, (worker_id, today))
            message = 'Auto-marked as Absent (Check-in required)'
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-in', methods=['POST'])
def check_in():
    """Worker checks in - changes status from Absent to Present"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        worker_id = session['user_id']
        today = datetime.now().date()
        current_time = datetime.now().strftime('%H:%M:%S')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check existing attendance record
        cursor.execute("""
            SELECT * FROM Attendance 
            WHERE worker_id = %s AND date = %s
        """, (worker_id, today))
        
        record = cursor.fetchone()
        
        if not record:
            # Create new record with Present status
            cursor.execute("""
                INSERT INTO Attendance (worker_id, date, status, in_time, auto_marked)
                VALUES (%s, %s, 'Present', %s, 0)
            """, (worker_id, today, current_time))
        else:
            if record['status'] == 'Leave':
                return jsonify({'success': False, 'error': 'Cannot check-in while on approved leave'})
            
            # Update existing record to Present
            cursor.execute("""
                UPDATE Attendance 
                SET status = 'Present', in_time = %s, auto_marked = 0
                WHERE worker_id = %s AND date = %s
            """, (current_time, worker_id, today))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Checked in successfully!'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/check-out', methods=['POST'])
def check_out():
    """Worker checks out - records out time"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        worker_id = session['user_id']
        today = datetime.now().date()
        current_time = datetime.now().strftime('%H:%M:%S')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check existing attendance record
        cursor.execute("""
            SELECT * FROM Attendance 
            WHERE worker_id = %s AND date = %s
        """, (worker_id, today))
        
        record = cursor.fetchone()
        
        if not record or record['status'] != 'Present':
            return jsonify({'success': False, 'error': 'Cannot check out without checking in first'})
        
        if record['out_time']:
            return jsonify({'success': False, 'error': 'Already checked out for today'})
        
        # Calculate working hours
        in_time = datetime.strptime(record['in_time'], '%H:%M:%S')
        out_time = datetime.strptime(current_time, '%H:%M:%S')
        working_hours = round((out_time - in_time).seconds / 3600, 2)
        
        # Update record with out time and working hours
        cursor.execute("""
            UPDATE Attendance 
            SET out_time = %s, working_hours = %s
            WHERE worker_id = %s AND date = %s
        """, (current_time, working_hours, worker_id, today))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Checked out successfully!', 'hours': working_hours})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/api/today-attendance')
def get_today_attendance():
    """Get today's attendance status for current worker"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        worker_id = session['user_id']
        today = datetime.now().date()
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM Attendance 
            WHERE worker_id = %s AND date = %s
        """, (worker_id, today))
        
        record = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if record:
            return jsonify({
                'success': True,
                'status': record['status'],
                'in_time': record['in_time'],
                'out_time': record['out_time'],
                'working_hours': record['working_hours'],
                'auto_marked': bool(record['auto_marked'])
            })
        else:
            return jsonify({
                'success': True,
                'status': 'Not Marked',
                'auto_marked': False
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/api/run-daily-attendance', methods=['POST'])
def run_daily_attendance():
    """Manually trigger daily attendance marking for ALL workers - FOR ADMIN USE"""
    try:
        today = datetime.now().date()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Mark attendance for all active workers
        cursor.execute("""
            INSERT INTO Attendance (worker_id, date, status, auto_marked)
            SELECT 
                w.worker_id, 
                %s as date,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM Leave_Applications 
                        WHERE worker_id = w.worker_id 
                        AND status = 'Approved'
                        AND %s BETWEEN start_date AND end_date
                    ) THEN 'Leave'
                    ELSE 'Absent'
                END as status,
                1 as auto_marked
            FROM Workers w 
            WHERE w.status = 'active'
            AND NOT EXISTS (
                SELECT 1 FROM Attendance 
                WHERE worker_id = w.worker_id 
                AND date = %s
            )
        """, (today, today, today))
        
        marked_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Daily attendance marked for {marked_count} workers on {today}")
        return jsonify({'success': True, 'marked_count': marked_count, 'date': str(today)})
        
    except Exception as e:
        print(f"❌ Error in daily attendance: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print(" Starting MSEDCL Grievance System...")
    print(" Access your app at: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)