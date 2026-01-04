use clap::{Parser, Subcommand};
use std::path::PathBuf;

mod ytdlp;
mod db;

use db::*;

#[derive(Parser)]
#[command(name = "wolfplayer")]
#[command(about = "Modern music player with YouTube downloader")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Download YouTube video as MP3
    Download {
        /// YouTube URL
        url: String,

        /// Output directory (default: "music")
        #[arg(short, long, default_value = "music")]
        output: PathBuf,
    },

    /// List all tracks in database
    List,

    /// Play a track
    Play {
        /// Track ID or file path
        identifier: String,
    },

    /// Delete a track
    Delete {
        /// Track ID
        id: String,
    },

    /// Clear all tracks
    Clear,

    /// Get track info
    Info {
        /// Track ID
        id: String,
    },
}

fn main() -> Result<(), String> {
    let cli = Cli::parse();

    // Initialize database
    let conn = init_db().map_err(|e| format!("Database init failed: {}", e))?;

    match cli.command {
        Commands::Download { url, output } => {
            println!("Fetching metadata for: {}", url);

            // Create output directory if it doesn't exist
            std::fs::create_dir_all(&output)
                .map_err(|e| format!("Failed to create directory: {}", e))?;

            // Fetch metadata
            let meta = ytdlp::fetch_metadata(&url)
                .map_err(|e| format!("Failed to fetch metadata: {}", e))?;

            println!("Downloading: {}", meta.title);

            // Download MP3
            ytdlp::download_mp3(&url, output.to_str().unwrap())
                .map_err(|e| format!("Download failed: {}", e))?;

            // Build expected file path
            let file_path = format!("{}/{}.mp3", output.display(), meta.title);

            // Insert into database
            insert_track(&conn, &meta, &file_path)
                .map_err(|e| format!("Database insert failed: {}", e))?;

            println!("Successfully downloaded and added: {}", meta.title);
        }

        Commands::List => {
            let tracks = get_all_tracks(&conn)
                .map_err(|e| format!("Failed to read tracks: {}", e))?;

            if tracks.is_empty() {
                println!("No tracks in database.");
            } else {
                println!("Tracks in database:");
                println!("{:<15} {:<40} {:<30} {:<10}", "ID", "Title", "Uploader", "Duration");
                println!("{}", "-".repeat(95));

                for track in tracks {
                    let duration = match track.duration {
                        Some(d) => {
                            let minutes = d / 60;
                            let seconds = d % 60;
                            format!("{}:{:02}", minutes, seconds)
                        }
                        None => "--:--".to_string(),
                    };

                    println!(
                        "{:<15} {:<40} {:<30} {:<10}",
                        track.id.chars().take(12).collect::<String>(),
                        track.title.chars().take(37).collect::<String>() + "...",
                        track.uploader.as_deref().unwrap_or("Unknown")
                            .chars().take(27).collect::<String>() + "...",
                        duration
                    );
                }
            }
        }

        Commands::Play { identifier } => {
            println!("Playing track: {}", identifier);
            // TODO: Implement audio playback
        }

        Commands::Delete { id } => {
            println!("Deleting track: {}", id);
            // TODO: Implement deletion
        }

        Commands::Clear => {
            println!("Clearing all tracks...");
            // TODO: Implement clear
        }

        Commands::Info { id } => {
            println!("Getting info for track: {}", id);
            // TODO: Implement info
        }
    }

    Ok(())
}
