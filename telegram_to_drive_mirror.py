"""
Telegram Channel to Google Drive Mirror Script
Designed for Google Colab Free Tier

This script downloads files from a Telegram channel and uploads them to Google Drive,
processing files sequentially to manage limited disk space.

Can run standalone or with optional Telegram bot interface.

You can use .env file - see .env.example
Or use load_env.py to load from .env file

Author: Open Source Project
License: MIT
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
from core.processor import MirrorProcessor
from core.utils import clean_channel_link


def get_user_inputs(config: Config):
    """Prompt user for missing configuration."""
    print("=" * 60)
    print("Telegram to Google Drive Mirror Setup")
    print("=" * 60)
    
    # Load from environment first
    config.load_from_env()
    
    # Prompt for missing values
    if not config.api_id:
        print("\nTo get your Telegram API credentials:")
        print("1. Go to https://my.telegram.org/apps")
        print("2. Log in with your phone number")
        print("3. Create a new application")
        print("4. Copy your 'api_id' and 'api_hash'")
        print("=" * 60)
        api_id = input("\nEnter your API_ID: ").strip()
        try:
            config.api_id = int(api_id)
        except ValueError:
            print("✗ Error: API_ID must be a number")
            return False
    
    if not config.api_hash:
        config.api_hash = input("Enter your API_HASH: ").strip()
    
    if not config.channel_link:
        channel_link = input("Enter the Telegram Channel Link (e.g., @channelname, https://t.me/channelname, or -1001234567890 for numeric ID): ").strip()
        config.channel_link = clean_channel_link(channel_link)
    
    if not config.folder_name:
        folder_name = input("Enter the target folder name in Google Drive (will be created if it doesn't exist): ").strip()
        config.folder_name = folder_name if folder_name else "Telegram_Mirror"
    
    # Ask for download direction (only if interactive)
    if not os.getenv('DOWNLOAD_REVERSE'):
        direction = input("\nDownload direction:\n1. Newest to Oldest (default)\n2. Oldest to Newest\nEnter choice (1 or 2): ").strip()
        config.reverse_order = (direction == '2')
    
    return True


def main():
    """Main execution function."""
    config = Config()
    
    # Get user inputs
    if not get_user_inputs(config):
        return
    
    # Validate inputs
    if not config.api_id or not config.api_hash:
        print("✗ Error: API_ID and API_HASH are required")
        return
    
    if not config.channel_link:
        print("✗ Error: Channel link is required")
        return
    
    # Create processor and run
    processor = MirrorProcessor(config)
    
    try:
        if not processor.initialize():
            print("✗ Failed to initialize. Exiting.")
            return
        
        processor.process_channel()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        processor.cleanup()


if __name__ == "__main__":
    main()
