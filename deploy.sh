#!/bin/bash

# SVN Trading Bot - Vercel Deployment Script
# Run this script to prepare and deploy your project to Vercel

echo "🚀 SVN Trading Bot - Vercel Deployment"
echo "======================================"

# Check if required tools are installed
echo "📋 Checking prerequisites..."

# Check for Python
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed"
    exit 1
fi
echo "✅ Python found"

# Check for Git
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    exit 1
fi
echo "✅ Git found"

# Check for Node.js (for Vercel CLI)
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed (required for Vercel CLI)"
    echo "📥 Install from: https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js found"

# Install or check Vercel CLI
echo "📦 Checking Vercel CLI..."
if ! command -v vercel &> /dev/null; then
    echo "📥 Installing Vercel CLI..."
    npm install -g vercel
fi
echo "✅ Vercel CLI ready"

# Prepare files for Vercel
echo "📁 Preparing files for Vercel..."

# Copy Vercel-optimized files
if [ -f "requirements-vercel.txt" ]; then
    cp requirements-vercel.txt requirements.txt
    echo "✅ Updated requirements.txt for Vercel"
fi

if [ -f "static/js/main-vercel.js" ]; then
    cp static/js/main-vercel.js static/js/main.js
    echo "✅ Updated main.js for Vercel"
fi

# Check for environment variables
echo "🔧 Environment variables check..."
if [ ! -f ".env.local" ]; then
    echo "⚠️  No .env.local file found"
    echo "📝 Creating from template..."
    cp .env.example .env.local
    echo "🔧 Please edit .env.local with your actual values:"
    echo "   - DATABASE_URL"
    echo "   - SECRET_KEY"
    echo "   - ALLOWED_EMAILS"
    echo ""
    read -p "Press Enter when you've updated .env.local..."
fi

# Git initialization
echo "📚 Git repository setup..."
if [ ! -d ".git" ]; then
    echo "📝 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial Vercel-ready commit"
    
    echo "🌐 Please create a GitHub repository and run:"
    echo "   git remote add origin https://github.com/yourusername/svn-trading-bot.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    read -p "Press Enter when you've pushed to GitHub..."
fi

# Database migration (optional)
echo "🗄️  Database migration..."
read -p "Do you want to migrate existing SQLite data? (y/N): " migrate_db
if [[ $migrate_db =~ ^[Yy]$ ]]; then
    if [ -f "migrate_db.py" ] && [ -f "src/SVNbot.db" ]; then
        echo "📊 Running database migration..."
        python migrate_db.py
    else
        echo "⚠️  Migration files not found, skipping..."
    fi
fi

# Vercel deployment
echo "🚀 Deploying to Vercel..."
echo "📝 This will:"
echo "   1. Link your GitHub repository"
echo "   2. Configure environment variables"
echo "   3. Deploy to production"
echo ""

# Login to Vercel if needed
vercel login

# Deploy
vercel --prod

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Go to Vercel dashboard to add environment variables:"
echo "      - DATABASE_URL"
echo "      - SECRET_KEY"  
echo "      - ALLOWED_EMAILS"
echo ""
echo "   2. Test your deployment:"
echo "      - Visit your Vercel URL"
echo "      - Test login with authorized email"
echo "      - Check dashboard functionality"
echo ""
echo "   3. Optional: Configure custom domain in Vercel dashboard"
echo ""
echo "📖 Need help? Check DEPLOYMENT_GUIDE.md"
echo "🔗 Vercel Dashboard: https://vercel.com/dashboard"
