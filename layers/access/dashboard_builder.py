#!/usr/bin/env python3
"""
AML Comprehensive Dashboard Generator
Analyzes ALL accounts and generates role-based HTML dashboards with 2-panel layout:
- Left Panel: Data Flow Visualization
- Right Panel: Detailed Analysis

Generates separate dashboards for:
1. Compliance Officer
2. Risk Analyst
3. Regulatory Officer
"""

from supabase import create_client, Client
import sys
import os
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import shap
from lime.lime_tabular import LimeTabularExplainer
import warnings
warnings.filterwarnings('ignore')

# Import new components
from layers.data_pipeline.data_lineage import get_lineage_tracker
from layers.human_interaction.feedback_system import add_feedback_to_dashboard

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


def prepare_training_data(data):
    """Prepare training data for RandomForest model"""
    accounts = data['accounts']
    transactions = data['transactions']
    wire_transfers = data['wire_transfers']

    features_list = []
    labels = []
    account_ids = []

    for account in accounts:
        account_id = account['account_id']
        account_txns = [t for t in transactions if t['account_id'] == account_id]
        account_wires = [w for w in wire_transfers if w['account_id'] == account_id]

        features = {
            'initial_deposit': float(account.get('initial_deposit', 0)),
            'risk_score': float(account.get('risk_score', 0)),
            'is_pep': 1 if account.get('is_pep') else 0,
            'is_sanctioned': 1 if account.get('is_sanctioned') else 0,
            'kyc_incomplete': 1 if account.get('kyc_status') == 'INCOMPLETE' else 0,
            'has_anomaly': 1 if account.get('anomaly_type') else 0,
            'total_transactions': len(account_txns),
            'suspicious_transactions': len([t for t in account_txns if t.get('alert_generated')]),
            'avg_transaction_amount': np.mean([float(t.get('amount', 0)) for t in account_txns]) if account_txns else 0,
            'max_transaction_amount': np.max([float(t.get('amount', 0)) for t in account_txns]) if account_txns else 0,
            'total_wires': len(account_wires),
            'suspicious_wires': len([w for w in account_wires if w.get('is_suspicious')]),
            'avg_wire_amount': np.mean([float(w.get('amount', 0)) for w in account_wires]) if account_wires else 0,
            'max_wire_amount': np.max([float(w.get('amount', 0)) for w in account_wires]) if account_wires else 0,
        }

        features_list.append(features)
        account_ids.append(account_id)

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
    """Train RandomForest model and create SHAP and LIME explainers"""
    print("Training RandomForest model...")

    X, y, account_ids = prepare_training_data(data)

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X, y)

    print(f"✓ Model trained (Accuracy: {model.score(X, y):.2%})")

    print("Creating SHAP explainer...")
    shap_explainer = shap.TreeExplainer(model)
    shap_values = shap_explainer.shap_values(X)

    print("✓ SHAP explainer ready")

    print("Creating LIME explainer...")
    lime_explainer = LimeTabularExplainer(
        X.values,
        feature_names=X.columns.tolist(),
        class_names=['Low Risk', 'High Risk'],
        mode='classification',
        random_state=42
    )
    print("✓ LIME explainer ready\n")


    return model, shap_explainer, lime_explainer, X, shap_values, account_ids


def analyze_all_accounts(data, model, lime_explainer, X, shap_values, account_ids_list):
    """Analyze all accounts and return comprehensive results with LIME and SHAP explanations"""
    print("Analyzing all accounts with XAI models (LIME & SHAP)...")

    accounts = data['accounts']
    transactions = data['transactions']
    wire_transfers = data['wire_transfers']
    audit_logs = data['audit_logs']

    predictions = model.predict(X)
    prediction_probas = model.predict_proba(X)

    results = []

    for i, account in enumerate(accounts):
        account_id = account['account_id']

        try:
            idx = account_ids_list.index(account_id)
        except ValueError:
            continue

        account_txns = [t for t in transactions if t['account_id'] == account_id]
        account_wires = [w for w in wire_transfers if w['account_id'] == account_id]
        account_logs = [l for l in audit_logs if l['account_id'] == account_id]

        risk_flags = []
        if account.get('is_sanctioned'):
            risk_flags.append('SANCTIONED')
        if account.get('is_pep'):
            risk_flags.append('PEP')
        if account.get('risk_score', 0) > 70:
            risk_flags.append('HIGH_RISK_SCORE')
        if account.get('kyc_status') == 'INCOMPLETE':
            risk_flags.append('INCOMPLETE_KYC')
        if account.get('anomaly_type'):
            risk_flags.append(account['anomaly_type'])

        confidence = prediction_probas[idx][1] * 100

        if confidence > 75:
            risk_level = "HIGH"
        elif confidence > 50:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Get SHAP values for this account
        if isinstance(shap_values, list) and len(shap_values) > 1:
            account_shap = shap_values[1][idx] if idx < len(shap_values[1]) else None
        else:
            account_shap = None

        # Get LIME explanation for this account
        lime_explanation = None
        if lime_explainer and idx < len(X):
            try:
                lime_exp = lime_explainer.explain_instance(
                    X.iloc[idx].values,
                    model.predict_proba,
                    num_features=len(X.columns)
                )
                lime_explanation = lime_exp.as_list()
            except:
                lime_explanation = None

        results.append({
            'account': account,
            'risk_level': risk_level,
            'confidence': confidence,
            'risk_flags': risk_flags,
            'transactions': account_txns,
            'wire_transfers': account_wires,
            'audit_logs': account_logs,
            'shap_values': account_shap,
            'lime_explanation': lime_explanation,
            'features': X.iloc[idx].to_dict() if idx < len(X) else {}
        })

    # Sort by confidence (highest risk first)
    results.sort(key=lambda x: x['confidence'], reverse=True)

    print(f"✓ Analyzed {len(results)} accounts with XAI explanations\n")

    return results


