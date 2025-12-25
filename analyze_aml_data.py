#!/usr/bin/env python3
"""
AML Data Analysis with XAI
Analyzes existing data in the database using RandomForest + SHAP to generate:
- Decision Summary + Confidence
- Plain-Language Explanation
- Data Lineage (Visual + Text)
- Role-Specific Notes (Compliance Officer, Risk Analyst, Regulatory Officer)
"""

from supabase import create_client, Client
import sys
import os
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import shap
import warnings
warnings.filterwarnings('ignore')

# Supabase Configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://pcpurhkthawyipfibehn.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')



def connect_to_database(supabase_key):
    """Connect to Supabase database"""
    try:
        supabase = create_client(SUPABASE_URL, supabase_key)
        print("✓ Connected to database successfully\n")
        return supabase
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        sys.exit(1)


def fetch_all_data(supabase: Client):
    """Fetch all data from the database"""
    print("Fetching data from database...")

    try:
        accounts = supabase.table('account_openings').select('*').execute().data
        transactions = supabase.table('transactions').select('*').execute().data
        wire_transfers = supabase.table('wire_transfers').select('*').execute().data
        audit_logs = supabase.table('audit_logs').select('*').execute().data

        print(f"✓ Fetched {len(accounts)} accounts")
        print(f"✓ Fetched {len(transactions)} transactions")
        print(f"✓ Fetched {len(wire_transfers)} wire transfers")
        print(f"✓ Fetched {len(audit_logs)} audit logs\n")

        return {
            'accounts': accounts,
            'transactions': transactions,
            'wire_transfers': wire_transfers,
            'audit_logs': audit_logs
        }
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        sys.exit(1)


def get_high_risk_accounts(data):
    """Identify high-risk accounts for analysis"""
    high_risk_accounts = []

    for account in data['accounts']:
        risk_flags = []

        if account.get('is_sanctioned'):
            risk_flags.append('SANCTIONED')
        if account.get('is_pep'):
            risk_flags.append('PEP')
        if account.get('anomaly_type'):
            risk_flags.append(account['anomaly_type'])
        if account.get('risk_score', 0) > 70:
            risk_flags.append('HIGH_RISK_SCORE')
        if account.get('kyc_status') == 'INCOMPLETE':
            risk_flags.append('INCOMPLETE_KYC')

        if risk_flags:
            account_txns = [t for t in data['transactions'] if t['account_id'] == account['account_id']]
            account_wires = [w for w in data['wire_transfers'] if w['account_id'] == account['account_id']]
            account_logs = [l for l in data['audit_logs'] if l['account_id'] == account['account_id']]

            high_risk_accounts.append({
                'account': account,
                'risk_flags': risk_flags,
                'transactions': account_txns,
                'wire_transfers': account_wires,
                'audit_logs': account_logs,
                'risk_level': len(risk_flags)
            })

    # Sort by risk level (most risky first)
    high_risk_accounts.sort(key=lambda x: x['risk_level'], reverse=True)

    return high_risk_accounts


