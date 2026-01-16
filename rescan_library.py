#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database
from modules.file_manager import FileManager

def main():
    print("Rescanning music library...")
    
    db = Database()
    file_manager = FileManager(db)
    
    # Clear existing songs (optional - comment out if you want to keep)
    # with db.get_connection() as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("DELETE FROM songs")
    #     conn.commit()
    
    # Rescan
    music_files = file_manager.scan_library()
    
    print(f"Found {len(music_files)} music files")
    print("Rescan complete!")

if __name__ == "__main__":
    main()