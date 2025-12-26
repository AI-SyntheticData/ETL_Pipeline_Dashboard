"""
Layer 1: Data Pipeline - Configuration
"""

# Supabase Configuration
SUPABASE_URL = 'https://pcpurhkthawyipfibehn.supabase.co'

# Database Tables
TABLES = {
    'accounts': 'account_openings',
    'transactions': 'transactions',
    'wire_transfers': 'wire_transfers',
    'audit_logs': 'audit_logs'
}

# AML Detection Thresholds
STRUCTURING_THRESHOLD = 10000
STRUCTURING_PATTERN_AMOUNT = 9500
HIGH_VALUE_THRESHOLD = 15000
HIGH_RISK_COUNTRIES = ['IR', 'KP', 'SY', 'VE', 'CU', 'MM', 'LB']
CASH_INTENSIVE_OCCUPATIONS = ['Money Service', 'Casino', 'Jewelry', 'Art Dealer', 'Real Estate']
SUSPICIOUS_HOURS = ['NIGHT']

# Data Generation Settings
DEFAULT_ACCOUNT_COUNT = 100
PROFILE_DISTRIBUTION = {
    'normal': 70,      # 70%
    'suspicious': 20,  # 20%
    'high_risk': 10    # 10%
}

# AI Model Settings
AI_MODEL = 'gpt-4o-mini'
AI_TEMPERATURE = 0.9
AI_MAX_TOKENS = 300

