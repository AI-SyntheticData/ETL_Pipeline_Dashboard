#!/usr/bin/env python3
"""
AI-Powered Raw Data Generator
Generates realistic financial transaction data with natural AML patterns
Uses AI model to create varied, non-hardcoded scenarios
"""

from supabase import create_client, Client
import sys
import os
from datetime import datetime, timedelta
import random
import numpy as np
from openai import OpenAI

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://pcpurhkthawyipfibehn.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')


def generate_customer_profile_with_ai(openai_client, profile_type='normal'):
    """Use AI to generate realistic customer profile"""

    prompt = f"""Generate a realistic customer profile for a financial institution. 
Profile type: {profile_type}

Return ONLY a JSON object with these exact fields (no other text):
{{
    "name": "Full Name",
    "country": "Country Code (2 letters)",
    "occupation": "Job Title",
    "age": number (25-70),
    "initial_deposit": number (1000-50000),
    "is_pep": boolean,
    "is_sanctioned": boolean,
    "risk_factors": ["list", "of", "risk", "factors"],
    "behavior_pattern": "description of typical transaction behavior"
}}

For {profile_type} profiles:
- normal: Regular customers, low risk, normal occupations, stable countries
- suspicious: High-risk occupations, cash businesses, unusual patterns
- high_risk: Sanctioned countries, PEPs, money service businesses
- random: Mix of all types with natural variation

Make it realistic and varied. Each call should generate different data."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial data generator. Always respond with valid JSON only, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,  # High temperature for variety
            max_tokens=300
        )

        import json
        profile_text = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if profile_text.startswith('```'):
            profile_text = profile_text.split('```')[1]
            if profile_text.startswith('json'):
                profile_text = profile_text[4:]

        profile = json.loads(profile_text)
        return profile
    except Exception as e:
        print(f"Warning: AI generation failed ({e}), using fallback")
        return generate_fallback_profile(profile_type)


def generate_fallback_profile(profile_type):
    """Fallback when AI is unavailable"""
    countries_normal = ['US', 'GB', 'CA', 'AU', 'DE', 'FR', 'JP']
    countries_high_risk = ['IR', 'KP', 'SY', 'VE', 'CU']
    occupations_normal = ['Teacher', 'Engineer', 'Accountant', 'Doctor', 'Lawyer']
    occupations_suspicious = ['Money Service', 'Casino Owner', 'Real Estate', 'Jewelry Dealer', 'Art Dealer']

    names = ['John Smith', 'Maria Garcia', 'Ahmed Hassan', 'Li Wei', 'Anna Mueller',
             'Carlos Rodriguez', 'Fatima Ali', 'Ivan Petrov', 'Yuki Tanaka', 'Sarah Johnson']

    if profile_type == 'high_risk':
        return {
            'name': random.choice(names),
            'country': random.choice(countries_high_risk),
            'occupation': random.choice(occupations_suspicious),
            'age': random.randint(35, 65),
            'initial_deposit': random.uniform(15000, 50000),
            'is_pep': random.random() < 0.3,
            'is_sanctioned': random.random() < 0.2,
            'risk_factors': ['HIGH_RISK_COUNTRY', 'CASH_BUSINESS'],
            'behavior_pattern': 'Frequent large transactions, multiple wire transfers'
        }
    elif profile_type == 'suspicious':
        return {
            'name': random.choice(names),
            'country': random.choice(countries_normal),
            'occupation': random.choice(occupations_suspicious),
            'age': random.randint(30, 60),
            'initial_deposit': random.uniform(8000, 25000),
            'is_pep': random.random() < 0.1,
            'is_sanctioned': False,
            'risk_factors': ['CASH_BUSINESS', 'UNUSUAL_PATTERN'],
            'behavior_pattern': 'Structured transactions, just below thresholds'
        }
    else:  # normal
        return {
            'name': random.choice(names),
            'country': random.choice(countries_normal),
            'occupation': random.choice(occupations_normal),
            'age': random.randint(25, 55),
            'initial_deposit': random.uniform(1000, 10000),
            'is_pep': False,
            'is_sanctioned': False,
            'risk_factors': [],
            'behavior_pattern': 'Regular salary deposits, bill payments, occasional purchases'
        }


def generate_transaction_pattern_with_ai(openai_client, customer_profile, num_transactions):
    """Use AI to generate realistic transaction patterns"""

    prompt = f"""Generate a realistic transaction pattern for this customer profile:
Name: {customer_profile['name']}
Occupation: {customer_profile['occupation']}
Behavior: {customer_profile['behavior_pattern']}
Risk Factors: {customer_profile.get('risk_factors', [])}

Generate {num_transactions} transactions over the past 6 months.

Return ONLY a JSON array of transaction objects (no other text):
[
    {{
        "type": "DEPOSIT|WITHDRAWAL|TRANSFER|PAYMENT",
        "amount": number,
        "days_ago": number (0-180),
        "destination_country": "Country Code",
        "description": "Brief description",
        "time_of_day": "MORNING|AFTERNOON|EVENING|NIGHT"
    }}
]

Make patterns realistic:
- Normal customers: Regular deposits, bill payments, small purchases
- Suspicious customers: Structured amounts (e.g., $9,500), odd timing, frequent transfers
- High-risk customers: Large amounts, high-risk countries, layering patterns

Be creative and varied. Each call should generate different patterns."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a financial transaction pattern generator. Always respond with valid JSON array only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=1000
        )

        import json
        pattern_text = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if pattern_text.startswith('```'):
            pattern_text = pattern_text.split('```')[1]
            if pattern_text.startswith('json'):
                pattern_text = pattern_text[4:]

        transactions = json.loads(pattern_text)
        return transactions
    except Exception as e:
        print(f"Warning: AI pattern generation failed ({e}), using fallback")
        return generate_fallback_transactions(customer_profile, num_transactions)


