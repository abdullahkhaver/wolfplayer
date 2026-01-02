use serde::Deserialize;
use std::process::Command;

#[derive(Debug, Deserialize)]
pub struct VideoMetadata {
    pub id: String,
    pub title: String,
    pub uploader: Option<String>,
    pub description: Option<String>,
    pub duration: Option<u64>,
    pub thumbnail: Option<String>,
    pub webpage_url: String,
}

pub fn fetch_metadata(url: &str) -> Result<VideoMetadata, String> {
    let output = Command::new("yt-dlp")
        .args([
            "--dump-json",
            "--no-playlist",
            url,
        ])
        .output()
        .map_err(|e| format!("failed to run yt-dlp: {e}"))?;

    if !output.status.success() {
        return Err(String::from_utf8_lossy(&output.stderr).to_string());
    }

    let stdout = String::from_utf8(output.stdout)
        .map_err(|e| format!("invalid utf8: {e}"))?;

    serde_json::from_str(&stdout)
        .map_err(|e| format!("json parse error: {e}"))
}
pub fn download_mp3(url: &str, output_dir: &str) -> Result<(), String> {
    let status = Command::new("yt-dlp")
        .args([
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
            "--embed-metadata",
            "--embed-thumbnail",
            "-o", &format!("{output_dir}/%(title)s.%(ext)s"),
            url,
        ])
        .status()
        .map_err(|e| format!("failed to start yt-dlp: {e}"))?;

    if !status.success() {
        return Err("yt-dlp download failed".into());
    }

    Ok(())
}
