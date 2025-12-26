#!/bin/bash

# AML Dashboard - Quick Setup Script
# This script helps you set up the project and configure GitHub secrets

set -e

echo "========================================"
echo "AML Dashboard - Setup Script"
echo "========================================"
echo ""

# Check if Git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Not a Git repository. Initializing..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository detected"
fi

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created - please edit it with your actual keys"
else
    echo "✅ .env file already exists"
fi

# Check Python version
echo ""
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo ""
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p output raw_data
echo "✅ Directories created"

# Check if GitHub CLI is installed
if command -v gh &> /dev/null; then
    echo ""
    echo "🔑 GitHub CLI detected. Do you want to set up GitHub secrets now? (y/n)"
    read -r setup_secrets

    if [ "$setup_secrets" = "y" ]; then
        echo ""
        echo "Please enter your Supabase service role key:"
        read -rs supabase_key
        gh secret set SUPABASE_KEY --body "$supabase_key"
        echo "✅ SUPABASE_KEY set"

        echo ""
        echo "Please enter your OpenAI API key (or press Enter to skip):"
        read -rs openai_key
        if [ -n "$openai_key" ]; then
            gh secret set OPENAI_API_KEY --body "$openai_key"
            echo "✅ OPENAI_API_KEY set"
        fi
    fi
else
    echo ""
    echo "ℹ️  GitHub CLI not installed. To set up secrets:"
    echo "   1. Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
    echo "   2. Add SUPABASE_KEY secret"
    echo "   3. Optionally add OPENAI_API_KEY secret"
fi

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your actual keys"
echo "2. Test locally: source venv/bin/activate && python start_web_dashboard.py"
echo "3. Set up GitHub secrets (see DEPLOYMENT.md)"
echo "4. Push to GitHub to trigger automatic deployment"
echo ""
echo "Deployment guide: DEPLOYMENT.md"
echo ""

