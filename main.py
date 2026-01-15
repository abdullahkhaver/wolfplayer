from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QSlider, QStyle, QFileDialog,
    QMessageBox, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, QUrl, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon, QLinearGradient
import sys
from modules.download_audio import download_song
from modules.player import SimpleMusicPlayer as MusicPlayer
import os

class DownloadThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        
    def run(self):
        try:
            song_info = download_song(self.url)
            self.finished.emit(song_info)
        except Exception as e:
            self.error.emit(str(e))

class MusicPlayerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player = MusicPlayer()
        self.current_song = None
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        self.setWindowTitle("Modern Animated Music Player")
        self.setGeometry(100, 100, 800, 600)
        
        # Set dark theme - FIXED CSS (removed -webkit properties)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
            }
            QLabel {
                color: #ffffff;
                font-family: 'Segoe UI';
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4776E6, stop:1 #8E54E9);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 15px;
                font-weight: bold;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8E54E9, stop:1 #4776E6);
            }
            QPushButton:pressed {
                background: #FF416C;
            }
            QPushButton:disabled {
                background: #555555;
                color: #888888;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #8E54E9;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
                font-family: 'Segoe UI';
            }
            QLineEdit:focus {
                border: 2px solid #FF416C;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #404040;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FF416C, stop:1 #FF4B2B);
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }
            QProgressBar {
                border: 2px solid #8E54E9;
                border-radius: 8px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF416C, stop:1 #FF4B2B);
                border-radius: 6px;
            }
            QFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 15px;
                padding: 10px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Header with gradient text effect
        header = QLabel("🎵 Modern Music Player")
        header.setFont(QFont("Segoe UI", 28, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        # Create gradient effect using stylesheet
        header.setStyleSheet("""
            QLabel {
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF416C, stop:1 #FF4B2B);
            }
        """)
        main_layout.addWidget(header)
        
        # Download section
        download_frame = QFrame()
        download_layout = QVBoxLayout(download_frame)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("🔗 Paste YouTube URL here...")
        self.url_input.setMinimumHeight(45)
        download_layout.addWidget(self.url_input)
        
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("⬇ Download & Play")
        self.download_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        button_layout.addWidget(self.download_btn)
        
        self.browse_btn = QPushButton("📁 Browse Local File")
        self.browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        button_layout.addWidget(self.browse_btn)
        
        download_layout.addLayout(button_layout)
        main_layout.addWidget(download_frame)
        
        # Song info display with album art placeholder
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        
        # Album art placeholder
        album_frame = QFrame()
        album_frame.setMinimumHeight(150)
        album_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8E54E9, stop:1 #4776E6);
                border-radius: 10px;
            }
        """)
        info_layout.addWidget(album_frame)
        
        self.song_title = QLabel("No song playing")
        self.song_title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.song_title.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.song_title)
        
        self.song_artist = QLabel("—")
        self.song_artist.setFont(QFont("Segoe UI", 14))
        self.song_artist.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.song_artist)
        
        # Download progress
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        info_layout.addWidget(self.download_progress)
        
        main_layout.addWidget(info_frame)
        
        # Playback controls section
        controls_frame = QFrame()
        controls_layout = QVBoxLayout(controls_frame)
        
        # Progress slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        controls_layout.addWidget(self.progress_slider)
        
        # Time labels
        time_layout = QHBoxLayout()
        self.current_time = QLabel("00:00")
        self.total_time = QLabel("00:00")
        self.total_time.setAlignment(Qt.AlignRight)
        time_layout.addWidget(self.current_time)
        time_layout.addWidget(self.total_time)
        controls_layout.addLayout(time_layout)
        
        # Control buttons
        button_row = QHBoxLayout()
        button_row.setAlignment(Qt.AlignCenter)
        
        # Create styled buttons with icons
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(50, 50)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                border-radius: 25px;
            }
        """)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(70, 70)
        self.play_btn.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                border-radius: 35px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF416C, stop:1 #FF4B2B);
            }
        """)
        
        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setFixedSize(50, 50)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                border-radius: 25px;
            }
        """)
        self.pause_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(50, 50)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                border-radius: 25px;
            }
        """)
        self.stop_btn.setEnabled(False)
        
        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(50, 50)
        self.next_btn.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                border-radius: 25px;
            }
        """)
        
        button_row.addWidget(self.prev_btn)
        button_row.addWidget(self.play_btn)
        button_row.addWidget(self.pause_btn)
        button_row.addWidget(self.stop_btn)
        button_row.addWidget(self.next_btn)
        
        controls_layout.addLayout(button_row)
        main_layout.addWidget(controls_frame)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_label = QLabel("🔈")
        volume_label.setFont(QFont("Segoe UI", 16))
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        volume_layout.addWidget(self.volume_slider)
        
        volume_label2 = QLabel("🔊")
        volume_label2.setFont(QFont("Segoe UI", 16))
        volume_layout.addWidget(volume_label2)
        main_layout.addLayout(volume_layout)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        self.status_bar.setStyleSheet("""
            QStatusBar {
                color: white;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.3);
            }
        """)
        
        # Timer for updating progress
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(100)  # Update every 100ms for smoother progress
        
    def setup_connections(self):
        self.download_btn.clicked.connect(self.download_and_play)
        self.browse_btn.clicked.connect(self.browse_local_file)
        self.play_btn.clicked.connect(self.play)
        self.pause_btn.clicked.connect(self.pause)
        self.stop_btn.clicked.connect(self.stop)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.progress_slider.sliderMoved.connect(self.seek_position)
        
    def download_and_play(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a YouTube URL!")
            return
        
        # Reset UI
        self.status_bar.showMessage("Downloading...")
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading...")
        
        # Simulate progress animation
        self.progress_timer = QTimer()
        self.progress_value = 0
        
        def update_progress_bar():
            self.progress_value += 1
            self.download_progress.setValue(min(self.progress_value, 90))  # Leave 10% for processing
            if self.progress_value >= 100:
                self.progress_timer.stop()
        
        self.progress_timer.timeout.connect(update_progress_bar)
        self.progress_timer.start(30)  # Update every 30ms
        
        # Start download in separate thread
        self.download_thread = DownloadThread(url)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()
    
    def on_download_finished(self, song_info):
        # Stop progress timer
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        
        self.download_progress.setValue(100)
        self.load_song(song_info)
        
        # Reset button
        self.download_btn.setEnabled(True)
        self.download_btn.setText("⬇ Download & Play")
        self.download_progress.setVisible(False)
        
        self.status_bar.showMessage("Download complete!")
        QMessageBox.information(self, "Success", "Download completed successfully!")
    
    def on_download_error(self, error_msg):
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
        
        self.download_progress.setVisible(False)
        self.download_btn.setEnabled(True)
        self.download_btn.setText("⬇ Download & Play")
        
        QMessageBox.critical(self, "Error", f"Download failed:\n{error_msg}")
        self.status_bar.showMessage("Download failed")
    
    def browse_local_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Music File", "", 
            "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg);;All Files (*)"
        )
        
        if file_path:
            song_info = {
                "title": os.path.basename(file_path).rsplit('.', 1)[0],
                "artist": "Local File",
                "duration": 0,
                "filepath": file_path,
                "thumbnail": None
            }
            self.load_song(song_info)
            self.status_bar.showMessage(f"Loaded: {os.path.basename(file_path)}")
    
    def load_song(self, song_info):
        self.current_song = song_info
        self.song_title.setText(f"🎶 {song_info['title'][:50]}")
        self.song_artist.setText(f"👤 {song_info['artist']}")
        
        if self.player.load_song(song_info['filepath']):
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
            # Update total time
            duration = song_info.get('duration', 0)
            if duration > 0:
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                self.total_time.setText(f"{minutes:02d}:{seconds:02d}")
    
    def play(self):
        if self.player.play():
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.status_bar.showMessage("Playing")
    
    def pause(self):
        if self.player.pause():
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.status_bar.showMessage("Paused")
    
    def stop(self):
        self.player.stop()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.current_time.setText("00:00")
        self.progress_slider.setValue(0)
        self.status_bar.showMessage("Stopped")
    
    def set_volume(self, value):
        self.player.set_volume(value)
        self.status_bar.showMessage(f"Volume: {value}%")
    
    def seek_position(self, value):
        if self.player.is_playing:  # Fixed: property, not method
            self.player.set_position(value / 100.0)
    
    def update_progress(self):
        if self.player.is_playing:  # Fixed: property, not method
            pos = self.player.get_position()
            length = self.player.get_length()
            
            if pos >= 0 and length > 0:
                # Update slider
                self.progress_slider.setValue(int((pos / length) * 100))
                
                # Update time labels
                current_min = int(pos // 60)
                current_sec = int(pos % 60)
                total_min = int(length // 60)
                total_sec = int(length % 60)
                
                self.current_time.setText(f"{current_min:02d}:{current_sec:02d}")
                self.total_time.setText(f"{total_min:02d}:{total_sec:02d}")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show window
    player = MusicPlayerGUI()
    player.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()