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
    
    def validate(self):
        """
        Validate configuration settings.
        
        Returns:
            tuple: (is_valid: bool, error_message: Optional[str])
        """
        if not self.api_id or not self.api_hash:
            return False, "API_ID and API_HASH are required"
        
        if not self.channel_link:
            return False, "Channel link is required"
        
        # Validate paths exist and are writable (if not in Colab)
        if not self.is_colab:
            # Check temp directory
            temp_dir = os.path.dirname(self.temp_download_dir) or self.temp_download_dir
            if not os.path.exists(temp_dir):
                try:
                    os.makedirs(temp_dir, exist_ok=True)
                except Exception as e:
                    return False, f"Cannot create temp directory: {str(e)}"
            
            # Check drive base path
            if not os.path.exists(self.drive_base_path):
                return False, f"Drive base path does not exist: {self.drive_base_path}"
            
            if not os.access(self.drive_base_path, os.W_OK):
                return False, f"Drive base path is not writable: {self.drive_base_path}"
        
        return True, None
        
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
        """
        Get the path to the Telegram session file.
        Uses a persistent location (home directory or current directory) instead of temp.
        """
        if self.is_colab:
            # In Colab, use /content (persists across restarts if runtime is kept)
            session_dir = '/content'
        else:
            # On local machine, use home directory
            session_dir = os.path.expanduser('~')
        
        # Create .tg_mirror directory for session files
        session_dir = os.path.join(session_dir, '.tg_mirror')
        os.makedirs(session_dir, exist_ok=True)
        
        return os.path.join(session_dir, 'telegram_session')
    
    def mount_drive(self) -> bool:
        """Check if Google Drive is mounted (should be mounted in Colab notebook cell)."""
        if self.is_colab:
            # Check if Drive is already mounted
            if os.path.exists('/content/drive/MyDrive'):
                print("✓ Google Drive is mounted")
                return True
            else:
                print("✗ Google Drive is not mounted!")
                print("  Please run the Drive mount cell in the Colab notebook first:")
                print("  from google.colab import drive")
                print("  drive.mount('/content/drive')")
                return False
        else:
            # Validate that drive path exists and is writable
            if not os.path.exists(self.drive_base_path):
                print(f"✗ Drive path does not exist: {self.drive_base_path}")
                return False
            if not os.access(self.drive_base_path, os.W_OK):
                print(f"✗ Drive path is not writable: {self.drive_base_path}")
                return False
            print("✓ Drive path is accessible")
            return True

