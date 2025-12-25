#!/usr/bin/env python3
"""
AML Dashboard Web Application
Flask-based web UI with login and role-based access control
URL: https://accessibleuidashboard-financialdata/
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# User database (in production, use a real database)
USERS = {
    'compliance@aml.com': {
        'password': generate_password_hash('Compliance@123'),
        'role': 'Compliance Officer',
        'name': 'John Compliance'
    },
    'risk@aml.com': {
        'password': generate_password_hash('Risk@123'),
        'role': 'Risk Analyst',
        'name': 'Sarah Risk'
    },
    'regulatory@aml.com': {
        'password': generate_password_hash('Regulatory@123'),
        'role': 'Regulatory Officer',
        'name': 'Mike Regulatory'
    },
    'admin@aml.com': {
        'password': generate_password_hash('Admin@123'),
        'role': 'Administrator',
        'name': 'Admin User'
    }
}

# Role to dashboard file mapping
ROLE_DASHBOARDS = {
    'Compliance Officer': 'dashboard_compliance_officer.html',
    'Risk Analyst': 'dashboard_risk_analyst.html',
    'Regulatory Officer': 'dashboard_regulatory_officer.html'
}


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(roles):
    """Decorator to require specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            if session['user_role'] not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/')
def index():
    """Landing page"""
    if 'user_email' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if 'user_email' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if email in USERS and check_password_hash(USERS[email]['password'], password):
            session.permanent = True
            session['user_email'] = email
            session['user_role'] = USERS[email]['role']
            session['user_name'] = USERS[email]['name']
            session['login_time'] = datetime.now().isoformat()

            flash(f'Welcome back, {USERS[email]["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - shows role-specific content"""
    user_role = session.get('user_role')
    user_name = session.get('user_name')

    # Get the latest report date
    output_dir = 'output'
    date_dirs = []
    if os.path.exists(output_dir):
        date_dirs = sorted([d for d in os.listdir(output_dir)
                          if os.path.isdir(os.path.join(output_dir, d))], reverse=True)

    if not date_dirs:
        flash('No reports available. Please generate reports first.', 'warning')
        return render_template('no_reports.html', user_name=user_name, user_role=user_role)

    latest_date = date_dirs[0]

    # Load the appropriate dashboard based on role
    dashboard_file = ROLE_DASHBOARDS.get(user_role)

    if not dashboard_file:
        if user_role == 'Administrator':
            # Admin can see all dashboards
            return render_template('admin_dashboard.html',
                                 user_name=user_name,
                                 user_role=user_role,
                                 latest_date=latest_date,
                                 available_dates=date_dirs)
        else:
            flash('Invalid role configuration.', 'danger')
            return redirect(url_for('logout'))

    dashboard_path = os.path.join(output_dir, latest_date, dashboard_file)

    if not os.path.exists(dashboard_path):
        flash(f'Dashboard not found for {user_role}. Please generate reports.', 'warning')
        return render_template('no_reports.html', user_name=user_name, user_role=user_role)

    # Read the dashboard HTML
    with open(dashboard_path, 'r', encoding='utf-8') as f:
        dashboard_html = f.read()

    # Inject user info and navigation into dashboard
    return render_template('dashboard_wrapper.html',
                         dashboard_html=dashboard_html,
                         user_name=user_name,
                         user_role=user_role,
                         report_date=latest_date,
                         available_dates=date_dirs)


@app.route('/reports/<date>/<role>')
@login_required
def view_report(date, role):
    """View a specific report by date and role"""
    user_role = session.get('user_role')

    # Check permissions (admin can view all, others only their own)
    if user_role != 'Administrator':
        allowed_role = user_role.lower().replace(' ', '_')
        requested_role = role
        if allowed_role not in requested_role:
            flash('You do not have permission to view this report.', 'danger')
            return redirect(url_for('dashboard'))

    dashboard_file = f'dashboard_{role}.html'
    dashboard_path = os.path.join('output', date, dashboard_file)

    if not os.path.exists(dashboard_path):
        flash('Report not found.', 'warning')
        return redirect(url_for('dashboard'))

    return send_from_directory(os.path.join('output', date), dashboard_file)


@app.route('/admin/users')
@role_required(['Administrator'])
def admin_users():
    """Admin page to manage users"""
    return render_template('admin_users.html',
                         users=USERS,
                         user_name=session.get('user_name'))


@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html',
                         user_name=session.get('user_name'),
                         user_email=session.get('user_email'),
                         user_role=session.get('user_role'),
                         login_time=session.get('login_time'))


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)

    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)

    print("\n" + "=" * 80)
    print("AML DASHBOARD WEB APPLICATION")
    print("=" * 80)
    print("\nStarting server...")
    print("\nAccess the dashboard at:")
    print("  http://localhost:5000")
    print("  http://127.0.0.1:5000")
    print("  or")
    print("  https://accessibleuidashboard-financialdata/ (with proper DNS/proxy)")
    print("\nDefault login credentials:")
    print("  Compliance Officer: compliance@aml.com / Compliance@123")
    print("  Risk Analyst:       risk@aml.com / Risk@123")
    print("  Regulatory Officer: regulatory@aml.com / Regulatory@123")
    print("  Administrator:      admin@aml.com / Admin@123")
    print("\n" + "=" * 80 + "\n")

    # Run with threaded mode and allow connections from any interface
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True, use_reloader=False)

