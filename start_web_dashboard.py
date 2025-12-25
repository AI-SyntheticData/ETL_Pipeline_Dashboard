#!/usr/bin/env python3
"""
AML Dashboard Web Application - Quick Start
Starts the Flask web server for the role-based dashboard UI
"""

import subprocess
import sys
import os

def check_flask():
    """Check if Flask is installed"""
    try:
        import flask
        return True
    except ImportError:
        return False

def main():
    print("\n" + "=" * 80)
    print("AML DASHBOARD WEB APPLICATION - STARTING")
    print("=" * 80 + "\n")

    # Check if Flask is installed
    if not check_flask():
        print("Flask is not installed. Installing required packages...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'flask', 'werkzeug'], check=True)
            print("✓ Flask installed successfully\n")
        except subprocess.CalledProcessError:
            print("✗ Failed to install Flask. Please run:")
            print("  pip install flask werkzeug")
            sys.exit(1)

    # Ensure templates directory exists
    if not os.path.exists('templates'):
        print("Creating templates directory...")
        os.makedirs('templates', exist_ok=True)
        print("✓ Templates directory created\n")

    # Ensure output directory exists
    if not os.path.exists('output'):
        print("Creating output directory...")
        os.makedirs('output', exist_ok=True)
        print("✓ Output directory created\n")

    # Check if reports exist
    has_reports = False
    if os.path.exists('output'):
        for date_dir in os.listdir('output'):
            if os.path.isdir(os.path.join('output', date_dir)):
                has_reports = True
                break

    if not has_reports:
        print("⚠️  WARNING: No reports found in output/ directory")
        print("\nYou should generate dashboards first:")
        print("  python3 run_dashboard.py")
        print("\nContinuing anyway (you can still login)...\n")

    print("Starting Flask web server...")
    print("\nThe dashboard will be available at:")
    print("  • http://localhost:5000")
    print("  • http://127.0.0.1:5000")
    print("\nFor production deployment with custom domain:")
    print("  • Configure DNS: accessibleuidashboard-financialdata → your_server_ip")
    print("  • Use reverse proxy (nginx/apache) with SSL certificate")
    print("\nDefault login credentials:")
    print("  Compliance Officer: compliance@aml.com / Compliance@123")
    print("  Risk Analyst:       risk@aml.com / Risk@123")
    print("  Regulatory Officer: regulatory@aml.com / Regulatory@123")
    print("  Administrator:      admin@aml.com / Admin@123")
    print("\n" + "=" * 80 + "\n")
    print("Press Ctrl+C to stop the server\n")
    print("If you get a 403 error:")
    print("  1. Try http://127.0.0.1:5000 instead of localhost:5000")
    print("  2. Check if another process is using port 5000")
    print("  3. Try clearing browser cache and cookies")
    print("\n")

    try:
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Server stopped")
        print("=" * 80 + "\n")
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

