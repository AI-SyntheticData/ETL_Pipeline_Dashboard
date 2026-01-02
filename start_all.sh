#!/bin/bash
# Automated ETL Pipeline Dashboard Startup
# This script runs the complete pipeline and starts the web dashboard
# Uses GitHub Codespaces secrets for API keys

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════════════════"
echo "   ETL PIPELINE DASHBOARD - AUTOMATED STARTUP"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if running in Codespaces
if [ -n "$CODESPACES" ]; then
    echo "✓ Running in GitHub Codespaces"
    echo ""
fi

# Check for required secrets
echo "📋 Checking environment configuration..."
echo ""

if [ -z "$SUPABASE_KEY" ]; then
    echo "⚠️  WARNING: SUPABASE_KEY not found in environment"
    echo "   Set it in GitHub Settings → Codespaces → Secrets"
    echo "   Pipeline will run but skip database loading"
    echo ""
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ℹ️  INFO: OPENAI_API_KEY not found"
    echo "   Will use rule-based data generation instead of AI"
    echo ""
fi

# Default number of accounts
NUM_ACCOUNTS=${1:-100}

echo "════════════════════════════════════════════════════════════════════════════"
echo "STEP 1: Running Complete ETL Pipeline"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "This will:"
echo "  • Generate $NUM_ACCOUNTS raw financial accounts"
echo "  • Apply AML detection rules"
echo "  • Validate and transform data"
echo "  • Load to database (if SUPABASE_KEY is set)"
echo "  • Generate role-based dashboards"
echo ""

# Run the complete pipeline
python3 run_complete_pipeline.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Pipeline failed. Please check the errors above."
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "STEP 2: Starting Web Dashboard"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Starting Flask web application..."
echo ""
echo "📊 Dashboard will be available at:"
if [ -n "$CODESPACES" ]; then
    echo "   • Codespace will automatically forward port 8080"
    echo "   • Click the notification or go to Ports tab"
else
    echo "   • http://localhost:8080"
    echo "   • http://127.0.0.1:8080"
fi
echo ""
echo "🔐 Default Login Credentials:"
echo "   • Compliance Officer: compliance@aml.com / Compliance@123"
echo "   • Risk Analyst:       risk@aml.com / Risk@123"
echo "   • Regulatory Officer: regulatory@aml.com / Regulatory@123"
echo "   • Administrator:      admin@aml.com / Admin@123"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

# Start the web dashboard
python3 start_web_dashboard.py

