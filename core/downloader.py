"""
Telegram downloader module with FloodWait handling
"""

import os
import time
from typing import Optional
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

from .utils import has_media, get_file_info


class TelegramDownloader:
    """Handles downloading files from Telegram with retry logic."""
    
    def __init__(self, client: TelegramClient, temp_dir: str):
        self.client = client
        self.temp_dir = temp_dir
    
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
        
        # Download with retry logic
        for attempt in range(max_retries):
            try:
                result = self.client.download_media(message, file=temp_file_path)
                if result and os.path.exists(result):
                    return result
                elif os.path.exists(temp_file_path):
                    return temp_file_path
                return None
            except FloodWaitError as e:
                wait_time = e.seconds
                print(f"  ⚠ FloodWait: Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
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

