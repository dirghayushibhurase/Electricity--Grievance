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
            # Get data from views
            cursor.execute("SELECT * FROM System_Stats_View")
            stats = cursor.fetchone()

            cursor.execute("SELECT * FROM Live_Service_Status_View")
            live_status = cursor.fetchall()

            cursor.execute("SELECT * FROM Recent_Activity_View")
            recent_activity = cursor.fetchall()

            cursor.execute("SELECT * FROM Top_Divisions_Summary_View")
            top_divisions = cursor.fetchall()

            cursor.execute("SELECT * FROM Issue_Type_Distribution_View")
            issue_types = cursor.fetchall()

            # Get user's issues
            cursor.execute("SELECT * FROM User_Issues_Summary_VIEW WHERE user_id = %s", (session.get('user_id'),))
            user_issues = cursor.fetchall()
            
        except Exception as e:
            print(f"Error in user dashboard: {e}")
        finally:
            cursor.close()
            conn.close()
        
    return render_template('dashboard.html',
                         stats=stats,
                         live_status=live_status,
                         recent_activity=recent_activity,
                         user_issues=user_issues,
                         top_divisions=top_divisions,
                         issue_types=issue_types,
                         user_name=session.get('user_name'))

# Worker Dashboard (Rough version)
@app.route('/worker-dashboard')
def worker_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'worker':
        return redirect(url_for('login'))
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Worker Dashboard - MSEDCL</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .header {{ background: #d32f2f; color: white; padding: 20px; border-radius: 10px; }}
            .content {{ background: white; padding: 20px; margin-top: 20px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>👷 Worker Dashboard</h1>
            <p>Welcome, {session.get('user_name')}!</p>
            <p><a href="/logout" style="color: white;">Logout</a></p>
        </div>
        <div class="content">
            <h2>Worker Functions</h2>
            <ul>
                <li>View Assigned Tasks</li>
                <li>Update Task Status</li>
                <li>Report Completion</li>
                <li>Request Equipment</li>
            </ul>
            <p><em>This is a basic worker dashboard. More features coming soon!</em></p>
        </div>
    </body>
    </html>
    """

# Division Head Dashboard (Rough version)
@app.route('/division-dashboard')
def division_dashboard():
    if not session.get('logged_in') or session.get('user_type') != 'division_head':
        return redirect(url_for('login'))
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Division Head Dashboard - MSEDCL</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .header {{ background: #1976d2; color: white; padding: 20px; border-radius: 10px; }}
            .content {{ background: white; padding: 20px; margin-top: 20px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>👨‍💼 Division Head Dashboard</h1>
            <p>Welcome, {session.get('user_name')}!</p>
            <p><a href="/logout" style="color: white;">Logout</a></p>
        </div>
        <div class="content">
            <h2>Division Head Functions</h2>
            <ul>
                <li>Manage Division Workers</li>
                <li>Assign Tasks to Workers</li>
                <li>Monitor Division Performance</li>
                <li>Approve Equipment Requests</li>
                <li>Generate Reports</li>
            </ul>
            <p><em>This is a basic division head dashboard. More features coming soon!</em></p>
        </div>
    </body>
    </html>
    """

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

if __name__ == '__main__':
    print("🚀 Starting MSEDCL Grievance System...")
    print("📍 Access your app at: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)