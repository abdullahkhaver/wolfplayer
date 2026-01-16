import os
from pathlib import Path
from yt_dlp import YoutubeDL
from config import Config
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.downloads_dir = Config.DOWNLOADS_DIR
        
    def download_audio(self, url, progress_callback=None):
        """Download audio from YouTube URL"""
        try:
            # Generate clean filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Simple options for better compatibility
            options = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'outtmpl': str(self.downloads_dir / f'%(title)s_{timestamp}.%(ext)s'),
                'quiet': True,
                'no_warnings': False,
                'noplaylist': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    },
                    {
                        'key': 'FFmpegMetadata'
                    },
                ],
                'progress_hooks': [self._progress_hook] if progress_callback else None,
                'ignoreerrors': True,
                'nooverwrites': True,
                'continuedl': True,
            }
            
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    raise Exception("Failed to extract video info")
                
                # Find the downloaded file
                downloaded_file = None
                for file in self.downloads_dir.glob(f'*_{timestamp}*'):
                    if file.suffix.lower() in ['.mp3', '.m4a', '.webm']:
                        downloaded_file = file
                        break
                
                if not downloaded_file:
                    # Try to find any new file with timestamp
                    for file in self.downloads_dir.glob('*'):
                        if timestamp in file.name:
                            downloaded_file = file
                            break
                
                if not downloaded_file:
                    raise Exception("Could not find downloaded file")
                
                # Ensure it's MP3 (convert if needed)
                if downloaded_file.suffix.lower() != '.mp3':
                    mp3_file = downloaded_file.with_suffix('.mp3')
                    try:
                        # Try to rename (if already converted)
                        if mp3_file.exists():
                            downloaded_file = mp3_file
                        else:
                            # Try to convert
                            import subprocess
                            subprocess.run([
                                'ffmpeg', '-i', str(downloaded_file),
                                '-codec:a', 'libmp3lame', '-q:a', '2',
                                str(mp3_file)
                            ], check=False)
                            if mp3_file.exists():
                                downloaded_file = mp3_file
                                # Remove original
                                try:
                                    downloaded_file.with_suffix(downloaded_file.suffix).unlink()
                                except:
                                    pass
                    except:
                        pass
                
                # Get metadata
                metadata = {
                    'title': info.get('title', 'Unknown').replace('/', '_').replace('\\', '_')[:100],
                    'artist': info.get('uploader', 'Unknown')[:50],
                    'duration': info.get('duration', 0),
                    'filepath': str(downloaded_file),
                    'filesize': downloaded_file.stat().st_size if downloaded_file.exists() else 0,
                    'thumbnail': info.get('thumbnail'),
                    'url': url,
                    'channel': info.get('channel', 'Unknown')[:50],
                    'views': info.get('view_count', 0),
                    'description': info.get('description', '')[:200],
                }
                
                logger.info(f"Downloaded: {metadata['title']} ({metadata['filesize']} bytes)")
                return metadata
                
        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            raise Exception(f"Download failed: {str(e)}")
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total and total > 0:
                percentage = (downloaded / total) * 100
                # You can emit a signal here if needed
                pass