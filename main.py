from yt_dlp import YoutubeDL

def download_audio(url:str):
    option = {
        "format" : "bestaudio/best", # downlaod in audio form 
        "outtmpl": "%(artist)s - %(title)s.%(ext)s", # save using title name + artist
        "noplaylist" : True, # downloads only a single video
        # write meta data and thumbnail to audio
        "writethumbnail" : True 
        "embedthumbnail" : True
        "addmetadata" : True
        # convert to mp3 format using ffmpeg
        "postprocessors": [
            {
                "key" : "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            },
            {
                "key" : "FFmpegMetaData"
            },
            {
                "key" : "EmbedThumbnail"
            }
        ],
        "quiet": False
    }

    with YoutubeDL(option) as ytdl : 
        yt.download([url])

