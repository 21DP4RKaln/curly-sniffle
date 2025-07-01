# Project Overview

## What is SVN Trading Bot?

SVN Trading Bot is an AI-powered trading dashboard that provides real-time analytics and machine learning predictions for trading activities. The project has been optimized for serverless deployment on Vercel.

## Quick Start

**Windows users:** Double-click `start.bat`
**Linux/Mac users:** Run `bash start.sh`

Or manually:
```bash
# For immediate deployment
./scripts/deploy.bat    # Windows
bash scripts/deploy.sh  # Linux/Mac

# For local development
vercel dev
```

## Project Components

### 🌐 Web Application
- **Frontend**: HTML templates with responsive CSS and JavaScript
- **Backend**: Python Flask serverless functions
- **Authentication**: JWT-based with email verification

### 🤖 AI/ML Features
- Real-time prediction algorithms
- Trading signal analysis
- Performance metrics tracking

### 📊 MetaTrader 5 Integration
- Custom indicators and expert advisors
- Automated trading algorithms
- Risk management systems

## File Structure Explained

| Directory | Purpose |
|-----------|---------|
| `api/` | Serverless functions for the web API |
| `static/` | CSS, JavaScript, and images |
| `templates/` | HTML templates for the web interface |
| `mt5/` | MetaTrader 5 files (.mq5, .mqh) |
| `scripts/` | Deployment and utility scripts |
| `docs/` | Project documentation |

## Environment Setup

1. Copy `.env.example` to `.env.local`
2. Fill in your database URL and other settings
3. Deploy using the provided scripts

## Support

- Check `docs/DEPLOYMENT_GUIDE.md` for detailed instructions
- Review `README.md` for API documentation
- Use GitHub Issues for bug reports