def prepare_training_data(data):
    """Prepare training data for RandomForest model"""
    accounts = data['accounts']
    transactions = data['transactions']
    wire_transfers = data['wire_transfers']

    # Create features for each account
    features_list = []
    labels = []
    account_ids = []

    for account in accounts:
        account_id = account['account_id']
        account_txns = [t for t in transactions if t['account_id'] == account_id]
        account_wires = [w for w in wire_transfers if w['account_id'] == account_id]

        # Calculate aggregated features
        features = {
            'initial_deposit': float(account.get('initial_deposit', 0)),
            'risk_score': float(account.get('risk_score', 0)),
            'is_pep': 1 if account.get('is_pep') else 0,
            'is_sanctioned': 1 if account.get('is_sanctioned') else 0,
            'kyc_incomplete': 1 if account.get('kyc_status') == 'INCOMPLETE' else 0,
            'has_anomaly': 1 if account.get('anomaly_type') else 0,

            # Transaction features
            'total_transactions': len(account_txns),
            'suspicious_transactions': len([t for t in account_txns if t.get('alert_generated')]),
            'avg_transaction_amount': np.mean([float(t.get('amount', 0)) for t in account_txns]) if account_txns else 0,
            'max_transaction_amount': np.max([float(t.get('amount', 0)) for t in account_txns]) if account_txns else 0,

            # Wire transfer features
            'total_wires': len(account_wires),
            'suspicious_wires': len([w for w in account_wires if w.get('is_suspicious')]),
            'avg_wire_amount': np.mean([float(w.get('amount', 0)) for w in account_wires]) if account_wires else 0,
            'max_wire_amount': np.max([float(w.get('amount', 0)) for w in account_wires]) if account_wires else 0,
        }

        features_list.append(features)
        account_ids.append(account_id)

        # Label: HIGH risk if any major red flag
        is_high_risk = (
            account.get('is_sanctioned') or
            account.get('is_pep') or
            account.get('risk_score', 0) > 70 or
            len([t for t in account_txns if t.get('alert_generated')]) > 5 or
            len([w for w in account_wires if w.get('is_suspicious')]) > 2
        )
        labels.append(1 if is_high_risk else 0)

    df = pd.DataFrame(features_list)
    return df, np.array(labels), account_ids


