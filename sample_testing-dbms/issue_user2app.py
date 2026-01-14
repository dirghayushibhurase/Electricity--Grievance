from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'msedcl_secret_key_2024'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Asnani_320726',
    'database': 'EGS'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

# Login Route - Checks all user types
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['email']  # Can be email or phone
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            return render_template('login.html', error='Database connection failed')

        cursor = conn.cursor(dictionary=True)
        try:
            user = None
            
            # Check in Users table
            cursor.execute("""
                SELECT user_id, name, 'user' as user_type 
                FROM Users 
                WHERE (email = %s OR phone = %s) AND password = %s
            """, (identifier, identifier, password))
            user = cursor.fetchone()
            
            if not user:
                # Check in Workers table
                cursor.execute("""
                    SELECT worker_id as user_id, name, 'worker' as user_type 
                    FROM Workers 
                    WHERE (email = %s OR phone_no = %s) AND password = %s AND is_active = TRUE
                """, (identifier, identifier, password))
                user = cursor.fetchone()
            
            if not user:
                # Check in Division_Heads table
                cursor.execute("""
                    SELECT head_id as user_id, name, 'division_head' as user_type 
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
                
                flash(f'Welcome back, {user["name"]}!', 'success')
                
                # Redirect based on user type
                if user['user_type'] == 'user':
                    return redirect(url_for('dashboard'))
                elif user['user_type'] == 'worker':
                    return redirect(url_for('worker_dashboard'))
                elif user['user_type'] == 'division_head':
                    return redirect(url_for('division_dashboard'))
                
            else:
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
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            try:
                # Check if email already exists
                cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return render_template('signup.html', error='An account with this email already exists')

                # Insert new user
                insert_cursor = conn.cursor()
                insert_cursor.execute("""
                    INSERT INTO Users (name, phone, email, password, address_line1, address_line2, city, pincode, division_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (name, phone, email, password, address_line1, address_line2, city, pincode, division_id))
                conn.commit()
                insert_cursor.close()
                
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))
                
            except mysql.connector.Error as e:
                return render_template('signup.html', error=f'Registration failed: {e}')
            finally:
                cursor.close()
                conn.close()
    
    # Get divisions for dropdown
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

# Public Routes
@app.route('/')
def index():
    """Public homepage - visible to all"""
    conn = get_db_connection()
    stats = {}
    top_divisions = []
    issue_types = []
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            # Get system stats from view
            cursor.execute("SELECT * FROM System_Stats_View")
            stats = cursor.fetchone()
            
            # Get top divisions from view
            cursor.execute("SELECT * FROM Top_Divisions_Summary_View")
            top_divisions = cursor.fetchall()
            
            # Get issue type distribution
            cursor.execute("SELECT * FROM Issue_Type_Distribution_View")
            issue_types = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching homepage data: {e}")
            # Provide fallback data if views don't exist
            stats = {'total_workers': 25, 'resolved_issues': 150, 'total_users': 300, 'satisfaction_rate': 92}
        finally:
            cursor.close()
            conn.close()
    
    return render_template('index.html', stats=stats, top_divisions=top_divisions, issue_types=issue_types)

# User Dashboard
# User Dashboard
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

            # DEBUG: Get user's issues - FIXED QUERY
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
# Worker Dashboard (Rough version)
# Worker Dashboard
@app.route('/worker-dashboard')
def worker_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    return render_template('worker_dashboard.html', user_name=session.get('user_name'))

# Division Head Dashboard
@app.route('/division-dashboard')
def division_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'division_head':
        return redirect(url_for('login'))
    
    return render_template('division_dashboard.html', user_name=session.get('user_name'))

# API Routes
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

# Add these routes to your app.py

@app.route('/raise-issue')
def raise_issue():
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    return render_template('raise_issue.html', user_name=session.get('user_name'))

@app.route('/track-issues')
def track_issues():
    if not session.get('logged_in') or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')
    issue_type_filter = request.args.get('issue_type', '')
    division_filter = request.args.get('division', '')
    
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
                    i.created_at, i.resolved_at, d.division_name, d.division_id
                FROM Issues i
                JOIN Divisions d ON i.division_id = d.division_id
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
            
            query += " ORDER BY i.created_at DESC"
            
            cursor.execute(query, params)
            user_issues = cursor.fetchall()
            
            # Get divisions for filter dropdown
            cursor.execute("SELECT division_id, division_name FROM Divisions ORDER BY division_name")
            divisions = cursor.fetchall()
            
        except Exception as e:
            print(f"Error fetching user issues: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cursor.close()
            conn.close()
    
    return render_template('track_issues.html', 
                         user_issues=user_issues,
                         divisions=divisions,
                         user_name=session.get('user_name'))


@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user_data = {}
    divisions = []
    
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
            
        except Exception as e:
            print(f"Error fetching user profile: {e}")
        finally:
            cursor.close()
            conn.close()
    
    return render_template('profile.html', 
                         user_data=user_data,
                         divisions=divisions,
                         user_name=session.get('user_name'))

if __name__ == '__main__':
    print("🚀 Starting MSEDCL Grievance System...")
    print("📍 Access your app at: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)