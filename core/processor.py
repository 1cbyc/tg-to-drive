"""
Main processing orchestration for mirroring
"""

import os
import time
from typing import Optional, Callable
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError

from .config import Config
from .downloader import TelegramDownloader
from .uploader import DriveUploader
from .utils import format_size, get_file_info, get_existing_files, setup_directories


class MirrorProcessor:
    """Main processor for mirroring Telegram channels to Google Drive."""
    
    def __init__(self, config: Config):
        self.config = config
        self.downloader: Optional[TelegramDownloader] = None
        self.uploader: Optional[DriveUploader] = None
        self.client: Optional[TelegramClient] = None
        
        # Statistics
        self.downloaded_count = 0
        self.skipped_count = 0
        self.failed_count = 0
        self.total_size = 0
        
        # Progress callback (optional, for bot integration)
        self.progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable):
        """Set a callback function for progress updates."""
        self.progress_callback = callback
    
    def _notify_progress(self, message: str, **kwargs):
        """Notify progress via callback if set."""
        if self.progress_callback:
            self.progress_callback(message, **kwargs)
    
    def initialize(self) -> bool:
        """Initialize clients and connections."""
        try:
            # Mount Drive if in Colab
            if self.config.is_colab:
                if not self.config.mount_drive():
                    print("✗ Cannot proceed without Drive access")
                    return False
            
            # Setup directories
            drive_folder_path = self.config.get_drive_folder_path()
            setup_directories(self.config.temp_download_dir, drive_folder_path)
            print(f"\n✓ Directories set up:")
            print(f"  - Temp: {self.config.temp_download_dir}")
            print(f"  - Drive: {drive_folder_path}")
            
            # Initialize Telegram client
            print("\n" + "=" * 60)
            print("Connecting to Telegram...")
            print("=" * 60)
            
            session_file = self.config.get_session_file()
            self.client = TelegramClient(
                session_file,
                self.config.api_id,
                self.config.api_hash
            )
            self.client.start()
            
            # Initialize downloader and uploader
            self.downloader = TelegramDownloader(self.client, self.config.temp_download_dir)
            self.uploader = DriveUploader(drive_folder_path)
            
            return True
            
        except SessionPasswordNeededError:
            print("\n✗ Error: This account has 2FA enabled. Please disable 2FA or use a different account.")
            return False
        except Exception as e:
            print(f"\n✗ Fatal error during initialization: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_channel(self) -> bool:
        """Process all files from the configured channel."""
        if not self.client or not self.downloader or not self.uploader:
            print("✗ Error: Not initialized. Call initialize() first.")
            return False
        
        try:
            # Verify channel access
            print(f"\n✓ Connected! Accessing channel: {self.config.channel_link}")
            
            # Try to get entity - handle numeric IDs specially
            channel_link = self.config.channel_link
            entity = None
            
            # If it's a numeric ID, try converting to int first
            if channel_link.startswith('-') and channel_link.lstrip('-').isdigit():
                try:
                    # Try as integer
                    channel_id = int(channel_link)
                    entity = self.client.loop.run_until_complete(
                        self.client.get_entity(channel_id)
                    )
                except Exception as e:
                    # If that fails, try as string
                    print(f"  ⚠ Integer lookup failed: {str(e)}, trying as string...")
                    try:
                        entity = self.client.loop.run_until_complete(
                            self.client.get_entity(channel_link)
                        )
                    except Exception as e2:
                        print(f"  ⚠ String lookup also failed: {str(e2)}")
                        entity = None
            else:
                # For usernames, use as-is
                try:
                    entity = self.client.loop.run_until_complete(
                        self.client.get_entity(channel_link)
                    )
                except Exception as e:
                    print(f"  ⚠ Username lookup failed: {str(e)}")
                    entity = None
            
            # If still not found, try searching through dialogs
            if not entity:
                print("  ⚠ Channel not found directly, searching through your dialogs...")
                try:
                    dialogs = self.client.loop.run_until_complete(self.client.get_dialogs())
                    print(f"  📋 Searching through {len(dialogs)} dialogs...")
                    
                    # Normalize the target channel_link for comparison
                    target_id_str = channel_link.strip()
                    # Extract numeric part (remove -100 prefix if present)
                    if target_id_str.startswith('-100'):
                        target_numeric = target_id_str[4:]  # Remove '-100'
                    elif target_id_str.startswith('-'):
                        target_numeric = target_id_str[1:]  # Remove '-'
                    else:
                        target_numeric = target_id_str
                    
                    for dialog in dialogs:
                        if dialog.is_channel:
                            dialog_entity = dialog.entity
                            dialog_id = dialog_entity.id
                            
                            # Format the dialog ID the same way list_channels.py does
                            # Channel IDs: entity.id is positive, we format as -100{id}
                            if dialog_id > 0:
                                formatted_id = f"-100{dialog_id}"
                            else:
                                formatted_id = str(dialog_id)
                            
                            # Also try just the numeric part
                            dialog_numeric = str(abs(dialog_id))
                            
                            # Check multiple formats
                            if (formatted_id == target_id_str or
                                str(dialog_id) == target_id_str or
                                dialog_numeric == target_numeric or
                                f"-100{dialog_numeric}" == target_id_str):
                                entity = dialog_entity
                                print(f"  ✓ Found channel in dialogs: {dialog_entity.title}")
                                print(f"     Matched ID: {formatted_id}")
                                break
                except Exception as e:
                    print(f"  ⚠ Could not search dialogs: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            if not entity:
                error_msg = (
                    f"\n✗ Cannot find channel: {channel_link}\n"
                    f"  Possible reasons:\n"
                    f"  1. You don't have access to this channel\n"
                    f"  2. The channel ID is incorrect\n"
                    f"  3. The channel was deleted\n\n"
                    f"  💡 Try running 'python list_channels.py' to see all channels you have access to."
                )
                raise ValueError(error_msg)
            
            channel_title = entity.title if hasattr(entity, 'title') else self.config.channel_link
            print(f"✓ Channel found: {channel_title}")
            
            # Get all messages
            print("\n" + "=" * 60)
            print("Fetching messages from channel...")
            print("=" * 60)
            
            messages = list(self.downloader.get_channel_messages(
                entity,
                reverse=self.config.reverse_order
            ))
            
            total_files = len(messages)
            print(f"\n✓ Found {total_files} messages with media files")
            
            if total_files == 0:
                print("No media files found in the channel. Exiting.")
                return True
            
            # Get existing files for resume capability
            drive_folder_path = self.config.get_drive_folder_path()
            existing_files = get_existing_files(drive_folder_path)
            print(f"\n✓ Found {len(existing_files)} existing files in Drive folder (will skip if already downloaded)")
            
            # Process files
            print("\n" + "=" * 60)
            print("Starting download and upload process...")
            print("=" * 60)
            
            self._notify_progress("started", total=total_files)
            
            for idx, message in enumerate(messages, 1):
                try:
                    filename, file_size = get_file_info(message)
                    
                    if not filename:
                        print(f"\n[{idx}/{total_files}] ⚠ Skipping message {message.id}: Could not extract file info")
                        continue
                    
                    # Check if file already exists (resume capability)
                    if filename in existing_files:
                        print(f"\n[{idx}/{total_files}] ⊘ SKIPPED (already exists): {filename}")
                        self.skipped_count += 1
                        if file_size:
                            self.total_size += file_size
                        self._notify_progress("skipped", current=idx, total=total_files, filename=filename)
                        continue
                    
                    print(f"\n[{idx}/{total_files}] ↓ Downloading: {filename}")
                    if file_size:
                        print(f"    Size: {format_size(file_size)}")
                    
                    self._notify_progress("downloading", current=idx, total=total_files, filename=filename, size=file_size)
                    
                    # Download file
                    downloaded_path = self.downloader.download_file(message)
                    
                    if not downloaded_path or not os.path.exists(downloaded_path):
                        print(f"  ✗ Download failed")
                        self.failed_count += 1
                        self._notify_progress("failed", current=idx, total=total_files, filename=filename, reason="download")
                        continue
                    
                    # Upload to Drive
                    print(f"  ↑ Uploading to Drive...")
                    self._notify_progress("uploading", current=idx, total=total_files, filename=filename)
                    
                    success, final_path = self.uploader.upload_file(downloaded_path, filename)
                    
                    if success:
                        self.downloaded_count += 1
                        actual_size = os.path.getsize(final_path)
                        self.total_size += actual_size
                        print(f"  ✓ Success! ({format_size(actual_size)})")
                        self._notify_progress("completed", current=idx, total=total_files, filename=filename, size=actual_size)
                    else:
                        self.failed_count += 1
                        print(f"  ✗ Upload failed")
                        self._notify_progress("failed", current=idx, total=total_files, filename=filename, reason="upload")
                
                except FloodWaitError as e:
                    wait_time = e.seconds
                    print(f"\n  ⚠ FloodWait: Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    # Retry this message
                    idx -= 1
                    continue
                except (TimeoutError, ConnectionError) as e:
                    print(f"\n  ⚠ Timeout/Connection error on message {message.id}: {str(e)}")
                    print(f"  ⏳ Waiting 30 seconds before retry...")
                    time.sleep(30)
                    # Retry this message
                    idx -= 1
                    continue
                except Exception as e:
                    print(f"\n  ✗ Error processing message {message.id}: {str(e)}")
                    self.failed_count += 1
                    self._notify_progress("error", current=idx, total=total_files, error=str(e))
                    continue
            
            # Summary
            self._print_summary(total_files)
            self._notify_progress("finished", 
                                total=total_files,
                                downloaded=self.downloaded_count,
                                skipped=self.skipped_count,
                                failed=self.failed_count,
                                total_size=self.total_size)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Fatal error: {str(e)}")
            import traceback
            traceback.print_exc()
            self._notify_progress("error", error=str(e))
            return False
    
    def _print_summary(self, total_files: int):
        """Print processing summary."""
        print("\n" + "=" * 60)
        print("PROCESS COMPLETE")
        print("=" * 60)
        print(f"Total files processed: {total_files}")
        print(f"  ✓ Downloaded: {self.downloaded_count}")
        print(f"  ⊘ Skipped (already exists): {self.skipped_count}")
        print(f"  ✗ Failed: {self.failed_count}")
        print(f"Total size: {format_size(self.total_size)}")
        print("=" * 60)
    
    def cleanup(self):
        """Clean up resources."""
        if self.uploader:
            drive_folder_path = self.config.get_drive_folder_path()
            self.uploader.cleanup_temp_files(self.config.temp_download_dir, keep_session=True)
            print("\n✓ Cleanup complete")
        
        if self.client:
            try:
                self.client.disconnect()
                print("✓ Disconnected from Telegram")
            except Exception as e:
                # Ignore errors during disconnect (e.g., corrupted session file)
                # These are non-critical and don't affect the actual mirroring
                if "disk I/O error" in str(e).lower() or "sqlite" in str(e).lower():
                    print("⚠ Session file cleanup warning (non-critical): " + str(e))
                else:
                    print(f"⚠ Disconnect warning: {str(e)}")

