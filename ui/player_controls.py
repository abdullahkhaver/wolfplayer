from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QSlider, QLabel, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from config import Config

class PlayerControls(QWidget):
    playClicked = pyqtSignal()
    pauseClicked = pyqtSignal()
    stopClicked = pyqtSignal()
    nextClicked = pyqtSignal()
    prevClicked = pyqtSignal()
    volumeChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(float)  # 0.0 to 1.0
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Progress slider and time
        progress_layout = QHBoxLayout()
        
        self.current_time = QLabel("00:00")
        self.current_time.setFont(QFont("Segoe UI", 10))
        self.current_time.setFixedWidth(50)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        self.progress_slider.setEnabled(False)
        
        self.total_time = QLabel("00:00")
        self.total_time.setFont(QFont("Segoe UI", 10))
        self.total_time.setFixedWidth(50)
        self.total_time.setAlignment(Qt.AlignRight)
        
        progress_layout.addWidget(self.current_time)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time)
        
        layout.addLayout(progress_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)
        
        # Skip backward button
        self.skip_back_btn = QPushButton("⏪ 10s")
        self.skip_back_btn.setFixedSize(80, 40)
        self.skip_back_btn.clicked.connect(self._skip_backward)
        
        # Previous button
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(40, 40)
        self.prev_btn.clicked.connect(self.prevClicked.emit)
        
        # Play button
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(50, 50)
        self.play_btn.clicked.connect(self.playClicked.emit)
        
        # Pause button
        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setFixedSize(40, 40)
        self.pause_btn.clicked.connect(self.pauseClicked.emit)
        self.pause_btn.setEnabled(False)
        
        # Stop button
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.clicked.connect(self.stopClicked.emit)
        
        # Next button
        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(40, 40)
        self.next_btn.clicked.connect(self.nextClicked.emit)
        
        # Skip forward button
        self.skip_forward_btn = QPushButton("10s ⏩")
        self.skip_forward_btn.setFixedSize(80, 40)
        self.skip_forward_btn.clicked.connect(self._skip_forward)
        
        controls_layout.addWidget(self.skip_back_btn)
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addWidget(self.skip_forward_btn)
        
        layout.addLayout(controls_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        
        volume_icon = QLabel("🔈")
        volume_icon.setFont(QFont("Segoe UI", 14))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(Config.DEFAULT_VOLUME)
        self.volume_slider.valueChanged.connect(self.volumeChanged.emit)
        self.volume_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        
        layout.addLayout(volume_layout)
    
    def _skip_backward(self):
        """Skip backward 10 seconds"""
        self.positionChanged.emit(-10)  # Negative value indicates skip backward
    
    def _skip_forward(self):
        """Skip forward 10 seconds"""
        self.positionChanged.emit(-20)  # Special value for skip forward
    
    def _on_slider_moved(self, value):
        """Handle slider movement (for visual feedback)"""
        percentage = value / 1000.0
        # Update time label to show where we're seeking to
        if hasattr(self, '_total_seconds') and self._total_seconds > 0:
            seek_time = percentage * self._total_seconds
            self.current_time.setText(self._format_time(seek_time))
    
    def _on_slider_released(self):
        """Handle slider release (actual seeking)"""
        value = self.progress_slider.value()
        percentage = value / 1000.0
        self.positionChanged.emit(percentage)
    
    def update_progress(self, current_time, total_time, percentage):
        """Update progress display"""
        # Store total time for slider calculations
        self._total_seconds = total_time
        
        # Update time labels
        self.current_time.setText(self._format_time(current_time))
        self.total_time.setText(self._format_time(total_time))
        
        # Update slider without triggering signal
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(int(percentage * 1000))
        self.progress_slider.blockSignals(False)
        
        # Enable slider if we have a valid song
        self.progress_slider.setEnabled(total_time > 0)
    
    def _format_time(self, seconds):
        """Format seconds to MM:SS or HH:MM:SS"""
        if seconds < 0:
            return "00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def set_playing_state(self, is_playing):
        """Update button states based on playing state"""
        self.play_btn.setEnabled(not is_playing)
        self.pause_btn.setEnabled(is_playing)
        self.stop_btn.setEnabled(is_playing or self.progress_slider.value() > 0)