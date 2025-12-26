# AML Pipeline Dashboard

A production-grade Anti-Money Laundering (AML) detection system with AI-powered data generation, ETL processing, ML analysis, and role-based dashboards.

## Architecture

This system follows a **4-layer architecture** for clean separation of concerns:

```
┌─────────────────────────────────────────┐
│  LAYER 4: Human Interaction            │
│  Web UI, Authentication, Templates     │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  LAYER 3: Access                        │
│  Reports, Dashboards, Data Aggregation  │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  LAYER 2: Explanation                   │
│  ML Models, SHAP, Risk Analysis         │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│  LAYER 1: Data Pipeline                 │
│  Raw Data, ETL, Database Operations     │
└─────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_KEY="your_supabase_service_key"
export OPENAI_API_KEY="your_openai_api_key"  # Optional, for AI-powered generation
```

### Complete End-to-End Flow

```bash
# Run the complete pipeline (all stages)
python3 run_complete_pipeline.py
```

This will:
1. ✅ Generate raw financial data with AI
2. ✅ Apply ETL rules and detect AML patterns
3. ✅ Load clean data to database
4. ✅ Generate role-based dashboards
5. ✅ Start web application

### Step-by-Step Execution

If you prefer to run each stage separately:

```bash
# Stage 1: Generate raw data
python3 -m layers.data_pipeline.raw_data_generator

# Stage 2: Apply ETL and load to database
python3 -m layers.data_pipeline.etl_processor raw_data/*/raw_accounts.json

# Stage 3: Generate dashboards
python3 -m layers.access.dashboard_builder

# Stage 4: Start web application
python3 start_web_dashboard.py
```

### Access the Dashboard

After running the pipeline:

```bash
# Start web server
python3 start_web_dashboard.py

# Open in browser
http://127.0.0.1:5000
```

**Login Credentials:**
- Compliance Officer: `compliance@aml.com` / `Compliance@123`
- Risk Analyst: `risk@aml.com` / `Risk@123`
- Regulatory Officer: `regulatory@aml.com` / `Regulatory@123`
- Administrator: `admin@aml.com` / `Admin@123`

## Project Structure

```
ETL_Pipeline_Dashboard/
├── layers/
│   ├── data_pipeline/          # Layer 1: Data operations
│   │   ├── config.py
│   │   ├── raw_data_generator.py
│   │   ├── etl_processor.py
│   │   └── database_loader.py
│   │
│   ├── explanation/            # Layer 2: ML & analysis (placeholder)
│   │   └── __init__.py
│   │
│   ├── access/                 # Layer 3: Reports & dashboards
│   │   └── dashboard_builder.py
│   │
│   └── human_interaction/      # Layer 4: Web UI
│       ├── web_application.py
│       └── templates/
│
├── run_complete_pipeline.py    # Main entry point
├── start_web_dashboard.py      # Start web server
├── requirements.txt            # Python dependencies
├── ARCHITECTURE.py             # Detailed architecture docs
└── README.md                   # This file
```

## Features

### Layer 1: Data Pipeline
- **AI-Powered Data Generation**: Uses OpenAI GPT-4o-mini to generate realistic customer profiles and transaction patterns
- **ETL Processing**: Applies industry-standard AML detection rules
- **Pattern Detection**: Identifies structuring, layering, smurfing, and other suspicious patterns
- **Database Integration**: Loads clean data into Supabase

### Layer 2: Explanation
- **ML Models**: RandomForest classifier for risk prediction
- **SHAP Explainability**: Provides transparent, explainable AI decisions
- **Risk Scoring**: Calculates risk scores based on multiple factors

### Layer 3: Access
- **Role-Based Reports**: Generates separate dashboards for Compliance, Risk, and Regulatory roles
- **Data Aggregation**: Aggregates data specifically for each user role
- **HTML Dashboards**: Professional, interactive dashboards

### Layer 4: Human Interaction
- **Web Application**: Flask-based web server
- **Authentication**: Secure login with role-based access control
- **Session Management**: 8-hour session timeout
- **Responsive UI**: Works on desktop, tablet, and mobile

## AML Detection Rules

The system detects:

1. **Structuring**: Multiple transactions just below $10,000 reporting threshold
2. **Layering**: Complex rapid transfers to obscure money origin
3. **Smurfing**: Many small deposits to avoid detection
4. **High-Value Transactions**: Transactions exceeding $15,000
5. **Unusual Timing**: Transactions during suspicious hours
6. **PEP/Sanctions**: Politically Exposed Persons and sanctioned entities
7. **High-Risk Jurisdictions**: Transactions to/from high-risk countries
8. **KYC Compliance**: Incomplete or missing documentation

## Configuration

All configuration is centralized in `layers/data_pipeline/config.py`:

- Supabase connection settings
- AML detection thresholds
- High-risk countries list
- Detection parameters

## Output

The system generates:

1. **Raw Data**: `raw_data/YYYYMMDD_HHMMSS/raw_accounts.json`
2. **Database Tables**: 
   - `account_openings`
   - `transactions`
   - `wire_transfers`
   - `audit_logs`
3. **Dashboards**: `output/YYYYMMDD/dashboard_*.html`

## API Keys Required

- **SUPABASE_KEY**: Required for database access
- **OPENAI_API_KEY**: Optional, for AI-powered data generation (uses fallback rules if not provided)

## Documentation

- `ARCHITECTURE.py`: Complete architecture documentation and design principles
- Inline code documentation in each module
- Layer-specific README files (coming soon)

## Development

### Running Individual Layers

```bash
# Layer 1 - Data Pipeline
python3 -m layers.data_pipeline.raw_data_generator
python3 -m layers.data_pipeline.etl_processor

# Layer 3 - Access
python3 -m layers.access.dashboard_builder

# Layer 4 - Human Interaction
python3 -m layers.human_interaction.web_application
```

### Testing

Each layer can be tested independently due to clean separation of concerns.

## Troubleshooting

### Common Issues

1. **Port 5000 in use**: Change port in `web_application.py` or kill existing process
2. **Database connection error**: Check SUPABASE_KEY environment variable
3. **Import errors**: Ensure you're running from the project root directory
4. **403 error on web**: Try `http://127.0.0.1:5000` instead of `localhost:5000`

## Security

- Passwords hashed with Werkzeug
- Session-based authentication
- Role-based access control
- PII data masked (SSN: XXXXX999)
- Secure session cookies

## License

[Your License Here]

## Support

For detailed architecture information:
```bash
python3 ARCHITECTURE.py
```