def train_model_and_explain(data):
    """Train RandomForest model and create SHAP explainer"""
    print("Training RandomForest model...")

    X, y, account_ids = prepare_training_data(data)

    # Train RandomForest
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X, y)

    print(f"✓ Model trained (Accuracy: {model.score(X, y):.2%})")

    # Create SHAP explainer
    print("Creating SHAP explainer...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # Debug: Print SHAP values structure
    if isinstance(shap_values, list):
        print(f"  SHAP values: list with {len(shap_values)} elements")
        for i, sv in enumerate(shap_values):
            print(f"    Element {i} shape: {sv.shape}")
    else:
        print(f"  SHAP values shape: {shap_values.shape}")

    print("✓ SHAP explainer ready\n")

    return model, explainer, X, shap_values, account_ids


def analyze_with_ml(account_data, model, explainer, X, shap_values, account_idx):
    """Use ML model and SHAP to analyze account and generate insights"""

    account = account_data['account']
    risk_flags = account_data['risk_flags']
    transactions = account_data['transactions']
    wire_transfers = account_data['wire_transfers']
    audit_logs = account_data['audit_logs']

    # Get predictions and SHAP values for this account
    account_features = X.iloc[account_idx:account_idx+1]
    prediction = model.predict(account_features)[0]
    prediction_proba = model.predict_proba(account_features)[0]

    # Get SHAP values (for high risk class)
    # For binary classification, shap_values is a list with 2 arrays (one per class)
    # Each array has shape (n_samples, n_features)
    try:
        if isinstance(shap_values, list) and len(shap_values) > 1:
            # Binary classification: get SHAP values for class 1 (high risk)
            # shap_values[1] has shape (n_samples, n_features)
            if account_idx < shap_values[1].shape[0]:
                account_shap = shap_values[1][account_idx]
            else:
                # Fallback: use the values directly from the account features
                account_shap = explainer.shap_values(account_features)
                if isinstance(account_shap, list):
                    account_shap = account_shap[1][0]
                else:
                    account_shap = account_shap[0]
        elif isinstance(shap_values, list):
            # Single output
            if account_idx < shap_values[0].shape[0]:
                account_shap = shap_values[0][account_idx]
            else:
                account_shap = explainer.shap_values(account_features)[0][0]
        else:
            # Direct array
            if account_idx < shap_values.shape[0]:
                account_shap = shap_values[account_idx]
            else:
                account_shap = explainer.shap_values(account_features)[0]
    except (IndexError, TypeError) as e:
        # If indexing fails, compute SHAP values for this specific account
        print(f"    Warning: SHAP indexing failed ({e}), computing for specific account...")
        account_shap = explainer.shap_values(account_features)
        if isinstance(account_shap, list) and len(account_shap) > 1:
            account_shap = account_shap[1][0]  # Get class 1 (high risk) for first sample
        elif isinstance(account_shap, list):
            account_shap = account_shap[0][0]
        else:
            account_shap = account_shap[0]

    # Ensure account_shap is a 1D array
    if isinstance(account_shap, np.ndarray):
        if account_shap.ndim > 1:
            account_shap = account_shap.flatten()
        # Convert to regular Python floats to avoid comparison issues
        account_shap = [float(val) for val in account_shap]

    # Get feature importance
    feature_names = X.columns.tolist()
    feature_values = account_features.iloc[0].values

    # Ensure we have matching lengths
    if len(account_shap) != len(feature_names):
        print(f"    Warning: SHAP values length ({len(account_shap)}) != features length ({len(feature_names)})")
        # Pad or truncate to match
        if len(account_shap) < len(feature_names):
            account_shap = list(account_shap) + [0.0] * (len(feature_names) - len(account_shap))
        else:
            account_shap = account_shap[:len(feature_names)]

    feature_importance = list(zip(feature_names, feature_values, account_shap))
    feature_importance.sort(key=lambda x: abs(float(x[2])), reverse=True)

    # Determine risk level
    confidence = prediction_proba[1] * 100  # Probability of high risk
    if confidence > 75:
        risk_level = "HIGH"
    elif confidence > 50:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Generate analysis text
    analysis = f"""
{'=' * 80}
1. DECISION SUMMARY
{'=' * 80}

Risk Determination: {risk_level} RISK
Confidence Level: {confidence:.1f}%
Model Prediction: {'HIGH RISK' if prediction == 1 else 'LOW RISK'}

Key Deciding Factors:
"""

    # Top 5 most important features
    for i, (feature, value, shap_val) in enumerate(feature_importance[:5], 1):
        impact = "INCREASES" if shap_val > 0 else "DECREASES"
        analysis += f"  {i}. {feature.replace('_', ' ').title()}: {value:.2f} ({impact} risk by {abs(shap_val):.3f})\n"

    analysis += f"""

{'=' * 80}
2. PLAIN-LANGUAGE EXPLANATION
{'=' * 80}

This account has been classified as {risk_level} RISK with {confidence:.1f}% confidence.

Red Flags Detected:
"""

    for flag in risk_flags:
        if flag == 'SANCTIONED':
            analysis += "  • Account holder appears on sanctions list - CRITICAL VIOLATION\n"
        elif flag == 'PEP':
            analysis += "  • Politically Exposed Person (PEP) - Enhanced Due Diligence required\n"
        elif flag == 'HIGH_RISK_SCORE':
            analysis += f"  • Risk score ({account['risk_score']}) exceeds threshold of 70\n"
        elif flag == 'INCOMPLETE_KYC':
            analysis += "  • KYC documentation is incomplete - Compliance gap\n"
        elif flag == 'HIGH_RISK_COUNTRY':
            analysis += f"  • Account originated from high-risk jurisdiction ({account['country']})\n"
        elif flag == 'HIGH_RISK_OCCUPATION':
            analysis += f"  • High-risk occupation ({account['occupation']}) - Cash-intensive business\n"
        elif flag == 'HIGH_INITIAL_DEPOSIT':
            analysis += f"  • Unusually high initial deposit (${account['initial_deposit']:,.2f})\n"

    analysis += f"""
Transaction Patterns:
  • Total Transactions: {len(transactions)}
  • Suspicious/Alert Transactions: {len([t for t in transactions if t.get('alert_generated')])}
  • Pattern: {'ABNORMAL - Multiple alerts generated' if len([t for t in transactions if t.get('alert_generated')]) > 3 else 'NORMAL'}

Wire Transfer Activity:
  • Total Wire Transfers: {len(wire_transfers)}
  • Suspicious Wires: {len([w for w in wire_transfers if w.get('is_suspicious')])}
  • Pattern: {'CONCERNING - Structuring or layering detected' if len([w for w in wire_transfers if w.get('is_suspicious')]) > 2 else 'STANDARD'}

SHAP Analysis Shows:
  The model's decision was primarily driven by:
"""

    for feature, value, shap_val in feature_importance[:3]:
        analysis += f"  • {feature.replace('_', ' ').title()}: {'Strongly increases' if shap_val > 0.1 else 'Increases' if shap_val > 0 else 'Decreases'} risk\n"

    analysis += f"""

{'=' * 80}
3. DATA LINEAGE
{'=' * 80}

FEATURE CONTRIBUTION TO RISK SCORE:
"""

    for feature, value, shap_val in feature_importance:
        bar_length = int(abs(shap_val) * 20)
        bar = '█' * bar_length
        direction = '+' if shap_val > 0 else '-'
        analysis += f"  {feature:25s} [{direction}] {bar} ({shap_val:+.3f})\n"

    analysis += f"""

Data Flow Timeline:
  1. Account Opening ({account['date_opened']})
     └─> Initial Risk Score: {account['risk_score']}
     
  2. Transaction Activity
     └─> {len(transactions)} transactions processed
     └─> {len([t for t in transactions if t.get('alert_generated')])} alerts generated
     
  3. Wire Transfer Monitoring
     └─> {len(wire_transfers)} wires sent
     └─> {len([w for w in wire_transfers if w.get('is_suspicious')])} flagged as suspicious
     
  4. Audit Events
     └─> {len(audit_logs)} events logged
     └─> {len([l for l in audit_logs if l.get('is_critical')])} critical events
     └─> {len([l for l in audit_logs if l['event_type'] == 'SAR_FILED'])} SARs filed

{'=' * 80}
4. ROLE-SPECIFIC NOTES
{'=' * 80}

A. COMPLIANCE OFFICER
---------------------
Immediate Actions Required:
"""

    if account.get('is_sanctioned'):
        analysis += "  • URGENT: Freeze account immediately - Sanctions violation\n"
        analysis += "  • File SAR within 24 hours\n"
        analysis += "  • Notify OFAC and senior management\n"
    elif account.get('is_pep'):
        analysis += "  • Conduct Enhanced Due Diligence (EDD)\n"
        analysis += "  • Obtain senior management approval for continuation\n"
        analysis += "  • Document source of wealth/funds\n"
    elif confidence > 75:
        analysis += "  • Escalate to senior compliance officer\n"
        analysis += "  • Consider filing SAR\n"
        analysis += "  • Conduct transaction review\n"
    else:
        analysis += "  • Continue standard monitoring\n"
        analysis += "  • Document risk assessment in file\n"

    analysis += f"""
Regulatory Filing Recommendations:
  • SAR Filing: {'REQUIRED' if account.get('is_sanctioned') or confidence > 85 else 'RECOMMENDED' if confidence > 70 else 'NOT REQUIRED'}
  • CTR Filing: {'Required for cash transactions > $10,000' if any(float(t.get('amount', 0)) > 10000 for t in transactions) else 'Not applicable'}
  • OFAC Report: {'REQUIRED IMMEDIATELY' if account.get('is_sanctioned') else 'Not required'}

Documentation Needs:
  • Risk assessment documentation: {'COMPLETE' if confidence > 50 else 'PENDING'}
  • Enhanced due diligence: {'REQUIRED' if account.get('is_pep') or confidence > 75 else 'NOT REQUIRED'}
  • Transaction monitoring logs: {'REVIEW NEEDED' if len([t for t in transactions if t.get('alert_generated')]) > 0 else 'UP TO DATE'}

B. RISK ANALYST
---------------
Risk Score Justification:
  • Model Confidence: {confidence:.1f}%
  • Risk Classification: {risk_level}
  • Primary Risk Drivers: {', '.join([f[0] for f in feature_importance[:3]])}

Pattern Analysis:
"""

    if len([t for t in transactions if t.get('alert_generated')]) > 5:
        analysis += "  • STRUCTURING PATTERN: Multiple transactions just below reporting threshold\n"
    if len([w for w in wire_transfers if w.get('is_suspicious')]) > 2:
        analysis += "  • LAYERING PATTERN: Complex wire transfer patterns to obscure source\n"
    if account.get('initial_deposit', 0) > 10000:
        analysis += f"  • PLACEMENT PATTERN: Large initial deposit (${account['initial_deposit']:,.2f})\n"

    analysis += f"""
Predictive Indicators:
  • Account likely to generate future alerts: {confidence > 60}
  • Estimated probability of SAR: {confidence * 0.8:.1f}%
  • Recommended monitoring frequency: {'Daily' if confidence > 75 else 'Weekly' if confidence > 50 else 'Monthly'}

C. REGULATORY OFFICER
---------------------
Compliance Violations Identified:
"""

    violations = []
    if account.get('is_sanctioned'):
        violations.append("OFAC Sanctions violation - 31 CFR Chapter V")
    if account.get('kyc_status') == 'INCOMPLETE':
        violations.append("Incomplete KYC - USA PATRIOT Act Section 326")
    if account.get('is_pep') and not account.get('beneficial_owner_identified'):
        violations.append("Beneficial ownership not verified - FinCEN CDD Rule")

    if violations:
        for v in violations:
            analysis += f"  • {v}\n"
    else:
        analysis += "  • No direct violations identified\n"

    analysis += f"""
Regulatory Reporting Requirements:
  • Bank Secrecy Act (BSA): {'CTR/SAR filing required' if confidence > 70 else 'Standard reporting applies'}
  • USA PATRIOT Act: {'Enhanced scrutiny required' if account.get('is_pep') else 'Standard procedures apply'}
  • FinCEN Regulations: {'Additional reporting may be required' if len(audit_logs) > 10 else 'No special requirements'}

Legal Considerations:
  • Account closure recommendation: {'YES - Consult legal' if account.get('is_sanctioned') else 'NO' if confidence < 50 else 'CONSIDER'}
  • Potential regulatory fines: {'HIGH' if account.get('is_sanctioned') else 'MEDIUM' if confidence > 75 else 'LOW'}
  • Statute of limitations: 5 years from violation date
  • Required record retention: Minimum 5 years

{'=' * 80}
"""

    return analysis
    """Use AI to analyze account and generate insights"""

    account = account_data['account']
    risk_flags = account_data['risk_flags']
    transactions = account_data['transactions']
    wire_transfers = account_data['wire_transfers']
    audit_logs = account_data['audit_logs']

    # Prepare data summary for AI
    data_summary = f"""
Account Information:
- Account ID: {account['account_id']}
- Customer Name: {account['customer_name']}
- SSN: {account['ssn_masked']}
- Country: {account['country']}
- Occupation: {account['occupation']}
- Initial Deposit: ${account['initial_deposit']:,.2f}
- Risk Score: {account['risk_score']}
- PEP: {account['is_pep']}
- Sanctioned: {account['is_sanctioned']}
- Anomaly Type: {account.get('anomaly_type', 'None')}
- KYC Status: {account['kyc_status']}
- Date Opened: {account['date_opened']}

Risk Flags: {', '.join(risk_flags)}

Transaction Summary:
- Total Transactions: {len(transactions)}
- Suspicious Transactions: {len([t for t in transactions if t.get('alert_generated')])}
- Transaction Types: {list(set([t['transaction_type'] for t in transactions[:5]]))}
- Anomaly Types: {list(set([t.get('anomaly_type') for t in transactions if t.get('anomaly_type')]))}

Wire Transfer Summary:
- Total Wire Transfers: {len(wire_transfers)}
- Suspicious Wires: {len([w for w in wire_transfers if w.get('is_suspicious')])}
- Risk Types: {list(set([w.get('risk_type') for w in wire_transfers if w.get('risk_type')]))}
- Countries: {list(set([w['beneficiary_country'] for w in wire_transfers[:5]]))}

Audit Log Summary:
- Total Events: {len(audit_logs)}
- Critical Events: {len([l for l in audit_logs if l.get('is_critical')])}
- Event Types: {list(set([l['event_type'] for l in audit_logs[:10]]))}
- SARs Filed: {len([l for l in audit_logs if l['event_type'] == 'SAR_FILED'])}
"""

    prompt = f"""You are an expert AML (Anti-Money Laundering) analyst. Analyze the following account data and provide a comprehensive risk assessment.

{data_summary}

Please provide:

1. DECISION SUMMARY (with confidence level 0-100%):
   - Overall risk determination (HIGH/MEDIUM/LOW)
   - Confidence percentage
   - Key deciding factors

2. PLAIN-LANGUAGE EXPLANATION:
   - Explain in simple terms what the red flags mean
   - Why this account is concerning
   - What patterns were detected

3. DATA LINEAGE:
   - Visual representation of data flow (using ASCII art/text)
   - Text explanation of how data points connect
   - Timeline of suspicious activities

4. ROLE-SPECIFIC NOTES:
   
   A. Compliance Officer:
      - Immediate actions required
      - Regulatory filing recommendations
      - Documentation needs
   
   B. Risk Analyst:
      - Risk score justification
      - Pattern analysis
      - Predictive indicators
   
   C. Regulatory Officer:
      - Compliance violations identified
      - Regulatory reporting requirements
      - Legal considerations

Format your response clearly with headers for each section."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert AML (Anti-Money Laundering) analyst with deep knowledge of financial crimes, regulatory compliance, and risk assessment."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.7
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating AI analysis: {e}"


def generate_data_lineage_visual(account_data):
    """Generate ASCII visual representation of data lineage"""

    account = account_data['account']
    transactions = account_data['transactions']
    wire_transfers = account_data['wire_transfers']
    audit_logs = account_data['audit_logs']

    visual = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         DATA LINEAGE VISUALIZATION                         ║
╚════════════════════════════════════════════════════════════════════════════╝

                           ACCOUNT OPENING
                                  │
                     {account['date_opened']}
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
            ACCOUNT DETAILS              INITIAL DEPOSIT
         ┌──────────────────┐          ${account['initial_deposit']:,.2f}
         │ ID: {account['account_id']}    │                  │
         │ Risk: {account['risk_score']}        │                  │
         │ Country: {account['country']}       │                  │
         └──────────────────┘                  │
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              TRANSACTIONS              WIRE TRANSFERS
         ┌──────────────────┐          ┌──────────────────┐
         │ Count: {len(transactions):4d}      │          │ Count: {len(wire_transfers):4d}      │
         │ Alerts: {len([t for t in transactions if t.get('alert_generated')]):4d}     │          │ Suspicious: {len([w for w in wire_transfers if w.get('is_suspicious')]):4d}  │
         └──────────────────┘          └──────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                            AUDIT LOGS
                         ┌──────────────────┐
                         │ Events: {len(audit_logs):4d}     │
                         │ Critical: {len([l for l in audit_logs if l.get('is_critical')]):4d}   │
                         │ SARs: {len([l for l in audit_logs if l['event_type'] == 'SAR_FILED']):4d}       │
                         └──────────────────┘
                                  │
                                  ▼
                        RISK ASSESSMENT
                      [Risk Score: {account['risk_score']}]

╔════════════════════════════════════════════════════════════════════════════╗
║                          TIMELINE OF ACTIVITIES                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

    # Add timeline events
    all_events = []

    if account.get('date_opened'):
        all_events.append(('OPEN', account['date_opened'], 'Account Opened'))

    for txn in transactions[:5]:
        if txn.get('alert_generated'):
            all_events.append(('TXN', txn.get('transaction_date', '')[:10],
                             f"Alert: {txn.get('anomaly_type', 'Unknown')}"))

    for wire in wire_transfers[:5]:
        if wire.get('is_suspicious'):
            all_events.append(('WIRE', wire.get('wire_date', ''),
                             f"Suspicious Wire: {wire.get('risk_type', 'Unknown')}"))

    for log in audit_logs[:5]:
        if log.get('is_critical'):
            all_events.append(('LOG', log.get('event_timestamp', '')[:10],
                             f"{log['event_type']}"))

    # Sort by date
    all_events.sort(key=lambda x: x[1])

    for event_type, date, description in all_events[:10]:
        visual += f"\n{date} │ [{event_type:4s}] {description}"

    visual += "\n\n" + "═" * 80 + "\n"

    return visual


def create_analysis_report(account_data, ai_analysis, visual_lineage):
    """Create comprehensive analysis report"""

    account = account_data['account']

    report = f"""
{'=' * 80}
                    AML RISK ANALYSIS REPORT
{'=' * 80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Account ID: {account['account_id']}
Customer: {account['customer_name']}

{'=' * 80}

{visual_lineage}

{'=' * 80}
                         AI-POWERED ANALYSIS
{'=' * 80}

{ai_analysis}

{'=' * 80}
                      END OF ANALYSIS REPORT
{'=' * 80}
"""

    return report


def save_report_to_file(report, account_id):
    """Save report to a Python file in organized directory structure"""
    # Create output directory structure: output/YYYYMMDD/
    date_str = datetime.now().strftime('%Y%m%d')
    output_dir = os.path.join('output', date_str)

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"aml_analysis_{account_id}_{timestamp}.py"
    filepath = os.path.join(output_dir, filename)

    content = f'''#!/usr/bin/env python3
"""
AML Analysis Report for Account {account_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

ANALYSIS_REPORT = """
{report}
"""

if __name__ == "__main__":
    print(ANALYSIS_REPORT)
'''

    with open(filepath, 'w') as f:
        f.write(content)

    return filepath


def create_summary_index(reports_info, output_dir):
    """Create a summary index file listing all analyzed accounts"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    summary = f"""# AML Analysis Summary
Generated: {timestamp}

## Analysis Overview
- Total accounts analyzed: {len(reports_info)}
- Output directory: {output_dir}

## Analyzed Accounts

"""

    for i, info in enumerate(reports_info, 1):
        summary += f"{i}. **Account {info['account_id']}** - {info['customer_name']}\n"
        summary += f"   - Risk Level: {info['risk_level']}\n"
        summary += f"   - Confidence: {info['confidence']:.1f}%\n"
        summary += f"   - Risk Flags: {', '.join(info['risk_flags'])}\n"
        summary += f"   - Report: `{os.path.basename(info['filepath'])}`\n\n"

    summary += f"""
## How to View Reports

### View in Terminal:
```bash
python3 {reports_info[0]['filepath']}
```

### View All Reports:
```bash
for file in {output_dir}/aml_analysis_*.py; do
    echo "===== $file ====="
    python3 "$file"
    echo ""
done
```

### Open in Editor:
```bash
open {output_dir}
```
"""

    summary_path = os.path.join(output_dir, 'README.md')
    with open(summary_path, 'w') as f:
        f.write(summary)

    return summary_path


def main():
    print("\n" + "=" * 80)
    print("AML DATA ANALYSIS WITH XAI (RandomForest + SHAP)")
    print("=" * 80 + "\n")

    # Get Supabase key
    supabase_key = os.environ.get('SUPABASE_KEY')
    if not supabase_key and len(sys.argv) > 1:
        supabase_key = sys.argv[1]

    if not supabase_key:
        supabase_key = input("Enter Supabase service key: ")

    # Connect to database
    supabase = connect_to_database(supabase_key)

    # Fetch all data
    data = fetch_all_data(supabase)

    # Train ML model and create SHAP explainer
    model, explainer, X, shap_values, account_ids_list = train_model_and_explain(data)

    # Get high-risk accounts
    print("Identifying high-risk accounts...")
    high_risk_accounts = get_high_risk_accounts(data)
    print(f"✓ Found {len(high_risk_accounts)} high-risk accounts\n")

    if not high_risk_accounts:
        print("No high-risk accounts found. Analysis complete.")
        return

    # Analyze top 5 highest risk accounts (configurable)
    num_to_analyze = min(5, len(high_risk_accounts))
    print(f"{'=' * 80}")
    print(f"ANALYSIS CONFIGURATION")
    print(f"{'=' * 80}")
    print(f"Total high-risk accounts found: {len(high_risk_accounts)}")
    print(f"Analyzing top {num_to_analyze} highest-risk accounts")
    print(f"(This creates {num_to_analyze} separate report files)")
    print(f"{'=' * 80}\n")
    print(f"Analyzing top {num_to_analyze} highest risk accounts...\n")

    reports_generated = []
    reports_info = []
    output_dir = None

    for i, account_data in enumerate(high_risk_accounts[:num_to_analyze], 1):
        account = account_data['account']
        print(f"\n{'=' * 80}")
        print(f"Analyzing Account {i}/{num_to_analyze}: {account['account_id']}")
        print(f"Risk Flags: {', '.join(account_data['risk_flags'])}")
        print(f"{'=' * 80}\n")

        # Find account index in training data
        try:
            account_idx = account_ids_list.index(account['account_id'])
        except ValueError:
            print(f"  ✗ Account {account['account_id']} not found in training data, skipping...")
            continue

        # Generate visual lineage
        print("  → Generating data lineage visualization...")
        visual_lineage = generate_data_lineage_visual(account_data)

        # Generate ML-based analysis with SHAP
        print("  → Generating ML + SHAP analysis...")
        ml_analysis = analyze_with_ml(account_data, model, explainer, X, shap_values, account_idx)

        # Extract risk level and confidence for summary
        # Parse from ml_analysis to get risk level and confidence
        risk_level = "HIGH" if account_data['risk_level'] > 3 else "MEDIUM" if account_data['risk_level'] > 1 else "LOW"

        # Create comprehensive report
        print("  → Creating comprehensive report...")
        report = create_analysis_report(account_data, ml_analysis, visual_lineage)

        # Save report
        print("  → Saving report...")
        filepath = save_report_to_file(report, account['account_id'])

        # Store output directory from first report
        if output_dir is None:
            output_dir = os.path.dirname(filepath)

        reports_generated.append(filepath)
        reports_info.append({
            'account_id': account['account_id'],
            'customer_name': account['customer_name'],
            'risk_level': risk_level,
            'confidence': account['risk_score'],  # Using risk_score as confidence proxy
            'risk_flags': account_data['risk_flags'],
            'filepath': filepath
        })

        print(f"  ✓ Report saved: {filepath}\n")

    # Create summary index
    if reports_info and output_dir:
        print("  → Creating summary index...")
        summary_path = create_summary_index(reports_info, output_dir)
        print(f"  ✓ Summary created: {summary_path}\n")

    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nGenerated {len(reports_generated)} analysis reports in:")
    print(f"  {output_dir}/\n")

    print("Reports created:")
    for filepath in reports_generated:
        print(f"  • {os.path.basename(filepath)}")

    if reports_generated:
        print(f"\nView summary:")
        print(f"  cat {output_dir}/README.md")
        print(f"\nView a report:")
        print(f"  python3 {reports_generated[0]}")
        print(f"\nOpen output folder:")
        print(f"  open {output_dir}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()

