#!/usr/bin/env python3
"""
Accessible ETL Pipeline UI dashboard - Quick Start
Launches the web application with auto-port detection
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

def run_pipeline():
    """Run the complete ETL pipeline to generate dashboards"""
    print("\n" + "=" * 80)
    print("STEP 1: RUNNING COMPLETE PIPELINE")
    print("=" * 80 + "\n")

    print("This will:")
    print("  1. Generate raw financial data")
    print("  2. Apply ETL transformations and AML detection")
    print("  3. Load data to database (if SUPABASE_KEY is set)")
    print("  4. Generate role-based dashboards")
    print()

    # Get environment variables
    supabase_key = os.environ.get('SUPABASE_KEY', '')
    openai_key = os.environ.get('OPENAI_API_KEY', '')

    # Build command - run in non-interactive mode
    cmd = [sys.executable, 'run_complete_pipeline.py']

    if supabase_key:
        cmd.append(supabase_key)
        print("✓ SUPABASE_KEY detected")
    else:
        print("ℹ️  SUPABASE_KEY not set - will skip database loading")
        # Use a dummy key to keep the script running
        cmd.append('dummy_key_skip_db')

    if openai_key:
        cmd.append(openai_key)
        print("✓ OPENAI_API_KEY detected - will use AI generation")
    else:
        print("ℹ️  OPENAI_API_KEY not set - will use rule-based generation")

    # Use fewer accounts for faster startup (50 instead of 100)
    cmd.append('50')

    print("\nStarting pipeline...\n")

    try:
        # Run pipeline with stdin redirected to prevent interactive prompts
        result = subprocess.run(
            cmd,
            check=True,
            stdin=subprocess.DEVNULL,  # Prevent interactive prompts
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Show output immediately
        )
        print("\n✓ Pipeline completed successfully!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Pipeline failed with error: {e}")
        print("\nℹ️  You can still start the web server, but dashboards may be missing.")
        return False
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        return False

def main():
    print("\n" + "=" * 80)
    print("AML DASHBOARD - COMPLETE STARTUP")
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

    # Check if templates exist in layers
    templates_path = os.path.join('layers', 'human_interaction', 'templates')
    if not os.path.exists(templates_path):
        print("⚠️  WARNING: Templates directory not found")
        print(f"  Expected location: {templates_path}")
        print("\nWeb application may not work correctly.\n")

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

    # Run pipeline if no reports exist OR if user wants fresh data
    if not has_reports:
        print("ℹ️  No dashboards found. Running pipeline to generate them...\n")
        run_pipeline()
    else:
        print("✓ Existing dashboards found in output/ directory")
        print("  Using existing dashboards to start server faster...\n")
        print("  💡 To regenerate dashboards, run: python3 run_complete_pipeline.py\n")

    print("\n" + "=" * 80)
    print("STEP 2: STARTING WEB SERVER")
    print("=" * 80 + "\n")

    print("Starting Flask web server...")
    print("\nThe dashboard will be available at:")
    print("  • http://localhost:5000")
    print("  • http://127.0.0.1:5000")

    # Check if running in Codespaces or container
    if os.environ.get('CODESPACES') or os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN'):
        print("  • Port 8080 will be automatically forwarded in Codespaces")

    print("\nFor production deployment with custom domain:")
    print("  • Configure DNS: accessibleuidashboard-financialdata → your_server_ip")
    print("  • Use reverse proxy (nginx/apache) with SSL certificate")
    print("\nDefault login credentials:")
    print("  👔 Compliance Officer: compliance@aml.com / Compliance@123")
    print("  📊 Risk Analyst:       risk@aml.com / Risk@123")
    print("  📋 Regulatory Officer: regulatory@aml.com / Regulatory@123")
    print("  🔧 Administrator:      admin@aml.com / Admin@123")
    print("\n" + "=" * 80 + "\n")
    print("Press Ctrl+C to stop the server\n")

    try:
        subprocess.run([sys.executable, '-m', 'layers.human_interaction.web_application'])
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Server stopped")
        print("=" * 80 + "\n")
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

