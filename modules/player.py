import pygame
import os
from pathlib import Path
import time
from config import Config
import logging

logger = logging.getLogger(__name__)

class MusicPlayer:
    def __init__(self, database):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        self.db = database
        self.current_song = None
        self._is_playing = False
        self.paused_position = 0
        self.length = 0
        self.start_time = 0
        self.volume = Config.DEFAULT_VOLUME
        self.current_song_id = None
        self.audio = None  # For tracking playback
    def _get_audio_duration(self, filepath):
        """Get audio duration using multiple methods"""
        try:
            # Try mutagen first
            try:
                from mutagen.mp3 import MP3
                if filepath.suffix.lower() == '.mp3':
                    audio = MP3(filepath)
                    return audio.info.length
            except:
                pass
            
            # Try using a simpler method: file size estimation
            try:
                file_size = filepath.stat().st_size
                # Rough estimate for MP3: 1MB ≈ 1 minute at 128kbps
                # More accurate: (file_size * 8) / (bitrate * 1000)
                if filepath.suffix.lower() == '.mp3':
                    # Assume 128kbps for MP3
                    bitrate = 128000  # bits per second
                    estimated_seconds = (file_size * 8) / bitrate
                    return estimated_seconds
                else:
                    # Default estimate
                    estimated_minutes = file_size / (1024 * 1024)
                    return estimated_minutes * 60
            except:
                pass
            
        except:
            pass
        
        return 180  # Default 3 minutes
    def load_song(self, song_id):
        """Load a song by ID"""
        song = self.db.get_song(song_id)
        if not song:
            logger.error(f"Song {song_id} not found in database")
            return False
        
        filepath = Path(song['filepath'])
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return False
        
        try:
            # First, verify file can be loaded
            try:
                pygame.mixer.music.load(str(filepath))
                pygame.mixer.music.unload()  # Unload after testing
            except pygame.error as e:
                logger.error(f"Pygame cannot load file {filepath}: {e}")
                # Try alternative loading method
                if not self._try_alternative_load(filepath):
                    return False
            
            self.current_song = filepath
            self.current_song_id = song_id
            self._is_playing = False
            self.paused_position = 0
            
            # Get duration from database or file
            if song['duration'] and song['duration'] > 0:
                self.length = song['duration']
            else:
                self.length = self._get_audio_duration(filepath)
                # Update database with actual duration
                self.db.update_song(song_id, duration=self.length)
            
            # Set volume
            pygame.mixer.music.set_volume(self.volume / 100.0)
            
            logger.info(f"Loaded song: {song['title']}, duration: {self.length}s")
            return True
            
        except Exception as e:
            logger.error(f"Error loading song {filepath}: {e}")
            return False
    
    def _try_alternative_load(self, filepath):
        """Try alternative methods to load problematic audio files"""
        try:
            # Try different buffer size
            pygame.mixer.quit()
            pygame.mixer.init(frequency=22050, buffer=2048)
            
            # Try loading again
            pygame.mixer.music.load(str(filepath))
            return True
        except:
            return False
    
    def play(self):
        """Start or resume playback"""
        try:
            if not self.current_song:
                logger.error("No song loaded to play")
                return False
            
            if self._is_playing:
                return True
            
            if self.paused_position > 0:
                # For pygame, we need to reload and seek
                pygame.mixer.music.load(str(self.current_song))
                pygame.mixer.music.play()
                # Seek to paused position
                if self.paused_position > 0:
                    time.sleep(0.1)  # Small delay
                    # Note: pygame doesn't support precise seeking, 
                    # so we'll track time manually
                    self.start_time = time.time() - self.paused_position
            else:
                pygame.mixer.music.load(str(self.current_song))
                pygame.mixer.music.play()
                self.start_time = time.time()
            
            self._is_playing = True
            self.paused_position = 0
            
            # Update play count
            if self.current_song_id:
                self.db.increment_play_count(self.current_song_id)
            
            logger.info(f"Started playing: {self.current_song.name}")
            return True
            
        except Exception as e:
            logger.error(f"Play error: {e}")
            return False
    
    def pause(self):
        """Pause playback"""
        try:
            if self._is_playing:
                pygame.mixer.music.pause()
                self._is_playing = False
                # Calculate paused position
                if self.start_time > 0:
                    self.paused_position = time.time() - self.start_time
                logger.info("Playback paused")
                return True
            return False
        except Exception as e:
            logger.error(f"Pause error: {e}")
            return False
    
    def unpause(self):
        """Unpause playback (alternative to play for paused state)"""
        try:
            if not self._is_playing and self.paused_position > 0:
                pygame.mixer.music.unpause()
                self._is_playing = True
                self.start_time = time.time() - self.paused_position
                self.paused_position = 0
                logger.info("Playback unpaused")
                return True
            return False
        except Exception as e:
            logger.error(f"Unpause error: {e}")
            return False
    
    def stop(self):
        """Stop playback"""
        try:
            pygame.mixer.music.stop()
            self._is_playing = False
            self.paused_position = 0
            self.start_time = 0
            logger.info("Playback stopped")
        except Exception as e:
            logger.error(f"Stop error: {e}")
    
    def set_volume(self, volume):
        """Set volume (0-100)"""
        try:
            self.volume = max(0, min(100, volume))
            pygame.mixer.music.set_volume(self.volume / 100.0)
        except Exception as e:
            logger.error(f"Volume error: {e}")
    
    def get_position(self):
        """Get current position in seconds"""
        try:
            if not self._is_playing:
                return self.paused_position
            
            if self.start_time > 0:
                elapsed = time.time() - self.start_time
                return min(elapsed, self.length)
            return 0
        except:
            return 0
    
    def set_position(self, position):
        """Set playback position in seconds"""
        try:
            if position < 0 or position > self.length:
                return False
            
            was_playing = self._is_playing
            
            if was_playing:
                pygame.mixer.music.stop()
            
            self.paused_position = position
            
            if was_playing:
                # Reload and play from position
                pygame.mixer.music.load(str(self.current_song))
                pygame.mixer.music.play()
                # We'll track the start time to simulate seeking
                self.start_time = time.time() - position
                self._is_playing = True
                self.paused_position = 0
            else:
                self._is_playing = False
            
            logger.info(f"Seeked to position: {position}s")
            return True
            
        except Exception as e:
            logger.error(f"Set position error: {e}")
            return False
    
    def skip_forward(self, seconds=10):
        """Skip forward by seconds"""
        current = self.get_position()
        new_position = min(current + seconds, self.length)
        return self.set_position(new_position)
    
    def skip_backward(self, seconds=10):
        """Skip backward by seconds"""
        current = self.get_position()
        new_position = max(current - seconds, 0)
        return self.set_position(new_position)
    
    @property
    def is_playing(self):
        """Check if currently playing"""
        return self._is_playing and pygame.mixer.music.get_busy()
    
    def get_current_song_info(self):
        """Get information about current song"""
        if not self.current_song_id:
            return None
        
        song = self.db.get_song(self.current_song_id)
        if not song:
            return None
        
        return dict(song)
    
    def get_state(self):
        """Get player state"""
        if self._is_playing:
            return "playing"
        elif self.paused_position > 0:
            return "paused"
        else:
            return "stopped"