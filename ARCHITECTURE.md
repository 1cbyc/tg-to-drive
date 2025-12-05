# Architecture Overview

## Project Structure

```
tg-to-drive/
├── telegram_to_drive_mirror.py  # Standalone script entry point
├── run_bot.py                   # Bot interface entry point
├── core/                        # Core processing modules
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── downloader.py           # Telegram download logic
│   ├── uploader.py             # Drive upload logic
│   ├── processor.py            # Main orchestration
│   └── utils.py                # Utility functions
├── bot/                        # Optional bot interface
│   ├── __init__.py
│   └── bot.py                  # Telegram bot handler
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
├── LICENSE                     # MIT License
└── .gitignore                  # Git ignore rules
```

## Module Responsibilities

### Core Modules

**`config.py`**
- Manages all configuration settings
- Handles environment variables
- Provides Colab detection
- Drive mounting logic

**`downloader.py`**
- Telegram file downloading
- FloodWait error handling
- Retry logic
- Channel message iteration

**`uploader.py`**
- Google Drive file uploads
- File conflict resolution
- Verification and cleanup

**`processor.py`**
- Main orchestration logic
- Coordinates downloader and uploader
- Progress tracking
- Statistics collection
- Progress callback support (for bot integration)

**`utils.py`**
- File size formatting
- Media detection
- File info extraction
- Directory management
- Filename conflict resolution

### Bot Module

**`bot.py`**
- Telegram bot interface
- Command handlers (/start, /mirror, /status, /stop, /help)
- Progress monitoring
- Async task management

## Usage Patterns

### Standalone Mode
```python
from core.config import Config
from core.processor import MirrorProcessor

config = Config()
config.load_from_env()
# ... set config values ...

processor = MirrorProcessor(config)
processor.initialize()
processor.process_channel()
processor.cleanup()
```

### Bot Mode
```python
from core.config import Config
from bot.bot import MirrorBot

config = Config()
config.load_from_env()
# ... set config values ...

bot = MirrorBot(config)
await bot.start()
```

## Design Decisions

1. **Modular Architecture**: Separated concerns into distinct modules for maintainability
2. **Optional Bot**: Bot is completely optional - script works standalone
3. **Progress Callbacks**: Processor supports callbacks for bot integration
4. **Environment Variables**: All configuration can be set via env vars
5. **Backward Compatible**: Main script still works as before

## Extension Points

- **Custom Downloaders**: Add new download sources by extending downloader interface
- **Custom Uploaders**: Add new storage backends by extending uploader interface
- **Progress Handlers**: Add custom progress reporting via callbacks
- **Bot Commands**: Easily add new bot commands in `bot.py`

