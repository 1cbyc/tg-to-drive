"""
Helper script to load environment variables from .env file
This allows you to use .env files instead of setting environment variables manually

Usage:
    python load_env.py
    # Then run your script
    python run_bot.py
    # or
    python telegram_to_drive_mirror.py

Or import in your code:
    from load_env import load_env
    load_env()
"""

import os
from pathlib import Path


def load_env(env_file: str = '.env') -> bool:
    """
    Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file (default: .env)
        
    Returns:
        True if file was loaded, False otherwise
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        print(f"⚠ {env_file} file not found. Using environment variables or prompts.")
        return False
    
    print(f"📄 Loading environment from {env_file}...")
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Only set if not already in environment
                if key and value and key not in os.environ:
                    os.environ[key] = value
                    print(f"  ✓ {key} = {'*' * min(len(value), 20)}")
    
    print("✓ Environment loaded from .env file")
    return True


if __name__ == "__main__":
    load_env()
    print("\nEnvironment variables loaded. You can now run:")
    print("  python run_bot.py")
    print("  or")
    print("  python telegram_to_drive_mirror.py")

