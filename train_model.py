#!/usr/bin/env python3
"""
Train AML Risk Prediction Model
Standalone script to train and evaluate the ML model
"""

import sys
import os
from supabase import create_client

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from layers.explanation.ml_model import train_aml_model

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://pcpurhkthawyipfibehn.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')


def fetch_training_data(supabase_key):
    """Fetch data from Supabase for training"""
    print("Connecting to database...")

    supabase = create_client(SUPABASE_URL, supabase_key)
    print("✓ Connected to database\n")

    print("Fetching training data...")
    accounts = supabase.table('account_openings').select('*').execute().data
    transactions = supabase.table('transactions').select('*').execute().data
    wire_transfers = supabase.table('wire_transfers').select('*').execute().data

    print(f"✓ Fetched {len(accounts)} accounts")
    print(f"✓ Fetched {len(transactions)} transactions")
    print(f"✓ Fetched {len(wire_transfers)} wire transfers\n")

    return {
        'accounts': accounts,
        'transactions': transactions,
        'wire_transfers': wire_transfers
    }


def main():
    print("\n" + "=" * 70)
    print("AML RISK PREDICTION MODEL - TRAINING")
    print("=" * 70 + "\n")

    # Get Supabase key
    supabase_key = os.environ.get('SUPABASE_KEY')
    if not supabase_key and len(sys.argv) > 1:
        supabase_key = sys.argv[1]

    if not supabase_key:
        supabase_key = input("Enter Supabase service key: ")

    # Fetch data
    data = fetch_training_data(supabase_key)

    # Train model
    model, metrics = train_aml_model(data, model_dir='models', save=True)

    # Print summary
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"\nTest Set Performance:")
    print(f"  Accuracy:  {metrics['test']['accuracy']:.2%}")
    print(f"  Precision: {metrics['test']['precision']:.2%}")
    print(f"  Recall:    {metrics['test']['recall']:.2%}")
    print(f"  F1-Score:  {metrics['test']['f1_score']:.2%}")
    print(f"  ROC-AUC:   {metrics['test']['roc_auc']:.2%}")

    print("\n✅ Model training complete!")
    print(f"✅ Model saved to: models/")
    print("\nYou can now use this model in the dashboard generation.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

