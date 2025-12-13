"""
Utility functions for the mirror script
"""

import os
import hashlib
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto


def has_media(message) -> bool:
    """Check if a message contains downloadable media."""
    return isinstance(message.media, (MessageMediaDocument, MessageMediaPhoto))


def get_file_info(message):
    """
    Extract file information from a message.
    
    Returns:
        tuple: (filename, file_size) or (None, None) if no media
    """
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


def format_size(size_bytes) -> str:
    """Format file size in human-readable format."""
    if size_bytes is None:
        return "Unknown"
    
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def setup_directories(*paths):
    """Create necessary directories if they don't exist."""
    for path in paths:
        os.makedirs(path, exist_ok=True)


def get_existing_files(drive_folder_path) -> dict:
    """
    Get a dict of existing files in the Drive folder for resume capability.
    
    Returns:
        dict: {filename: file_size} mapping for files that exist
    """
    existing_files = {}
    if os.path.exists(drive_folder_path):
        for file in os.listdir(drive_folder_path):
            file_path = os.path.join(drive_folder_path, file)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                existing_files[file] = file_size
    return existing_files


def resolve_filename_conflict(base_path, filename):
    """
    Resolve filename conflicts by appending numbers.
    
    Returns:
        str: Path to file without conflicts
    """
    if not os.path.exists(os.path.join(base_path, filename)):
        return os.path.join(base_path, filename)
    
    name, ext = os.path.splitext(filename)
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = os.path.join(base_path, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    Calculate hash of a file for integrity verification.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('md5' or 'sha256')
        
    Returns:
        str: Hexadecimal hash of the file
    """
    hash_obj = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        return None

