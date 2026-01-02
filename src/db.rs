use rusqlite::{Connection, Result};
use crate::ytdlp::VideoMetadata;

pub fn init_db() -> Result<Connection> {
    let conn = Connection::open("wolfplayer.db")?;

    conn.execute(
        "
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            uploader TEXT,
            description TEXT,
            duration INTEGER,
            thumbnail TEXT,
            file_path TEXT NOT NULL,
            added_at INTEGER DEFAULT (strftime('%s','now'))
        )
        ",
        [],
    )?;

    Ok(conn)
}

pub fn insert_track(
    conn: &Connection,
    meta: &VideoMetadata,
    file_path: &str,
) -> Result<()> {
    conn.execute(
        "
        INSERT OR IGNORE INTO tracks
        (id, title, uploader, description, duration, thumbnail, file_path)
        VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)
        ",
        (
            meta.id.clone(),
            meta.title.clone(),
            meta.uploader.clone(),
            meta.description.clone(),
            meta.duration,
            meta.thumbnail.clone(),
            file_path,
        ),
    )?;

    Ok(())
}


#[derive(Debug)]
pub struct Track {
    pub id: String,
    pub title: String,
    pub uploader: Option<String>,
    pub duration: Option<u64>,
    pub file_path: String,
}

pub fn get_all_tracks(conn: &Connection) -> Result<Vec<Track>> {
    let mut stmt = conn.prepare(
        "
        SELECT id, title, uploader, duration, file_path
        FROM tracks
        ORDER BY added_at DESC
        ",
    )?;

    let tracks = stmt
        .query_map([], |row| {
            Ok(Track {
                id: row.get(0)?,
                title: row.get(1)?,
                uploader: row.get(2)?,
                duration: row.get::<_, Option<i64>>(3)?.map(|d| d as u64),
                file_path: row.get(4)?,
            })
        })?
        .collect::<Result<Vec<_>>>()?;

    Ok(tracks)
}

