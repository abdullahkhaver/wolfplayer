#!/usr/bin/env python3
import sys
from pathlib import Path
from modules.audio_fixer import AudioFixer

def main():
    downloads_dir = Path("downloads")
    
    if not downloads_dir.exists():
        print("Downloads directory not found!")
        return
    
    corrupted_files = []
    
    print("Scanning for corrupted MP3 files...")
    
    for file in downloads_dir.glob("*.mp3"):
        print(f"Checking: {file.name}")
        
        if not AudioFixer.verify_mp3_file(file):
            corrupted_files.append(file)
            print(f"  -> Corrupted!")
    
    if not corrupted_files:
        print("No corrupted files found!")
        return
    
    print(f"\nFound {len(corrupted_files)} corrupted files:")
    for file in corrupted_files:
        print(f"  - {file.name}")
    
    response = input("\nAttempt to fix these files? (y/n): ")
    if response.lower() != 'y':
        return
    
    print("\nFixing files...")
    fixed_count = 0
    
    for file in corrupted_files:
        print(f"Fixing: {file.name}...", end=" ")
        if AudioFixer.fix_mp3_file(file):
            print("SUCCESS")
            fixed_count += 1
        else:
            print("FAILED")
    
    print(f"\nFixed {fixed_count} out of {len(corrupted_files)} files.")
    
    # Suggest rescan
    print("\nPlease restart the music player to rescan the library.")

if __name__ == "__main__":
    main()