use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct VideoMetadata {
    pub id: String,
    pub title: String,
    pub duration: Option<u64>,
    pub uploader: Option<String>,
    pub thumbnail: Option<String>,
}
