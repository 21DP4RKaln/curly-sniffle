# 🚀 SVN Trading Bot - Pilnā Platformas Instalācija

Tagad jums ir pilnīga MT5 bota monitorings platforma! Šeit ir instrukcijas, kā to izmantot.

## ✅ Kas ir izveidots

### 🌐 Tīmekļa platforma
- **E-pasta autentifikācija** ar 6-ciparu kodiem
- **Reāllaika dashboard** ar statistiku
- **AI prognozes** un analītika
- **Botu monitorings** un datu vizualizācija

### 🔧 API endpoints
- `/api/auth/login` - Autentifikācija
- `/api/dashboard` - Galvenā statistika
- `/api/users` - Botu saraksts
- `/api/predict` - AI prognozes
- `/api/data` - Datu saņemšana no MT5
- `/api/feedback` - Darījumu rezultāti

### 🗃️ Datubāze
- Automātiska SQLite datubāze
- Lietotāju tabula
- Darījumu vēsture
- Market dati AI analīzei

## 🏃‍♂️ Ātrs sākums

### 1. Lokālā testēšana

```bash
# 1. Konfigurējiet vides mainīgos
copy .env.example .env.local

# 2. Rediģējiet .env.local ar saviem datiem:
#    - ALLOWED_EMAILS=sitvain12@gmail.com
#    - SMTP_USER=jūsu@gmail.com
#    - SMTP_PASSWORD=jūsu-app-password

# 3. Palaidiet platformu
scripts\start_local.bat

# 4. Atveriet brauswerī: http://localhost:5000
```

### 2. Gmail konfigurācija

```bash
# 1. Google Account → Security → 2-Step Verification
# 2. App passwords → Create new → "SVN Trading Bot"  
# 3. Izmantojiet ģenerēto password .env.local failā
```

### 3. Testēšana

```bash
# Palaižiet testu
scripts\test_platform.bat

# Pārbaudiet vai viss darbojas:
# ✅ Health check
# ✅ API endpoints
# ✅ Login page
# ✅ Dashboard
```

## 🌍 Deployment uz Vercel

### 1. Sagatavošana

```bash
# Instalējiet Vercel CLI
npm install -g vercel

# Pieteikties Vercel
vercel login
```

### 2. Deployment

```bash
# Automātiskais deployment
scripts\deploy_vercel.bat

# Vai manuāli:
vercel --prod
```

### 3. Vercel konfigurācija

Vercel dashboard → Settings → Environment Variables:

```
SECRET_KEY=your-secret-key-32-chars-minimum
ALLOWED_EMAILS=sitvain12@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
MT5_API_KEY=61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f
ENVIRONMENT=production
DEBUG=false
```

## 🤖 MT5 Bot konfigurācija

### Jūsu SVN.mq5 failā jau ir viss konfigurēts:

```mql5
// Izmainiet tikai URL uz savu Vercel domēnu
input string ServerURL = "https://jūsu-vercel-url.vercel.app/api";
input string APIKey = "61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f";
```

### Bot automātiski sūtīs:
- ✅ Darījumu rezultātus
- ✅ Market datus analīzei  
- ✅ AI features
- ✅ Statistiku un peļņu
- ✅ Real-time updates

## 📊 Dashboard funkcijas

### 🏠 Galvenā lapa
- **Aktīvi boti** - Real-time status
- **Kopējā peļņa** - Visu botu peļņa
- **Darījumi šodien** - Šodienas aktivitāte
- **AI precizitāte** - Prognozes kvalitāte

### 📈 Grafiki
- **Peļņas grafiks** - Dinamika laika gaitā
- **AI prognozes** - Real-time signāli
- **Darījumu sadalījums** - Win/Loss ratio

### 🤖 Botu saraksts
- Bot ID un status
- Pēdējā aktivitāte
- Darījumu skaits
- Peļņa/zaudējumi
- Individuāla analīze

## 🔄 Datu plūsma

### MT5 Bot → Platforma
```mql5
// Bots automātiski sūta:
SendDataToServer();     // Statistiku katru minūti
SendTradeResult();      // Katru darījumu
GetAIPrediction();      // AI prognozes
```

### Platforma → AI → Bot
```
1. Bot sūta market datus
2. AI analizē un prognozē  
3. Prognoza atgriežas botam
4. Bot pieņem lēmumus
5. Rezultāti tiek saglabāti
```

## 🔐 Drošība

- ✅ JWT tokens ar 24h dzīvlaiku
- ✅ E-pasta verifikācija
- ✅ Rate limiting
- ✅ HTTPS konekcijas
- ✅ API key autentifikācija

## 📱 Mobilā versija

Dashboard pilnībā responsive:
- 📱 Telefoni (iOS/Android)
- 💻 Planšetes  
- 🖥️ Desktop

## 🛠️ Troubleshooting

### Problēma: E-pasts netiek nosūtīts
```bash
# Risinājums:
1. Pārbaudiet Gmail App Password
2. Aktivizējiet 2FA uz Gmail
3. Pārbaudiet SMTP_USER un SMTP_PASSWORD
```

### Problēma: Dashboard nerāda datus
```bash
# Risinājums:
1. Pārbaudiet MT5 bota ServerURL
2. Pārliecinieties ka bots sūta datus
3. Skatiet API logs Vercel dashboard
```

### Problēma: AI prognozes nedarbojas
```bash
# Risinājums:  
1. Pārbaudiet /api/predict endpoint
2. Pārliecinieties ka features tiek sūtīti
3. Pārbaudiet numpy instalāciju
```

## 📈 Kā uzlabot sistēmu

### 1. Advanced ML modeļi
```python
# Pievienojiet api/predict.py:
from sklearn.ensemble import RandomForestClassifier
# Vai TensorFlow/PyTorch modeļus
```

### 2. Telegram notifikācijas
```python
# Pievienojiet Telegram bot
import telegram
```

### 3. Vairāki boti
```python
# Multi-account support
# Portfolio management
# Risk diversification
```

## 🎯 Nākamie soļi

1. **Testējiet platformu** - `scripts\start_local.bat`
2. **Konfigurējiet Gmail** - App password
3. **Deploy to Vercel** - `scripts\deploy_vercel.bat`  
4. **Konfigurējiet MT5** - Jaunais URL
5. **Monitorējiet rezultātus** - Dashboard analīze

## 📞 Atbalsts

Ja rodas jautājumi:
1. Pārbaudiet log failus
2. Testējiet ar `test_platform.bat`
3. Pārbaudiet Vercel dashboard logs
4. Salīdziniet ar .env.example

---

**🎉 Apsveicu!** Tagad jums ir pilnīga MT5 AI monitoringa platforma!

**Izveidoja:** SVN Team  
**Versija:** 2.0.0  
**Izveidots:** 2025.01.07
