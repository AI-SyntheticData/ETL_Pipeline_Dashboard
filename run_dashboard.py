#!/usr/bin/env python3
"""
Quick runner for comprehensive AML dashboard generation
Analyzes ALL accounts and generates role-based HTML dashboards
"""

import subprocess
import sys
import os

def main():
    print("\n" + "=" * 80)
    print("AML COMPREHENSIVE DASHBOARD - QUICK START")
    print("=" * 80 + "\n")

    print("This will generate 3 role-based HTML dashboards:")
    print("  1. Compliance Officer Dashboard")
    print("  2. Risk Analyst Dashboard")
    print("  3. Regulatory Officer Dashboard")
    print("\nEach dashboard includes:")
    print("  • Left Panel: Data flow visualization with all metrics")
    print("  • Right Panel: Role-specific comprehensive analysis")
    print("\nAnalyzes: ALL accounts (not just top 5)")
    print("\n" + "=" * 80 + "\n")

    # Check for environment variable
    supabase_key = os.environ.get('SUPABASE_KEY')

    if not supabase_key:
        print("SUPABASE_KEY environment variable not set.")
        if len(sys.argv) > 1:
            supabase_key = sys.argv[1]
        else:
            supabase_key = input("Enter your Supabase service key: ")

    print("\n" + "=" * 80)
    print("Generating Dashboards...")
    print("=" * 80 + "\n")

    # Run the dashboard generator
    try:
        cmd = ['python3', 'generate_dashboard.py', supabase_key]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Dashboard generation failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nDashboard generation interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()

