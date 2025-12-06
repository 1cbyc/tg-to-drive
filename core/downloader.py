"""
Telegram downloader module with FloodWait handling
"""

import os
import time
import asyncio
import threading
from typing import Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

from .utils import has_media, get_file_info, format_size


class TelegramDownloader:
    """Handles downloading files from Telegram with retry logic."""
    
    def __init__(self, client: TelegramClient, temp_dir: str):
        self.client = client
        self.temp_dir = temp_dir
    
    def _progress_callback(self, downloaded_bytes: int, total_bytes: int):
        """Progress callback for download updates."""
        if total_bytes and total_bytes > 0:
            percent = (downloaded_bytes / total_bytes) * 100
            downloaded_mb = downloaded_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            # Show progress with a simple progress bar
            bar_length = 30
            filled = int(bar_length * downloaded_bytes // total_bytes)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f"  📥 [{bar}] {percent:.1f}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)", end='\r', flush=True)
            self._last_progress_bytes = downloaded_bytes
            self._last_progress_time = time.time()
    
    def _monitor_file_size(self, file_path: str, total_size: int, stop_event: threading.Event):
        """Monitor file size and show progress if callback isn't working."""
        last_size = 0
        last_update = time.time()
        stalled_count = 0
        check_interval = 5  # Check every 5 seconds
        wait_count = 0
        start_time = time.time()
        
        # Show heartbeat while waiting for file to appear
        while not os.path.exists(file_path) and wait_count < 12 and not stop_event.is_set():  # Up to 60 seconds
            elapsed = int(time.time() - start_time)
            if wait_count % 2 == 0:  # Every 10 seconds
                print(f"  ⏳ Waiting for download to start... ({elapsed}s elapsed)", end='\r', flush=True)
            time.sleep(5)
            wait_count += 1
        
        if not os.path.exists(file_path) and not stop_event.is_set():
            elapsed = int(time.time() - start_time)
            print(f"\n  ⚠ File not created after {elapsed}s - download may be stuck at API level")
            print(f"  💡 This might indicate a network/Telegram server issue")
        
        while not stop_event.is_set():
            time.sleep(check_interval)
            
            if os.path.exists(file_path):
                current_size = os.path.getsize(file_path)
                current_time = time.time()
                elapsed = int(current_time - start_time)
                
                # If file is growing, show progress
                if current_size > last_size:
                    percent = (current_size / total_size * 100) if total_size > 0 else 0
                    time_diff = current_time - last_update if current_time > last_update else check_interval
                    speed = (current_size - last_size) / time_diff if time_diff > 0 else 0
                    speed_mb = speed / (1024 * 1024)
                    
                    bar_length = 30
                    filled = int(bar_length * current_size // total_size) if total_size > 0 else 0
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"  📥 [{bar}] {percent:.1f}% ({format_size(current_size)} / {format_size(total_size)}) @ {speed_mb:.1f} MB/s [{elapsed}s]", end='\r', flush=True)
                    
                    last_size = current_size
                    last_update = current_time
                    stalled_count = 0
                else:
                    # File not growing - might be stalled
                    stalled_count += 1
                    if stalled_count >= 3:  # 15 seconds of no growth (3 checks * 5s)
                        elapsed = int(current_time - start_time)
                        print(f"\n  ⚠ Download stalled (no progress for 15s). Current: {format_size(current_size)} / {format_size(total_size)} [{elapsed}s total]")
                        stalled_count = 0  # Reset to avoid spam
                
                # If file is complete
                if total_size > 0 and current_size >= total_size * 0.99:  # 99% complete
                    stop_event.set()
                    break
            elif not stop_event.is_set():
                # File doesn't exist yet or was deleted
                elapsed = int(time.time() - start_time)
                if elapsed > 60:  # After 60 seconds, warn
                    print(f"\n  ⚠ Download seems stuck - no file created after {elapsed}s")
                time.sleep(2)
    
    def download_file(self, message, max_retries: int = 3) -> Optional[str]:
        """
        Download a file from a Telegram message with FloodWait handling.
        
        Args:
            message: Telegram message object
            max_retries: Maximum number of retry attempts
            
        Returns:
            Path to downloaded file or None if failed
        """
        if not has_media(message):
            return None
        
        filename, file_size = get_file_info(message)
        if not filename:
            return None
        
        temp_file_path = os.path.join(self.temp_dir, filename)
        
        # Handle filename conflicts
        counter = 1
        original_path = temp_file_path
        while os.path.exists(temp_file_path):
            name, ext = os.path.splitext(filename)
            temp_file_path = os.path.join(self.temp_dir, f"{name}_{counter}{ext}")
            counter += 1
        
        # Create progress callback for large files (>50MB)
        progress_callback = None
        monitor_thread = None
        stop_monitor = threading.Event()
        
        if file_size and file_size > 50 * 1024 * 1024:  # > 50MB
            print(f"  ⏳ Starting download... (this may take a while for large files)")
            print(f"  📊 Monitoring progress (updates every 5 seconds)...")
            progress_callback = self._progress_callback
            self._last_progress_bytes = 0
            self._last_progress_time = time.time()
            
            # Start file size monitor as backup (will show progress even if callback fails)
            monitor_thread = threading.Thread(
                target=self._monitor_file_size,
                args=(temp_file_path, file_size, stop_monitor),
                daemon=True
            )
            monitor_thread.start()
        
        # Calculate timeout: 5 minutes per GB, minimum 10 minutes, maximum 2 hours
        # But add a shorter initial connection timeout (2 minutes) to detect API-level hangs
        timeout_seconds = max(600, min(7200, int(file_size / (1024**3) * 300))) if file_size else 3600
        initial_timeout = 120  # 2 minutes to detect if download starts at all
        
        # Download with retry logic
        # download_media is async, so we need to await it properly
        for attempt in range(max_retries):
            try:
                # Check if file exists after initial timeout to detect API-level hangs
                download_started = False
                
                # Use the event loop to run the async download with timeout
                download_task = self.client.download_media(
                    message, 
                    file=temp_file_path,
                    progress_callback=progress_callback
                )
                
                # First check: wait for initial connection (2 minutes)
                # This helps detect if the download is stuck at API level
                try:
                    # Create a wrapper that checks if file appears
                    async def download_with_check():
                        nonlocal download_started
                        result = await download_task
                        download_started = True
                        return result
                    
                    # Try initial timeout first
                    try:
                        result = self.client.loop.run_until_complete(
                            asyncio.wait_for(download_with_check(), timeout=initial_timeout)
                        )
                    except asyncio.TimeoutError:
                        # Check if file started appearing
                        if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
                            # File started, continue with longer timeout
                            print(f"\n  ✓ Download started! Continuing with full timeout...")
                            result = self.client.loop.run_until_complete(
                                asyncio.wait_for(download_task, timeout=timeout_seconds)
                            )
                        else:
                            # No file created - likely stuck at API level
                            raise asyncio.TimeoutError("Download didn't start - no file created after 2 minutes")
                except asyncio.TimeoutError as e:
                    if "Download didn't start" in str(e):
                        raise  # Re-raise our custom timeout
                    # Otherwise, it's the full timeout
                    raise
                
                # Stop monitor thread
                if monitor_thread:
                    stop_monitor.set()
                    monitor_thread.join(timeout=2)
                
                if result and os.path.exists(result):
                    if progress_callback or monitor_thread:
                        print()  # New line after progress
                    return result
                elif os.path.exists(temp_file_path):
                    if progress_callback or monitor_thread:
                        print()  # New line after progress
                    return temp_file_path
                return None
                
            except asyncio.TimeoutError:
                # Stop monitor thread
                if monitor_thread:
                    stop_monitor.set()
                    monitor_thread.join(timeout=2)
                
                if attempt < max_retries - 1:
                    current_size = os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 0
                    print(f"\n  ⚠ Download timeout after {timeout_seconds}s (attempt {attempt + 1}/{max_retries})")
                    if current_size > 0:
                        print(f"  📊 Downloaded so far: {format_size(current_size)} / {format_size(file_size)}")
                    print(f"  ⏳ Retrying in 30 seconds...")
                    time.sleep(30)
                    # Increase timeout for next attempt
                    timeout_seconds = int(timeout_seconds * 1.5)
                    continue
                else:
                    print(f"\n  ✗ Download failed: Timeout after {max_retries} attempts")
                    return None
            except FloodWaitError as e:
                wait_time = e.seconds
                print(f"  ⚠ FloodWait: Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            except (TimeoutError, ConnectionError) as e:
                # Handle timeout and connection errors with longer wait
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 10  # Progressive backoff: 10s, 20s, 30s
                    print(f"  ⚠ Timeout/Connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"  ⏳ Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  ✗ Download failed after {max_retries} attempts: {str(e)}")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠ Download error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(5)
                else:
                    print(f"  ✗ Download failed after {max_retries} attempts: {str(e)}")
                    return None
        
        return None
    
    def get_channel_messages(self, entity, reverse: bool = False):
        """
        Get all messages with media from a Telegram channel.
        
        Args:
            entity: Telegram channel entity
            reverse: If True, get oldest first; if False, get newest first
            
        Yields:
            Messages with media
        """
        for message in self.client.iter_messages(entity, reverse=reverse):
            if has_media(message):
                yield message

