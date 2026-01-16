from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton, QLabel,
    QMessageBox, QProgressBar, QMenuBar, QMenu, QAction, QFileDialog,
    QInputDialog, QSplitter, QHeaderView, QTableWidget, QTableWidgetItem,
    QAbstractItemView
)
from PyQt5.QtCore import QThread
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import os
from pathlib import Path

from config import Config
from database import Database
from modules.downloader import YouTubeDownloader
from modules.file_manager import FileManager
from modules.player import MusicPlayer
from ui.player_controls import PlayerControls
from ui.playlist_widget import PlaylistWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.db = Database()
        self.downloader = YouTubeDownloader()
        self.file_manager = FileManager(self.db)
        self.player = MusicPlayer(self.db)
        
        self.current_song_id = None
        self.is_playing = False
        
        self.init_ui()
        self.setup_connections()
        self.scan_library()
        
        # Timer for updating player progress
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_player_display)
        self.update_timer.start(100)  # Update every 100ms
    
    def init_ui(self):
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(Config.get_stylesheet())
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Library and Playlists
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Library section
        library_label = QLabel("Music Library")
        library_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        left_layout.addWidget(library_label)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs...")
        self.search_input.textChanged.connect(self.search_songs)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)
        
        # Songs list
        self.songs_table = QTableWidget()
        self.songs_table.setColumnCount(5)
        self.songs_table.setHorizontalHeaderLabels(["Title", "Artist", "Album", "Duration", "Plays"])
        self.songs_table.horizontalHeader().setStretchLastSection(True)
        self.songs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.songs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.songs_table.doubleClicked.connect(self.on_song_double_clicked)
        self.songs_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.songs_table.customContextMenuRequested.connect(self.show_song_context_menu)
        left_layout.addWidget(self.songs_table)
        
        # Download section
        download_label = QLabel("Download from YouTube")
        download_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        left_layout.addWidget(download_label)
        
        download_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube URL...")
        download_layout.addWidget(self.url_input)
        
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.download_song)
        download_layout.addWidget(self.download_btn)
        left_layout.addLayout(download_layout)
        
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        left_layout.addWidget(self.download_progress)
        
        left_layout.addStretch()
        splitter.addWidget(left_widget)
        
        # Right side - Playlists
        self.playlist_widget = PlaylistWidget(self.db)
        splitter.addWidget(self.playlist_widget)
        
        # Set splitter sizes
        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter)
        
        # Player controls at bottom
        self.player_controls = PlayerControls()
        main_layout.addWidget(self.player_controls)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        scan_action = QAction("Scan Library", self)
        scan_action.triggered.connect(self.scan_library)
        file_menu.addAction(scan_action)
        
        import_action = QAction("Import Music", self)
        import_action.triggered.connect(self.import_music)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("Edit")
        
        rename_action = QAction("Rename Song", self)
        rename_action.triggered.connect(self.rename_selected_song)
        edit_menu.addAction(rename_action)
        
        delete_action = QAction("Delete Song", self)
        delete_action.triggered.connect(self.delete_selected_song)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        organize_action = QAction("Organize Library", self)
        organize_action.triggered.connect(self.organize_library)
        edit_menu.addAction(organize_action)
        
        # Playback menu
        playback_menu = menu_bar.addMenu("Playback")
        
        play_action = QAction("Play/Pause", self)
        play_action.triggered.connect(self.toggle_playback)
        playback_menu.addAction(play_action)
        
        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop_playback)
        playback_menu.addAction(stop_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    

# In the setup_connections method, update these lines:
    def setup_connections(self):
        # Player controls
        self.player_controls.playClicked.connect(self.play_current_song)
        self.player_controls.pauseClicked.connect(self.pause_playback)
        self.player_controls.stopClicked.connect(self.stop_playback)
        self.player_controls.volumeChanged.connect(self.player.set_volume)
        self.player_controls.positionChanged.connect(self.on_position_changed)  # Changed!
        self.player_controls.nextClicked.connect(self.next_song)
        self.player_controls.prevClicked.connect(self.previous_song)
        
        # Playlist widget
        self.playlist_widget.songSelected.connect(self.play_song_by_id)
        self.playlist_widget.playlistRenamed.connect(self.on_playlist_renamed)
        self.playlist_widget.playlistDeleted.connect(self.on_playlist_deleted)

    def on_position_changed(self, value):
        """Handle position changes from slider or skip buttons"""
        if value < 0:
            # This is a skip request
            if value == -10:
                self.player.skip_backward(10)
            elif value == -20:
                self.player.skip_forward(10)
        else:
            # This is a slider seek request (0.0 to 1.0)
            if self.player.length > 0:
                position = value * self.player.length
                self.player.set_position(position)

    def next_song(self):
        """Play next song in current playlist or library"""
        if self.playlist_widget.current_playlist_id:
            # Get current playlist songs
            songs = self.db.get_playlist_songs(self.playlist_widget.current_playlist_id)
            if songs:
                current_index = next((i for i, s in enumerate(songs) 
                                    if s['id'] == self.current_song_id), -1)
                if current_index >= 0 and current_index < len(songs) - 1:
                    next_song_id = songs[current_index + 1]['id']
                    self.play_song_by_id(next_song_id)
        else:
            # Play next song in library
            songs = self.db.get_all_songs()
            if songs:
                current_index = next((i for i, s in enumerate(songs) 
                                    if s['id'] == self.current_song_id), -1)
                if current_index >= 0 and current_index < len(songs) - 1:
                    next_song_id = songs[current_index + 1]['id']
                    self.play_song_by_id(next_song_id)

    def previous_song(self):
        """Play previous song in current playlist or library"""
        if self.playlist_widget.current_playlist_id:
            # Get current playlist songs
            songs = self.db.get_playlist_songs(self.playlist_widget.current_playlist_id)
            if songs:
                current_index = next((i for i, s in enumerate(songs) 
                                    if s['id'] == self.current_song_id), -1)
                if current_index > 0:
                    prev_song_id = songs[current_index - 1]['id']
                    self.play_song_by_id(prev_song_id)
        else:
            # Play previous song in library
            songs = self.db.get_all_songs()
            if songs:
                current_index = next((i for i, s in enumerate(songs) 
                                    if s['id'] == self.current_song_id), -1)
                if current_index > 0:
                    prev_song_id = songs[current_index - 1]['id']
                    self.play_song_by_id(prev_song_id)

    def scan_library(self):
        """Scan downloads folder for music"""
        self.status_bar.showMessage("Scanning library...")
        
        try:
            music_files = self.file_manager.scan_library()
            self.load_songs()
            self.status_bar.showMessage(f"Library scanned: {len(music_files)} songs found")
        except Exception as e:
            self.status_bar.showMessage(f"Error scanning library: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to scan library: {str(e)}")
    
    def load_songs(self):
        """Load songs into table"""
        songs = self.db.get_all_songs()
        self.songs_table.setRowCount(len(songs))
        
        for row, song in enumerate(songs):
            # Title
            title_item = QTableWidgetItem(song['title'])
            title_item.setData(Qt.UserRole, song['id'])
            self.songs_table.setItem(row, 0, title_item)
            
            # Artist
            artist_item = QTableWidgetItem(song['artist'])
            self.songs_table.setItem(row, 1, artist_item)
            
            # Album
            album_item = QTableWidgetItem(song['album'] or '')
            self.songs_table.setItem(row, 2, album_item)
            
            # Duration
            duration = self.format_duration(song['duration'])
            duration_item = QTableWidgetItem(duration)
            self.songs_table.setItem(row, 3, duration_item)
            
            # Play count
            plays_item = QTableWidgetItem(str(song['play_count']))
            self.songs_table.setItem(row, 4, plays_item)
        
        self.songs_table.resizeColumnsToContents()
    
    def search_songs(self):
        """Search songs based on search input"""
        query = self.search_input.text()
        if not query:
            self.load_songs()
            return
        
        songs = self.db.search_songs(query)
        self.songs_table.setRowCount(len(songs))
        
        for row, song in enumerate(songs):
            # Title
            title_item = QTableWidgetItem(song['title'])
            title_item.setData(Qt.UserRole, song['id'])
            self.songs_table.setItem(row, 0, title_item)
            
            # Artist
            artist_item = QTableWidgetItem(song['artist'])
            self.songs_table.setItem(row, 1, artist_item)
            
            # Album
            album_item = QTableWidgetItem(song['album'] or '')
            self.songs_table.setItem(row, 2, album_item)
            
            # Duration
            duration = self.format_duration(song['duration'])
            duration_item = QTableWidgetItem(duration)
            self.songs_table.setItem(row, 3, duration_item)
            
            # Play count
            plays_item = QTableWidgetItem(str(song['play_count']))
            self.songs_table.setItem(row, 4, plays_item)
    
    def download_song(self):
        """Download song from YouTube"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a YouTube URL")
            return
        
        self.download_btn.setEnabled(False)
        self.url_input.clear()
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.status_bar.showMessage("Downloading...")
        
        # Start download in thread
        
        
        class DownloadThread(QThread):
            finished = pyqtSignal(dict)
            error = pyqtSignal(str)
            progress = pyqtSignal(int)
            
            def __init__(self, url, downloader):
                super().__init__()
                self.url = url
                self.downloader = downloader
            
            def run(self):
                try:
                    metadata = self.downloader.download_audio(self.url)
                    self.finished.emit(metadata)
                except Exception as e:
                    self.error.emit(str(e))
        
        self.download_thread = DownloadThread(url, self.downloader)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()
    
    def on_download_finished(self, metadata):
        """Handle download completion"""
        # Add to database
        song_id = self.db.add_song(
            title=metadata['title'],
            artist=metadata['artist'],
            filepath=metadata['filepath'],
            duration=metadata['duration'],
            filesize=metadata['filesize']
        )
        
        self.download_progress.setValue(100)
        self.download_btn.setEnabled(True)
        self.download_progress.setVisible(False)
        
        # Reload songs
        self.load_songs()
        
        self.status_bar.showMessage(f"Downloaded: {metadata['title']}")
        QMessageBox.information(self, "Success", f"Downloaded: {metadata['title']}")
    
    def on_download_error(self, error_msg):
        """Handle download error"""
        self.download_btn.setEnabled(True)
        self.download_progress.setVisible(False)
        
        self.status_bar.showMessage(f"Download failed: {error_msg}")
        QMessageBox.critical(self, "Error", f"Download failed: {error_msg}")
    
    def play_song_by_id(self, song_id):
        """Play song by ID"""
        self.current_song_id = song_id
        
        if self.player.load_song(song_id):
            self.player.play()
            self.is_playing = True
            self.player_controls.set_playing_state(True)
            
            # Update UI
            song = self.db.get_song(song_id)
            if song:
                self.status_bar.showMessage(f"Now playing: {song['title']} - {song['artist']}")
    
    def play_current_song(self):
        """Play currently selected song"""
        if not self.current_song_id:
            return
        
        if self.player.play():
            self.is_playing = True
            self.player_controls.set_playing_state(True)
    
    def pause_playback(self):
        """Pause playback"""
        if self.player.pause():
            self.is_playing = False
            self.player_controls.set_playing_state(False)
    
    def stop_playback(self):
        """Stop playback"""
        self.player.stop()
        self.is_playing = False
        self.player_controls.set_playing_state(False)
    
    def toggle_playback(self):
        """Toggle play/pause"""
        if self.is_playing:
            self.pause_playback()
        else:
            self.play_current_song()
    
    def update_player_display(self):
        """Update player controls display"""
        try:
            if self.player.is_playing:
                current_time = self.player.get_position()
                total_time = self.player.length
                
                if total_time > 0:
                    percentage = current_time / total_time
                    self.player_controls.update_progress(current_time, total_time, percentage)
                else:
                    # Show indefinite progress
                    self.player_controls.update_progress(current_time, 0, 0)
        except Exception as e:
            logger.error(f"Error updating player display: {e}")
    
    def on_song_double_clicked(self, index):
        """Handle song double click in table"""
        row = index.row()
        song_id = self.songs_table.item(row, 0).data(Qt.UserRole)
        self.play_song_by_id(song_id)
    
    def show_song_context_menu(self, position):
        """Show context menu for songs in table"""
        indexes = self.songs_table.selectedIndexes()
        if not indexes:
            return
        
        # Get unique song IDs from selected rows
        song_ids = set()
        for index in indexes:
            if index.column() == 0:  # Only get from title column
                song_id = self.songs_table.item(index.row(), 0).data(Qt.UserRole)
                if song_id:
                    song_ids.add(song_id)
        
        if not song_ids:
            return
        
        menu = QMenu()
        
        play_action = menu.addAction("Play")
        menu.addSeparator()
        
        # Get playlists for adding songs
        playlists = self.db.get_playlists()
        if playlists:
            add_to_menu = menu.addMenu("Add to Playlist")
            for playlist in playlists:
                playlist_action = add_to_menu.addAction(playlist['name'])
                playlist_action.setData(playlist['id'])
        
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(self.songs_table.mapToGlobal(position))
        
        if action == play_action:
            # Play first selected song
            self.play_song_by_id(next(iter(song_ids)))
        elif action == rename_action:
            self.rename_selected_song()
        elif action == delete_action:
            self.delete_selected_song()
        elif action and action.parent() == add_to_menu:
            playlist_id = action.data()
            for song_id in song_ids:
                self.db.add_song_to_playlist(playlist_id, song_id)
            
            # Refresh playlist if it's currently selected
            if self.playlist_widget.current_playlist_id == playlist_id:
                self.playlist_widget.load_playlist_songs(playlist_id)
    
    def rename_selected_song(self):
        """Rename selected song"""
        indexes = self.songs_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Warning", "Please select a song to rename")
            return
        
        # Get first selected song
        row = indexes[0].row()
        song_id = self.songs_table.item(row, 0).data(Qt.UserRole)
        song = self.db.get_song(song_id)
        
        if not song:
            return
        
        new_title, ok = QInputDialog.getText(
            self, "Rename Song", "Enter new title:",
            text=song['title']
        )
        
        if ok and new_title and new_title != song['title']:
            if self.file_manager.rename_song(song_id, new_title):
                self.load_songs()
                self.status_bar.showMessage(f"Renamed: {new_title}")
            else:
                QMessageBox.critical(self, "Error", "Failed to rename song")
    
    def delete_selected_song(self):
        """Delete selected song"""
        indexes = self.songs_table.selectedIndexes()
        if not indexes:
            QMessageBox.warning(self, "Warning", "Please select songs to delete")
            return
        
        reply = QMessageBox.question(
            self, "Delete Songs",
            f"Delete {len(set(index.row() for index in indexes))} selected songs?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            delete_file = QMessageBox.question(
                self, "Delete Files",
                "Also delete the audio files from disk?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if delete_file == QMessageBox.Cancel:
                return
            
            delete_from_disk = (delete_file == QMessageBox.Yes)
            
            # Get unique song IDs
            song_ids = set()
            for index in indexes:
                if index.column() == 0:
                    song_id = self.songs_table.item(index.row(), 0).data(Qt.UserRole)
                    if song_id:
                        song_ids.add(song_id)
            
            # Delete songs
            for song_id in song_ids:
                self.file_manager.delete_song(song_id, delete_from_disk)
            
            # Reload songs
            self.load_songs()
            self.status_bar.showMessage(f"Deleted {len(song_ids)} songs")
    
    def import_music(self):
        """Import music files from disk"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg)")
        
        if file_dialog.exec_():
            files = file_dialog.selectedFiles()
            
            # Copy files to downloads directory
            for file in files:
                try:
                    src_path = Path(file)
                    dst_path = Config.DOWNLOADS_DIR / src_path.name
                    
                    # Handle duplicate names
                    counter = 1
                    while dst_path.exists():
                        name = src_path.stem + f" ({counter})" + src_path.suffix
                        dst_path = Config.DOWNLOADS_DIR / name
                        counter += 1
                    
                    shutil.copy2(str(src_path), str(dst_path))
                    
                except Exception as e:
                    QMessageBox.warning(self, "Warning", f"Failed to import {file}: {str(e)}")
            
            # Rescan library
            self.scan_library()
            self.status_bar.showMessage(f"Imported {len(files)} files")
    
    def organize_library(self):
        """Organize library into folders"""
        reply = QMessageBox.question(
            self, "Organize Library",
            "Organize music library into Artist/Album folders?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.file_manager.organize_library("Artist/Album")
            self.scan_library()
            self.status_bar.showMessage("Library organized")
    
    def on_playlist_renamed(self, playlist_id, new_name):
        """Handle playlist renamed"""
        pass  # Already handled in playlist widget
    
    def on_playlist_deleted(self, playlist_id):
        """Handle playlist deleted"""
        pass  # Already handled in playlist widget
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        {Config.APP_NAME} v{Config.VERSION}
        
        A modern music player with playlist management
        and YouTube download capabilities.
        
        Features:
        • Play local music files
        • Download from YouTube
        • Create and manage playlists
        • Rename and organize music library
        • Search and filter songs
        
        © 2024 Kodu Desktop
        """
        
        QMessageBox.about(self, "About", about_text)
    
    def format_duration(self, seconds):
        """Format duration to MM:SS or HH:MM:SS"""
        if not seconds:
            return "00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def closeEvent(self, event):
        """Handle application close"""
        self.player.stop()
        event.accept()