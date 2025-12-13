"""
Google Drive uploader module
"""

import os
import shutil
from typing import Optional, Tuple
from .utils import calculate_file_hash


class DriveUploader:
    """Handles uploading files to Google Drive."""
    
    def __init__(self, drive_folder_path: str):
        self.drive_folder_path = drive_folder_path
    
    def upload_file(self, temp_file_path: str, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Move file from temp directory to Drive and verify.
        
        Args:
            temp_file_path: Path to temporary file
            filename: Target filename in Drive
            
        Returns:
            tuple: (success: bool, final_path: Optional[str])
        """
        # Handle filename conflicts in Drive
        drive_file_path = os.path.join(self.drive_folder_path, filename)
        counter = 1
        original_path = drive_file_path
        while os.path.exists(drive_file_path):
            name, ext = os.path.splitext(filename)
            drive_file_path = os.path.join(self.drive_folder_path, f"{name}_{counter}{ext}")
            counter += 1
        
        try:
            # Calculate hash before move for integrity verification
            source_hash = calculate_file_hash(temp_file_path, 'md5')
            source_size = os.path.getsize(temp_file_path)
            
            # Move the file
            shutil.move(temp_file_path, drive_file_path)
            
            # Verify the move was successful and file integrity
            if os.path.exists(drive_file_path):
                dest_size = os.path.getsize(drive_file_path)
                
                # Check size matches
                if dest_size != source_size:
                    print(f"  ✗ Verification failed: Size mismatch (source: {source_size}, dest: {dest_size})")
                    # Try to clean up
                    try:
                        os.remove(drive_file_path)
                    except:
                        pass
                    return False, None
                
                # Verify file integrity with hash (for files < 100MB to avoid long delays)
                if source_size < 100 * 1024 * 1024 and source_hash:
                    dest_hash = calculate_file_hash(drive_file_path, 'md5')
                    if dest_hash != source_hash:
                        print(f"  ✗ Verification failed: File integrity check failed (hash mismatch)")
                        try:
                            os.remove(drive_file_path)
                        except:
                            pass
                        return False, None
                
                # Ensure temp file is deleted
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                return True, drive_file_path
            else:
                print(f"  ✗ Verification failed: File not found in Drive after move")
                return False, None
        except Exception as e:
            print(f"  ✗ Move failed: {str(e)}")
            # Clean up temp file if move failed
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            return False, None
    
    def cleanup_temp_files(self, temp_dir: str, keep_session: bool = True):
        """Clean up temporary files in the download directory."""
        if not os.path.exists(temp_dir):
            return
        
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                # Keep session files if requested
                if keep_session and file.endswith('.session'):
                    continue
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"  ⚠ Could not remove {file}: {str(e)}")

