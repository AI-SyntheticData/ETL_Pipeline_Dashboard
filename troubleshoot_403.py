#!/usr/bin/env python3
"""
Troubleshooting HTTP 403 Error
===============================

SYMPTOM:
--------
When accessing http://localhost:5000, you see:
"Access to localhost was denied
You don't have authorization to view this page.
HTTP ERROR 403"

COMMON CAUSES & SOLUTIONS:
--------------------------

1. BROWSER CACHE/COOKIES ISSUE
   Solution:
   • Clear browser cache and cookies
   • Try in Incognito/Private mode
   • Try a different browser

2. LOCALHOST vs 127.0.0.1
   Solution:
   • Try http://127.0.0.1:5000 instead of http://localhost:5000
   • Some systems have DNS resolution issues with 'localhost'

3. PORT ALREADY IN USE
   Solution:
   • Check if port 5000 is already in use:
     lsof -ti:5000
   • Kill the process:
     lsof -ti:5000 | xargs kill
   • Or change the port in app.py

4. FIREWALL BLOCKING
   Solution:
   • Temporarily disable firewall
   • Or allow port 5000:
     sudo ufw allow 5000

5. FLASK NOT RUNNING PROPERLY
   Solution:
   • Stop the server (Ctrl+C)
   • Restart with: python3 start_web_dashboard.py
   • Check for error messages in terminal

6. PERMISSION ISSUES
   Solution:
   • Ensure you have read/write permissions in the directory
   • Run: chmod -R 755 .
   • Ensure templates/ and output/ directories exist

7. FLASK CONFIGURATION ISSUE
   Solution:
   • The app.py has been updated to use host='127.0.0.1'
   • This should fix most 403 errors
   • If still having issues, check app.py configuration

STEP-BY-STEP TROUBLESHOOTING:
------------------------------

Step 1: Stop the Server
   Press Ctrl+C in the terminal where Flask is running

Step 2: Clear Browser Data
   • Chrome: Cmd+Shift+Delete → Clear browsing data
   • Firefox: Preferences → Privacy → Clear Data
   • Safari: Preferences → Privacy → Manage Website Data → Remove All

Step 3: Restart Server
   python3 start_web_dashboard.py

Step 4: Try Different URL
   • http://127.0.0.1:5000 (try this first)
   • http://localhost:5000
   • http://0.0.0.0:5000

Step 5: Check Terminal Output
   Look for error messages like:
   • "Address already in use" → Port conflict
   • "Permission denied" → Permission issue
   • "Template not found" → Missing template files

Step 6: Try Different Browser
   • Chrome/Edge
   • Firefox
   • Safari
   • Incognito/Private mode

Step 7: Check File Permissions
   cd /path/to/ETL_Pipeline_Dashboard
   ls -la
   # Ensure you can read/write files

Step 8: Verify Flask Installation
   python3 -c "import flask; print('Flask version:', flask.__version__)"

QUICK FIXES:
------------

Fix 1: Use 127.0.0.1 instead of localhost
   Open: http://127.0.0.1:5000

Fix 2: Clear everything and restart
   1. Stop server (Ctrl+C)
   2. Close all browser windows
   3. python3 start_web_dashboard.py
   4. Open http://127.0.0.1:5000 in new browser window

Fix 3: Check if port is free
   lsof -ti:5000
   # If shows a number, run:
   lsof -ti:5000 | xargs kill
   # Then restart server

Fix 4: Ensure templates exist
   ls -la templates/
   # Should see: login.html, dashboard_wrapper.html, etc.
   # If missing, the system should auto-create them

Fix 5: Try different port
   Edit app.py, change:
   app.run(host='127.0.0.1', port=5000, ...)
   to:
   app.run(host='127.0.0.1', port=8080, ...)

   Then access: http://127.0.0.1:8080

STILL NOT WORKING?
------------------

Try this command-by-command:

1. cd /Users/mac/Documents/GitHub/ETL_Pipeline_Dashboard

2. python3 -c "import flask; print('Flask OK')"

3. ls templates/
   # Should see login.html and other templates

4. python3 app.py
   # Check terminal output for errors

5. In browser (incognito mode):
   http://127.0.0.1:5000

6. If you see login page, try credentials:
   compliance@aml.com / Compliance@123

ALTERNATIVE: Run with Flask CLI
--------------------------------

1. export FLASK_APP=app.py
2. export FLASK_ENV=development
3. flask run --host=127.0.0.1 --port=5000

LOGS TO CHECK:
--------------
The Flask server outputs to terminal. Look for:
   * Running on http://127.0.0.1:5000
   * WARNING messages
   * ERROR messages
   * 403 response codes

NETWORK DIAGNOSTICS:
--------------------

Test 1: Is Flask running?
   netstat -an | grep 5000
   # Should show LISTEN on port 5000

Test 2: Can you connect?
   curl http://127.0.0.1:5000
   # Should show HTML response, not 403

Test 3: Browser DevTools
   • Open browser DevTools (F12)
   • Go to Network tab
   • Try accessing http://127.0.0.1:5000
   • Check the request/response headers
   • Look for specific error messages

CONFIGURATION CHANGES MADE:
----------------------------
The following changes have been made to fix 403 errors:

1. Changed host from '0.0.0.0' to '127.0.0.1'
2. Added threaded=True for better handling
3. Added use_reloader=False to prevent double-start
4. Added session cookie configuration
5. Disabled file caching for development
6. Created all missing template files
7. Added proper directory creation in startup

CONTACT POINTS:
---------------
If still having issues after all troubleshooting:

1. Check Flask documentation: https://flask.palletsprojects.com/
2. Verify system requirements:
   • Python 3.7+
   • Flask 2.0+
   • Modern browser
   • No VPN interfering
3. Try on different network
4. Check antivirus software isn't blocking

PREVENTION:
-----------
To avoid 403 errors in future:

• Always use http://127.0.0.1:5000 (not localhost)
• Clear browser cache when restarting server
• Ensure proper permissions on directories
• Don't run multiple Flask instances on same port
• Keep Flask and dependencies updated
"""

def main():
    print(__doc__)

    print("\n" + "=" * 80)
    print("IMMEDIATE ACTIONS")
    print("=" * 80)
    print("\n1. Stop current server (if running): Ctrl+C")
    print("\n2. Restart server:")
    print("   python3 start_web_dashboard.py")
    print("\n3. Try this URL in browser:")
    print("   http://127.0.0.1:5000")
    print("\n4. If that doesn't work, clear browser cache and try again")
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()