def generate_compliance_charts_html(stats, results):
    """Generate charts specific to Compliance Officer role"""

    # SAR Filing trends
    sar_filed = len([r for r in results if any(l.get('event_type') == 'SAR_FILED' for l in r.get('audit_logs', []))])
    sar_pending = stats['high_risk_count'] - sar_filed

    charts_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    
    <style>
        .charts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .chart-box {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .chart-box h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .chart-canvas {{
            max-height: 300px;
        }}
    </style>
    
    <div class="charts-container">
        <!-- SAR Status Chart -->
        <div class="chart-box">
            <h3>🚨 SAR Filing Status</h3>
            <canvas id="sarChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- Compliance Priority Chart -->
        <div class="chart-box">
            <h3>⚠️ Compliance Priorities</h3>
            <canvas id="compliancePriorityChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- Account Status Chart -->
        <div class="chart-box">
            <h3>📋 Account Status</h3>
            <canvas id="accountStatusChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- Action Required Chart -->
        <div class="chart-box">
            <h3>✅ Actions Required</h3>
            <canvas id="actionChart" class="chart-canvas"></canvas>
        </div>
    </div>
    
    <script>
    // SAR Status Chart
    const sarCtx = document.getElementById('sarChart').getContext('2d');
    new Chart(sarCtx, {{
        type: 'doughnut',
        data: {{
            labels: ['SARs Filed', 'SARs Pending', 'No Action Needed'],
            datasets: [{{
                data: [{sar_filed}, {sar_pending}, {stats['low_risk_count']}],
                backgroundColor: ['#10b981', '#f59e0b', '#3b82f6'],
                borderWidth: 2,
                borderColor: '#fff'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ position: 'bottom' }}
            }}
        }}
    }});
    
    // Compliance Priority Chart
    const priorityCtx = document.getElementById('compliancePriorityChart').getContext('2d');
    new Chart(priorityCtx, {{
        type: 'bar',
        data: {{
            labels: ['Sanctioned', 'PEP', 'High Risk', 'KYC Incomplete'],
            datasets: [{{
                label: 'Count',
                data: [{stats['sanctioned_count']}, {stats['pep_count']}, {stats['high_risk_count']}, {len([r for r in results if 'INCOMPLETE_KYC' in r['risk_flags']])}],
                backgroundColor: ['#ef4444', '#f59e0b', '#f97316', '#8b5cf6'],
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    
    // Account Status Chart
    const statusCtx = document.getElementById('accountStatusChart').getContext('2d');
    new Chart(statusCtx, {{
        type: 'bar',
        data: {{
            labels: ['High Risk', 'Medium Risk', 'Low Risk'],
            datasets: [{{
                label: 'Accounts',
                data: [{stats['high_risk_count']}, {stats['medium_risk_count']}, {stats['low_risk_count']}],
                backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
                borderWidth: 1
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ x: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    
    // Action Required Chart
    const actionCtx = document.getElementById('actionChart').getContext('2d');
    new Chart(actionCtx, {{
        type: 'bar',
        data: {{
            labels: ['EDD Required', 'SAR Pending', 'Account Freeze', 'Document Review'],
            datasets: [{{
                label: 'Actions',
                data: [{stats['pep_count']}, {sar_pending}, {stats['sanctioned_count']}, {stats['alert_count']}],
                backgroundColor: '#667eea',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    </script>
    """

    return charts_html


def generate_risk_analyst_charts_html(stats, results):
    """Generate charts specific to Risk Analyst role"""

    # Pattern analysis
    structuring = len([r for r in results if any('STRUCTURING' in str(t.get('anomaly_type', '')) for t in r['transactions'])])
    layering = len([r for r in results if len(r['wire_transfers']) >= 3])
    high_value = len([r for r in results if any(float(t.get('amount', 0)) > 15000 for t in r['transactions'])])

    charts_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    
    <style>
        .charts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .chart-box {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .chart-box h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .chart-canvas {{
            max-height: 300px;
        }}
    </style>
    
    <div class="charts-container">
        <!-- Risk Score Distribution -->
        <div class="chart-box">
            <h3>📊 Risk Score Distribution</h3>
            <canvas id="riskScoreChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- AML Pattern Detection -->
        <div class="chart-box">
            <h3>🔍 AML Pattern Detection</h3>
            <canvas id="patternChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- Transaction Risk Analysis -->
        <div class="chart-box">
            <h3>💰 Transaction Risk Analysis</h3>
            <canvas id="txnRiskChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- Risk Confidence Levels -->
        <div class="chart-box">
            <h3>🎯 ML Model Confidence</h3>
            <canvas id="confidenceChart" class="chart-canvas"></canvas>
        </div>
    </div>
    
    <script>
    // Risk Score Distribution
    const riskScoreCtx = document.getElementById('riskScoreChart').getContext('2d');
    new Chart(riskScoreCtx, {{
        type: 'doughnut',
        data: {{
            labels: ['High Risk (75-100)', 'Medium Risk (50-75)', 'Low Risk (0-50)'],
            datasets: [{{
                data: [{stats['high_risk_count']}, {stats['medium_risk_count']}, {stats['low_risk_count']}],
                backgroundColor: ['#ef4444', '#f59e0b', '#10b981'],
                borderWidth: 2,
                borderColor: '#fff'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'bottom' }} }}
        }}
    }});
    
    // AML Pattern Detection
    const patternCtx = document.getElementById('patternChart').getContext('2d');
    new Chart(patternCtx, {{
        type: 'bar',
        data: {{
            labels: ['Structuring', 'Layering', 'High Value', 'Suspicious Wires'],
            datasets: [{{
                label: 'Detected Patterns',
                data: [{structuring}, {layering}, {high_value}, {stats['suspicious_wires']}],
                backgroundColor: ['#8b5cf6', '#ec4899', '#f59e0b', '#ef4444'],
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    
    // Transaction Risk Analysis
    const txnRiskCtx = document.getElementById('txnRiskChart').getContext('2d');
    new Chart(txnRiskCtx, {{
        type: 'bar',
        data: {{
            labels: ['Total Txns', 'Alert Txns', 'Wire Transfers', 'Suspicious Wires'],
            datasets: [{{
                label: 'Volume',
                data: [{stats['total_transactions']}, {stats['alert_count']}, {stats['total_wires']}, {stats['suspicious_wires']}],
                backgroundColor: ['#3b82f6', '#ef4444', '#10b981', '#f59e0b'],
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    
    // ML Model Confidence
    const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
    new Chart(confidenceCtx, {{
        type: 'bar',
        data: {{
            labels: ['>90% Confidence', '75-90%', '50-75%', '<50%'],
            datasets: [{{
                label: 'Accounts',
                data: [
                    {len([r for r in results if r['confidence'] > 90])},
                    {len([r for r in results if 75 < r['confidence'] <= 90])},
                    {len([r for r in results if 50 < r['confidence'] <= 75])},
                    {len([r for r in results if r['confidence'] <= 50])}
                ],
                backgroundColor: '#667eea',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    </script>
    """

    return charts_html


def generate_regulatory_charts_html(stats, results):
    """Generate charts specific to Regulatory Officer role"""

    # Regulatory compliance metrics
    ctr_candidates = len([r for r in results if any(float(t.get('amount', 0)) > 10000 for t in r['transactions'])])
    kyc_complete = len([r for r in results if 'INCOMPLETE_KYC' not in r['risk_flags']])
    kyc_pending = len([r for r in results if 'INCOMPLETE_KYC' in r['risk_flags']])

    charts_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    
    <style>
        .charts-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .chart-box {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .chart-box h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .chart-canvas {{
            max-height: 300px;
        }}
    </style>
    
    <div class="charts-container">
        <!-- Regulatory Compliance Status -->
        <div class="chart-box">
            <h3>⚖️ Regulatory Compliance Status</h3>
            <canvas id="regComplianceChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- Reporting Requirements -->
        <div class="chart-box">
            <h3>📋 Reporting Requirements</h3>
            <canvas id="reportingChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- KYC/CDD Status -->
        <div class="chart-box">
            <h3>🔍 KYC/CDD Compliance</h3>
            <canvas id="kycChart" class="chart-canvas"></canvas>
        </div>
        
        <!-- Violation Severity -->
        <div class="chart-box">
            <h3>⚠️ Violation Severity</h3>
            <canvas id="violationChart" class="chart-canvas"></canvas>
        </div>
    </div>
    
    <script>
    // Regulatory Compliance Status
    const regComplianceCtx = document.getElementById('regComplianceChart').getContext('2d');
    new Chart(regComplianceCtx, {{
        type: 'doughnut',
        data: {{
            labels: ['Compliant', 'Minor Issues', 'Major Issues'],
            datasets: [{{
                data: [{stats['low_risk_count']}, {stats['medium_risk_count']}, {stats['high_risk_count']}],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 2,
                borderColor: '#fff'
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{ legend: {{ position: 'bottom' }} }}
        }}
    }});
    
    // Reporting Requirements
    const reportingCtx = document.getElementById('reportingChart').getContext('2d');
    new Chart(reportingCtx, {{
        type: 'bar',
        data: {{
            labels: ['SARs Filed', 'CTR Candidates', 'PEP Reports', 'Sanctions Hits'],
            datasets: [{{
                label: 'Count',
                data: [{stats['sar_count']}, {ctr_candidates}, {stats['pep_count']}, {stats['sanctioned_count']}],
                backgroundColor: ['#8b5cf6', '#3b82f6', '#f59e0b', '#ef4444'],
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    
    // KYC/CDD Status
    const kycCtx = document.getElementById('kycChart').getContext('2d');
    new Chart(kycCtx, {{
        type: 'bar',
        data: {{
            labels: ['KYC Complete', 'KYC Pending', 'EDD Required'],
            datasets: [{{
                label: 'Accounts',
                data: [{kyc_complete}, {kyc_pending}, {stats['pep_count']}],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                borderWidth: 1
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ x: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    
    // Violation Severity
    const violationCtx = document.getElementById('violationChart').getContext('2d');
    new Chart(violationCtx, {{
        type: 'bar',
        data: {{
            labels: ['Critical', 'High', 'Medium', 'Low'],
            datasets: [{{
                label: 'Violations',
                data: [
                    {stats['sanctioned_count']},
                    {len([r for r in results if r['risk_level'] == 'HIGH' and 'SANCTIONED' not in r['risk_flags']])},
                    {stats['medium_risk_count']},
                    {len([r for r in results if r['risk_level'] == 'LOW' and r['confidence'] > 30])}
                ],
                backgroundColor: ['#7f1d1d', '#ef4444', '#f59e0b', '#fde047'],
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{ y: {{ beginAtZero: true, ticks: {{ precision: 0 }} }} }},
            plugins: {{ legend: {{ display: false }} }}
        }}
    }});
    </script>
    """

    return charts_html


def generate_charts_html(stats, results):
    """Legacy function - no longer used, kept for compatibility"""
    return ""


def generate_data_flow_html(stats):
    """Generate data flow visualization HTML"""

    # Get lineage visualization
    lineage = get_lineage_tracker()
    lineage_html = ""
    if lineage.lineage_records:
        lineage_html = lineage.generate_lineage_visualization_html()

    return f"""
    <div class="data-flow">
        <h2>Data Flow Overview</h2>
        
        {lineage_html}
        
        <div class="flow-diagram">
            <div class="flow-node source">
                <h3>Data Sources</h3>
                <div class="stat">Total Accounts: {stats['total_accounts']}</div>
            </div>
            
            <div class="flow-arrow">↓</div>
            
            <div class="flow-node process">
                <h3>Risk Classification</h3>
                <div class="stat high">High Risk: {stats['high_risk_count']}</div>
                <div class="stat medium">Medium Risk: {stats['medium_risk_count']}</div>
                <div class="stat low">Low Risk: {stats['low_risk_count']}</div>
            </div>
            
            <div class="flow-arrow">↓</div>
            
            <div class="flow-node metrics">
                <h3>Key Metrics</h3>
                <div class="metric">
                    <span class="label">PEP Accounts:</span>
                    <span class="value">{stats['pep_count']}</span>
                </div>
                <div class="metric">
                    <span class="label">Sanctioned:</span>
                    <span class="value">{stats['sanctioned_count']}</span>
                </div>
                <div class="metric">
                    <span class="label">Transaction Alerts:</span>
                    <span class="value">{stats['alert_count']}</span>
                </div>
                <div class="metric">
                    <span class="label">Suspicious Wires:</span>
                    <span class="value">{stats['suspicious_wires']}</span>
                </div>
                <div class="metric">
                    <span class="label">SARs Filed:</span>
                    <span class="value">{stats['sar_count']}</span>
                </div>
            </div>
            
            <div class="flow-arrow">↓</div>
            
            <div class="flow-node output">
                <h3>Analysis Complete</h3>
                <div class="stat">Total Issues: {stats['total_issues']}</div>
            </div>
        </div>
        
        <div class="data-summary">
            <h3>Data Processing Pipeline</h3>
            <ul>
                <li>✓ {stats['total_accounts']} accounts analyzed</li>
                <li>✓ {stats['total_transactions']} transactions processed</li>
                <li>✓ {stats['total_wires']} wire transfers examined</li>
                <li>✓ {stats['total_logs']} audit log entries reviewed</li>
                <li>✓ ML model trained with {stats['total_accounts']} samples</li>
                <li>✓ XAI explainability (LIME + SHAP) computed</li>
            </ul>
        </div>
    </div>
    """


def generate_compliance_officer_report(results, stats):
    """Generate Compliance Officer specific report"""

    # Generate role-specific charts
    charts_html = generate_compliance_charts_html(stats, results)

    html = f"""
    <div class="role-report">
        <h2>🛡️ Compliance Officer Dashboard</h2>
        <p class="role-description">Focus: Regulatory compliance, SAR filing, immediate actions</p>
        
        {charts_html}
        
        <div class="priority-alerts">
            <h3>⚠️ Priority Actions Required</h3>
    """

    # Critical accounts requiring immediate action
    critical = [r for r in results if 'SANCTIONED' in r['risk_flags'] or r['confidence'] > 90]

    if critical:
        html += "<div class='critical-section'>"
        for r in critical[:10]:  # Top 10 critical
            acc = r['account']
            html += f"""
            <div class="alert-item critical">
                <h4>Account {acc['account_id']} - {acc['customer_name']}</h4>
                <div class="alert-details">
                    <span class="badge red">Confidence: {r['confidence']:.1f}%</span>
                    <span class="badge orange">Risk: {r['risk_level']}</span>
                </div>
                <div class="risk-flags">
                    {' '.join([f'<span class="flag">{flag}</span>' for flag in r['risk_flags']])}
                </div>
                <div class="action-required">
                    <strong>Required Actions:</strong>
                    <ul>
                        {'<li>URGENT: File SAR within 24 hours</li>' if 'SANCTIONED' in r['risk_flags'] else ''}
                        {'<li>Freeze account immediately</li>' if 'SANCTIONED' in r['risk_flags'] else ''}
                        {'<li>Conduct Enhanced Due Diligence (EDD)</li>' if 'PEP' in r['risk_flags'] else ''}
                        {'<li>Complete KYC documentation</li>' if 'INCOMPLETE_KYC' in r['risk_flags'] else ''}
                        <li>Document risk assessment</li>
                        <li>Escalate to senior management</li>
                    </ul>
                </div>
            </div>
            """
        html += "</div>"
    else:
        html += "<p class='no-critical'>No critical alerts requiring immediate action.</p>"

    html += f"""
        </div>
        
        <div class="compliance-stats">
            <h3>📊 Compliance Statistics</h3>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{stats['sar_count']}</div>
                    <div class="stat-label">SARs Filed</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{stats['sanctioned_count']}</div>
                    <div class="stat-label">Sanctioned Entities</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{stats['pep_count']}</div>
                    <div class="stat-label">PEP Accounts</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len([r for r in results if 'INCOMPLETE_KYC' in r['risk_flags']])}</div>
                    <div class="stat-label">Incomplete KYC</div>
                </div>
            </div>
        </div>
        
        <div class="all-accounts">
            <h3>📋 All Accounts Overview</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Account ID</th>
                        <th>Customer</th>
                        <th>Risk Level</th>
                        <th>Confidence</th>
                        <th>Risk Flags</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
    """

    for r in results:
        acc = r['account']
        risk_class = 'high' if r['risk_level'] == 'HIGH' else 'medium' if r['risk_level'] == 'MEDIUM' else 'low'

        actions = []
        if 'SANCTIONED' in r['risk_flags']:
            actions.append('File SAR')
        if 'PEP' in r['risk_flags']:
            actions.append('EDD Required')
        if 'INCOMPLETE_KYC' in r['risk_flags']:
            actions.append('Complete KYC')
        if not actions:
            actions.append('Monitor')

        html += f"""
                    <tr class="{risk_class}">
                        <td>{acc['account_id']}</td>
                        <td>{acc['customer_name']}</td>
                        <td><span class="badge {risk_class}">{r['risk_level']}</span></td>
                        <td>{r['confidence']:.1f}%</td>
                        <td>{', '.join(r['risk_flags'][:3])}</td>
                        <td>{', '.join(actions)}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    </div>
    """

    return html


def generate_risk_analyst_report(results, stats):
    """Generate Risk Analyst specific report"""

    # Generate role-specific charts
    charts_html = generate_risk_analyst_charts_html(stats, results)

    html = f"""
    <div class="role-report">
        <h2>📈 Risk Analyst Dashboard</h2>
        <p class="role-description">Focus: Pattern analysis, risk scoring, predictive modeling</p>
        
        {charts_html}
        
        <div class="pattern-analysis">
            <h3>🔍 Pattern Analysis</h3>
    """

    # Analyze patterns
    structuring = len([r for r in results if any('STRUCTURING' in str(t.get('anomaly_type', '')) for t in r['transactions'])])
    layering = len([r for r in results if any('LAYERING' in str(w.get('risk_type', '')) for w in r['wire_transfers'])])
    high_risk_country = len([r for r in results if 'HIGH_RISK_COUNTRY' in r['risk_flags']])

    html += f"""
            <div class="pattern-grid">
                <div class="pattern-box">
                    <h4>Structuring Pattern</h4>
                    <div class="pattern-value">{structuring} accounts</div>
                    <div class="pattern-desc">Multiple transactions just below reporting threshold</div>
                </div>
                <div class="pattern-box">
                    <h4>Layering Pattern</h4>
                    <div class="pattern-value">{layering} accounts</div>
                    <div class="pattern-desc">Complex wire transfers to obscure source</div>
                </div>
                <div class="pattern-box">
                    <h4>Geographic Risk</h4>
                    <div class="pattern-value">{high_risk_country} accounts</div>
                    <div class="pattern-desc">High-risk jurisdiction involvement</div>
                </div>
            </div>
        </div>
        
        <div class="risk-scoring">
            <h3>Risk Scoring Analysis</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Account ID</th>
                        <th>Risk Score</th>
                        <th>ML Confidence</th>
                        <th>Transactions</th>
                        <th>Alerts</th>
                        <th>Pattern</th>
                    </tr>
                </thead>
                <tbody>
    """

    for r in results[:50]:  # Top 50 by risk
        acc = r['account']
        pattern = 'Structuring' if any('STRUCTURING' in str(t.get('anomaly_type', '')) for t in r['transactions']) else 'Layering' if any('LAYERING' in str(w.get('risk_type', '')) for w in r['wire_transfers']) else 'Standard'

        html += f"""
                    <tr>
                        <td>{acc['account_id']}</td>
                        <td>{acc.get('risk_score', 0):.1f}</td>
                        <td>{r['confidence']:.1f}%</td>
                        <td>{len(r['transactions'])}</td>
                        <td>{len([t for t in r['transactions'] if t.get('alert_generated')])}</td>
                        <td>{pattern}</td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
    </div>
    """

    return html


def generate_regulatory_officer_report(results, stats):
    """Generate Regulatory Officer specific report"""

    # Generate role-specific charts
    charts_html = generate_regulatory_charts_html(stats, results)

    html = f"""
    <div class="role-report">
        <h2>⚖️ Regulatory Officer Dashboard</h2>
        <p class="role-description">Focus: Regulatory compliance, violations, reporting requirements</p>
        
        {charts_html}
        
        <div class="regulatory-summary">
            <h3>Regulatory Compliance Summary</h3>
            <div class="compliance-grid">
                <div class="compliance-box">
                    <h4>Bank Secrecy Act (BSA)</h4>
                    <div class="status">✓ {stats['sar_count']} SARs Filed</div>
                    <div class="status">✓ {len([r for r in results if any(float(t.get('amount', 0)) > 10000 for t in r['transactions'])])} CTR Candidates</div>
                </div>
                <div class="compliance-box">
                    <h4>USA PATRIOT Act</h4>
                    <div class="status">{'⚠️' if stats['pep_count'] > 0 else '✓'} {stats['pep_count']} PEP Accounts (EDD Required)</div>
                    <div class="status">✓ CIP Compliance Reviewed</div>
                </div>
                <div class="compliance-box">
                    <h4>OFAC Compliance</h4>
                    <div class="status">{'🔴' if stats['sanctioned_count'] > 0 else '✓'} {stats['sanctioned_count']} Sanctions Violations</div>
                    <div class="status">✓ Watchlist Screening Complete</div>
                </div>
                <div class="compliance-box">
                    <h4>FinCEN Regulations</h4>
                    <div class="status">✓ {len([r for r in results if 'INCOMPLETE_KYC' not in r['risk_flags']])} Accounts CDD Complete</div>
                    <div class="status">{'⚠️' if len([r for r in results if 'INCOMPLETE_KYC' in r['risk_flags']]) > 0 else '✓'} {len([r for r in results if 'INCOMPLETE_KYC' in r['risk_flags']])} Pending KYC</div>
                </div>
            </div>
        </div>
        
        <div class="violations-section">
            <h3>⚠️ Compliance Violations & Issues</h3>
    """

    # List all violations
    violations = []
    for r in results:
        acc = r['account']
        if 'SANCTIONED' in r['risk_flags']:
            violations.append({
                'type': 'CRITICAL',
                'regulation': 'OFAC',
                'account': acc['account_id'],
                'description': 'Account holder on sanctions list',
                'action': 'Immediate account freeze and OFAC reporting'
            })
        if 'PEP' in r['risk_flags'] and not acc.get('beneficial_owner_identified'):
            violations.append({
                'type': 'HIGH',
                'regulation': 'FinCEN CDD Rule',
                'account': acc['account_id'],
                'description': 'PEP beneficial ownership not verified',
                'action': 'Complete beneficial ownership verification'
            })
        if 'INCOMPLETE_KYC' in r['risk_flags']:
            violations.append({
                'type': 'MEDIUM',
                'regulation': 'USA PATRIOT Act Section 326',
                'account': acc['account_id'],
                'description': 'Incomplete KYC documentation',
                'action': 'Complete CIP requirements within 30 days'
            })

    if violations:
        html += "<table class='data-table violations-table'><thead><tr><th>Severity</th><th>Regulation</th><th>Account</th><th>Description</th><th>Required Action</th></tr></thead><tbody>"
        for v in violations[:20]:  # Top 20 violations
            severity_class = 'critical' if v['type'] == 'CRITICAL' else 'high' if v['type'] == 'HIGH' else 'medium'
            html += f"""
            <tr class="{severity_class}">
                <td><span class="badge {severity_class}">{v['type']}</span></td>
                <td>{v['regulation']}</td>
                <td>{v['account']}</td>
                <td>{v['description']}</td>
                <td>{v['action']}</td>
            </tr>
            """
        html += "</tbody></table>"
    else:
        html += "<p class='no-violations'>✓ No critical regulatory violations identified.</p>"

    html += f"""
        </div>
        
        <div class="reporting-requirements">
            <h3>📋 Reporting Requirements</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Report Type</th>
                        <th>Count</th>
                        <th>Deadline</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Suspicious Activity Reports (SAR)</td>
                        <td>{stats['sar_count']}</td>
                        <td>30 days from detection</td>
                        <td><span class="badge green">Filed</span></td>
                    </tr>
                    <tr>
                        <td>Currency Transaction Reports (CTR)</td>
                        <td>{len([r for r in results if any(float(t.get('amount', 0)) > 10000 for t in r['transactions'])])}</td>
                        <td>15 days from transaction</td>
                        <td><span class="badge yellow">Pending Review</span></td>
                    </tr>
                    <tr>
                        <td>OFAC Sanctions Reports</td>
                        <td>{stats['sanctioned_count']}</td>
                        <td>Immediate (within 24 hours)</td>
                        <td><span class="badge {'red' if stats['sanctioned_count'] > 0 else 'green'}">{'URGENT' if stats['sanctioned_count'] > 0 else 'None Required'}</span></td>
                    </tr>
                    <tr>
                        <td>Enhanced Due Diligence (EDD)</td>
                        <td>{stats['pep_count']}</td>
                        <td>Before account relationship</td>
                        <td><span class="badge yellow">In Progress</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    """

    return html


def generate_dashboard_html(role, results, stats, data_flow_html, role_report_html):
    """Generate complete HTML dashboard"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AML Dashboard - {role}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 5px;
        }}
        
        .header .subtitle {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .container {{
            display: flex;
            min-height: calc(100vh - 80px);
        }}
        
        .left-panel {{
            width: 35%;
            background: white;
            padding: 30px;
            box-shadow: 2px 0 10px rgba(0,0,0,0.05);
            overflow-y: auto;
        }}
        
        .right-panel {{
            width: 65%;
            padding: 30px;
            overflow-y: auto;
        }}
        
        .data-flow h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 22px;
        }}
        
        .flow-diagram {{
            margin: 30px 0;
        }}
        
        .flow-node {{
            background: #f8f9fa;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            text-align: center;
        }}
        
        .flow-node.source {{ border-color: #4CAF50; background: #e8f5e9; }}
        .flow-node.process {{ border-color: #2196F3; background: #e3f2fd; }}
        .flow-node.metrics {{ border-color: #FF9800; background: #fff3e0; }}
        .flow-node.output {{ border-color: #9C27B0; background: #f3e5f5; }}
        
        .flow-node h3 {{
            font-size: 16px;
            margin-bottom: 10px;
            color: #333;
        }}
        
        .flow-node .stat {{
            padding: 8px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            font-weight: bold;
        }}
        
        .flow-node .stat.high {{ color: #d32f2f; }}
        .flow-node .stat.medium {{ color: #f57c00; }}
        .flow-node .stat.low {{ color: #388e3c; }}
        
        .flow-arrow {{
            text-align: center;
            font-size: 30px;
            color: #999;
            margin: 10px 0;
        }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 8px;
            border-bottom: 1px solid #eee;
        }}
        
        .metric .label {{
            color: #666;
        }}
        
        .metric .value {{
            font-weight: bold;
            color: #333;
        }}
        
        .data-summary {{
            margin-top: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
        }}
        
        .data-summary h3 {{
            margin-bottom: 15px;
            color: #667eea;
        }}
        
        .data-summary ul {{
            list-style: none;
        }}
        
        .data-summary li {{
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .role-report h2 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 24px;
        }}
        
        .role-description {{
            color: #666;
            font-style: italic;
            margin-bottom: 30px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
        }}
        
        .priority-alerts {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .priority-alerts h3 {{
            color: #d32f2f;
            margin-bottom: 20px;
        }}
        
        .alert-item {{
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }}
        
        .alert-item.critical {{
            border-color: #d32f2f;
            background: #ffebee;
        }}
        
        .alert-item h4 {{
            margin-bottom: 10px;
            color: #333;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin: 5px 5px 5px 0;
        }}
        
        .badge.red {{ background: #d32f2f; color: white; }}
        .badge.orange {{ background: #f57c00; color: white; }}
        .badge.green {{ background: #388e3c; color: white; }}
        .badge.yellow {{ background: #fbc02d; color: #333; }}
        .badge.high {{ background: #d32f2f; color: white; }}
        .badge.medium {{ background: #f57c00; color: white; }}
        .badge.low {{ background: #388e3c; color: white; }}
        .badge.critical {{ background: #b71c1c; color: white; }}
        
        .flag {{
            display: inline-block;
            padding: 4px 10px;
            background: #e0e0e0;
            border-radius: 4px;
            font-size: 11px;
            margin: 3px;
        }}
        
        .action-required {{
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 5px;
        }}
        
        .action-required ul {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        
        .action-required li {{
            margin: 5px 0;
        }}
        
        .stats-grid, .compliance-grid, .pattern-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .stat-box, .compliance-box, .pattern-box {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        .stat-value, .pattern-value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .stat-label, .pattern-desc {{
            color: #666;
            font-size: 14px;
        }}
        
        .data-table {{
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin: 20px 0;
        }}
        
        .data-table thead {{
            background: #667eea;
            color: white;
        }}
        
        .data-table th, .data-table td {{
            padding: 12px 15px;
            text-align: left;
        }}
        
        .data-table tbody tr {{
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .data-table tbody tr:hover {{
            background: #f8f9fa;
        }}
        
        .data-table tbody tr.high {{
            background: #ffebee;
        }}
        
        .data-table tbody tr.medium {{
            background: #fff3e0;
        }}
        
        .data-table tbody tr.low {{
            background: #e8f5e9;
        }}
        
        .bar-chart {{
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            height: 200px;
            padding: 20px;
            background: white;
            border-radius: 10px;
        }}
        
        .bar {{
            width: 80px;
            background: #667eea;
            border-radius: 5px 5px 0 0;
            position: relative;
            min-height: 30px;
        }}
        
        .bar.high {{ background: #d32f2f; }}
        .bar.medium {{ background: #f57c00; }}
        .bar.low {{ background: #388e3c; }}
        
        .bar-label {{
            position: absolute;
            bottom: 5px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            font-size: 12px;
            font-weight: bold;
            text-align: center;
        }}
        
        .no-critical, .no-violations {{
            padding: 20px;
            background: #e8f5e9;
            color: #388e3c;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }}
        
        .compliance-box h4 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .status {{
            padding: 8px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 5px;
            font-size: 14px;
        }}
        
        .all-accounts, .risk-scoring, .violations-section, .reporting-requirements {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        
        h3 {{
            color: #667eea;
            margin-bottom: 20px;
        }}
        
        @media print {{
            .container {{
                display: block;
            }}
            .left-panel, .right-panel {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AML Risk Analysis Dashboard - {role}</h1>
        <div class="subtitle">Generated: {timestamp} | ML Model + XAI (LIME + SHAP) Explainability</div>
    </div>
    
    <div class="container">
        <div class="left-panel">
            {data_flow_html}
        </div>
        
        <div class="right-panel">
            {role_report_html}
        </div>
    </div>
</body>
</html>
    """

    # Add feedback UI to the dashboard
    html = add_feedback_to_dashboard(html)

    return html


def save_dashboard(role, html_content, output_dir):
    """Save dashboard HTML file"""
    filename = f"dashboard_{role.lower().replace(' ', '_')}.html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return filepath


def main():
    print("\n" + "=" * 80)
    print("AML COMPREHENSIVE DASHBOARD GENERATOR")
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

    # Train ML model with LIME and SHAP
    model, shap_explainer, lime_explainer, X, shap_values, account_ids_list = train_model_and_explain(data)

    # Analyze ALL accounts
    results = analyze_all_accounts(data, model, lime_explainer, X, shap_values, account_ids_list)

    # Calculate statistics
    stats = {
        'total_accounts': len(results),
        'high_risk_count': len([r for r in results if r['risk_level'] == 'HIGH']),
        'medium_risk_count': len([r for r in results if r['risk_level'] == 'MEDIUM']),
        'low_risk_count': len([r for r in results if r['risk_level'] == 'LOW']),
        'pep_count': len([r for r in results if 'PEP' in r['risk_flags']]),
        'sanctioned_count': len([r for r in results if 'SANCTIONED' in r['risk_flags']]),
        'alert_count': sum(len([t for t in r['transactions'] if t.get('alert_generated')]) for r in results),
        'suspicious_wires': sum(len([w for w in r['wire_transfers'] if w.get('is_suspicious')]) for r in results),
        'sar_count': sum(len([l for l in r['audit_logs'] if l.get('event_type') == 'SAR_FILED']) for r in results),
        'total_transactions': len(data['transactions']),
        'total_wires': len(data['wire_transfers']),
        'total_logs': len(data['audit_logs']),
        'total_issues': len([r for r in results if r['risk_level'] in ['HIGH', 'MEDIUM']])
    }

    # Create output directory
    date_str = datetime.now().strftime('%Y%m%d')
    output_dir = os.path.join('output', date_str)
    os.makedirs(output_dir, exist_ok=True)

    # Track lineage
    lineage = get_lineage_tracker()

    # Generate data flow HTML (same for all roles)
    data_flow_html = generate_data_flow_html(stats)

    # Generate role-specific dashboards
    print("Generating role-specific dashboards...\n")

    roles = [
        ('Compliance Officer', generate_compliance_officer_report),
        ('Risk Analyst', generate_risk_analyst_report),
        ('Regulatory Officer', generate_regulatory_officer_report)
    ]

    generated_files = []

    for role_name, report_generator in roles:
        print(f"  → Generating {role_name} dashboard...")
        role_report_html = report_generator(results, stats)
        dashboard_html = generate_dashboard_html(role_name, results, stats, data_flow_html, role_report_html)
        filepath = save_dashboard(role_name, dashboard_html, output_dir)
        generated_files.append(filepath)
        print(f"  ✓ Saved: {filepath}")

        # Track dashboard generation
        lineage.record_dashboard_generation(role_name, stats['total_accounts'], filepath)

    # Print summary
    print("\n" + "=" * 80)
    print("DASHBOARD GENERATION COMPLETE")
    print("=" * 80)
    print(f"\nAnalyzed ALL {stats['total_accounts']} accounts")
    print(f"Output directory: {output_dir}/\n")
    print("Generated dashboards:")
    for filepath in generated_files:
        print(f"  • {os.path.basename(filepath)}")

    print(f"\nTo view dashboards:")
    print(f"  open {generated_files[0]}")
    print(f"\nOr open all:")
    for filepath in generated_files:
        print(f"  open {filepath}")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()

