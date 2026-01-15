from yt_dlp import YoutubeDL

def download_audio(url:str):
    option = {
        "format" : "bestaudio/best", # downlaod in audio form 
        "outtmpl": "%(title)s.%(ext)s", # save using title name
        "noplaylist" : True, # downloads only a single video
        # write meta data and thumbnail to audio
        "writethumbnail" : True ,
        "embedthumbnail" : True,
        "addmetadata" : True,
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
        ytdl.download([url])

