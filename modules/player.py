import vlc
import os
from mutagen.mp3 import MP3
import time

class SimpleMusicPlayer:
    def __init__(self):
        self.instance = vlc.Instance()
        self.player = None
        self.current_file = None
        self.length = 0
        self.start_time = 0

    def load_song(self, filepath: str) -> bool:
        """Load a song without playing it"""
        try:
            if not os.path.exists(filepath):
                return False

            self.current_file = filepath
            self.player = self.instance.media_player_new()
            media = self.instance.media_new(filepath)
            self.player.set_media(media)

            # Get duration
            try:
                if filepath.lower().endswith(".mp3"):
                    audio = MP3(filepath)
                    self.length = audio.info.length
                else:
                    self.length = 180
            except:
                self.length = 180

            return True
        except Exception as e:
            print(f"Error loading song: {e}")
            return False

    def play(self) -> bool:
        """Start or resume playback"""
        if not self.player or not self.current_file:
            return False
        self.player.play()
        self.start_time = time.time()
        return True

    def pause(self) -> bool:
        """Pause playback"""
        if self.player and self.player.is_playing():
            self.player.pause()
            return True
        return False

    def stop(self):
        """Stop playback"""
        if self.player:
            self.player.stop()
            self.start_time = 0

    def set_volume(self, volume: int):
        """Set volume (0-100)"""
        if self.player:
            self.player.audio_set_volume(volume)

    def get_volume(self) -> int:
        """Get current volume"""
        if self.player:
            return self.player.audio_get_volume()
        return 0

    def get_position(self) -> float:
        """Get current position in seconds"""
        if self.player and self.current_file:
            pos = self.player.get_time() / 1000  # VLC returns milliseconds
            return pos
        return 0

    def get_length(self) -> float:
        """Get total length in seconds"""
        return self.length

    def set_position(self, percentage: float):
        """Seek to position (0.0 - 1.0)"""
        if self.player and self.length > 0:
            ms = int(self.length * percentage * 1000)
            self.player.set_time(ms)

    @property
    def is_playing(self) -> bool:
        """Check if currently playing"""
        return self.player.is_playing() if self.player else False
