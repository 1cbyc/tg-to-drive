"""
Logging utility for the mirror script
"""

import os
import logging
from datetime import datetime
from typing import Optional


class MirrorLogger:
    """Logger for mirror operations with optional file logging."""
    
    def __init__(self, log_file: Optional[str] = None, enable_file_logging: bool = True):
        """
        Initialize logger.
        
        Args:
            log_file: Path to log file (optional, defaults to mirror.log in current directory)
            enable_file_logging: Whether to enable file logging
        """
        self.logger = logging.getLogger('tg_mirror')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler (always enabled)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if enable_file_logging:
            if not log_file:
                # Default log file location
                log_dir = os.path.expanduser('~/.tg_mirror')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, 'mirror.log')
            
            # Create log directory if needed
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            self.log_file = log_file
            self.logger.info(f"Logging to file: {log_file}")
        else:
            self.log_file = None
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)

