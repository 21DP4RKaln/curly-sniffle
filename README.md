# SVN Trading Bot 🚀

AI-powered trading bot dashboard optimized for Vercel deployment with serverless architecture.

## 🌟 Features

- **Real-time Dashboard** - Live trading statistics and AI predictions
- **User Management** - Track connected trading bots and their performance  
- **AI Analytics** - Machine learning predictions with confidence scoring
- **Secure Authentication** - JWT-based auth with email verification
- **Responsive Design** - Works on desktop and mobile devices
- **Serverless Architecture** - Optimized for Vercel's edge functions

## 📁 Project Structure

```
├── api/                   # Vercel serverless functions
│   ├── auth.py           # Authentication endpoints
│   ├── dashboard.py      # Dashboard data API
│   ├── index.py          # Page routing
│   ├── predict.py        # AI prediction API
│   ├── status.py         # System status API
│   └── users.py          # User management API
├── static/               # Static assets (CSS, JS, images)
│   ├── css/style.css     # Main stylesheet
│   └── js/main.js        # Frontend JavaScript
├── templates/            # HTML templates
│   ├── base.html         # Base layout
│   ├── dashboard.html    # Main dashboard
│   ├── login.html        # Login page
│   └── users.html        # Users management
├── mt5/                  # MetaTrader 5 integration files
│   ├── AI_ML_Algorithms.mqh
│   ├── Config.mqh
│   └── SVN.mq5
├── scripts/              # Deployment and utility scripts
│   ├── deploy.bat        # Windows deployment script
│   ├── deploy.sh         # Linux/Mac deployment script
│   └── migrate_db.py     # Database migration script
├── docs/                 # Project documentation
│   └── DEPLOYMENT_GUIDE.md # Detailed deployment instructions
├── vercel.json           # Vercel deployment configuration
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

## 🚀 Quick Start

### Super Quick Start (Recommended)
```bash
# Windows
start.bat

# Linux/Mac  
bash start.sh
```

### Manual Deployment
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/svn-trading-bot)

### Manual Deployment

1. **Clone & Setup**
   ```bash
   git clone https://github.com/yourusername/svn-trading-bot.git
   cd svn-trading-bot
   ```

2. **Environment Variables**
   ```bash
   # Copy environment template
   cp .env.example .env.local
   
   # Add to Vercel dashboard or .env.local:
   DATABASE_URL=postgresql://user:pass@host:port/dbname
   SECRET_KEY=your-super-secure-secret-key
   ALLOWED_EMAILS=your-email@example.com
   ```

3. **Deploy**
   ```bash
   # Automated deployment
   ./scripts/deploy.bat     # Windows
   # or
   bash scripts/deploy.sh   # Linux/Mac
   
   # Or manual
   vercel --prod
   ```

## 🔧 Environment Variables

Required environment variables for deployment:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (generate random 32+ chars)
- `ALLOWED_EMAILS` - Comma-separated list of authorized emails

## 🛠️ Local Development

```bash
# Install Vercel CLI
npm i -g vercel

# Setup environment
cp .env.example .env.local
# Edit .env.local with your values

# Run locally
vercel dev
```

## 📊 API Endpoints

- `GET /api/status` - System status and statistics
- `POST /api/auth` - User authentication
- `GET /api/dashboard` - Dashboard data
- `GET /api/users` - User management
- `POST /api/predict` - AI predictions

## 🔐 Authentication

The system uses JWT-based authentication with email verification. Add authorized emails to the `ALLOWED_EMAILS` environment variable.

## 🗄️ Database

The application supports PostgreSQL databases. Use the migration script to transfer data from SQLite:

```bash
python scripts/migrate_db.py
```

## 📋 Deployment Checklist

- [ ] Database created and migrated
- [ ] Environment variables configured  
- [ ] GitHub repository setup
- [ ] Vercel project created
- [ ] Authentication tested
- [ ] Dashboard loading correctly

## 🚨 Troubleshooting

See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for detailed instructions and troubleshooting.

## 📞 Support

- **Documentation**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **Vercel Docs**: https://vercel.com/docs
- **Issues**: GitHub Issues tab

## 📄 License

This project is licensed under the MIT License.

---

**Ready to deploy?** Follow the [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for step-by-step instructions! 🚀
