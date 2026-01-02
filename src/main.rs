mod ytdlp;
mod db;

use ytdlp::*;
use db::*;

fn main() {
    let url = "https://youtu.be/bWJCIt9LgLY";

    // 1. Init DB (auto-creates everything)
    let conn = init_db().expect("db init failed");

    // 2. Fetch metadata
    let meta = fetch_metadata(url).expect("metadata failed");

    println!("Downloaded: {}", meta.title);

    // 3. Download MP3
    let music_dir = "music";
    std::fs::create_dir_all(music_dir).unwrap();

    download_mp3(url, music_dir).expect("download failed");

    // 4. Build expected file path
    let file_path = format!("{}/{}.mp3", music_dir, meta.title);

    // 5. Insert into DB (automatic, no duplicates)
    insert_track(&conn, &meta, &file_path).expect("db insert failed");

    // 6. Read everything back
    let tracks = get_all_tracks(&conn).expect("db read failed");

    println!("Tracks in database:");
    for t in tracks {
        println!("{:?}", t);
    }
}
