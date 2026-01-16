import subprocess
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AudioFixer:
    @staticmethod
    def fix_mp3_file(filepath):
        """Try to fix corrupted MP3 files"""
        filepath = Path(filepath)
        if not filepath.exists():
            return False
        
        backup_path = filepath.with_suffix('.mp3.backup')
        
        try:
            # Create backup
            import shutil
            shutil.copy2(str(filepath), str(backup_path))
            
            # Try to fix with ffmpeg
            fixed_path = filepath.with_suffix('.fixed.mp3')
            
            result = subprocess.run([
                'ffmpeg', '-i', str(filepath),
                '-c', 'copy',  # Copy without re-encoding if possible
                str(fixed_path)
            ], capture_output=True, text=True)
            
            if fixed_path.exists() and fixed_path.stat().st_size > 1000:
                # Replace original with fixed version
                filepath.unlink()
                fixed_path.rename(filepath)
                logger.info(f"Fixed MP3 file: {filepath.name}")
                return True
            else:
                # Try re-encoding
                fixed_path.unlink(missing_ok=True)
                result = subprocess.run([
                    'ffmpeg', '-i', str(filepath),
                    '-codec:a', 'libmp3lame', '-q:a', '2',
                    str(fixed_path)
                ], capture_output=True, text=True)
                
                if fixed_path.exists() and fixed_path.stat().st_size > 1000:
                    filepath.unlink()
                    fixed_path.rename(filepath)
                    logger.info(f"Re-encoded MP3 file: {filepath.name}")
                    return True
            
            # If all fails, restore backup
            if filepath.exists():
                filepath.unlink()
            backup_path.rename(filepath)
            return False
            
        except Exception as e:
            logger.error(f"Failed to fix MP3 file {filepath}: {e}")
            # Try to restore backup
            if backup_path.exists():
                if filepath.exists():
                    filepath.unlink()
                backup_path.rename(filepath)
            return False
    
    @staticmethod
    def verify_mp3_file(filepath):
        """Verify if MP3 file is playable"""
        filepath = Path(filepath)
        if not filepath.exists():
            return False
        
        try:
            # Try to read with mutagen
            from mutagen.mp3 import MP3
            audio = MP3(filepath)
            return audio.info.length > 0
        except:
            # Try with ffprobe
            try:
                result = subprocess.run([
                    'ffprobe', '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(filepath)
                ], capture_output=True, text=True)
                
                duration = float(result.stdout.strip())
                return duration > 0
            except:
                return False