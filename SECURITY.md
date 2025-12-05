# Security Guidelines

## ⚠️ IMPORTANT: Never Share Your Tokens!

**Your bot token and API credentials are sensitive. Never:**
- Commit them to git
- Share them in chat/forums
- Include them in screenshots
- Post them publicly

## If You Accidentally Shared a Token

1. **Immediately regenerate it:**
   - For bot tokens: Message @BotFather → `/revoke` → Select your bot → Get new token
   - For API credentials: Go to https://my.telegram.org/apps → Revoke and create new

2. **Check your repository:**
   - Search for the token in your git history
   - If found, remove it and consider rotating credentials

## Secure Setup

### Option 1: Environment Variables (Recommended)

**Windows PowerShell:**
```powershell
$env:TELEGRAM_BOT_TOKEN = "your_token_here"
$env:TELEGRAM_API_ID = "your_api_id"
$env:TELEGRAM_API_HASH = "your_api_hash"
python run_bot.py
```

**Linux/Mac:**
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_API_ID="your_api_id"
export TELEGRAM_API_HASH="your_api_hash"
python run_bot.py
```

### Option 2: .env File (Local Only)

Create a `.env` file (already in .gitignore):
```
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
```

Then use a library like `python-dotenv` to load it.

### Option 3: PowerShell Script (Local Only)

Use `run_bot.ps1` for local testing (already in .gitignore):
```powershell
# Edit run_bot.ps1 with your credentials
# Never commit this file!
.\run_bot.ps1
```

## Files to Never Commit

- `.env` files
- `*.session` files (Telegram session data)
- `run_bot.ps1` (if it contains tokens)
- Any file with hardcoded credentials

## Current Security Status

✅ `.env` files are in `.gitignore`
✅ `*.session` files are in `.gitignore`
✅ `run_bot.ps1` is in `.gitignore`
✅ `.env.example` is provided as a template (no real tokens)

