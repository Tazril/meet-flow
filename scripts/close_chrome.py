#!/usr/bin/env python3
"""Close existing Chrome instances to avoid profile conflicts."""

import os
import subprocess
import sys

def close_chrome():
    """Close all Chrome instances on macOS."""
    try:
        print("🔄 Closing existing Chrome instances...")
        
        # Close Chrome on macOS
        subprocess.run(["pkill", "-f", "Google Chrome"], check=False)
        subprocess.run(["pkill", "-f", "Chromium"], check=False)
        
        print("✅ Chrome instances closed")
        return True
        
    except Exception as e:
        print(f"⚠️ Error closing Chrome: {e}")
        return False

if __name__ == "__main__":
    close_chrome() 