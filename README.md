# Telegram to Google Drive Mirror

A Python tool designed to mirror files from Telegram channels to Google Drive, optimized for Google Colab Free Tier. Processes files sequentially to manage limited disk space (download → upload → delete).

**Now with optional Telegram bot interface for monitoring and control!**

## Features

- **Sequential Processing**: Downloads one file at a time to manage limited disk space
- **FloodWait Handling**: Automatically handles Telegram rate limits with retry logic
- **Resume Capability**: Skips files that already exist in Drive folder
- **Media Filtering**: Only processes messages with downloadable media (documents/photos)
- **Progress Tracking**: Real-time progress with file counts and sizes
- **Error Recovery**: Robust error handling with automatic retries
- **Optional Bot Interface**: Monitor and control via Telegram bot commands
- **Modular Architecture**: Clean, maintainable code structure

## Architecture

The project is organized into modular components:

```
tg-to-drive/
├── telegram_to_drive_mirror.py  # Standalone script (main entry point)
├── run_bot.py                   # Bot interface entry point
├── core/                        # Core modules
│   ├── config.py               # Configuration management
│   ├── downloader.py           # Telegram download logic
│   ├── uploader.py             # Drive upload logic
│   ├── processor.py            # Main orchestration
│   └── utils.py                # Utility functions
├── bot/                        # Optional bot interface
│   └── bot.py                  # Telegram bot handler
└── requirements.txt            # Dependencies
```

## Prerequisites

1. **Telegram API Credentials**
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Copy your `api_id` and `api_hash`

2. **Google Colab Account** (Free tier works) - for Colab usage

3. **Access to the Telegram Channel** you want to mirror

4. **Bot Token** (optional, for bot interface)
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token

## Installation

### For Google Colab

1. Open a new Colab notebook
2. Upload the project files or clone the repository
3. Install dependencies:
   ```python
   !pip install -r requirements.txt
   ```
4. Run the script:
   ```python
   !python telegram_to_drive_mirror.py
   ```

### For Local Use

1. Clone this repository:
   ```bash
   git clone https://github.com/1cbyc/tg-to-drive.git
   cd tg-to-drive
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Mode 1: Standalone Script (Recommended for Colab)

Run the script directly - it will prompt for any missing configuration:

```bash
python telegram_to_drive_mirror.py
```

**With Environment Variables:**
```bash
export TELEGRAM_API_ID="12345678"
export TELEGRAM_API_HASH="your_hash_here"
export TELEGRAM_CHANNEL="@your_channel"
export DRIVE_TARGET_FOLDER="MyMirror"
export DOWNLOAD_REVERSE="false"  # true for oldest to newest
python telegram_to_drive_mirror.py
```

### Mode 2: Bot Interface (Optional)

Run with Telegram bot for monitoring and control:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_API_ID="12345678"
export TELEGRAM_API_HASH="your_hash_here"
python run_bot.py
```

**Bot Commands:**
- `/start` - Show welcome message
- `/mirror [@channel]` - Start mirroring a channel
- `/status` - Check current mirror status
- `/stop` - Stop current mirror operation
- `/help` - Show help message

**Example:**
```
You: /mirror @my_channel
Bot: Starting mirror for @my_channel...

You: /status
Bot: Mirror Status
    Downloaded: 45
    Skipped: 12
    Failed: 2
    Total Size: 12.34 GB
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_API_ID` | Your Telegram API ID | - | Yes |
| `TELEGRAM_API_HASH` | Your Telegram API Hash | - | Yes |
| `TELEGRAM_CHANNEL` | Channel to mirror | - | Yes* |
| `DRIVE_TARGET_FOLDER` | Target folder name | `Telegram_Mirror` | No |
| `DRIVE_BASE_PATH` | Base path for Drive | `/content/drive/MyDrive` | No |
| `TEMP_DOWNLOAD_DIR` | Temp download directory | `/content/temp_downloads` | No |
| `DOWNLOAD_REVERSE` | Download oldest first | `false` | No |
| `TELEGRAM_BOT_TOKEN` | Bot token (for bot mode) | - | Bot mode only |
| `TELEGRAM_USER_ID` | Your Telegram user ID | - | No |

*Required unless using bot interface where you can specify via `/mirror` command

## How It Works

1. **Mounts Google Drive** (if running in Colab)
2. **Connects to Telegram** using your API credentials
3. **Scans the channel** for messages with media files
4. **For each file**:
   - Checks if file already exists in Drive (resume capability)
   - Downloads to temporary directory
   - Moves file to Google Drive folder
   - Verifies transfer and deletes local copy
   - Handles FloodWait errors automatically

## Project Structure

- **`core/`**: Core processing modules (config, downloader, uploader, processor)
- **`bot/`**: Optional Telegram bot interface
- **`telegram_to_drive_mirror.py`**: Main standalone script
- **`run_bot.py`**: Bot interface entry point

## Limitations

- **Colab Free Tier**: ~80GB disk space limit
- **Runtime Disconnections**: Colab may disconnect after inactivity
- **File Size**: Limited by Colab's disk space and Telegram's file size limits
- **Rate Limits**: Telegram may throttle requests (handled automatically)

## Troubleshooting

### "SessionPasswordNeededError"
Your Telegram account has 2FA enabled. Either:
- Disable 2FA temporarily, or
- Use a different Telegram account without 2FA

### "FloodWait" errors
The script handles these automatically. If you see many FloodWait messages, the channel may be rate-limiting. The script will wait and retry automatically.

### Drive not mounting
- Ensure you're running in Google Colab
- Check that you've authorized Drive access
- Verify the mount path is correct

### Files not downloading
- Verify you have access to the Telegram channel
- Check that the channel link is correct (include @ symbol)
- Ensure the channel has media files

### Bot not responding
- Verify `TELEGRAM_BOT_TOKEN` is set correctly
- Check that you've started the bot with `python run_bot.py`
- Ensure you're messaging the bot in private chat

## Security Notes

- **Never commit** `.session` files (they contain authentication tokens)
- **Never share** your API credentials or bot tokens
- Session files are automatically ignored by `.gitignore`
- All credentials should be provided via environment variables or prompts (never hardcoded)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Disclaimer

This tool is for personal use and educational purposes. Ensure you have the right to download and store the content you're mirroring. Respect copyright and terms of service.
