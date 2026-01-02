#!/usr/bin/env python3
"""
ETL Pipeline for AML Risk Detection
Processes raw data, applies risk detection rules, generates alerts
"""

from supabase import create_client, Client
import sys
import os
from datetime import datetime, timedelta
import json
import random

# Import new components
from layers.data_pipeline.data_validator import DataValidator
from layers.data_pipeline.data_lineage import get_lineage_tracker

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://pcpurhkthawyipfibehn.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')

# AML Detection Rules
STRUCTURING_THRESHOLD = 10000
STRUCTURING_PATTERN_AMOUNT = 9500
HIGH_VALUE_THRESHOLD = 15000
SUSPICIOUS_HOURS = ['NIGHT']  # 10 PM - 6 AM
HIGH_RISK_COUNTRIES = ['IR', 'KP', 'SY', 'VE', 'CU', 'MM', 'LB']
CASH_INTENSIVE_OCCUPATIONS = ['Money Service', 'Casino', 'Jewelry', 'Art Dealer', 'Real Estate']


def load_raw_data(filepath):
    """Load raw data from JSON file"""
    print(f"Loading raw data from: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f"✓ Loaded {len(raw_data)} raw accounts")
    return raw_data


def apply_kyc_rules(account):
    """Apply KYC compliance rules"""
    issues = []

    # Rule 1: PEP requires enhanced due diligence
    if account.get('is_pep'):
        issues.append('PEP_ENHANCED_DUE_DILIGENCE_REQUIRED')

    # Rule 2: High-risk country requires additional verification
    if account.get('country') in HIGH_RISK_COUNTRIES:
        issues.append('HIGH_RISK_COUNTRY_VERIFICATION')

    # Rule 3: Sanctioned entities
    if account.get('is_sanctioned'):
        issues.append('SANCTIONED_ENTITY_BLOCKED')

    # Rule 4: Cash-intensive business requires ongoing monitoring
    occupation = account.get('occupation', '')
    if any(keyword in occupation for keyword in CASH_INTENSIVE_OCCUPATIONS):
        issues.append('CASH_INTENSIVE_BUSINESS_MONITORING')

    # Rule 5: Incomplete data
    if not account.get('name') or not account.get('country'):
        issues.append('INCOMPLETE_KYC_DATA')

    return issues


def detect_structuring(transactions):
    """Detect structuring patterns (transactions just below reporting threshold)"""
    alerts = []

    # Group transactions by day
    daily_transactions = {}
    for txn in transactions:
        days_ago = txn.get('days_ago', 0)
        if days_ago not in daily_transactions:
            daily_transactions[days_ago] = []
        daily_transactions[days_ago].append(txn)

    # Rule: Multiple transactions just below $10,000 in same day
    for day, txns in daily_transactions.items():
        below_threshold = [t for t in txns if 9000 < t.get('amount', 0) < STRUCTURING_THRESHOLD]

        if len(below_threshold) >= 2:
            total = sum(t.get('amount', 0) for t in below_threshold)
            if total > STRUCTURING_THRESHOLD:
                alerts.append({
                    'type': 'STRUCTURING',
                    'severity': 'HIGH',
                    'description': f'{len(below_threshold)} transactions totaling ${total:,.2f} just below $10k threshold',
                    'transactions_affected': len(below_threshold)
                })

    # Rule: Consistent amounts just below threshold over time
    near_threshold = [t for t in transactions if 9000 < t.get('amount', 0) < STRUCTURING_THRESHOLD]
    if len(near_threshold) >= 5:
        alerts.append({
            'type': 'REPEATED_STRUCTURING',
            'severity': 'HIGH',
            'description': f'{len(near_threshold)} transactions with amounts just below reporting threshold',
            'transactions_affected': len(near_threshold)
        })

    return alerts


def detect_layering(transactions):
    """Detect layering patterns (complex movements to obscure origin)"""
    alerts = []

    # Rule: Multiple rapid transfers in sequence
    transfers = [t for t in transactions if t.get('type') == 'TRANSFER']
    transfers.sort(key=lambda x: x.get('days_ago', 999))

    rapid_transfers = []
    for i in range(len(transfers) - 1):
        days_diff = abs(transfers[i].get('days_ago', 0) - transfers[i+1].get('days_ago', 0))
        if days_diff <= 1:  # Within 1 day
            rapid_transfers.append(transfers[i])

    if len(rapid_transfers) >= 3:
        total = sum(t.get('amount', 0) for t in rapid_transfers)
        alerts.append({
            'type': 'LAYERING',
            'severity': 'MEDIUM',
            'description': f'Rapid sequence of {len(rapid_transfers)} transfers totaling ${total:,.2f}',
            'transactions_affected': len(rapid_transfers)
        })

    # Rule: Transfers to multiple high-risk countries
    high_risk_transfers = [t for t in transfers if t.get('destination_country') in HIGH_RISK_COUNTRIES]
    if len(high_risk_transfers) >= 2:
        countries = list(set(t.get('destination_country') for t in high_risk_transfers))
        alerts.append({
            'type': 'HIGH_RISK_JURISDICTION_LAYERING',
            'severity': 'HIGH',
            'description': f'Transfers to {len(countries)} high-risk jurisdictions: {", ".join(countries)}',
            'transactions_affected': len(high_risk_transfers)
        })

    return alerts


def detect_smurfing(transactions):
    """Detect smurfing (many small deposits to avoid detection)"""
    alerts = []

    deposits = [t for t in transactions if t.get('type') == 'DEPOSIT']
    small_deposits = [d for d in deposits if 1000 < d.get('amount', 0) < 3000]

    # Rule: Many small deposits in short time period
    recent_small = [d for d in small_deposits if d.get('days_ago', 999) <= 30]

    if len(recent_small) >= 10:
        total = sum(d.get('amount', 0) for d in recent_small)
        alerts.append({
            'type': 'SMURFING',
            'severity': 'MEDIUM',
            'description': f'{len(recent_small)} small deposits (${total:,.2f}) in 30 days - possible smurfing',
            'transactions_affected': len(recent_small)
        })

    return alerts


def detect_unusual_timing(transactions):
    """Detect transactions at unusual times"""
    alerts = []

    night_transactions = [t for t in transactions if t.get('time_of_day') in SUSPICIOUS_HOURS]

    if len(night_transactions) >= 5:
        alerts.append({
            'type': 'UNUSUAL_TIMING',
            'severity': 'LOW',
            'description': f'{len(night_transactions)} transactions during unusual hours (late night)',
            'transactions_affected': len(night_transactions)
        })

    return alerts


def detect_high_value_transactions(transactions):
    """Detect unusually high value transactions"""
    alerts = []

    high_value = [t for t in transactions if t.get('amount', 0) > HIGH_VALUE_THRESHOLD]

    if high_value:
        for txn in high_value:
            alerts.append({
                'type': 'HIGH_VALUE_TRANSACTION',
                'severity': 'MEDIUM',
                'description': f'{txn.get("type")} of ${txn.get("amount", 0):,.2f} exceeds threshold',
                'transactions_affected': 1
            })

    return alerts


def apply_transaction_rules(transactions):
    """Apply all transaction-based detection rules"""
    all_alerts = []

    # Apply each detection rule
    all_alerts.extend(detect_structuring(transactions))
    all_alerts.extend(detect_layering(transactions))
    all_alerts.extend(detect_smurfing(transactions))
    all_alerts.extend(detect_unusual_timing(transactions))
    all_alerts.extend(detect_high_value_transactions(transactions))

    return all_alerts


def calculate_risk_score(account, kyc_issues, transaction_alerts):
    """Calculate overall risk score based on issues and alerts"""
    score = 50.0  # Base score

    # KYC issues
    if 'SANCTIONED_ENTITY_BLOCKED' in kyc_issues:
        score += 40
    if 'PEP_ENHANCED_DUE_DILIGENCE_REQUIRED' in kyc_issues:
        score += 15
    if 'HIGH_RISK_COUNTRY_VERIFICATION' in kyc_issues:
        score += 10
    if 'CASH_INTENSIVE_BUSINESS_MONITORING' in kyc_issues:
        score += 8
    if 'INCOMPLETE_KYC_DATA' in kyc_issues:
        score += 5

    # Transaction alerts
    for alert in transaction_alerts:
        severity = alert.get('severity', 'LOW')
        if severity == 'HIGH':
            score += 15
        elif severity == 'MEDIUM':
            score += 8
        elif severity == 'LOW':
            score += 3

    # Cap at 100
    return min(score, 100.0)


def transform_to_database_format(raw_accounts_with_alerts):
    """Transform processed data to database schema format"""

    accounts = []
    transactions = []
    wire_transfers = []
    audit_logs = []

    transaction_counter = 1
    wire_counter = 1
    log_counter = 1

    for raw in raw_accounts_with_alerts:
        # Account record
        account_id = raw['account_id']

        # Determine primary anomaly type
        anomaly_type = None
        if raw['kyc_issues']:
            if 'SANCTIONED_ENTITY_BLOCKED' in raw['kyc_issues']:
                anomaly_type = 'SANCTIONED'
            elif 'PEP_ENHANCED_DUE_DILIGENCE_REQUIRED' in raw['kyc_issues']:
                anomaly_type = 'PEP'
            elif 'HIGH_RISK_COUNTRY_VERIFICATION' in raw['kyc_issues']:
                anomaly_type = 'HIGH_RISK_COUNTRY'
            elif 'INCOMPLETE_KYC_DATA' in raw['kyc_issues']:
                anomaly_type = 'INCOMPLETE_KYC'

        accounts.append({
            'account_id': account_id,
            'customer_name': raw.get('name', 'Unknown'),
            'ssn_masked': raw.get('ssn_masked', 'XXXXX000'),
            'date_opened': raw.get('date_opened'),
            'country': raw.get('country', 'US'),
            'occupation': raw.get('occupation', 'Unknown'),
            'initial_deposit': round(raw.get('initial_deposit', 0), 2),
            'risk_score': round(raw['risk_score'], 2),
            'is_pep': raw.get('is_pep', False),
            'is_sanctioned': raw.get('is_sanctioned', False),
            'anomaly_type': anomaly_type,
            'kyc_status': 'INCOMPLETE' if 'INCOMPLETE_KYC_DATA' in raw['kyc_issues'] else 'COMPLETE'
        })

        # Transaction records
        for txn in raw.get('raw_transactions', []):
            transaction_id = f"TXN{transaction_counter:06d}"
            transaction_counter += 1

            txn_date = (datetime.now() - timedelta(days=txn.get('days_ago', 0))).strftime('%Y-%m-%d')

            # Check if this transaction triggered an alert
            alert_generated = any(
                alert.get('type') in ['STRUCTURING', 'REPEATED_STRUCTURING', 'SMURFING',
                                     'HIGH_VALUE_TRANSACTION']
                for alert in raw.get('transaction_alerts', [])
            )

            # Determine anomaly type for transaction
            txn_anomaly_type = None
            if alert_generated:
                for alert in raw.get('transaction_alerts', []):
                    if 'STRUCTURING' in alert.get('type', ''):
                        txn_anomaly_type = 'STRUCTURING'
                        break
                    elif alert.get('type') == 'HIGH_VALUE_TRANSACTION':
                        txn_anomaly_type = 'LARGE_CASH'
                        break

            transactions.append({
                'transaction_id': transaction_id,
                'account_id': account_id,
                'transaction_date': txn_date,
                'transaction_type': txn.get('type', 'PAYMENT'),
                'amount': round(txn.get('amount', 0), 2),
                'destination_country': txn.get('destination_country', raw.get('country', 'US')),
                'alert_generated': alert_generated,
                'anomaly_type': txn_anomaly_type
            })

        # Wire transfer records (subset of transfers)
        transfer_txns = [t for t in raw.get('raw_transactions', []) if t.get('type') == 'TRANSFER']
        for txn in transfer_txns[:5]:  # Limit to 5 wires per account
            wire_id = f"WIRE{wire_counter:06d}"
            wire_counter += 1

            wire_date = (datetime.now() - timedelta(days=txn.get('days_ago', 0))).strftime('%Y-%m-%d')

            # Check for wire-specific alerts
            is_suspicious = any(
                alert.get('type') in ['LAYERING', 'HIGH_RISK_JURISDICTION_LAYERING']
                for alert in raw.get('transaction_alerts', [])
            )

            risk_type = None
            if is_suspicious:
                if txn.get('destination_country') in HIGH_RISK_COUNTRIES:
                    risk_type = 'HIGH_RISK_COUNTRY'
                else:
                    risk_type = 'LAYERING_PATTERN'

            wire_transfers.append({
                'wire_id': wire_id,
                'account_id': account_id,
                'amount': round(txn.get('amount', 0), 2),
                'wire_date': wire_date,
                'beneficiary_name': f"Beneficiary {wire_counter}",
                'beneficiary_bank': f"Bank {txn.get('destination_country', 'XX')}",
                'beneficiary_country': txn.get('destination_country', 'US'),
                'purpose': txn.get('description', 'Business Payment'),
                'risk_type': risk_type,
                'is_suspicious': is_suspicious,
                'investigated': False
            })

        # Audit log records
        # Log for account opening
        log_counter += 1
        audit_logs.append({
            'log_id': f"LOG{log_counter:06d}",
            'account_id': account_id,
            'event_timestamp': raw.get('date_opened') + ' 10:00:00',
            'event_type': 'ACCOUNT_OPENED',
            'user_role': 'SYSTEM',
            'description': f"Account opened for {raw.get('name')}",
            'is_critical': False,
            'ip_address': f"192.168.1.{random.randint(1, 255)}"
        })

        # Log for each alert
        for alert in raw.get('transaction_alerts', []):
            log_counter += 1
            is_critical = alert.get('severity') == 'HIGH'

            event_type = 'ALERT_GENERATED'
            if alert.get('type') == 'STRUCTURING':
                event_type = 'STRUCTURING_DETECTED'
            elif alert.get('type') == 'LAYERING':
                event_type = 'LAYERING_DETECTED'

            audit_logs.append({
                'log_id': f"LOG{log_counter:06d}",
                'account_id': account_id,
                'event_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': event_type,
                'user_role': 'AML_SYSTEM',
                'description': alert.get('description', 'Alert detected'),
                'is_critical': is_critical,
                'ip_address': f"10.0.0.{random.randint(1, 255)}"
            })

        # Log SAR filing if very high risk
        if raw['risk_score'] > 90:
            log_counter += 1
            audit_logs.append({
                'log_id': f"LOG{log_counter:06d}",
                'account_id': account_id,
                'event_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': 'SAR_FILED',
                'user_role': 'COMPLIANCE_OFFICER',
                'description': f"SAR filed due to high risk score ({raw['risk_score']:.1f})",
                'is_critical': True,
                'ip_address': f"10.0.1.{random.randint(1, 255)}"
            })

    return {
        'accounts': accounts,
        'transactions': transactions,
        'wire_transfers': wire_transfers,
        'audit_logs': audit_logs
    }


def load_to_database(supabase, transformed_data):
    """Load transformed data into Supabase database"""

    print("\nClearing existing data from database...")

    # Clear existing data (in reverse order due to foreign keys)
    tables_config = [
        ('audit_logs', 'log_id'),
        ('wire_transfers', 'wire_id'),
        ('transactions', 'transaction_id'),
        ('account_openings', 'account_id')
    ]

    for table_name, pk_field in tables_config:
        try:
            result = supabase.table(table_name).delete().neq(pk_field, '').execute()
            print(f"  ✓ Cleared {table_name}")
        except Exception as e:
            print(f"  ⚠ Could not clear {table_name}: {e}")

    print("\nLoading transformed data into database...")

    # Insert data
    for table_name in ['accounts', 'transactions', 'wire_transfers', 'audit_logs']:
        data = transformed_data.get(table_name if table_name != 'accounts' else 'accounts', [])

        if not data:
            continue

        # Map table names
        db_table_name = {
            'accounts': 'account_openings',
            'transactions': 'transactions',
            'wire_transfers': 'wire_transfers',
            'audit_logs': 'audit_logs'
        }[table_name]

        # Insert in batches
        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]

            # Convert datetime objects to strings
            processed_batch = []
            for record in batch:
                processed_record = {}
                for key, value in record.items():
                    if isinstance(value, datetime):
                        processed_record[key] = value.isoformat()
                    else:
                        processed_record[key] = value
                processed_batch.append(processed_record)

            try:
                supabase.table(db_table_name).insert(processed_batch).execute()
            except Exception as e:
                print(f"  ✗ Error inserting into {db_table_name}: {e}")
                raise

        print(f"  ✓ Loaded {len(data)} records into {db_table_name}")


