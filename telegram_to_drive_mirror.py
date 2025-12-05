"""
Telegram Channel to Google Drive Mirror Script
Designed for Google Colab Free Tier

This script downloads files from a Telegram channel and uploads them to Google Drive,
processing files sequentially to manage limited disk space.

Author: Open Source Project
License: MIT
"""

import os
import sys
import shutil
import time
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

# Try to import Colab-specific modules (will fail gracefully if not in Colab)
try:
    from google.colab import drive
    IS_COLAB = True
except ImportError:
    IS_COLAB = False

# Configuration - can be overridden via environment variables
TEMP_DOWNLOAD_DIR = os.getenv('TEMP_DOWNLOAD_DIR', '/content/temp_downloads')
DRIVE_BASE_PATH = os.getenv('DRIVE_BASE_PATH', '/content/drive/MyDrive')

def get_user_inputs():
    """
    Prompt user for API credentials and channel information.
    
    Supports environment variables for automation:
    - TELEGRAM_API_ID
    - TELEGRAM_API_HASH
    - TELEGRAM_CHANNEL
    - DRIVE_TARGET_FOLDER
    """
    print("=" * 60)
    print("Telegram to Google Drive Mirror Setup")
    print("=" * 60)
    
    # Check for environment variables first
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    channel_link = os.getenv('TELEGRAM_CHANNEL')
    folder_name = os.getenv('DRIVE_TARGET_FOLDER')
    
    if not api_id:
        print("\nTo get your Telegram API credentials:")
        print("1. Go to https://my.telegram.org/apps")
        print("2. Log in with your phone number")
        print("3. Create a new application")
        print("4. Copy your 'api_id' and 'api_hash'")
        print("=" * 60)
        api_id = input("\nEnter your API_ID: ").strip()
    
    if not api_hash:
        api_hash = input("Enter your API_HASH: ").strip()
    
    if not channel_link:
        channel_link = input("Enter the Telegram Channel Link (e.g., @channelname or https://t.me/channelname): ").strip()
    
    # Clean channel link
    if channel_link.startswith('https://t.me/'):
        channel_link = '@' + channel_link.split('/')[-1]
    elif not channel_link.startswith('@'):
        channel_link = '@' + channel_link
    
    if not folder_name:
        folder_name = input("Enter the target folder name in Google Drive (will be created if it doesn't exist): ").strip()
        if not folder_name:
            folder_name = "Telegram_Mirror"
    
    # Ask for download direction (only if interactive)
    if not os.getenv('DOWNLOAD_REVERSE'):
        direction = input("\nDownload direction:\n1. Newest to Oldest (default)\n2. Oldest to Newest\nEnter choice (1 or 2): ").strip()
        reverse_order = (direction == '2')
    else:
        reverse_order = os.getenv('DOWNLOAD_REVERSE', 'false').lower() == 'true'
    
    return api_id, api_hash, channel_link, folder_name, reverse_order

def setup_directories(drive_folder_path):
    """Create necessary directories if they don't exist."""
    os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(drive_folder_path, exist_ok=True)
    print(f"\n✓ Directories set up:")
    print(f"  - Temp: {TEMP_DOWNLOAD_DIR}")
    print(f"  - Drive: {drive_folder_path}")

def get_existing_files(drive_folder_path):
    """Get a set of existing filenames in the Drive folder for resume capability."""
    existing_files = set()
    if os.path.exists(drive_folder_path):
        for file in os.listdir(drive_folder_path):
            if os.path.isfile(os.path.join(drive_folder_path, file)):
                existing_files.add(file)
    print(f"\n✓ Found {len(existing_files)} existing files in Drive folder (will skip if already downloaded)")
    return existing_files

def has_media(message):
    """Check if a message contains downloadable media."""
    return isinstance(message.media, (MessageMediaDocument, MessageMediaPhoto))

