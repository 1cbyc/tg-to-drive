"""
Entry point for running with Telegram bot interface

Usage:
    python run_bot.py

Requires:
    - TELEGRAM_BOT_TOKEN environment variable
    - TELEGRAM_API_ID and TELEGRAM_API_HASH

You can use .env file - see .env.example
Or use load_env.py to load from .env file
"""

import os
import sys

# Try to load from .env file if it exists
try:
    from load_env import load_env
    load_env()
except ImportError:
    pass  # load_env.py is optional

from core.config import Config
from bot.bot import MirrorBot


def main():
    """Main function for bot mode."""
    config = Config()
    
    # Load from environment
    config.load_from_env()
    
    # Check for bot token
    if not config.bot_token:
        print("✗ Error: TELEGRAM_BOT_TOKEN environment variable is required for bot mode")
        print("\nTo get a bot token:")
        print("1. Message @BotFather on Telegram")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the token and set it as TELEGRAM_BOT_TOKEN")
        return
    
    # Validate required config
    if not config.api_id or not config.api_hash:
        print("✗ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH are required for bot mode")
        print("\nSet them as environment variables:")
        print("  $env:TELEGRAM_API_ID = 'your_api_id'")
        print("  $env:TELEGRAM_API_HASH = 'your_api_hash'")
        print("\nOr use the standalone script: python telegram_to_drive_mirror.py")
        return
    
    # Create bot
    bot = MirrorBot(config)
    
    # Initialize bot client
    bot.initialize()
    
    # Start the bot using Pyrogram's run() method
    print("🤖 Starting Telegram bot...")
    try:
        bot.bot.run()
    except KeyboardInterrupt:
        print("\n⚠ Bot stopped by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
