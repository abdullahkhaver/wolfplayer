use tokio::process::Command;
use crate::models::VideoMetadata;

pub fn fetch_metadata(url: &str) -> Result<VideoMetadata, String> {
    // Create a small runtime for this single call
    let rt = tokio::runtime::Runtime::new().map_err(|e| e.to_string())?;

    rt.block_on(async {
        let output = Command::new("yt-dlp")
            .arg("-j")
            .arg("--skip-download")
            .arg(url)
            .output()
            .await
            .map_err(|e: std::io::Error| e.to_string())?;

        if !output.status.success() {
            return Err("yt-dlp failed".into());
        }

        let json = String::from_utf8(output.stdout)
            .map_err(|e| e.to_string())?;

        let metadata: VideoMetadata = serde_json::from_str(&json)
            .map_err(|e| e.to_string())?;

        Ok(metadata)
    })
}
