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
from datetime import datetime

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

    # Get API keys
    supabase_key = os.environ.get('SUPABASE_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')

    # Check if running in interactive mode
    is_interactive = sys.stdin.isatty()

    if not supabase_key:
        if len(sys.argv) > 1:
            supabase_key = sys.argv[1]
        elif is_interactive:
            supabase_key = input("Enter Supabase service key: ")
        else:
            print("✗ Error: SUPABASE_KEY environment variable is required in non-interactive mode")
            sys.exit(1)

    use_ai = False
    if not openai_key:
        if len(sys.argv) > 2:
            openai_key = sys.argv[2]
            use_ai = True
        elif is_interactive:
            response = input("Enter OpenAI API key (or press Enter to skip AI generation): ")
            if response.strip():
                openai_key = response.strip()
                use_ai = True
        else:
            print("Warning: OpenAI API key not provided, skipping AI generation")
    else:
        use_ai = True

    # Get number of accounts
    num_accounts = 500
    if len(sys.argv) > 3:
        try:
            num_accounts = int(sys.argv[3])
        except ValueError:
            pass

    print("\nConfiguration:")
    print(f"  Supabase Key: {'✓ Provided' if supabase_key else '✗ Missing'}")
    print(f"  OpenAI Key: {'✓ Provided (AI-powered)' if use_ai else '✗ Not provided (rule-based)'}")
    print(f"  Number of accounts: {num_accounts}")
    print()

    # Skip interactive prompts in CI/CD environments
    if is_interactive:
        input("Press Enter to start the pipeline...")
    else:
        print("Running in non-interactive mode, starting pipeline automatically...")

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

    cmd = ['python3', '-m', 'layers.data_pipeline.etl_processor', raw_data_file, supabase_key]

    if not run_command(cmd, "Running ETL pipeline..."):
        print("\n✗ Failed to run ETL pipeline")
        sys.exit(1)

    print("\n✓ ETL pipeline completed successfully")

    # Stage 3: Generate dashboards
    print("\n" + "=" * 80)
    print("STAGE 3: GENERATE ANALYSIS DASHBOARDS")
    print("=" * 80)

    # Auto-generate dashboards in non-interactive mode
    if is_interactive:
        response = input("\nGenerate comprehensive dashboards now? (y/n): ")
    else:
        print("\nAuto-generating dashboards in non-interactive mode...")
        response = 'y'

    if response.lower() == 'y':
        cmd = ['python3', '-m', 'layers.access.dashboard_builder']

        if not run_command(cmd, "Generating dashboards..."):
            print("\n✗ Failed to generate dashboards")
            sys.exit(1)

        print("\n✓ Dashboards generated successfully")
    else:
        print("\nSkipping dashboard generation. You can run later with:")
        print("  python3 -m layers.access.dashboard_builder")

    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE!")
    print("=" * 80)

    print("\nWhat was done:")
    print("  ✓ Generated raw financial data (with natural AML patterns)")
    print("  ✓ Applied ETL transformation rules")
    print("  ✓ Detected AML risks and generated alerts")
    print("  ✓ Loaded clean data into Supabase database")
    if response.lower() == 'y':
        print("  ✓ Generated role-based analysis dashboards")

    print("\nNext steps:")
    if response.lower() != 'y':
        print("  1. Generate dashboards: python3 -m layers.access.dashboard_builder")
        print("  2. Start web interface: python3 start_web_dashboard.py")
    else:
        print("  1. Start web interface: python3 start_web_dashboard.py")
        print("  2. Login at: http://127.0.0.1:5000")
        print("  3. View role-based dashboards")


    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()