def get_file_info(message):
    """Extract file information from a message."""
    if isinstance(message.media, MessageMediaDocument):
        doc = message.media.document
        # Get filename from attributes or use default
        filename = None
        for attr in doc.attributes:
            if hasattr(attr, 'file_name'):
                filename = attr.file_name
                break
        
        if not filename:
            # Generate filename from document ID
            filename = f"document_{doc.id}"
            # Try to get extension from mime type
            if doc.mime_type:
                ext = doc.mime_type.split('/')[-1]
                if ext:
                    filename += f".{ext}"
        
        file_size = doc.size
        return filename, file_size
    
    elif isinstance(message.media, MessageMediaPhoto):
        # For photos, generate a filename
        photo = message.media.photo
        filename = f"photo_{photo.id}.jpg"
        file_size = None  # Photo size not always available
        return filename, file_size
    
    return None, None

def download_with_retry(client, message, temp_path, max_retries=3):
    """Download a file with FloodWait error handling."""
    for attempt in range(max_retries):
        try:
            # Download the file
            result = client.download_media(message, file=temp_path)
            return result
        except FloodWaitError as e:
            wait_time = e.seconds
            print(f"  ⚠ FloodWait: Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)
            # Retry after waiting
            continue
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠ Download error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(5)  # Wait 5 seconds before retry
            else:
                raise
    return None

def move_to_drive(temp_file_path, drive_file_path):
    """Move file from temp directory to Drive and verify."""
    try:
        # Move the file
        shutil.move(temp_file_path, drive_file_path)
        
        # Verify the move was successful
        if os.path.exists(drive_file_path) and os.path.getsize(drive_file_path) > 0:
            # Ensure temp file is deleted
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return True
        else:
            print(f"  ✗ Verification failed: File not found or empty in Drive")
            return False
    except Exception as e:
        print(f"  ✗ Move failed: {str(e)}")
        # Clean up temp file if move failed
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        return False

def format_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes is None:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def mount_drive():
    """Mount Google Drive if running in Colab."""
    if IS_COLAB:
        try:
            drive.mount('/content/drive')
            print("✓ Google Drive mounted successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to mount Google Drive: {str(e)}")
            return False
    else:
        print("⚠ Not running in Colab - assuming Drive is already accessible at configured path")
        return True

def main():
    """Main execution function."""
    try:
        # Mount Drive if in Colab
        if IS_COLAB:
            if not mount_drive():
                print("✗ Cannot proceed without Drive access")
                return
        
        # Get user inputs
        api_id, api_hash, channel_link, folder_name, reverse_order = get_user_inputs()
        
        # Convert api_id to integer
        try:
            api_id = int(api_id)
        except ValueError:
            print("✗ Error: API_ID must be a number")
            return
        
        # Validate inputs
        if not api_id or not api_hash:
            print("✗ Error: API_ID and API_HASH are required")
            return
        
        if not channel_link:
            print("✗ Error: Channel link is required")
            return
        
        # Setup paths
        drive_folder_path = os.path.join(DRIVE_BASE_PATH, folder_name)
        setup_directories(drive_folder_path)
        
        # Get existing files for resume capability
        existing_files = get_existing_files(drive_folder_path)
        
        # Initialize Telegram client
        print("\n" + "=" * 60)
        print("Connecting to Telegram...")
        print("=" * 60)
        
        # Use a session file in temp directory
        session_file = os.path.join(TEMP_DOWNLOAD_DIR, 'telegram_session')
        client = TelegramClient(session_file, api_id, api_hash)
        
        client.start()
        
        # Verify channel access
        print(f"\n✓ Connected! Accessing channel: {channel_link}")
        entity = client.get_entity(channel_link)
        print(f"✓ Channel found: {entity.title if hasattr(entity, 'title') else channel_link}")
        
        # Get all messages
        print("\n" + "=" * 60)
        print("Fetching messages from channel...")
        print("=" * 60)
        
        messages = []
        for message in client.iter_messages(entity, reverse=reverse_order):
            if has_media(message):
                messages.append(message)
        
        total_files = len(messages)
        print(f"\n✓ Found {total_files} messages with media files")
        
        if total_files == 0:
            print("No media files found in the channel. Exiting.")
            return
        
        # Process files
        print("\n" + "=" * 60)
        print("Starting download and upload process...")
        print("=" * 60)
        
        downloaded_count = 0
        skipped_count = 0
        failed_count = 0
        total_size = 0
        
        for idx, message in enumerate(messages, 1):
            try:
                filename, file_size = get_file_info(message)
                
                if not filename:
                    print(f"\n[{idx}/{total_files}] ⚠ Skipping message {message.id}: Could not extract file info")
                    continue
                
                # Check if file already exists (resume capability)
                drive_file_path = os.path.join(drive_folder_path, filename)
                if filename in existing_files:
                    print(f"\n[{idx}/{total_files}] ⊘ SKIPPED (already exists): {filename}")
                    skipped_count += 1
                    if file_size:
                        total_size += file_size
                    continue
                
                print(f"\n[{idx}/{total_files}] ↓ Downloading: {filename}")
                if file_size:
                    print(f"    Size: {format_size(file_size)}")
                
                # Download to temp directory
                temp_file_path = os.path.join(TEMP_DOWNLOAD_DIR, filename)
                
                # Handle filename conflicts
                counter = 1
                original_temp_path = temp_file_path
                while os.path.exists(temp_file_path):
                    name, ext = os.path.splitext(filename)
                    temp_file_path = os.path.join(TEMP_DOWNLOAD_DIR, f"{name}_{counter}{ext}")
                    counter += 1
                
                # Download with retry logic
                downloaded_path = download_with_retry(client, message, temp_file_path)
                
                if not downloaded_path or not os.path.exists(downloaded_path):
                    print(f"  ✗ Download failed")
                    failed_count += 1
                    continue
                
                # Get actual downloaded file path (Telethon might rename it)
                actual_temp_path = downloaded_path if os.path.exists(downloaded_path) else temp_file_path
                
                # Handle filename conflicts in Drive
                counter = 1
                original_drive_path = drive_file_path
                while os.path.exists(drive_file_path):
                    name, ext = os.path.splitext(filename)
                    drive_file_path = os.path.join(drive_folder_path, f"{name}_{counter}{ext}")
                    counter += 1
                
                # Move to Drive
                print(f"  ↑ Uploading to Drive...")
                if move_to_drive(actual_temp_path, drive_file_path):
                    downloaded_count += 1
                    actual_size = os.path.getsize(drive_file_path)
                    total_size += actual_size
                    print(f"  ✓ Success! ({format_size(actual_size)})")
                else:
                    failed_count += 1
                    print(f"  ✗ Upload failed")
                
            except FloodWaitError as e:
                wait_time = e.seconds
                print(f"\n  ⚠ FloodWait: Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                # Retry this message
                idx -= 1
                continue
            except Exception as e:
                print(f"\n  ✗ Error processing message {message.id}: {str(e)}")
                failed_count += 1
                continue
        
        # Summary
        print("\n" + "=" * 60)
        print("PROCESS COMPLETE")
        print("=" * 60)
        print(f"Total files processed: {total_files}")
        print(f"  ✓ Downloaded: {downloaded_count}")
        print(f"  ⊘ Skipped (already exists): {skipped_count}")
        print(f"  ✗ Failed: {failed_count}")
        print(f"Total size: {format_size(total_size)}")
        print("=" * 60)
        
        # Cleanup
        print("\nCleaning up temporary files...")
        if os.path.exists(TEMP_DOWNLOAD_DIR):
            for file in os.listdir(TEMP_DOWNLOAD_DIR):
                file_path = os.path.join(TEMP_DOWNLOAD_DIR, file)
                if os.path.isfile(file_path) and file != 'telegram_session.session':
                    try:
                        os.remove(file_path)
                    except:
                        pass
        print("✓ Cleanup complete")
        
    except SessionPasswordNeededError:
        print("\n✗ Error: This account has 2FA enabled. Please disable 2FA or use a different account.")
    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if 'client' in locals():
            client.disconnect()
            print("\n✓ Disconnected from Telegram")

if __name__ == "__main__":
    main()


