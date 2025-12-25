#!/usr/bin/env python3
"""
AML Dashboard Web UI - Complete Documentation
==============================================

OVERVIEW:
---------
A Flask-based web application that provides role-based access to AML dashboards
with user authentication and session management.

URL: https://accessibleuidashboard-financialdata/

FEATURES:
---------
✓ User authentication with secure password hashing
✓ Role-based access control (RBAC)
✓ Session management (8-hour timeout)
✓ Four user roles:
  - Compliance Officer
  - Risk Analyst
  - Regulatory Officer
  - Administrator
✓ Same 2-panel layout for all dashboards
✓ Date-based report selection
✓ Profile management
✓ Admin panel for user management

ARCHITECTURE:
-------------

┌─────────────────────────────────────────┐
│         User Browser                    │
│  (any device, any location)             │
└──────────────┬──────────────────────────┘
               │
               │ HTTPS
               ↓
┌──────────────────────────────────────────┐
│    Flask Web Application (app.py)        │
│  - Authentication                        │
│  - Session Management                    │
│  - Role-Based Access Control             │
└──────────────┬───────────────────────────┘
               │
               │ File System
               ↓
┌──────────────────────────────────────────┐
│    Generated HTML Dashboards             │
│  output/                                 │
│    └── YYYYMMDD/                         │
│        ├── dashboard_compliance_...html  │
│        ├── dashboard_risk_...html        │
│        └── dashboard_regulatory_...html  │
└──────────────────────────────────────────┘

FILE STRUCTURE:
---------------
app.py                          - Main Flask application
start_web_dashboard.py          - Quick start script
templates/
  ├── login.html                - Login page
  ├── dashboard_wrapper.html    - Dashboard wrapper with nav
  ├── admin_dashboard.html      - Admin control panel
  ├── no_reports.html           - No reports available page
  ├── profile.html              - User profile page
  └── admin_users.html          - User management page
output/
  └── YYYYMMDD/
      └── dashboard_*.html      - Generated dashboards

USER ROLES & PERMISSIONS:
--------------------------

1. COMPLIANCE OFFICER
   Access: Own dashboard only
   Features:
   - Priority alerts requiring immediate action
   - Required actions (File SAR, EDD, KYC)
   - Compliance statistics
   - All accounts overview

2. RISK ANALYST
   Access: Own dashboard only
   Features:
   - Risk distribution analysis
   - Pattern detection (Structuring, Layering, Geographic)
   - Risk scoring and ML confidence
   - Top 50 accounts analysis

3. REGULATORY OFFICER
   Access: Own dashboard only
   Features:
   - Regulatory compliance summary
   - Violations and required actions
   - Reporting requirements (SAR, CTR, OFAC, EDD)
   - Compliance status tracking

4. ADMINISTRATOR
   Access: All dashboards + admin features
   Features:
   - View all role dashboards
   - User management
   - System administration
   - Report date selection for all roles

USAGE:
------

STEP 1: Generate Dashboards
  python3 run_dashboard.py

STEP 2: Start Web Server
  python3 start_web_dashboard.py

STEP 3: Access in Browser
  http://localhost:5000

STEP 4: Login with Credentials
  compliance@aml.com / Compliance@123
  risk@aml.com / Risk@123
  regulatory@aml.com / Regulatory@123
  admin@aml.com / Admin@123

DEFAULT CREDENTIALS:
--------------------
Email: compliance@aml.com
Password: Compliance@123
Role: Compliance Officer

Email: risk@aml.com
Password: Risk@123
Role: Risk Analyst

Email: regulatory@aml.com
Password: Regulatory@123
Role: Regulatory Officer

Email: admin@aml.com
Password: Admin@123
Role: Administrator

SECURITY FEATURES:
------------------
✓ Password hashing with Werkzeug
✓ Session-based authentication
✓ 8-hour session timeout
✓ Role-based access control
✓ CSRF protection (Flask built-in)
✓ Secure session cookies
✓ Input validation

SESSION MANAGEMENT:
-------------------
- Sessions expire after 8 hours of inactivity
- Users are automatically logged out
- Session data stored server-side
- Secure session cookie with httponly flag

DEPLOYMENT:
-----------

DEVELOPMENT (Local):
  python3 start_web_dashboard.py
  Access: http://localhost:5000

PRODUCTION (Custom Domain):

1. DNS Configuration:
   Add A record: accessibleuidashboard-financialdata → your_server_ip

2. Install Gunicorn:
   pip install gunicorn

3. Run with Gunicorn:
   gunicorn -w 4 -b 0.0.0.0:8000 app:app

4. Nginx Reverse Proxy Configuration:
   server {
       listen 80;
       server_name accessibleuidashboard-financialdata;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }

5. SSL Certificate (Let's Encrypt):
   certbot --nginx -d accessibleuidashboard-financialdata

6. Systemd Service (Auto-start):
   Create /etc/systemd/system/aml-dashboard.service

   [Unit]
   Description=AML Dashboard Web Application
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/ETL_Pipeline_Dashboard
   ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target

   Then:
   systemctl enable aml-dashboard
   systemctl start aml-dashboard

ADDING NEW USERS:
-----------------
Edit app.py and add to USERS dictionary:

USERS['newuser@company.com'] = {
    'password': generate_password_hash('SecurePassword123'),
    'role': 'Compliance Officer',
    'name': 'New User Name'
}

For production, use a proper database (SQLite, PostgreSQL, MySQL).

CUSTOMIZATION:
--------------

Change Session Timeout:
  In app.py:
  app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
  Change hours=8 to desired duration

Change Port:
  In app.py:
  app.run(host='0.0.0.0', port=5000, debug=True)
  Change port=5000 to desired port

Enable/Disable Debug Mode:
  In app.py:
  app.run(debug=True)  # Development
  app.run(debug=False) # Production

SECURITY BEST PRACTICES:
------------------------
1. Change default passwords immediately
2. Use strong passwords (12+ characters, mixed case, numbers, symbols)
3. Enable HTTPS in production
4. Use environment variables for secrets
5. Implement rate limiting for login attempts
6. Add 2FA for high-security environments
7. Regular security audits
8. Keep Flask and dependencies updated
9. Use a proper database in production
10. Enable logging and monitoring

MONITORING & LOGGING:
---------------------
Add logging to app.py:

import logging
logging.basicConfig(
    filename='aml_dashboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

TROUBLESHOOTING:
----------------

Issue: Port 5000 already in use
Solution: Change port in app.py or kill process using port 5000
  lsof -ti:5000 | xargs kill

Issue: Cannot access from other devices
Solution: Ensure firewall allows port 5000
  sudo ufw allow 5000

Issue: Session expires too quickly
Solution: Increase PERMANENT_SESSION_LIFETIME in app.py

Issue: Dashboard not loading
Solution: Generate reports first with run_dashboard.py

BROWSER COMPATIBILITY:
----------------------
✓ Chrome/Edge (recommended)
✓ Firefox
✓ Safari
✓ Any modern browser with JavaScript enabled

MOBILE RESPONSIVE:
------------------
The dashboards are responsive and work on:
✓ Desktop (optimal)
✓ Tablet
✓ Mobile (vertical scroll)

API ENDPOINTS:
--------------
/                       - Landing page (redirects to login/dashboard)
/login                  - Login page (GET/POST)
/logout                 - Logout (clears session)
/dashboard              - Main dashboard (role-specific)
/reports/<date>/<role>  - View specific report
/admin/users            - User management (admin only)
/profile                - User profile page

DEVELOPMENT ROADMAP:
--------------------
Future enhancements:
□ Database integration (PostgreSQL)
□ User registration with approval workflow
□ Password reset functionality
□ Email notifications
□ Activity logging and audit trail
□ API for programmatic access
□ Real-time data refresh
□ Export reports to PDF
□ Multi-language support
□ Dark mode theme
"""

def main():
    print(__doc__)

    print("\n" + "=" * 80)
    print("QUICK START")
    print("=" * 80)
    print("\n1. Generate dashboards:")
    print("   python3 run_dashboard.py")
    print("\n2. Start web server:")
    print("   python3 start_web_dashboard.py")
    print("\n3. Open browser:")
    print("   http://localhost:5000")
    print("\n4. Login with:")
    print("   compliance@aml.com / Compliance@123")
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()

