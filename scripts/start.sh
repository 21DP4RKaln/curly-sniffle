#!/bin/bash

# Quick Start Script for SVN Trading Bot
# This script provides easy access to common tasks

echo "🤖 SVN Trading Bot - Quick Start"
echo "================================"
echo ""
echo "Select an option:"
echo "1. Deploy to Vercel"
echo "2. Run local development"
echo "3. Migrate database"
echo "4. Open documentation"
echo "5. Exit"

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "🚀 Starting Vercel deployment..."
        bash scripts/deploy.sh
        ;;
    2)
        echo "💻 Starting local development server..."
        vercel dev
        ;;
    3)
        echo "📊 Starting database migration..."
        python scripts/migrate_db.py
        ;;
    4)
        echo "📖 Opening documentation..."
        if command -v xdg-open &> /dev/null; then
            xdg-open docs/DEPLOYMENT_GUIDE.md
        elif command -v open &> /dev/null; then
            open docs/DEPLOYMENT_GUIDE.md
        else
            echo "Please open docs/DEPLOYMENT_GUIDE.md manually"
        fi
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice. Please try again."
        ;;
esac
