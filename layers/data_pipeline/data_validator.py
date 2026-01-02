#!/usr/bin/env python3
"""
Data Validator for Raw Financial Data
Validates data quality, completeness, and business rules
"""

from datetime import datetime
import re


class DataValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class DataValidator:
    """Validates raw financial data before processing"""

    def __init__(self):
        self.validation_results = []
        self.errors = []
        self.warnings = []

    def validate_account(self, account, account_index):
        """Validate a single account record"""
        errors = []
        warnings = []

        # Required fields validation
        required_fields = ['account_id', 'name', 'country', 'date_opened', 'initial_deposit']
        for field in required_fields:
            if field not in account or account[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # Account ID format validation
        if not re.match(r'^[A-Z0-9]{6,20}$', str(account['account_id'])):
            warnings.append(f"Account ID format unusual: {account['account_id']}")

        # Name validation
        if len(account.get('name', '')) < 2:
            errors.append(f"Invalid customer name: {account.get('name')}")

        # Country code validation (2-letter ISO code)
        if 'country' in account and len(account['country']) != 2:
            errors.append(f"Invalid country code: {account['country']} (must be 2 letters)")

        # Date validation
        try:
            if 'date_opened' in account:
                date_obj = datetime.strptime(account['date_opened'], '%Y-%m-%d')
                if date_obj > datetime.now():
                    errors.append(f"Account opening date is in the future: {account['date_opened']}")
        except ValueError:
            errors.append(f"Invalid date format: {account.get('date_opened')} (expected YYYY-MM-DD)")

        # Initial deposit validation
        if 'initial_deposit' in account:
            try:
                deposit = float(account['initial_deposit'])
                if deposit < 0:
                    errors.append(f"Initial deposit cannot be negative: {deposit}")
                elif deposit > 1000000:
                    warnings.append(f"Very large initial deposit: ${deposit:,.2f} - requires enhanced due diligence")
            except (ValueError, TypeError):
                errors.append(f"Invalid initial deposit amount: {account.get('initial_deposit')}")

        # PEP and sanctioned flags validation
        if account.get('is_pep') and account.get('is_sanctioned'):
            warnings.append("Account is both PEP and sanctioned - high risk")

        # Occupation validation
        if 'occupation' in account and len(account['occupation']) < 2:
            warnings.append("Occupation field is too short or missing")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_transaction(self, transaction, txn_index, account_id):
        """Validate a single transaction record"""
        errors = []
        warnings = []

        # Required fields
        required_fields = ['type', 'amount', 'days_ago']
        for field in required_fields:
            if field not in transaction:
                errors.append(f"Transaction missing field: {field}")

        if errors:
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # Transaction type validation
        valid_types = ['DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'PAYMENT', 'WIRE_IN', 'WIRE_OUT', 'CASH_DEPOSIT', 'CASH_WITHDRAWAL']
        if transaction.get('type') not in valid_types:
            errors.append(f"Invalid transaction type: {transaction.get('type')}")

        # Amount validation
        try:
            amount = float(transaction['amount'])
            if amount <= 0:
                errors.append(f"Transaction amount must be positive: {amount}")
            elif amount > 10000000:
                warnings.append(f"Extremely large transaction: ${amount:,.2f}")
        except (ValueError, TypeError):
            errors.append(f"Invalid transaction amount: {transaction.get('amount')}")

        # Days ago validation
        try:
            days_ago = int(transaction['days_ago'])
            if days_ago < 0:
                errors.append(f"Days ago cannot be negative: {days_ago}")
            elif days_ago > 1825:  # 5 years
                warnings.append(f"Transaction is very old: {days_ago} days ago")
        except (ValueError, TypeError):
            errors.append(f"Invalid days_ago value: {transaction.get('days_ago')}")

        # Destination country validation for transfers
        if transaction.get('type') in ['TRANSFER', 'WIRE_OUT']:
            if 'destination_country' not in transaction:
                warnings.append("Transfer missing destination country")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_dataset(self, raw_data):
        """Validate entire dataset"""
        print("\n" + "=" * 80)
        print("DATA VALIDATION")
        print("=" * 80 + "\n")

        total_accounts = len(raw_data)
        valid_accounts = 0
        total_errors = 0
        total_warnings = 0

        validation_report = {
            'total_accounts': total_accounts,
            'valid_accounts': 0,
            'invalid_accounts': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'account_results': []
        }

        for i, account in enumerate(raw_data):
            account_result = self.validate_account(account, i)

            # Validate transactions for this account
            transactions = account.get('raw_transactions', [])
            txn_results = []

            for j, txn in enumerate(transactions):
                txn_result = self.validate_transaction(txn, j, account.get('account_id'))
                txn_results.append(txn_result)

                if not txn_result['valid']:
                    account_result['valid'] = False
                    account_result['errors'].extend([f"Transaction {j}: {e}" for e in txn_result['errors']])

                account_result['warnings'].extend([f"Transaction {j}: {w}" for w in txn_result['warnings']])

            # Update counters
            if account_result['valid']:
                valid_accounts += 1

            total_errors += len(account_result['errors'])
            total_warnings += len(account_result['warnings'])

            # Store result
            account_result['account_id'] = account.get('account_id', f'Unknown_{i}')
            account_result['transaction_count'] = len(transactions)
            validation_report['account_results'].append(account_result)

            # Print progress
            if not account_result['valid']:
                print(f"❌ Account {account.get('account_id', i)}: {len(account_result['errors'])} errors")
                for error in account_result['errors'][:3]:  # Show first 3 errors
                    print(f"   - {error}")

        validation_report['valid_accounts'] = valid_accounts
        validation_report['invalid_accounts'] = total_accounts - valid_accounts
        validation_report['total_errors'] = total_errors
        validation_report['total_warnings'] = total_warnings

        # Print summary
        print(f"\n{'=' * 80}")
        print("VALIDATION SUMMARY")
        print(f"{'=' * 80}\n")
        print(f"Total Accounts:     {total_accounts}")
        print(f"✓ Valid Accounts:   {valid_accounts} ({valid_accounts/total_accounts*100:.1f}%)")
        print(f"✗ Invalid Accounts: {total_accounts - valid_accounts}")
        print(f"Total Errors:       {total_errors}")
        print(f"Total Warnings:     {total_warnings}")

        if total_errors > 0:
            print(f"\n⚠️  WARNING: {total_errors} validation errors found!")
            print("   Review errors before proceeding with ETL processing.")
        else:
            print(f"\n✅ All data passed validation!")

        print(f"\n{'=' * 80}\n")

        return validation_report

    def get_validation_summary(self):
        """Get summary of validation results"""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }


def validate_raw_data(filepath):
    """Standalone function to validate raw data file"""
    import json

    print(f"Loading raw data from: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    validator = DataValidator()
    validation_report = validator.validate_dataset(raw_data)

    return validation_report


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python data_validator.py <raw_data_file.json>")
        sys.exit(1)

    raw_file = sys.argv[1]
    report = validate_raw_data(raw_file)

    # Exit with error code if validation failed
    if report['invalid_accounts'] > 0:
        sys.exit(1)

