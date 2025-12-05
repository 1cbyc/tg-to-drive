"""
Entry point for running with Telegram bot interface

Usage:
    python run_bot.py

Requires:
    - TELEGRAM_BOT_TOKEN environment variable
    - TELEGRAM_API_ID and TELEGRAM_API_HASH
"""

import asyncio
import os
import sys
from core.config import Config
from bot.bot import MirrorBot


async def main():
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
        print("✗ Error: TELEGRAM_API_ID and TELEGRAM_API_HASH are required")
        print("Set them as environment variables or they will be prompted")
        return
    
    # Create and start bot
    bot = MirrorBot(config)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n⚠ Bot stopped by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())