def process_raw_data(raw_data):
    """Main ETL processing logic"""

    print(f"\nProcessing {len(raw_data)} raw accounts...")
    print("Applying AML detection rules...\n")

    processed_accounts = []

    for i, raw_account in enumerate(raw_data):
        print(f"  Processing account {i+1}/{len(raw_data)}: {raw_account['account_id']}...", end='\r')

        # Apply KYC rules
        kyc_issues = apply_kyc_rules(raw_account)

        # Apply transaction rules
        transactions = raw_account.get('raw_transactions', [])
        transaction_alerts = apply_transaction_rules(transactions)

        # Calculate risk score
        risk_score = calculate_risk_score(raw_account, kyc_issues, transaction_alerts)

        # Add to processed data
        processed_account = raw_account.copy()
        processed_account['kyc_issues'] = kyc_issues
        processed_account['transaction_alerts'] = transaction_alerts
        processed_account['risk_score'] = risk_score

        processed_accounts.append(processed_account)

    print(f"\n✓ Processed {len(processed_accounts)} accounts with ETL rules")

    return processed_accounts


def main():
    print("\n" + "=" * 80)
    print("ETL PIPELINE - AML RISK DETECTION")
    print("=" * 80 + "\n")

    # Get raw data file path
    if len(sys.argv) < 2:
        print("Usage: python3 etl_pipeline.py <raw_data_file.json> [supabase_key]")
        print("\nOr with Supabase key:")
        print("  python3 etl_pipeline.py <raw_data_file.json> <supabase_key>")
        sys.exit(1)

    raw_data_file = sys.argv[1]

    # Get Supabase key
    supabase_key = os.environ.get('SUPABASE_KEY')
    if not supabase_key and len(sys.argv) > 2:
        supabase_key = sys.argv[2]

    if not supabase_key or supabase_key == 'skip_db_loading':
        print("⚠ No Supabase key provided. Data will be processed but not loaded to database.")
        print("  Set SUPABASE_KEY environment variable or provide as argument.")
        load_to_db = False
    else:
        load_to_db = True

    # Initialize lineage tracker
    lineage = get_lineage_tracker()
    batch_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    lineage.start_pipeline(batch_id)

    # Step 1: Extract - Load raw data
    print("STEP 1: EXTRACT")
    raw_data = load_raw_data(raw_data_file)
    lineage.record_extraction(raw_data_file, len(raw_data), {'format': 'JSON'})

    # Step 1.5: Validate - Validate raw data
    print("\nSTEP 1.5: VALIDATE")
    validator = DataValidator()
    validation_report = validator.validate_dataset(raw_data)
    lineage.record_validation(
        validation_report['valid_accounts'],
        validation_report['invalid_accounts'],
        validation_report['total_errors'],
        validation_report['total_warnings']
    )

    # Stop if validation failed critically
    if validation_report['invalid_accounts'] > len(raw_data) * 0.5:  # More than 50% invalid
        print("\n❌ CRITICAL: More than 50% of data failed validation!")
        lineage.end_pipeline(success=False, error_message="Data validation failed")
        lineage.save_lineage()
        sys.exit(1)

    # Step 2: Transform - Apply rules and detect issues
    print("\nSTEP 2: TRANSFORM")
    processed_data = process_raw_data(raw_data)
    lineage.record_transformation('aml_risk_detection', len(raw_data), len(processed_data), {
        'rules_applied': ['KYC', 'structuring', 'layering', 'smurfing', 'unusual_timing', 'high_value']
    })

    # Record each rule application
    total_alerts = sum(len(a.get('transaction_alerts', [])) for a in processed_data)
    lineage.record_rule_application('AML_Detection_Rules', len(processed_data), total_alerts)

    # Transform to database format
    print("\nTransforming to database schema...")
    transformed_data = transform_to_database_format(processed_data)
    print(f"✓ Transformed to database format:")
    print(f"  - {len(transformed_data['accounts'])} accounts")
    print(f"  - {len(transformed_data['transactions'])} transactions")
    print(f"  - {len(transformed_data['wire_transfers'])} wire transfers")
    print(f"  - {len(transformed_data['audit_logs'])} audit logs")

    lineage.record_transformation('database_schema_mapping', len(processed_data),
                                  len(transformed_data['accounts']), {
                                      'total_transactions': len(transformed_data['transactions']),
                                      'total_wires': len(transformed_data['wire_transfers']),
                                      'total_logs': len(transformed_data['audit_logs'])
                                  })

    # Step 3: Load - Insert into database
    if load_to_db:
        print("\nSTEP 3: LOAD")
        supabase = create_client(SUPABASE_URL, supabase_key)
        load_to_database(supabase, transformed_data)
        lineage.record_load('Supabase', len(transformed_data['accounts']), 'account_openings')
        lineage.record_load('Supabase', len(transformed_data['transactions']), 'transactions')
        lineage.record_load('Supabase', len(transformed_data['wire_transfers']), 'wire_transfers')
        lineage.record_load('Supabase', len(transformed_data['audit_logs']), 'audit_logs')

    # Print summary
    print("\n" + "=" * 80)
    print("ETL PIPELINE COMPLETE")
    print("=" * 80)

    # Statistics
    high_risk = len([a for a in processed_data if a['risk_score'] > 75])
    medium_risk = len([a for a in processed_data if 50 < a['risk_score'] <= 75])
    low_risk = len([a for a in processed_data if a['risk_score'] <= 50])

    total_alerts = sum(len(a.get('transaction_alerts', [])) for a in processed_data)
    critical_alerts = sum(1 for a in processed_data for alert in a.get('transaction_alerts', [])
                         if alert.get('severity') == 'HIGH')

    print(f"\nRisk Distribution:")
    print(f"  High Risk (>75):     {high_risk}")
    print(f"  Medium Risk (50-75): {medium_risk}")
    print(f"  Low Risk (<50):      {low_risk}")

    print(f"\nAlerts Generated:")
    print(f"  Total alerts:        {total_alerts}")
    print(f"  Critical alerts:     {critical_alerts}")

    # End pipeline tracking
    lineage.end_pipeline(success=True)
    lineage.print_lineage()
    lineage.save_lineage()

    if load_to_db:
        print(f"\nNext step: Analyze data")
        print(f"  python3 run_dashboard.py")
    else:
        print(f"\nData processed but not loaded to database (no Supabase key)")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()

