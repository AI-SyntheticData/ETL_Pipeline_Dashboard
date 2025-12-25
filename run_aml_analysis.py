#!/usr/bin/env python3
"""
Quick runner for AML Analysis
This script runs the complete AML analysis pipeline
"""

import subprocess
import sys
import os

def main():
    print("\n" + "=" * 80)
    print("AML DATA ANALYSIS - QUICK START")
    print("=" * 80 + "\n")

    print("This script will analyze your AML data using AI and generate:")
    print("  1. Decision Summary with Confidence Scores")
    print("  2. Plain-Language Explanations")
    print("  3. Data Lineage Visualizations")
    print("  4. Role-Specific Notes for:")
    print("     - Compliance Officers")
    print("     - Risk Analysts")
    print("     - Regulatory Officers")
    print("\n  Using: RandomForest + SHAP (Explainable AI)")
    print("\n" + "=" * 80 + "\n")

    # Check for environment variables
    supabase_key = os.environ.get('SUPABASE_KEY')

    if not supabase_key:
        print("SUPABASE_KEY environment variable not set.")
        if len(sys.argv) > 1:
            supabase_key = sys.argv[1]
        else:
            supabase_key = input("Enter your Supabase service key: ")

    print("\n" + "=" * 80)
    print("Starting Analysis...")
    print("=" * 80 + "\n")

    # Run the analysis
    try:
        cmd = ['python3', 'analyze_aml_data.py', supabase_key]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Analysis failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(1)

if __name__ == "__main__":
    main()

