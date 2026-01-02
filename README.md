# Accessible ETL Pipeline UI Dashboard

**AI-Powered Accessible ETL Pipeline with Role-Based Dashboards and Explainable AI**

A comprehensive ETL pipeline system for financial data processing with ML-powered risk analysis, explainable AI (SHAP & LIME), role-based access control, and interactive web dashboards.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [AI Model](#-ai-model)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### 🤖 AI/ML Capabilities
- **RandomForest Classifier** for AML risk prediction
- **SHAP & LIME Explainability** for transparent AI decisions
- **Model Persistence** with versioning and metadata tracking
- **Comprehensive Metrics** (Accuracy, Precision, Recall, F1, ROC-AUC)
- **Feature Importance Analysis**
- **Hyperparameter Tuning**

### 📊 Data Pipeline
- **Raw Data Generation** with realistic financial transactions
- **AML Pattern Detection** (structuring, layering, smurfing)
- **Data Validation & Transformation**
- **Multi-Table Analysis** (Accounts, Transactions, Wire Transfers, Audit Logs)
- **Database Integration** (Supabase/PostgreSQL)
- **Data Lineage Tracking**

### 📈 Interactive Dashboards
- **Role-Based Views** (Compliance Officer, Risk Analyst, Regulatory Officer)
- **4-Table Tabs** with explicit issue segregation
- **Dynamic Charts** (different per role)
- **Real-Time Analytics**
- **Issue Severity Badges** (Critical/Warning/Info)
- **Feedback System** (role-isolated)

### 🔐 Security & Access Control
- **User Authentication** with session management
- **Role-Based Access Control** (RBAC)
- **Password Hashing** (bcrypt)
- **Session Security**
- **Admin Dashboard** for user management

### 🎨 User Experience
- **Responsive Design**
- **Accessibility Features**
- **Interactive Tab Navigation**
- **Real-Time Feedback Forms**
- **Color-Coded Severity Indicators**

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Stage 1: INGEST                                                 │
│  └─> Raw Data Generation (100+ accounts, 2500+ transactions)    │
│      └─> AML Pattern Detection                                   │
│                                                                   │
│  Stage 2: VALIDATE & TRANSFORM                                   │
│  └─> Data Validation                                             │
│  └─> Schema Transformation                                       │
│  └─> Quality Checks                                              │
│                                                                   │
│  Stage 3: LOAD                                                   │
│  └─> Database Loading (Supabase)                                │
│  └─> 4 Tables: accounts, transactions, wire_transfers, logs     │
│                                                                   │
│  Stage 4: ML MODEL                                               │
│  └─> Feature Engineering (14+ features)                         │
│  └─> RandomForest Training                                       │
│  └─> SHAP & LIME Explainability                                 │
│  └─> Model Evaluation & Persistence                             │
│                                                                   │
│  Stage 5: DASHBOARD GENERATION                                   │
│  └─> Role-Specific Analysis                                      │
│  └─> Chart Generation (unique per role)                         │
│  └─> 4-Table Tabs with Issues                                   │
│  └─> HTML Dashboard Export                                       │
│                                                                   │
│  Stage 6: WEB APPLICATION                                        │
│  └─> Flask Web Server                                            │
│  └─> User Authentication                                         │
│  └─> Role-Based Access                                           │
│  └─> Interactive Feedback                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI Model

### Model Details

**Algorithm:** RandomForest Classifier
- 100 decision trees (configurable)
- Max depth: 10 (configurable)
- Balanced class weights
- Multi-threaded training (n_jobs=-1)

**Input Features (14):**
1. `initial_deposit` - Account opening deposit amount
2. `risk_score` - Pre-computed risk score
3. `is_pep` - Politically Exposed Person flag
4. `is_sanctioned` - Sanctions list match
5. `kyc_incomplete` - KYC documentation status
6. `has_anomaly` - Anomaly detection flag
7. `total_transactions` - Transaction count
8. `suspicious_transactions` - Alert count
9. `avg_transaction_amount` - Average transaction size
10. `max_transaction_amount` - Maximum transaction size
11. `total_wires` - Wire transfer count
12. `suspicious_wires` - Suspicious wire count
13. `avg_wire_amount` - Average wire amount
14. `max_wire_amount` - Maximum wire amount

**Output:** Binary classification (High Risk / Low Risk)

### Explainable AI (XAI)

**SHAP (SHapley Additive exPlanations):**
- Global feature importance
- Individual prediction explanations
- Feature contribution analysis
- Interaction effects

**LIME (Local Interpretable Model-agnostic Explanations):**
- Local linear approximations
- Feature impact on individual predictions
- Human-readable explanations

### Model Performance

Typical metrics on test data:
- **Accuracy:** 85-95%
- **Precision:** 80-90%
- **Recall:** 75-85%
- **F1-Score:** 78-88%
- **ROC-AUC:** 0.85-0.95

---

## 🚀 Quick Start

### For GitHub Codespaces Users

1. **Set Secrets** (Settings → Codespaces → Secrets):
   ```
   SUPABASE_KEY=your_supabase_service_role_key
   OPENAI_API_KEY=your_openai_api_key (optional)
   ```

2. **Run Everything:**
   ```bash
   ./start_all.sh
   ```

3. **Access Dashboard:**
   - Open browser to: `http://localhost:8080`
   - Login with demo credentials (see below)

### For Local Development

1. **Clone Repository:**
   ```bash
   git clone <repository-url>
   cd ETL_Pipeline_Dashboard
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables:**
   ```bash
   export SUPABASE_KEY="your_key_here"
   export OPENAI_API_KEY="your_key_here"  # optional
   ```

4. **Run Complete Pipeline:**
   ```bash
   python3 run_complete_pipeline.py
   ```

5. **Start Web Dashboard:**
   ```bash
   python3 start_web_dashboard.py
   ```

---

## 📦 Installation

### Prerequisites

- Python 3.8 - 3.12 (Python 3.13 supported with pinned dependencies)
- 2GB RAM minimum
- Internet connection for API calls

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
python3 -c "from layers.explanation.ml_model import AMLRiskModel; print('✅ All modules installed')"
```

---

## 🎯 Usage

### Command Reference

#### 1. Train ML Model Only
```bash
python3 train_model.py

# With custom Supabase key
python3 train_model.py YOUR_SUPABASE_KEY
```

**Output:**
- Trained model saved to `models/aml_model_YYYYMMDD_HHMMSS.pkl`
- Metadata saved to `models/aml_model_YYYYMMDD_HHMMSS_metadata.json`
- Performance metrics displayed

#### 2. Run Complete Pipeline
```bash
python3 run_complete_pipeline.py

# Generate 50 accounts instead of default 100
python3 run_complete_pipeline.py 50
```

**What it does:**
1. Generates raw financial data
2. Applies AML detection rules
3. Validates and transforms data
4. Loads to database
5. Trains ML model
6. Generates 3 role-based dashboards

**Output:**
- HTML dashboards in `output/YYYYMMDD/`
- Model in `models/`
- Raw data in `raw_data/YYYYMMDD_HHMMSS/`
- Lineage tracking in `lineage/`

#### 3. Start Web Dashboard
```bash
python3 start_web_dashboard.py
```

**Access at:** `http://localhost:8080`

**Demo Credentials:**
- **Compliance Officer:** `compliance@aml.com` / `CompliancePass123!`
- **Risk Analyst:** `risk@aml.com` / `RiskPass123!`
- **Regulatory Officer:** `regulatory@aml.com` / `RegulatoryPass123!`
- **Administrator:** `admin@aml.com` / `AdminPass123!`

#### 4. One-Command Startup
```bash
./start_all.sh

# With custom number of accounts
./start_all.sh 50
```

**This runs everything:**
- Complete pipeline
- Model training
- Dashboard generation
- Web server startup

---

## 📁 Project Structure

```
ETL_Pipeline_Dashboard/
├── layers/                          # Modular architecture
│   ├── data_pipeline/              # ETL components
│   │   ├── config.py               # Configuration
│   │   ├── raw_data_generator.py  # Data generation
│   │   ├── etl_processor.py       # Transform & validate
│   │   ├── database_loader.py     # Database operations
│   │   └── data_lineage.py        # Lineage tracking
│   │
│   ├── explanation/                # ML & Explainability
│   │   └── ml_model.py            # ML model with SHAP/LIME
│   │
│   ├── access/                     # Dashboard generation
│   │   └── dashboard_builder.py   # Role-based dashboards
│   │
│   └── human_interaction/          # Web interface
│       ├── web_application.py     # Flask app
│       ├── feedback_system.py     # Feedback management
│       └── templates/             # HTML templates
│
├── models/                         # Trained ML models
├── output/                         # Generated dashboards
├── raw_data/                       # Generated raw data
├── lineage/                        # Data lineage records
├── feedback/                       # User feedback
│
├── train_model.py                 # ML model training script
├── run_complete_pipeline.py       # Full pipeline script
├── start_web_dashboard.py         # Web server script
├── start_all.sh                   # One-command startup
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required for database functionality
export SUPABASE_KEY="your_supabase_service_role_key"

# Optional for OpenAI features
export OPENAI_API_KEY="your_openai_api_key"

# Optional: Custom Supabase URL
export SUPABASE_URL="https://your-project.supabase.co"
```

### Database Schema

**Supabase Tables:**

1. **account_openings** - Customer account data
2. **transactions** - Transaction records
3. **wire_transfers** - Wire transfer records
4. **audit_logs** - System audit trail

### Model Hyperparameters

Edit in `layers/explanation/ml_model.py`:

```python
model = RandomForestClassifier(
    n_estimators=100,      # Number of trees
    max_depth=10,          # Max tree depth
    random_state=42,       # Reproducibility
    class_weight='balanced',
    n_jobs=-1              # Use all CPU cores
)
```

---

## 🔌 API Endpoints

### Web Application (Port 8080)

**Authentication:**
- `GET /` - Login page
- `POST /login` - User login
- `GET /logout` - User logout

**Dashboards:**
- `GET /dashboard` - Role-specific dashboard view
- `GET /profile` - User profile

**Feedback:**
- `POST /api/feedback` - Submit feedback
- `GET /api/feedback/my-role` - Get role-specific feedback
- `GET /api/feedback/<account_id>` - Get feedback for account

**Admin (Admin role only):**
- `GET /admin` - Admin dashboard
- `GET /admin/users` - User management
- `POST /admin/users` - Create user
- `PUT /admin/users/<user_id>` - Update user
- `DELETE /admin/users/<user_id>` - Delete user

---

## 📊 Dashboard Features

### Role-Specific Views

**Compliance Officer:**
- SAR filing status
- Compliance priorities
- Immediate action items
- Regulatory deadlines

**Risk Analyst:**
- Risk score distribution
- Pattern detection (structuring, layering)
- ML model confidence
- Transaction risk analysis

**Regulatory Officer:**
- Regulatory compliance status
- Violation severity
- Reporting requirements
- KYC/CDD compliance

### 4-Table Tabs

Each dashboard includes tabs for:
1. **Accounts** - Risk scores, PEP, sanctions, KYC issues
2. **Transactions** - Alerts, anomalies, suspicious activity
3. **Wire Transfers** - Suspicious wires, high-risk countries
4. **Audit Logs** - SAR filings, compliance events

### Interactive Features

- **Clickable tabs** for table navigation
- **Severity badges** (Critical/Warning/Info)
- **Feedback forms** for each role
- **Real-time charts** with Chart.js
- **Responsive design** for all devices

---

## 🔬 ML Model Usage

### Training from Scratch

```python
from layers.explanation.ml_model import AMLRiskModel

# Initialize model
model = AMLRiskModel(model_dir='models')

# Fetch your data
data = {
    'accounts': [...],
    'transactions': [...],
    'wire_transfers': [...]
}

# Train
metrics = model.train(data)

# Save
model.save_model(version='v1.0')
```

### Loading Existing Model

```python
from layers.explanation.ml_model import AMLRiskModel

# Load model
model = AMLRiskModel()
model.load_model('models/aml_model_20260102_120000.pkl')

# To use LIME explainer after loading, provide sample data
# model.load_model('models/aml_model_20260102_120000.pkl', X_sample=X_train)

# Make predictions
predictions, probabilities = model.predict(X_test)

# Explain prediction (SHAP only if LIME not recreated)
explanation = model.explain_prediction(X_sample, method='shap')
# Or both if X_sample was provided during load
# explanation = model.explain_prediction(X_sample, method='both')
```

**Note:** LIME explainer contains lambda functions that can't be pickled, so it's recreated on load if you provide sample data.

### Model Evaluation

```python
# Train returns comprehensive metrics
metrics = model.train(data)

print(f"Test Accuracy: {metrics['test']['accuracy']:.2%}")
print(f"Test Precision: {metrics['test']['precision']:.2%}")
print(f"Test Recall: {metrics['test']['recall']:.2%}")
print(f"Test F1-Score: {metrics['test']['f1_score']:.2%}")
print(f"Test ROC-AUC: {metrics['test']['roc_auc']:.2%}")
```

---

## 🎓 Educational Use

This repository demonstrates:
- **ETL Pipeline Architecture** with clear separation of concerns
- **Machine Learning Integration** with proper feature engineering
- **Explainable AI** for transparent predictions
- **Role-Based Access Control** implementation
- **Data Lineage Tracking** for audit trails
- **Interactive Dashboards** with modern web technologies
- **Model Persistence** and versioning
- **Security Best Practices** (password hashing, session management)

---

## 📝 License

This project is for educational and demonstration purposes.

---

## 🤝 Contributing

For issues or questions, please refer to the troubleshooting section or examine the code structure.

---

## 📞 Support

**Quick Commands:**
- Training only: `python3 train_model.py`
- Full pipeline: `python3 run_complete_pipeline.py`
- Web dashboard: `python3 start_web_dashboard.py`
- Everything: `./start_all.sh`

**Default Login:**
- URL: `http://localhost:8080`
- User: `compliance@aml.com`
- Pass: `CompliancePass123!`

---

**Built with:** Python, Flask, RandomForest, SHAP, LIME, Chart.js, Supabase

**Last Updated:** January 2, 2026

