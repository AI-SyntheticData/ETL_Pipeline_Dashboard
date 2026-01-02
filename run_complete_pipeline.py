#!/usr/bin/env python3
"""
Complete AML Pipeline Workflow
Runs the full 2-stage process:
1. Generate raw data with AI
2. Apply ETL rules and load to database
3. Generate dashboards and analyze
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print("\n" + "=" * 80)
    print(description)
    print("=" * 80 + "\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        return False


def main():
    print("\n" + "=" * 80)
    print("COMPLETE AML PIPELINE WORKFLOW")
    print("=" * 80 + "\n")

    print("This will run the complete 2-stage AI-powered pipeline:")
    print("  Stage 1: Generate raw data with AI (varied, realistic)")
    print("  Stage 2: Apply ETL rules and detect AML risks")
    print("  Stage 3: Load to database")
    print("  Stage 4: Generate dashboards for analysis")
    print()

    # Get API keys from environment variables (GitHub Codespaces secrets)
    # These are automatically available in Codespaces if set in GitHub Settings
    supabase_key = os.environ.get('SUPABASE_KEY', '')
    openai_key = os.environ.get('OPENAI_API_KEY', '')

    # Check for command line arguments (for backward compatibility)
    if len(sys.argv) > 1 and sys.argv[1] and sys.argv[1] != 'dummy_key_skip_db':
        supabase_key = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2]:
        openai_key = sys.argv[2]

    # Determine if we'll use AI generation
    use_ai = bool(openai_key)

    # Determine if we'll use database loading
    use_database = bool(supabase_key and supabase_key != 'dummy_key_skip_db')

    # Get number of accounts (default: 100, can override via command line)
    num_accounts = 100
    if len(sys.argv) > 3:
        try:
            num_accounts = int(sys.argv[3])
        except ValueError:
            pass

    # Display configuration
    print("\n📊 Configuration:")
    if use_database:
        print("  ✓ Supabase Key: Detected - will load to database")
    else:
        print("  ℹ️  Supabase Key: Not set - will skip database loading")
        print("     (Set SUPABASE_KEY in GitHub Settings → Codespaces → Secrets)")

    if use_ai:
        print("  ✓ OpenAI Key: Detected - will use AI generation")
    else:
        print("  ℹ️  OpenAI Key: Not set - will use rule-based generation")
        print("     (Set OPENAI_API_KEY in GitHub Settings → Codespaces → Secrets)")

    print(f"  📈 Number of accounts: {num_accounts}")

    # Check if running in Codespaces
    if os.environ.get('CODESPACES') or os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN'):
        print("  🌐 Environment: GitHub Codespaces")

    print("\n🚀 Starting pipeline automatically (no manual input required)...\n")

    # Stage 1: Generate raw data
    print("\n" + "=" * 80)
    print("STAGE 1: GENERATE RAW DATA WITH AI")
    print("=" * 80)

    cmd = ['python3', '-m', 'layers.data_pipeline.raw_data_generator']
    if use_ai:
        cmd.append(openai_key)
    cmd.append(str(num_accounts))

    if not run_command(cmd, "Generating raw financial data..."):
        print("\n✗ Failed to generate raw data")
        sys.exit(1)

    # Find the generated raw data file
    import glob
    raw_files = sorted(glob.glob('raw_data/*/raw_accounts.json'), reverse=True)

    if not raw_files:
        print("\n✗ No raw data file found")
        sys.exit(1)

    raw_data_file = raw_files[0]
    print(f"\n✓ Raw data generated: {raw_data_file}")

    # Stage 2: ETL Pipeline
    print("\n" + "=" * 80)
    print("STAGE 2: ETL PIPELINE - APPLY AML DETECTION RULES")
    print("=" * 80)

    # Use dummy key if not provided (ETL processor will skip DB loading)
    etl_key = supabase_key if use_database else 'skip_db_loading'
    cmd = ['python3', '-m', 'layers.data_pipeline.etl_processor', raw_data_file, etl_key]

    if not run_command(cmd, "Running ETL pipeline..."):
        print("\n✗ Failed to run ETL pipeline")
        sys.exit(1)

    print("\n✓ ETL pipeline completed successfully")

    # Stage 3: Generate dashboards (always auto-generate, no prompts)
    print("\n" + "=" * 80)
    print("STAGE 3: GENERATE ANALYSIS DASHBOARDS")
    print("=" * 80)

    print("\n🎨 Auto-generating comprehensive dashboards...")

    cmd = ['python3', '-m', 'layers.access.dashboard_builder']

    if not run_command(cmd, "Generating dashboards..."):
        print("\n✗ Failed to generate dashboards")
        sys.exit(1)

    print("\n✓ Dashboards generated successfully")

    # Summary
    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 80)

    print("\n✅ What was done:")
    print("  ✓ Generated raw financial data (with natural AML patterns)")
    print("  ✓ Applied ETL transformation rules")
    print("  ✓ Detected AML risks and generated alerts")
    if use_database:
        print("  ✓ Loaded clean data into Supabase database")
    else:
        print("  ℹ️  Skipped database loading (no SUPABASE_KEY)")
    print("  ✓ Generated role-based analysis dashboards")

    print("\n🚀 Next steps:")
    print("  • Dashboards are ready in output/ directory")
    print("  • Start web interface: python3 start_web_dashboard.py")
    print("  • Login at: http://127.0.0.1:5000")

    # Show Codespaces-specific instructions
    if os.environ.get('CODESPACES') or os.environ.get('GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN'):
        print("\n💡 In Codespaces:")
        print("  • Port 8080 will be automatically forwarded")
        print("  • Click the notification to open in browser")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()

