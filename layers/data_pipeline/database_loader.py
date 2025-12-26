#!/usr/bin/env python3
"""
STANDALONE Data Generator
This script generates and loads synthetic AML data into existing Supabase tables.
Just run: python load_data.py SUPABASE_SERVICE_KEY
Or: python load_data.py postgresql://postgres:PASSWORD@db.pcpurhkthawyipfibehn.supabase.co:5432/postgres
"""

from supabase import create_client, Client
import random
from datetime import datetime, timedelta
import sys
import os
from urllib.parse import urlparse

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://pcpurhkthawyipfibehn.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

def parse_connection_url(url):
    """Parse PostgreSQL connection URL and extract password"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['postgres', 'postgresql']:
            return None
        return parsed.password
    except Exception:
        return None

def mask_ssn(ssn_num):
    """Mask SSN to show only last 3 digits"""
    return f"XXXXXXX{ssn_num:03d}"

def generate_account_openings(num_records=500):
    """Generate account opening records with AML red flags"""
    accounts = []

    countries_high_risk = ['RU', 'IR', 'KP', 'SY', 'MM', 'AF', 'IQ', 'VE', 'CU']
    countries_low_risk = ['US', 'UK', 'CA', 'DE', 'FR', 'AU', 'JP', 'SG', 'CH', 'NL']

    occupations_high_risk = ['Money Services', 'Casino Owner', 'Jeweler', 'Art Dealer', 'Cash Business', 'Used Car Dealer', 'Real Estate']
    occupations_low_risk = ['Teacher', 'Engineer', 'Doctor', 'Accountant', 'Nurse', 'Software Developer', 'Manager', 'Scientist']

    first_names = ['John', 'Mary', 'Robert', 'Patricia', 'Michael', 'Jennifer', 'William', 'Linda', 'David', 'Elizabeth']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

    for i in range(num_records):
        account_id = f"ACC{10000 + i}"
        is_high_risk = random.random() < 0.20

        if is_high_risk:
            country = random.choice(countries_high_risk)
            occupation = random.choice(occupations_high_risk)
            initial_deposit = random.uniform(15000, 500000)
            risk_score = random.uniform(70, 99)
        else:
            country = random.choice(countries_low_risk)
            occupation = random.choice(occupations_low_risk)
            initial_deposit = random.uniform(100, 15000)
            risk_score = random.uniform(10, 50)

        # Determine primary anomaly type (most severe)
        anomaly_type = None

        is_pep = random.random() < 0.05
        is_sanctioned = random.random() < 0.02

        if is_sanctioned:
            anomaly_type = 'SANCTIONED'
        elif is_pep:
            anomaly_type = 'PEP'
        elif country in countries_high_risk:
            anomaly_type = 'HIGH_RISK_COUNTRY'
        elif occupation in occupations_high_risk:
            anomaly_type = 'HIGH_RISK_OCCUPATION'
        elif initial_deposit > 10000:
            anomaly_type = 'HIGH_INITIAL_DEPOSIT'

        account = {
            'account_id': account_id,
            'customer_name': f"{random.choice(first_names)} {random.choice(last_names)}",
            'ssn_masked': mask_ssn(random.randint(1, 999)),
            'date_opened': (datetime.now() - timedelta(days=random.randint(1, 730))).strftime('%Y-%m-%d'),
            'country': country,
            'occupation': occupation,
            'initial_deposit': round(initial_deposit, 2),
            'risk_score': round(risk_score, 2),
            'is_pep': is_pep,
            'is_sanctioned': is_sanctioned,
            'anomaly_type': anomaly_type,
            'kyc_status': 'INCOMPLETE' if is_high_risk and random.random() < 0.3 else 'COMPLETE',
            'beneficial_owner_identified': not (is_high_risk and random.random() < 0.2)
        }
        accounts.append(account)

    return accounts

def generate_transactions(num_records=2000, account_ids=None):
    """Generate transaction records with suspicious patterns"""
    transactions = []
    transaction_types = ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'PAYMENT', 'CASH_DEPOSIT', 'CASH_WITHDRAWAL', 'WIRE_IN', 'WIRE_OUT']

    for i in range(num_records):
        transaction_id = f"TXN{100000 + i}"
        account_id = random.choice(account_ids) if account_ids else f"ACC{10000 + random.randint(0, 499)}"
        txn_type = random.choice(transaction_types)
        is_suspicious = random.random() < 0.15

        if is_suspicious:
            if random.random() < 0.3:
                amount = random.uniform(9000, 9990)
                anomaly = 'STRUCTURING'
            elif random.random() < 0.3:
                amount = random.uniform(20000, 500000)
                txn_type = random.choice(['CASH_DEPOSIT', 'CASH_WITHDRAWAL'])
                anomaly = 'LARGE_CASH'
            elif random.random() < 0.2:
                amount = random.choice([5000, 7000, 8000, 9000, 9500, 9900])
                anomaly = 'ROUND_AMOUNT'
            else:
                amount = random.uniform(5000, 50000)
                anomaly = 'RAPID_MOVEMENT'
        else:
            amount = random.uniform(10, 5000)
            anomaly = None

        high_risk_countries = ['RU', 'IR', 'KP', 'SY', 'CN', 'VE', 'CU']
        destination_country = random.choice(high_risk_countries) if random.random() < 0.1 else random.choice(['US', 'UK', 'CA'])

        if destination_country in high_risk_countries and anomaly is None:
            anomaly = 'HIGH_RISK_DESTINATION'

        hour = random.randint(0, 23)
        if hour in [0, 1, 2, 3, 4, 5] and amount > 5000 and anomaly is None:
            anomaly = 'ODD_HOURS'

        transaction_date = datetime.now() - timedelta(days=random.randint(0, 180), hours=hour)

        transaction = {
            'transaction_id': transaction_id,
            'account_id': account_id,
            'transaction_type': txn_type,
            'amount': round(amount, 2),
            'transaction_date': transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
            'destination_country': destination_country,
            'description': f"{txn_type.replace('_', ' ').title()} transaction",
            'anomaly_type': anomaly,
            'alert_generated': anomaly is not None,
            'reviewed': random.random() < 0.5 if anomaly else False
        }
        transactions.append(transaction)

    return transactions

def generate_wire_transfers(num_records=800, account_ids=None):
    """Generate wire transfer records with AML issues"""
    wire_transfers = []
    high_risk_banks = ['Bank of Tehran', 'Moscow Financial', 'Pyongyang Bank', 'Damascus Trust']
    normal_banks = ['Chase Bank', 'Bank of America', 'Wells Fargo', 'HSBC', 'Deutsche Bank']
    high_risk_countries = ['IR', 'RU', 'KP', 'SY', 'VE', 'CU', 'MM']
    normal_countries = ['US', 'UK', 'CA', 'DE', 'FR', 'AU']

    for i in range(num_records):
        wire_id = f"WIRE{50000 + i}"
        account_id = random.choice(account_ids) if account_ids else f"ACC{10000 + random.randint(0, 499)}"
        is_suspicious = random.random() < 0.25

        risk_type = None

        if is_suspicious:
            if random.random() < 0.4:
                beneficiary_country = random.choice(high_risk_countries)
                beneficiary_bank = random.choice(high_risk_banks)
                amount = random.uniform(10000, 500000)
                risk_type = 'HIGH_RISK_COUNTRY'
            elif random.random() < 0.5:
                beneficiary_country = random.choice(normal_countries)
                beneficiary_bank = random.choice(normal_banks)
                amount = random.uniform(15000, 100000)
                risk_type = 'LAYERING_PATTERN'
            else:
                beneficiary_country = random.choice(normal_countries)
                beneficiary_bank = random.choice(normal_banks)
                amount = random.uniform(9000, 9950)
                risk_type = 'STRUCTURING'
        else:
            beneficiary_country = random.choice(normal_countries)
            beneficiary_bank = random.choice(normal_banks)
            amount = random.uniform(500, 15000)

        shell_company_names = ['LLC Holdings', 'International Trade Corp', 'Global Investments Ltd', 'Trading Company SA']
        normal_company_names = ['Acme Corporation', 'Tech Solutions Inc', 'Retail Store', 'Manufacturing Co']

        is_shell = random.random() < 0.1
        if is_shell:
            beneficiary_name = random.choice(shell_company_names)
            if not risk_type:
                risk_type = 'SHELL_COMPANY'
        else:
            beneficiary_name = random.choice(normal_company_names)

        missing_info = random.random() < 0.08
        if missing_info and not risk_type:
            risk_type = 'INCOMPLETE_INFO'

        wire_transfer = {
            'wire_id': wire_id,
            'account_id': account_id,
            'amount': round(amount, 2),
            'wire_date': (datetime.now() - timedelta(days=random.randint(0, 180))).strftime('%Y-%m-%d'),
            'beneficiary_name': beneficiary_name if not missing_info else None,
            'beneficiary_bank': beneficiary_bank,
            'beneficiary_country': beneficiary_country,
            'purpose': random.choice(['Business Payment', 'Investment', 'Trade', 'Services']) if not missing_info else None,
            'risk_type': risk_type,
            'is_suspicious': risk_type is not None,
            'investigated': random.random() < 0.3 if risk_type else False
        }
        wire_transfers.append(wire_transfer)

    return wire_transfers

def generate_audit_logs(num_records=1500, account_ids=None):
    """Generate audit log entries"""
    audit_logs = []
    event_types = ['ACCOUNT_OPENED', 'ALERT_GENERATED', 'ALERT_REVIEWED', 'ALERT_CLEARED', 'ALERT_ESCALATED',
                   'SAR_FILED', 'CTR_FILED', 'KYC_UPDATED', 'RISK_SCORE_CHANGED', 'WATCHLIST_HIT']
    user_roles = ['COMPLIANCE_OFFICER', 'SYSTEM', 'ANALYST', 'MANAGER', 'AML_SPECIALIST']

    for i in range(num_records):
        log_id = f"LOG{200000 + i}"
        account_id = random.choice(account_ids) if account_ids else f"ACC{10000 + random.randint(0, 499)}"
        event_type = random.choice(event_types)
        user_role = 'SYSTEM' if event_type in ['ACCOUNT_OPENED', 'ALERT_GENERATED', 'WATCHLIST_HIT'] else random.choice(user_roles)

        event_descriptions = {
            'ACCOUNT_OPENED': 'New account opened',
            'ALERT_GENERATED': 'Automated alert triggered for suspicious transaction pattern',
            'ALERT_REVIEWED': 'Alert reviewed by compliance team',
            'ALERT_CLEARED': 'Alert cleared - no suspicious activity found',
            'ALERT_ESCALATED': 'Alert escalated to senior compliance officer',
            'SAR_FILED': 'Suspicious Activity Report filed with FinCEN',
            'CTR_FILED': 'Currency Transaction Report filed',
            'WATCHLIST_HIT': 'Customer matched against OFAC/sanctions watchlist'
        }

        is_critical = event_type in ['SAR_FILED', 'ALERT_ESCALATED', 'WATCHLIST_HIT']
        action_taken = random.random() < 0.7 if is_critical else random.random() < 0.9
        log_date = datetime.now() - timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))

        if is_critical and not action_taken:
            notes = f"Issue pending for {random.randint(15, 90)} days - requires immediate attention"
        else:
            notes = event_descriptions.get(event_type, 'System event')

        audit_log = {
            'log_id': log_id,
            'account_id': account_id,
            'event_type': event_type,
            'event_timestamp': log_date.strftime('%Y-%m-%d %H:%M:%S'),
            'user_role': user_role,
            'description': notes,
            'action_taken': action_taken,
            'is_critical': is_critical,
            'ip_address': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        }
        audit_logs.append(audit_log)

    return audit_logs


def clear_existing_data(supabase: Client):
    """Clear all existing data from tables (in reverse order due to foreign keys)"""
    tables_config = [
        ('audit_logs', 'log_id'),
        ('wire_transfers', 'wire_id'),
        ('transactions', 'transaction_id'),
        ('account_openings', 'account_id')
    ]

    print("Clearing existing data from tables...")
    for table_name, pk_field in tables_config:
        try:
            # Delete all records using neq filter (not equal to empty string deletes all)
            # This performs a bulk delete operation, similar to TRUNCATE but respects foreign keys
            result = supabase.table(table_name).delete().neq(pk_field, '').execute()
            print(f"✓ Cleared all records from {table_name}")
        except Exception as e:
            # If table is empty or other error, just continue
            if "No rows deleted" in str(e) or "0 rows" in str(e):
                print(f"✓ Table {table_name} is already empty")
            else:
                print(f"  Warning: Could not clear {table_name}: {e}")

def insert_data(supabase: Client, table_name, data):
    """Insert data using Supabase client"""
    if not data:
        return

    # Convert date/datetime objects to strings for JSON serialization
    processed_data = []
    for record in data:
        processed_record = {}
        for key, value in record.items():
            if isinstance(value, (datetime, )):
                processed_record[key] = value.isoformat()
            elif isinstance(value, dict):
                processed_record[key] = value
            else:
                processed_record[key] = value
        processed_data.append(processed_record)

    # Insert in batches of 100 to avoid payload size issues
    batch_size = 100
    for i in range(0, len(processed_data), batch_size):
        batch = processed_data[i:i+batch_size]
        supabase.table(table_name).insert(batch).execute()

    print(f"✓ Inserted {len(data)} records into {table_name}")

def print_summary(supabase: Client):
    """Print statistics using Supabase client"""

    pep_count = len(supabase.table('account_openings').select('*').eq('is_pep', True).execute().data)
    sanctioned_count = len(supabase.table('account_openings').select('*').eq('is_sanctioned', True).execute().data)
    alerts_count = len(supabase.table('transactions').select('*').eq('alert_generated', True).execute().data)
    suspicious_wires = len(supabase.table('wire_transfers').select('*').eq('is_suspicious', True).execute().data)
    sar_count = len(supabase.table('audit_logs').select('*').eq('event_type', 'SAR_FILED').execute().data)


    print("\n" + "=" * 60)
    print("AML ISSUES SUMMARY")
    print("=" * 60)
    print(f"PEP Accounts: {pep_count}")
    print(f"Sanctioned Accounts: {sanctioned_count}")
    print(f"Transaction Alerts: {alerts_count}")
    print(f"Suspicious Wire Transfers: {suspicious_wires}")
    print(f"SARs Filed: {sar_count}")
    print("=" * 60)

def main():
    print("\n" + "=" * 60)
    print("ETL PIPELINE - SYNTHETIC DATA GENERATOR")
    print("=" * 60)
    print("\nGenerating AML compliance data with masked PII...")

    # Check if Supabase key is provided
    supabase_key = os.environ.get('SUPABASE_KEY')
    if not supabase_key and len(sys.argv) > 1:
        supabase_key = sys.argv[1]

    # Try to parse as connection URL to extract password
    if supabase_key and supabase_key.startswith(('postgres://', 'postgresql://')):
        password = parse_connection_url(supabase_key)
        if password:
            supabase_key = password
            print("Extracted password from connection URL")

    if not supabase_key:
        supabase_key = input("Enter Supabase service key or database password: ")
        if supabase_key.startswith(('postgres://', 'postgresql://')):
            password = parse_connection_url(supabase_key)
            if password:
                supabase_key = password

    print(f"\nConnection Details:")
    print(f"  Supabase URL: {SUPABASE_URL}")
    print()

    try:
        print("Connecting to Supabase...")
        supabase: Client = create_client(SUPABASE_URL, supabase_key)
        print("✓ Connected successfully\n")

        # Clear existing data first to avoid duplicate key errors
        clear_existing_data(supabase)
        print()

        print("Generating account openings data...")
        accounts = generate_account_openings(500)
        account_ids = [acc['account_id'] for acc in accounts]
        insert_data(supabase, 'account_openings', accounts)

        print("Generating transactions data...")
        transactions = generate_transactions(2000, account_ids)
        insert_data(supabase, 'transactions', transactions)

        print("Generating wire transfers data...")
        wire_transfers = generate_wire_transfers(800, account_ids)
        insert_data(supabase, 'wire_transfers', wire_transfers)

        print("Generating audit logs data...")
        audit_logs = generate_audit_logs(1500, account_ids)
        insert_data(supabase, 'audit_logs', audit_logs)

        print_summary(supabase)

        print("\n✓ Data generation completed successfully!\n")

    except Exception as e:
        error_msg = str(e)
        print(f"\n✗ Error: {error_msg}\n")

        if "API key" in error_msg or "Invalid API" in error_msg or "JWT" in error_msg:
            print("Authentication Failed!")
            print("\nPlease check:")
            print("1. Your Supabase service key is correct")
            print("2. You're using the 'service_role' key (not 'anon' key)")
            print("3. Your Supabase project is active")
        elif "violates foreign key constraint" in error_msg:
            print("Foreign Key Constraint Error!")
            print("\nThis may happen if:")
            print("1. Tables already have data")
            print("2. Clear existing data first or use different account IDs")
        else:
            print("\nPlease check your configuration and try again.")

        sys.exit(1)

if __name__ == "__main__":
    main()

