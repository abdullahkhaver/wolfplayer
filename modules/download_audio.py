from yt_dlp import YoutubeDL
import os
from typing import Dict

MUSIC_DIR = "downloads"
os.makedirs(MUSIC_DIR, exist_ok=True)

def download_song(url: str) -> Dict[str, str]:
    """
    Downloads the song from YouTube and returns a dictionary with metadata.
    """
    try:
        options = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(MUSIC_DIR, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "writethumbnail": True,
            "embedthumbnail": True,
            "addmetadata": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "quiet": False,
            "no_warnings": True,
            "extract_flat": False,
        }

        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            
        # Get file extension
        ext = info.get('ext', 'mp3')
        if ext == 'webm':
            ext = 'mp3'
            
        title = info.get('title', 'Unknown').replace('/', '_').replace('\\', '_')
        filename = f"{title}.{ext}"
        
        return {
            "title": info.get("title", "Unknown"),
            "artist": info.get("uploader", "Unknown"),
            "duration": info.get("duration", 0),
            "filepath": os.path.join(MUSIC_DIR, filename),
            "thumbnail": os.path.join(MUSIC_DIR, f"{title}.jpg") if info.get('thumbnails') else None,
            "url": url,
            "channel": info.get('channel', 'Unknown'),
            "views": info.get('view_count', 0)
        }
        
    except Exception as e:
        raise Exception(f"Download failed: {str(e)}")