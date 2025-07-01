# SVN Trading Bot - MT5 AI Monitorings Platforma 🚀

Šī platforma ļauj jums monitore jūsu MT5 botus, redzēt to statistiku un AI prognoza reāllaikā.

## 🌟 Galvenās iespējas

- **E-pasta autentifikācija** - Droša pieejas sistēma ar 6-ciparu kodiem
- **Reāllaika monitorings** - Skatiet savu botu statistiku tiešraidē
- **AI prognozes** - Mašīnmācīšanās algoritmi uzlabo botu veiktspēju
- **Darījumu analīze** - Detalizēta statistika par peļņu, zaudējumiem un precizitāti
- **Datu krājums** - Visi botu dati tiek saglabāti analīzei

## 🔧 Ātrs sākums

### 1. Iestatīšana

```bash
# Klonējiet projektu
git clone https://github.com/yourusername/svn-trading-bot.git
cd svn-trading-bot

# Izveidojiet vides failu
copy .env.example .env.local

# Rediģējiet .env.local failu ar saviem datiem
```

### 2. Konfigurācija

Rediģējiet `.env.local` failu:

```bash
# Jūsu e-pasts autorizācijai
ALLOWED_EMAILS=sitvain12@gmail.com

# E-pasta konfigurācija (Gmail)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Drošības atslēga
SECRET_KEY=your-secret-32-character-key
```

### 3. Gmail konfigurācija

1. Aktivizējiet 2-Factor Authentication savā Gmail kontā
2. Izveidojiet "App Password":
   - Google Account Settings → Security → 2-Step Verification → App passwords
   - Izveidojiet jaunu "SVN Trading Bot" aplikācijai
3. Izmantojiet šo password kā `SMTP_PASSWORD`

### 4. Palaišana

```bash
# Windows
scripts\start.bat

# Linux/Mac
./scripts/start.sh
```

## 🎯 Kā lietot

### Sākums
1. Atveriet: `http://localhost:5000`
2. Ievadiet savu e-pastu
3. Ievadiet saņemto 6-ciparu kodu
4. Nokļūsiet dashboard

### MT5 Bot konfigurācija

Jūsu MT5 botā izmantojiet šos iestatījumus:

```mql5
input string ServerURL = "https://jūsu-domēns.vercel.app/api";
input string APIKey = "61c2f3467e03e633d25a9bbc3caf05ed990aa6eaa59d2435601309148e48892f";
```

## 📊 Dashboard funkcijas

### Galvenā statistika
- **Aktīvi boti** - Cik boti pašlaik darbojas
- **Kopējā peļņa** - Visu botu kopējā peļņa
- **Darījumi šodien** - Šodienas darījumu skaits
- **AI precizitāte** - Cik precīzi ir AI prognozes

### Grafiki
- **Peļņas grafiks** - Peļņas dinamika laika gaitā
- **AI prognozes** - Reāllaika prognozes ar uzticamības līmeni

### Botu saraksts
- Redziet visus savus botus
- Monitore to aktivitāti
- Analizējiet individuālu veiktspēju

## 🔗 API dokumentācija

### Autentifikācija
```javascript
// Pieprasīt kodu
POST /api/auth/login
{
  "email": "jūsu@epasts.lv"
}

// Verificēt kodu
POST /api/auth/login
{
  "email": "jūsu@epasts.lv",
  "code": "123456"
}
```

### Datu sūtīšana no MT5
```javascript
// Sūtīt bota datus
POST /api/data
Authorization: Bearer YOUR_TOKEN
{
  "account_id": "12345",
  "symbol": "EURUSD",
  "balance": 1000.00,
  "equity": 1050.00,
  "total_trades": 25,
  "daily_profit": 50.00
}
```

### AI prognozes
```javascript
// Iegūt AI prognozi
POST /api/predict
{
  "features": [0.1, 0.2, 0.3, ...],
  "symbol": "EURUSD"
}
```

## 🚀 Deployment uz Vercel

### 1. Sagatavošana
```bash
npm install -g vercel
vercel login
```

### 2. Deployment
```bash
vercel --prod
```

### 3. Vides mainīgie Vercel dashboard
- `SECRET_KEY`
- `ALLOWED_EMAILS`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `DATABASE_URL` (ja izmantojat PostgreSQL)

## 🔧 MT5 Bot integrācija

### SVN.mq5 konfigurācija

Jūsu MT5 eksperts automātiski sūtīs datus uz platformu:

```mql5
// Galvenie parametri
input string ServerURL = "https://jūsu-domēns.vercel.app/api";
input string APIKey = "jūsu-api-key";

// Bots automātiski sūtīs:
// - Darījumu rezultātus
// - Market datus
// - AI features analīzei
// - Statistiku
```

### Datu plūsma

1. **MT5 Bot** → sūta datus → **Platforma**
2. **Platforma** → analizē → **AI prognoze**
3. **AI prognoze** → atpakaļ → **MT5 Bot**
4. **Dashboard** → rāda visu reāllaikā

## 📱 Mobilā versija

Dashboard ir responsive un darbojas uz:
- 📱 Mobilajiem telefoniem
- 💻 Planšetdatoriem
- 🖥️ Desktop datoriem

## 🛡️ Drošība

- JWT token autentifikācija
- E-pasta verifikācija
- Drošas HTTPS konekcijas
- Datu šifrēšana
- Rate limiting

## 🆘 Atbalsts

Ja rodas problēmas:

1. Pārbaudiet `.env.local` konfigurāciju
2. Pārliecinieties par Gmail iestatījumiem
3. Pārbaudiet MT5 bota iestatījumus
4. Skatiet log failus errors

## 📈 Nākotnes plāni

- [ ] Advanced ML modeļi
- [ ] Telegram notifikācijas
- [ ] Multi-broker atbalsts
- [ ] Portfolio optimization
- [ ] Risk management tools
- [ ] Advanced analytics

---

**Izveidoja:** SVN Team  
**Versija:** 2.0.0  
**Pēdējā atjaunošana:** 2025.01.07
