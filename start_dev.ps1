# Test environment variables for development
$env:SECRET_KEY = "test-secret-key-for-development-only"
$env:MT5_API_KEY = "test-mt5-api-key"
$env:ACCESS_CODE = "123456"
$env:ALLOWED_EMAILS = "silvain12@gmail.com,test@example.com"
$env:ALLOWED_IPS = "127.0.0.1,::1,192.168.1.1"

# Optional email settings (for testing without actual email)
$env:SMTP_EMAIL = ""
$env:SMTP_PASSWORD = ""

Write-Host "Environment variables set for development"
Write-Host "Starting Flask server..."

python api/index.py
