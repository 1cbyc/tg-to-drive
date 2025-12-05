# Quick Start Guide

## Environment Setup

### Step 1: Set Bot Token (Already Done)
```powershell
$env:TELEGRAM_BOT_TOKEN = "7551239789:AAEBZQsIlyVTwJzkAco9xCwnR332A2pnRFk"
```

### Step 2: Get Your API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy your `api_id` and `api_hash`

### Step 3: Set API Credentials

```powershell
$env:TELEGRAM_API_ID = "your_api_id_here"
$env:TELEGRAM_API_HASH = "your_api_hash_here"
```

### Step 4: (Optional) Set Channel and Folder

```powershell
$env:TELEGRAM_CHANNEL = "@your_channel_name"
$env:DRIVE_TARGET_FOLDER = "MyMirror"
```

## Running the Bot

Once all environment variables are set:

```powershell
python run_bot.py
```

The bot will start and you can:
- Send `/start` to your bot
- Send `/mirror @channelname` to start mirroring
- Send `/status` to check progress
- Send `/stop` to stop

## Running Standalone Script

If you prefer the standalone script (no bot):

```powershell
python telegram_to_drive_mirror.py
```

It will prompt for any missing credentials.

## Verify Setup

Check if everything is set:

```powershell
Write-Host "Bot Token: $($env:TELEGRAM_BOT_TOKEN -ne $null)"
Write-Host "API ID: $($env:TELEGRAM_API_ID -ne $null)"
Write-Host "API Hash: $($env:TELEGRAM_API_HASH -ne $null)"
```

