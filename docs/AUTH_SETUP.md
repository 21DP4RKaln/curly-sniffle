# SVN Trading Bot - Jaunā Autentifikācijas sistēma

## 📝 Izmaiņas

Sistēma ir uzlabota ar jaunu autentifikācijas procesu:

### 🔐 Jaunā Autentifikācijas plūsma:

1. **Sākuma lapa** - Parāda pieteikšanās logu
2. **E-pasta pārbaude** - Pārbauda vai e-pasts ir ierakstīts `.env.local` failā
3. **Koda nosūtīšana** - Nosūta 6-ciparu kodu uz e-pastu
4. **Koda ievade** - Lietotājs ievada kodu no e-pasta
5. **Piekļuve** - Pēc veiksmīgas autentifikācijas var redzēt statistiku

## ⚙️ Konfigurācija

### 1. Iestatīt `.env.local` failu:

```bash
# Database
DATABASE_URL=sqlite:///svnbot.db

# Authentication
SECRET_KEY=your-secret-key-here-32-chars-minimum
ALLOWED_EMAILS=sitvain12@gmail.com

# Email Configuration (Production)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 2. Gmail konfigurācija (Produkcijai):

1. Aktivizējiet 2-Factor Authentication savā Gmail kontā
2. Izveidojiet "App Password":
   - Iet uz Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Izveidojiet jaunu app password "SVN Trading Bot"
3. Izmantojiet šo app password kā `SMTP_PASSWORD`

## 🚀 Pokšana

### Lokāli:
```bash
cd BotTR
python -c "from api.auth import app; app.run(debug=True, port=5000)"
```

### Vercel:
```bash
vercel dev
```

## 🔧 Kā darbojas

1. **Sākums**: Lietotājs apmeklē vietni
2. **Login**: Ievada e-pastu (kas sakrīt ar `.env` faila `ALLOWED_EMAILS`)
3. **E-pasta pārbaude**: Sistēma pārbauda vai e-pasts ir autorizēts
4. **Koda ģenerēšana**: Izveido 6-ciparu kodu
5. **E-pasta sūtīšana**: Nosūta kodu (vai parāda development mode)
6. **Verifikācija**: Pārbauda ievadīto kodu
7. **Tokens**: Izveido JWT token (derīgs 24h)
8. **Dashboard**: Novirza uz galveno kontrolpaneli

## 📱 Latviešu valoda

Visa sistēma ir tulkota latviešu valodā:
- Login ziņojumi
- Kļūdu paziņojumi  
- E-pasta saturs
- Interface elementi

## 🛡️ Drošība

- JWT tokens ar 24h derīgumu
- Kodu derīgums: 10 minūtes
- Maksimums 3 mēģinājumi
- Tikai autorizēti e-pasti
- SMTP drošība ar TLS

## 📊 Development vs Production

**Development mode**: 
- Ja nav konfigurēts SMTP, rāda kodu konzolē
- Demo kods tiek parādīts lietotājam

**Production mode**:
- Nosūta īstus e-pastus
- Nav demo koda rādīšanas
- Drošāka konfigurācija
