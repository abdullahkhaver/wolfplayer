from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QMenu, QInputDialog, QMessageBox,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class PlaylistWidget(QWidget):
    songSelected = pyqtSignal(int)  # song_id
    addToPlaylist = pyqtSignal(int, int)  # playlist_id, song_id
    removeFromPlaylist = pyqtSignal(int, int)  # playlist_id, song_id
    playlistRenamed = pyqtSignal(int, str)  # playlist_id, new_name
    playlistDeleted = pyqtSignal(int)  # playlist_id
    
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.db = database
        self.current_playlist_id = None
        self.init_ui()
        self.load_playlists()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Playlist header
        header_layout = QHBoxLayout()
        
        self.playlist_label = QLabel("Playlists")
        self.playlist_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        
        self.new_playlist_btn = QPushButton("+ New")
        self.new_playlist_btn.clicked.connect(self.create_playlist)
        self.new_playlist_btn.setMaximumWidth(80)
        
        header_layout.addWidget(self.playlist_label)
        header_layout.addStretch()
        header_layout.addWidget(self.new_playlist_btn)
        
        layout.addLayout(header_layout)
        
        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.itemClicked.connect(self.on_playlist_selected)
        self.playlist_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self.show_playlist_context_menu)
        self.playlist_label.setStyleSheet("color: black;")

        layout.addWidget(self.playlist_list)
        
        # Current playlist songs
        self.songs_label = QLabel("")
        self.songs_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(self.songs_label)
        
        self.songs_list = QListWidget()
        self.songs_list.itemDoubleClicked.connect(self.on_song_double_clicked)
        self.songs_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.songs_list.customContextMenuRequested.connect(self.show_song_context_menu)
        self.songs_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.songs_label.setStyleSheet("color: black;")

        self.songs_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: black;
            }

            QListWidget::item:selected {
                background-color: #E0E0E0;
                color: black;
            }
        """)

        layout.addWidget(self.songs_list)
    
    def load_playlists(self):
        """Load all playlists from database"""
        self.playlist_list.clear()
        playlists = self.db.get_playlists()
        
        for playlist in playlists:
            item = QListWidgetItem(f"{playlist['name']} ({playlist['song_count']})")
            item.setData(Qt.UserRole, playlist['id'])
            self.playlist_list.addItem(item)
    
    def create_playlist(self):
        """Create a new playlist"""
        name, ok = QInputDialog.getText(
            self, "New Playlist", "Enter playlist name:"
        )
        
        if ok and name:
            playlist_id = self.db.create_playlist(name)
            if playlist_id:
                self.load_playlists()
    
    def on_playlist_selected(self, item):
        """Handle playlist selection"""
        playlist_id = item.data(Qt.UserRole)
        self.current_playlist_id = playlist_id
        self.load_playlist_songs(playlist_id)
        
        playlist = self.db.get_playlist(playlist_id)
        if playlist:
            self.songs_label.setText(f"{playlist['name']} - {playlist['song_count']} songs")
    
    def load_playlist_songs(self, playlist_id):
        """Load songs for selected playlist"""
        self.songs_list.clear()
        songs = self.db.get_playlist_songs(playlist_id)
        
        for song in songs:
            duration = self._format_duration(song['duration'])
            item_text = f"{song['title']} - {song['artist']} [{duration}]"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, song['id'])
            self.songs_list.addItem(item)
    
    def on_song_double_clicked(self, item):
        """Handle song double click"""
        song_id = item.data(Qt.UserRole)
        self.songSelected.emit(song_id)
    
    def show_playlist_context_menu(self, position):
        """Show context menu for playlists"""
        item = self.playlist_list.itemAt(position)
        if not item:
            return
        
        playlist_id = item.data(Qt.UserRole)
        
        menu = QMenu()
        
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(self.playlist_list.mapToGlobal(position))
        
        if action == rename_action:
            self.rename_playlist(playlist_id)
        elif action == delete_action:
            self.delete_playlist(playlist_id)
    
    def show_song_context_menu(self, position):
        """Show context menu for songs in playlist"""
        item = self.songs_list.itemAt(position)
        if not item or not self.current_playlist_id:
            return
        
        song_id = item.data(Qt.UserRole)
        
        menu = QMenu()
        
        play_action = menu.addAction("Play")
        menu.addSeparator()
        remove_action = menu.addAction("Remove from Playlist")
        
        action = menu.exec_(self.songs_list.mapToGlobal(position))
        
        if action == play_action:
            self.songSelected.emit(song_id)
        elif action == remove_action:
            self.remove_song_from_playlist(song_id)
    
    def rename_playlist(self, playlist_id):
        """Rename selected playlist"""
        playlist = self.db.get_playlist(playlist_id)
        if not playlist:
            return
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Playlist", "Enter new name:",
            text=playlist['name']
        )
        
        if ok and new_name and new_name != playlist['name']:
            self.db.update_playlist(playlist_id, name=new_name)
            self.playlistRenamed.emit(playlist_id, new_name)
            self.load_playlists()
            
            if self.current_playlist_id == playlist_id:
                self.songs_label.setText(f"{new_name} - {playlist['song_count']} songs")
    
    def delete_playlist(self, playlist_id):
        """Delete selected playlist"""
        reply = QMessageBox.question(
            self, "Delete Playlist",
            "Are you sure you want to delete this playlist?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_playlist(playlist_id)
            self.playlistDeleted.emit(playlist_id)
            self.load_playlists()
            self.songs_list.clear()
            self.songs_label.setText("")
            self.current_playlist_id = None
    
    def remove_song_from_playlist(self, song_id):
        """Remove song from current playlist"""
        if not self.current_playlist_id:
            return
        
        self.db.remove_song_from_playlist(self.current_playlist_id, song_id)
        self.load_playlist_songs(self.current_playlist_id)
        
        # Update playlist count
        playlist = self.db.get_playlist(self.current_playlist_id)
        if playlist:
            self.songs_label.setText(f"{playlist['name']} - {playlist['song_count']} songs")
    
    def _format_duration(self, seconds):
        """Format duration to MM:SS"""
        if not seconds:
            return "00:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"