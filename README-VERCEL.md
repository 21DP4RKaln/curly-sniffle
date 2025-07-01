# SVN Trading Bot - Vercel Ready 🚀

AI-powered trading bot dashboard optimized for Vercel deployment with serverless architecture.

## 🌟 Features

- **Real-time Dashboard** - Live trading statistics and AI predictions
- **User Management** - Track connected trading bots and their performance  
- **AI Analytics** - Machine learning predictions with confidence scoring
- **Secure Authentication** - JWT-based auth with email verification
- **Responsive Design** - Works on desktop and mobile devices
- **Serverless Architecture** - Optimized for Vercel's edge functions

## 🏗️ Architecture

```
Frontend (Static) → Vercel Edge CDN
        ↓
API Functions → Vercel Serverless Functions  
        ↓
Database → PostgreSQL (Vercel/Railway/Supabase)
```

## 📁 Project Structure

```
├── api/                    # Vercel serverless functions
│   ├── auth.py            # Authentication endpoints
│   ├── dashboard.py       # Dashboard data API
│   ├── index.py           # Page routing
│   ├── predict.py         # AI prediction API
│   ├── status.py          # System status API
│   └── users.py           # User management API
├── static/                # Static assets (CSS, JS, images)
│   ├── css/style.css      # Main stylesheet
│   └── js/
│       ├── main.js        # Original JavaScript
│       └── main-vercel.js # Vercel-optimized JavaScript
├── templates/             # HTML templates
│   ├── base.html          # Base layout
│   ├── dashboard.html     # Main dashboard
│   ├── login.html         # Login page
│   └── users.html         # Users management
├── vercel.json            # Vercel deployment configuration
├── requirements-vercel.txt # Python dependencies for Vercel
├── migrate_db.py          # Database migration script
└── DEPLOYMENT_GUIDE.md    # Detailed deployment instructions
```

## 🚀 Quick Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/svn-trading-bot)

### Manual Deployment

1. **Clone & Setup**
   ```bash
   git clone https://github.com/yourusername/svn-trading-bot.git
   cd svn-trading-bot
   cp requirements-vercel.txt requirements.txt
   cp static/js/main-vercel.js static/js/main.js
   ```

2. **Database Setup** (Choose one)
   ```bash
   # Vercel Postgres
   vercel env add DATABASE_URL
   
   # Or Railway
   railway login && railway new
   
   # Or Supabase
   # Create project at supabase.com
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

## 🔧 Environment Variables

Required environment variables for deployment:

```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=your-super-secure-secret-key
ALLOWED_EMAILS=email1@example.com,email2@example.com
```

## 🔐 Authentication

The system uses JWT-based authentication:

1. **Email Verification** - Enter authorized email
2. **Code Generation** - 6-digit code sent to email  
3. **Token Creation** - JWT token stored in localStorage
4. **Protected Routes** - All dashboard routes require valid token

### Authorized Users

Add your email addresses to the `ALLOWED_EMAILS` environment variable:
```
ALLOWED_EMAILS=sitvain12@gmail.com,sitvain89@gmail.com
```

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - Email verification and login
- `GET /api/status` - System health check

### Dashboard
- `GET /api/dashboard` - Dashboard statistics and data
- `GET /api/users` - User list and statistics
- `GET /api/users/{id}/details` - Individual user details

### AI/Trading
- `POST /api/predict` - AI prediction endpoint
- `POST /api/training_data` - Receive training data from MT5

## 🎨 Frontend Features

### Dashboard
- Real-time trading statistics
- AI prediction confidence scores
- Connected bot monitoring  
- Profit/loss tracking
- System status indicators

### Users Page
- Active/inactive bot status
- Individual bot performance
- Trading history per user
- Risk level assessment

### Responsive Design
- Bootstrap 5 for responsive layout
- Font Awesome icons
- Chart.js for data visualization
- Mobile-friendly interface

## 🧠 AI/ML Features

- **Random Forest** models for prediction
- **Real-time learning** from trading results
- **Confidence scoring** for all predictions
- **Feature engineering** from market data
- **Model caching** for performance

## 🗄️ Database Schema

```sql
-- Users table
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP,
    total_trades INTEGER DEFAULT 0,
    profit REAL DEFAULT 0.0
);

-- Market data table  
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    symbol TEXT,
    features TEXT,
    signal INTEGER,
    confidence REAL
);

-- Trades table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    symbol TEXT,
    signal TEXT,
    profit REAL,
    confidence REAL
);
```

## 🔄 Migration from PythonAnywhere

If migrating from existing PythonAnywhere deployment:

1. **Export Data**
   ```bash
   python migrate_db.py
   ```

2. **Update Code**
   - Replace Flask sessions with JWT
   - Convert routes to serverless functions
   - Update frontend API calls

3. **Test & Deploy**
   - Test locally with Vercel CLI
   - Deploy to staging
   - Update DNS when ready

## 📈 Performance Optimizations

### Vercel-Specific
- Serverless function optimization
- Edge caching for static assets
- Automatic image optimization
- Global CDN distribution

### Database
- Connection pooling
- Query optimization
- Proper indexing
- Data cleanup policies

### Frontend
- Minified assets
- Lazy loading
- Client-side caching
- Optimized API calls

## 🛠️ Development

### Local Development
```bash
# Install Vercel CLI
npm i -g vercel

# Clone and setup
git clone <repo>
cd svn-trading-bot
cp .env.example .env.local

# Run locally
vercel dev
```

### Testing
```bash
# Test API endpoints
curl http://localhost:3000/api/health
curl http://localhost:3000/api/status

# Test frontend
open http://localhost:3000
```

## 📋 Deployment Checklist

- [ ] Database created and migrated
- [ ] Environment variables configured
- [ ] GitHub repository setup
- [ ] Vercel project created
- [ ] Domain configured (optional)
- [ ] SSL certificate active
- [ ] Authentication tested
- [ ] API endpoints working
- [ ] Dashboard loading correctly
- [ ] Mobile responsiveness verified

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python version compatibility
   - Verify requirements.txt syntax
   - Review build logs in Vercel dashboard

2. **Database Connection**
   - Verify DATABASE_URL format
   - Check network connectivity
   - Test connection string locally

3. **Authentication Problems**
   - Clear localStorage in browser
   - Verify SECRET_KEY is set
   - Check ALLOWED_EMAILS format

### Performance Issues

1. **Slow Loading**
   - Check database query performance
   - Optimize API responses
   - Enable browser caching

2. **Cold Starts**
   - Minimize dependencies
   - Use connection pooling
   - Implement warming strategies

## 📞 Support

- **Documentation**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Vercel Docs**: https://vercel.com/docs
- **Issues**: GitHub Issues tab

## 📄 License

This project is licensed under the MIT License.

---

**Ready to deploy?** Follow the [Deployment Guide](DEPLOYMENT_GUIDE.md) for step-by-step instructions! 🚀