def generate_fallback_transactions(customer_profile, num_transactions):
    """Fallback transaction generation"""
    transactions = []
    behavior = customer_profile.get('behavior_pattern', '')

    for _ in range(num_transactions):
        if 'Structured' in behavior:
            # Structuring pattern
            amount = random.choice([9500, 9800, 9900, 4900, 4500])
        elif 'large' in behavior.lower():
            amount = random.uniform(10000, 50000)
        else:
            amount = random.uniform(100, 5000)

        transactions.append({
            'type': random.choice(['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'PAYMENT']),
            'amount': round(amount, 2),
            'days_ago': random.randint(0, 180),
            'destination_country': customer_profile.get('country', 'US'),
            'description': random.choice(['Business Payment', 'Purchase', 'Transfer', 'Salary']),
            'time_of_day': random.choice(['MORNING', 'AFTERNOON', 'EVENING', 'NIGHT'])
        })

    return transactions


def generate_raw_data_with_ai(num_accounts=100, use_ai=True):
    """Generate raw financial data using AI model"""

    print(f"\nGenerating {num_accounts} raw customer accounts...")

    # Initialize OpenAI if available
    openai_client = None
    if use_ai and OPENAI_API_KEY:
        try:
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            print("✓ AI model initialized (OpenAI GPT-4o-mini)")
        except Exception as e:
            print(f"⚠ AI initialization failed: {e}")
            print("  Falling back to rule-based generation")

    raw_accounts = []

    # Distribution of profile types
    profile_distribution = (
        ['normal'] * 70 +      # 70% normal
        ['suspicious'] * 20 +   # 20% suspicious
        ['high_risk'] * 10      # 10% high risk
    )
    random.shuffle(profile_distribution)

    for i in range(num_accounts):
        profile_type = profile_distribution[i] if i < len(profile_distribution) else 'random'

        if openai_client and random.random() < 0.8:  # 80% use AI, 20% fallback for variety
            print(f"  Generating account {i+1}/{num_accounts} with AI ({profile_type})...", end='\r')
            profile = generate_customer_profile_with_ai(openai_client, profile_type)
        else:
            profile = generate_fallback_profile(profile_type)

        # Add metadata
        account_id = f"RAW{10000 + i}"
        profile['account_id'] = account_id
        profile['date_opened'] = (datetime.now() - timedelta(days=random.randint(30, 730))).strftime('%Y-%m-%d')
        profile['ssn_masked'] = f"XXXXX{random.randint(100, 999)}"

        # Generate transactions for this account
        num_transactions = random.randint(5, 50)
        if openai_client and random.random() < 0.5:  # 50% use AI for transactions
            transactions = generate_transaction_pattern_with_ai(openai_client, profile, num_transactions)
        else:
            transactions = generate_fallback_transactions(profile, num_transactions)

        profile['raw_transactions'] = transactions

        raw_accounts.append(profile)

    print(f"\n✓ Generated {len(raw_accounts)} raw accounts with AI patterns")

    return raw_accounts


def save_raw_data(raw_accounts):
    """Save raw data to JSON file"""
    import json

    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join('raw_data', date_str)
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, 'raw_accounts.json')

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(raw_accounts, f, indent=2, ensure_ascii=False)

    print(f"✓ Raw data saved to: {filepath}")

    return filepath


def main():
    print("\n" + "=" * 80)
    print("AI-POWERED RAW DATA GENERATOR")
    print("=" * 80 + "\n")

    print("This generates realistic financial data with natural AML patterns")
    print("using AI models for variety and realism.\n")

    # Check for OpenAI API key
    openai_key = os.environ.get('OPENAI_API_KEY')
    if not openai_key and len(sys.argv) > 1:
        openai_key = sys.argv[1]

    use_ai = False
    if openai_key:
        os.environ['OPENAI_API_KEY'] = openai_key
        use_ai = True
        print("✓ OpenAI API key provided - will use AI generation")
    else:
        print("⚠ No OpenAI API key - will use rule-based generation")
        print("  Set OPENAI_API_KEY environment variable for AI-powered generation")

    print()

    # Get number of accounts to generate
    num_accounts = 100
    if len(sys.argv) > 2:
        try:
            num_accounts = int(sys.argv[2])
        except ValueError:
            pass

    # Generate raw data
    raw_accounts = generate_raw_data_with_ai(num_accounts, use_ai)

    # Save to file
    filepath = save_raw_data(raw_accounts)

    # Print summary
    print("\n" + "=" * 80)
    print("RAW DATA GENERATION COMPLETE")
    print("=" * 80)
    print(f"\nGenerated: {len(raw_accounts)} accounts")

    # Count characteristics
    normal = len([a for a in raw_accounts if not a.get('is_sanctioned') and not a.get('is_pep')])
    pep = len([a for a in raw_accounts if a.get('is_pep')])
    sanctioned = len([a for a in raw_accounts if a.get('is_sanctioned')])

    print(f"  Normal accounts: {normal}")
    print(f"  PEP accounts: {pep}")
    print(f"  Sanctioned accounts: {sanctioned}")

    total_txns = sum(len(a.get('raw_transactions', [])) for a in raw_accounts)
    print(f"  Total transactions: {total_txns}")

    print(f"\nNext step: Run ETL pipeline to process this data")
    print(f"  python3 etl_pipeline.py {filepath}")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()

