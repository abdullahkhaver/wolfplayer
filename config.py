import os
from pathlib import Path

class Config:
    APP_NAME = "Kodu Music Player"
    VERSION = "1.0.0"
    
    # Paths
    BASE_DIR = Path(__file__).parent
    ASSETS_DIR = BASE_DIR / "assets"
    DOWNLOADS_DIR = BASE_DIR / "downloads"
    DATABASE_PATH = BASE_DIR / "music_library.db"
    
    # Create directories
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    
    # UI Settings
    PRIMARY_COLOR = "#2C3E50"
    SECONDARY_COLOR = "#34495E"
    ACCENT_COLOR = "#3498DB"
    TEXT_COLOR = "#ECF0F1"
    BORDER_COLOR = "#7F8C8D"
    
    # Player Settings
    DEFAULT_VOLUME = 70
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
    
    @classmethod
    def get_stylesheet(cls):
        return f"""
            QMainWindow {{
                background-color: {cls.PRIMARY_COLOR};
            }}
            QWidget {{
                # color: {cls.TEXT_COLOR};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QPushButton {{
                background-color: {cls.SECONDARY_COLOR};
                color: {cls.TEXT_COLOR};
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {cls.ACCENT_COLOR};
                border-color: {cls.ACCENT_COLOR};
            }}
            QPushButton:pressed {{
                background-color: #2980B9;
            }}
            QPushButton:disabled {{
                background-color: #465963;
                color: #95A5A6;
            }}
            QListWidget {{
                background-color: {cls.SECONDARY_COLOR};
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {cls.BORDER_COLOR};
            }}
            QListWidget::item:selected {{
                background-color: {cls.ACCENT_COLOR};
            }}
            QLineEdit, QTextEdit {{
                background-color: {cls.SECONDARY_COLOR};
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {cls.ACCENT_COLOR};
            }}
            QSlider::groove:horizontal {{
                height: 6px;
                background: {cls.SECONDARY_COLOR};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {cls.ACCENT_COLOR};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QProgressBar {{
                border: 1px solid {cls.BORDER_COLOR};
                border-radius: 4px;
                text-align: center;
                background-color: {cls.SECONDARY_COLOR};
            }}
            QProgressBar::chunk {{
                background-color: {cls.ACCENT_COLOR};
                border-radius: 3px;
            }}
            QMenuBar {{
                background-color: {cls.PRIMARY_COLOR};
                color: {cls.TEXT_COLOR};
            }}
            QMenuBar::item:selected {{
                background-color: {cls.ACCENT_COLOR};
            }}
            QMenu {{
                background-color: {cls.SECONDARY_COLOR};
                border: 1px solid {cls.BORDER_COLOR};
            }}
            QMenu::item:selected {{
                background-color: {cls.ACCENT_COLOR};
            }}
            QTabWidget::pane {{
                border: 1px solid {cls.BORDER_COLOR};
                background-color: {cls.PRIMARY_COLOR};
            }}
            QTabBar::tab {{
                background-color: {cls.SECONDARY_COLOR};
                color: {cls.TEXT_COLOR};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {cls.ACCENT_COLOR};
            }}
        """