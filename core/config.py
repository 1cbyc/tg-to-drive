"""
Configuration management for the mirror script
"""

import os
from typing import Optional

# Try to import Colab-specific modules
try:
    from google.colab import drive
    IS_COLAB = True
except ImportError:
    IS_COLAB = False


class Config:
    """Configuration class for managing settings."""
    
    def __init__(self):
        self.temp_download_dir = os.getenv('TEMP_DOWNLOAD_DIR', '/content/temp_downloads')
        self.drive_base_path = os.getenv('DRIVE_BASE_PATH', '/content/drive/MyDrive')
        self.is_colab = IS_COLAB
        
        # Telegram credentials (set via environment or prompts)
        self.api_id: Optional[int] = None
        self.api_hash: Optional[str] = None
        self.channel_link: Optional[str] = None
        self.folder_name: Optional[str] = None
        self.reverse_order: bool = False
        
        # Bot settings (optional)
        self.bot_token: Optional[str] = os.getenv('TELEGRAM_BOT_TOKEN')
        self.bot_enabled: bool = bool(self.bot_token)
        self.user_id: Optional[int] = None
        
    def load_from_env(self):
        """Load configuration from environment variables."""
        api_id = os.getenv('TELEGRAM_API_ID')
        if api_id:
            try:
                self.api_id = int(api_id)
            except ValueError:
                pass
        
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.channel_link = os.getenv('TELEGRAM_CHANNEL')
        self.folder_name = os.getenv('DRIVE_TARGET_FOLDER', 'Telegram_Mirror')
        
        reverse = os.getenv('DOWNLOAD_REVERSE', 'false').lower()
        self.reverse_order = reverse == 'true'
        
        user_id = os.getenv('TELEGRAM_USER_ID')
        if user_id:
            try:
                self.user_id = int(user_id)
            except ValueError:
                pass
    
    def get_drive_folder_path(self) -> str:
        """Get the full path to the Drive target folder."""
        if not self.folder_name:
            self.folder_name = 'Telegram_Mirror'
        return os.path.join(self.drive_base_path, self.folder_name)
    
    def get_session_file(self) -> str:
        """Get the path to the Telegram session file."""
        return os.path.join(self.temp_download_dir, 'telegram_session')
    
    def mount_drive(self) -> bool:
        """Mount Google Drive if running in Colab."""
        if self.is_colab:
            try:
                drive.mount('/content/drive')
                return True
            except Exception as e:
                print(f"✗ Failed to mount Google Drive: {str(e)}")
                return False
        else:
            print("⚠ Not running in Colab - assuming Drive is already accessible")
            return True

