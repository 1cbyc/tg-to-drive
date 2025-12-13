"""
Helper script to list all your Telegram channels/groups and show their IDs

This is useful for finding the numeric ID of private channels that don't have usernames.

Usage:
    python list_channels.py

You'll be prompted for:
- API_ID
- API_HASH
- Phone number (for authentication)
"""

import os
import sys

# Try to load from .env file if it exists
try:
    from load_env import load_env
    load_env()
except ImportError:
    pass

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

def main():
    """List all channels and groups with their IDs."""
    print("=" * 60)
    print("Telegram Channel/Group ID Finder")
    print("=" * 60)
    
    # Get API credentials
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    
    if not api_id:
        api_id = input("\nEnter your API_ID: ").strip()
        try:
            api_id = int(api_id)
        except ValueError:
            print("✗ Error: API_ID must be a number")
            return
    
    if not api_hash:
        api_hash = input("Enter your API_HASH: ").strip()
    
    # Initialize client
    print("\n" + "=" * 60)
    print("Connecting to Telegram...")
    print("=" * 60)
    
    client = TelegramClient('channel_finder_session', api_id, api_hash)
    
    try:
        client.start()
        print("✓ Connected!")
        
        print("\n" + "=" * 60)
        print("Fetching your channels and groups...")
        print("=" * 60)
        
        # Get all dialogs (channels, groups, chats)
        dialogs = client.loop.run_until_complete(client.get_dialogs())
        
        # Filter for channels and groups
        channels = []
        groups = []
        
        for dialog in dialogs:
            if dialog.is_channel:
                channels.append(dialog)
            elif dialog.is_group:
                groups.append(dialog)
        
        print(f"\n✓ Found {len(channels)} channels and {len(groups)} groups\n")
        
        if channels:
            print("📢 CHANNELS:")
            print("-" * 60)
            for dialog in channels:
                entity = dialog.entity
                channel_id = entity.id
                # Channel IDs are negative, format: -1001234567890
                full_id = f"-100{channel_id}" if channel_id > 0 else str(channel_id)
                
                username = getattr(entity, 'username', None)
                title = getattr(entity, 'title', 'Unknown')
                
                print(f"  Title: {title}")
                if username:
                    print(f"  Username: @{username}")
                print(f"  ID: {full_id}")
                print(f"  Access Hash: {entity.access_hash}")
                print()
        
        if groups:
            print("\n👥 GROUPS:")
            print("-" * 60)
            for dialog in groups:
                entity = dialog.entity
                group_id = entity.id
                # Group IDs are negative
                full_id = f"-{group_id}" if group_id > 0 else str(group_id)
                
                title = getattr(entity, 'title', 'Unknown')
                
                print(f"  Title: {title}")
                print(f"  ID: {full_id}")
                print(f"  Access Hash: {entity.access_hash}")
                print()
        
        print("=" * 60)
        print("💡 TIP: Use the ID (e.g., -1001234567890) as the channel link")
        print("   Example: Enter '-1001234567890' when prompted for channel link")
        print("=" * 60)
        
    except SessionPasswordNeededError:
        print("\n✗ Error: This account has 2FA enabled.")
        print("   Please disable 2FA or use a different account.")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

