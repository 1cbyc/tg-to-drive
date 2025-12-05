# Telegram to Google Drive Mirror

A Python script designed to mirror files from a Telegram channel to Google Drive, optimized for Google Colab Free Tier. Processes files sequentially to manage limited disk space (download → upload → delete).

## Features

- ✅ **Sequential Processing**: Downloads one file at a time to manage limited disk space
- ✅ **FloodWait Handling**: Automatically handles Telegram rate limits with retry logic
- ✅ **Resume Capability**: Skips files that already exist in Drive folder
- ✅ **Media Filtering**: Only processes messages with downloadable media (documents/photos)
- ✅ **Progress Tracking**: Real-time progress with file counts and sizes
- ✅ **Error Recovery**: Robust error handling with automatic retries

## Prerequisites

1. **Telegram API Credentials**
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Copy your `api_id` and `api_hash`

2. **Google Colab Account** (Free tier works)

3. **Access to the Telegram Channel** you want to mirror

## Installation

### For Google Colab

1. Open a new Colab notebook
2. Upload `telegram_to_drive_mirror.py` or copy the code
3. Install dependencies:
   ```python
   !pip install telethon
   ```
4. Run the script

### For Local Use

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd tg-to-drive
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables (optional):
   ```bash
   export TELEGRAM_API_ID="your_api_id"
   export TELEGRAM_API_HASH="your_api_hash"
   export TELEGRAM_CHANNEL="@your_channel"
   export DRIVE_TARGET_FOLDER="YourFolderName"
   export DRIVE_BASE_PATH="/path/to/drive"
   ```

4. Run the script:
   ```bash
   python telegram_to_drive_mirror.py
   ```

## Usage

### Interactive Mode

Simply run the script and follow the prompts:

```bash
python telegram_to_drive_mirror.py
```

You'll be asked for:
- API_ID
- API_HASH
- Telegram Channel Link (e.g., `@channelname` or `https://t.me/channelname`)
- Target folder name in Google Drive
- Download direction (newest to oldest, or oldest to newest)

### Environment Variables Mode

Set environment variables to skip prompts:

```bash
export TELEGRAM_API_ID="12345678"
export TELEGRAM_API_HASH="your_hash_here"
export TELEGRAM_CHANNEL="@your_channel"
export DRIVE_TARGET_FOLDER="MyMirror"
export DOWNLOAD_REVERSE="false"  # true for oldest to newest
python telegram_to_drive_mirror.py
```

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

## Configuration

You can customize the following via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `TEMP_DOWNLOAD_DIR` | Temporary download directory | `/content/temp_downloads` |
| `DRIVE_BASE_PATH` | Base path for Google Drive | `/content/drive/MyDrive` |
| `TELEGRAM_API_ID` | Your Telegram API ID | (prompted) |
| `TELEGRAM_API_HASH` | Your Telegram API Hash | (prompted) |
| `TELEGRAM_CHANNEL` | Channel to mirror | (prompted) |
| `DRIVE_TARGET_FOLDER` | Target folder name | (prompted) |
| `DOWNLOAD_REVERSE` | Download oldest first | `false` |

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

## Security Notes

- **Never commit** `.session` files (they contain authentication tokens)
- **Never share** your API credentials
- Session files are automatically ignored by `.gitignore`
- All credentials should be provided via environment variables or prompts (never hardcoded)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for personal use and educational purposes. Ensure you have the right to download and store the content you're mirroring. Respect copyright and terms of service.

