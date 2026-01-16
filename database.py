import sqlite3
from pathlib import Path
from datetime import datetime
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Songs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    artist TEXT DEFAULT 'Unknown',
                    album TEXT DEFAULT '',
                    duration INTEGER DEFAULT 0,
                    filepath TEXT UNIQUE NOT NULL,
                    filesize INTEGER DEFAULT 0,
                    bitrate INTEGER DEFAULT 0,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_played TIMESTAMP,
                    play_count INTEGER DEFAULT 0
                )
            ''')
            
            # Playlists table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    song_count INTEGER DEFAULT 0
                )
            ''')
            
            # Playlist songs junction table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playlist_songs (
                    playlist_id INTEGER,
                    song_id INTEGER,
                    position INTEGER,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (playlist_id, song_id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_songs_title ON songs(title)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(artist)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_playlist_songs ON playlist_songs(playlist_id, position)')
            
            conn.commit()
    
    # Song operations
    def add_song(self, title, artist, filepath, duration=0, album='', filesize=0, bitrate=0):
        """Add a song to database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO songs 
                (title, artist, album, duration, filepath, filesize, bitrate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, artist, album, duration, str(filepath), filesize, bitrate))
            conn.commit()
            return cursor.lastrowid
    
    def get_song(self, song_id):
        """Get song by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM songs WHERE id = ?', (song_id,))
            return cursor.fetchone()
    
    def get_all_songs(self):
        """Get all songs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM songs ORDER BY title')
            return cursor.fetchall()
    
    def search_songs(self, query):
        """Search songs by title or artist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f'%{query}%'
            cursor.execute('''
                SELECT * FROM songs 
                WHERE title LIKE ? OR artist LIKE ? 
                ORDER BY title
            ''', (search_term, search_term))
            return cursor.fetchall()
    
    def update_song(self, song_id, **kwargs):
        """Update song information"""
        if not kwargs:
            return
        
        set_clause = ', '.join([f'{k} = ?' for k in kwargs.keys()])
        values = list(kwargs.values())
        values.append(song_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE songs SET {set_clause} WHERE id = ?
            ''', values)
            conn.commit()
    
    def delete_song(self, song_id):
        """Delete song from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM songs WHERE id = ?', (song_id,))
            conn.commit()
    
    def increment_play_count(self, song_id):
        """Increment play count and update last played"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE songs 
                SET play_count = play_count + 1, 
                    last_played = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (song_id,))
            conn.commit()
    
    # Playlist operations
    def create_playlist(self, name, description=''):
        """Create a new playlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO playlists (name, description)
                VALUES (?, ?)
            ''', (name, description))
            conn.commit()
            return cursor.lastrowid
    
    def get_playlists(self):
        """Get all playlists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM playlists ORDER BY name')
            return cursor.fetchall()
    
    def get_playlist(self, playlist_id):
        """Get playlist by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM playlists WHERE id = ?', (playlist_id,))
            return cursor.fetchone()
    
    def update_playlist(self, playlist_id, name=None, description=None):
        """Update playlist information"""
        updates = []
        values = []
        
        if name:
            updates.append('name = ?')
            values.append(name)
        if description is not None:
            updates.append('description = ?')
            values.append(description)
        
        if not updates:
            return
        
        values.append(playlist_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE playlists 
                SET {', '.join(updates)} 
                WHERE id = ?
            ''', values)
            conn.commit()
    
    def delete_playlist(self, playlist_id):
        """Delete playlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM playlists WHERE id = ?', (playlist_id,))
            conn.commit()
    
    def add_song_to_playlist(self, playlist_id, song_id):
        """Add song to playlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current max position
            cursor.execute('''
                SELECT MAX(position) FROM playlist_songs 
                WHERE playlist_id = ?
            ''', (playlist_id,))
            result = cursor.fetchone()
            position = (result[0] or 0) + 1
            
            # Add song
            cursor.execute('''
                INSERT OR IGNORE INTO playlist_songs (playlist_id, song_id, position)
                VALUES (?, ?, ?)
            ''', (playlist_id, song_id, position))
            
            # Update song count
            cursor.execute('''
                UPDATE playlists 
                SET song_count = (
                    SELECT COUNT(*) FROM playlist_songs 
                    WHERE playlist_id = ?
                )
                WHERE id = ?
            ''', (playlist_id, playlist_id))
            
            conn.commit()
    
    def remove_song_from_playlist(self, playlist_id, song_id):
        """Remove song from playlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM playlist_songs 
                WHERE playlist_id = ? AND song_id = ?
            ''', (playlist_id, song_id))
            
            # Update positions
            cursor.execute('''
                UPDATE playlist_songs 
                SET position = position - 1 
                WHERE playlist_id = ? AND position > (
                    SELECT position FROM playlist_songs 
                    WHERE playlist_id = ? AND song_id = ?
                )
            ''', (playlist_id, playlist_id, song_id))
            
            # Update song count
            cursor.execute('''
                UPDATE playlists 
                SET song_count = (
                    SELECT COUNT(*) FROM playlist_songs 
                    WHERE playlist_id = ?
                )
                WHERE id = ?
            ''', (playlist_id, playlist_id))
            
            conn.commit()
    
    def get_playlist_songs(self, playlist_id):
        """Get all songs in a playlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, ps.position 
                FROM songs s
                JOIN playlist_songs ps ON s.id = ps.song_id
                WHERE ps.playlist_id = ?
                ORDER BY ps.position
            ''', (playlist_id,))
            return cursor.fetchall()
    
    def reorder_playlist_song(self, playlist_id, song_id, new_position):
        """Reorder song in playlist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current position
            cursor.execute('''
                SELECT position FROM playlist_songs 
                WHERE playlist_id = ? AND song_id = ?
            ''', (playlist_id, song_id))
            result = cursor.fetchone()
            
            if not result:
                return
            
            old_position = result[0]
            
            if old_position < new_position:
                # Move down
                cursor.execute('''
                    UPDATE playlist_songs 
                    SET position = position - 1 
                    WHERE playlist_id = ? 
                    AND position > ? 
                    AND position <= ?
                ''', (playlist_id, old_position, new_position))
            else:
                # Move up
                cursor.execute('''
                    UPDATE playlist_songs 
                    SET position = position + 1 
                    WHERE playlist_id = ? 
                    AND position >= ? 
                    AND position < ?
                ''', (playlist_id, new_position, old_position))
            
            # Update moved song
            cursor.execute('''
                UPDATE playlist_songs 
                SET position = ? 
                WHERE playlist_id = ? AND song_id = ?
            ''', (new_position, playlist_id, song_id))
            
            conn.commit()