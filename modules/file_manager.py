import os
import shutil
from pathlib import Path
from config import Config
import logging
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB
from mutagen.easyid3 import EasyID3

logger = logging.getLogger(__name__)

class FileManager:
    def __init__(self, database):
        self.db = database
        self.downloads_dir = Config.DOWNLOADS_DIR
    
    def scan_library(self):
        """Scan downloads folder for music files"""
        music_files = []
        
        for file in self.downloads_dir.rglob('*'):
            if file.suffix.lower() in Config.SUPPORTED_FORMATS:
                try:
                    # Extract metadata
                    metadata = self.extract_metadata(file)
                    
                    # Add to database
                    song_id = self.db.add_song(
                        title=metadata['title'],
                        artist=metadata['artist'],
                        filepath=str(file),
                        duration=metadata['duration'],
                        album=metadata['album'],
                        filesize=file.stat().st_size,
                        bitrate=metadata.get('bitrate', 0)
                    )
                    
                    if song_id:
                        music_files.append({
                            'id': song_id,
                            'path': str(file),
                            'metadata': metadata
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing {file}: {e}")
        
        return music_files
    
    def extract_metadata(self, file_path):
        """Extract metadata from audio file"""
        try:
            if file_path.suffix.lower() == '.mp3':
                return self._extract_mp3_metadata(file_path)
            else:
                # For non-mp3 files, return basic info
                return self._get_basic_metadata(file_path)
                
        except Exception as e:
            logger.error(f"Metadata extraction failed for {file_path}: {e}")
            return self._get_basic_metadata(file_path)
    
    def _extract_mp3_metadata(self, file_path):
        """Extract metadata from MP3 file"""
        try:
            audio = MP3(file_path)
            
            # Default values
            title = file_path.stem
            artist = 'Unknown'
            album = ''
            duration = audio.info.length
            bitrate = 0
            
            # Try to get ID3 tags with EasyID3 first (simpler)
            try:
                easy = EasyID3(file_path)
                if 'title' in easy:
                    title = easy['title'][0]
                if 'artist' in easy:
                    artist = easy['artist'][0]
                if 'album' in easy:
                    album = easy['album'][0]
            except:
                # Fallback to raw ID3 tags
                try:
                    id3 = ID3(file_path)
                    if 'TIT2' in id3:
                        title = str(id3['TIT2'])
                    if 'TPE1' in id3:
                        artist = str(id3['TPE1'])
                    if 'TALB' in id3:
                        album = str(id3['TALB'])
                except:
                    pass
            
            # Get bitrate
            if hasattr(audio.info, 'bitrate'):
                bitrate = audio.info.bitrate // 1000  # Convert to kbps
            
            return {
                'title': title[:200],
                'artist': artist[:100],
                'album': album[:100],
                'duration': duration,
                'bitrate': bitrate
            }
                
        except Exception as e:
            logger.warning(f"MP3 metadata extraction failed for {file_path}: {e}")
            # Fallback to basic info
            return self._get_basic_metadata(file_path)
    
    def _get_basic_metadata(self, file_path):
        """Get basic metadata when extraction fails"""
        return {
            'title': file_path.stem[:200],
            'artist': 'Unknown',
            'album': '',
            'duration': 0,
            'bitrate': 0
        }
    
    def rename_song(self, song_id, new_title):
        """Rename song file and update metadata"""
        song = self.db.get_song(song_id)
        if not song:
            return False
        
        old_path = Path(song['filepath'])
        
        if not old_path.exists():
            return False
        
        # Create new filename
        new_filename = f"{new_title}{old_path.suffix}"
        new_path = old_path.parent / new_filename
        
        try:
            # Rename file
            shutil.move(str(old_path), str(new_path))
            
            # Update ID3 tags if MP3
            if old_path.suffix.lower() == '.mp3':
                self._update_mp3_tags(new_path, new_title, song['artist'], song['album'])
            
            # Update database
            self.db.update_song(song_id, title=new_title, filepath=str(new_path))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to rename song: {e}")
            return False
    
    def _update_mp3_tags(self, file_path, title, artist, album):
        """Update MP3 ID3 tags"""
        try:
            # Try with EasyID3 first
            try:
                audio = EasyID3(file_path)
                audio['title'] = title
                audio['artist'] = artist
                audio['album'] = album
                audio.save()
            except:
                # Fallback to raw ID3
                try:
                    id3 = ID3(file_path)
                    id3.add(TIT2(encoding=3, text=title))
                    id3.add(TPE1(encoding=3, text=artist))
                    id3.add(TALB(encoding=3, text=album))
                    id3.save()
                except Exception as e:
                    logger.error(f"Failed to update MP3 tags with ID3: {e}")
                    # Create new ID3 tags if file doesn't have them
                    try:
                        id3 = ID3()
                        id3.add(TIT2(encoding=3, text=title))
                        id3.add(TPE1(encoding=3, text=artist))
                        id3.add(TALB(encoding=3, text=album))
                        id3.save(file_path)
                    except Exception as e2:
                        logger.error(f"Failed to create new ID3 tags: {e2}")
                        
        except Exception as e:
            logger.error(f"Failed to update MP3 tags: {e}")
    
    def delete_song(self, song_id, delete_file=False):
        """Delete song from library and optionally delete file"""
        song = self.db.get_song(song_id)
        if not song:
            return False
        
        # Delete file if requested
        if delete_file:
            try:
                file_path = Path(song['filepath'])
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete file: {e}")
        
        # Delete from database
        self.db.delete_song(song_id)
        
        return True
    
    def organize_library(self, pattern="Artist/Album"):
        """Organize music library into folders"""
        songs = self.db.get_all_songs()
        
        for song in songs:
            try:
                old_path = Path(song['filepath'])
                if not old_path.exists():
                    continue
                
                # Create directory structure based on pattern
                if pattern == "Artist/Album":
                    artist = song['artist'] or 'Unknown Artist'
                    album = song['album'] or 'Unknown Album'
                    new_dir = self.downloads_dir / artist / album
                elif pattern == "Artist":
                    artist = song['artist'] or 'Unknown Artist'
                    new_dir = self.downloads_dir / artist
                else:  # pattern == "Flat"
                    new_dir = self.downloads_dir
                
                new_dir.mkdir(parents=True, exist_ok=True)
                new_path = new_dir / old_path.name
                
                # Move file
                if old_path != new_path:
                    shutil.move(str(old_path), str(new_path))
                    # Update database
                    self.db.update_song(song['id'], filepath=str(new_path))
                    
            except Exception as e:
                logger.error(f"Failed to organize {song['title']}: {e}")