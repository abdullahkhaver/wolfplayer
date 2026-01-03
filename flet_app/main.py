import flet as ft
import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

# Constants
APP_NAME = "WolfPlayer"
APP_VERSION = "1.0.0"

class WolfPlayer:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_track = None
        self.tracks = []
        self.current_theme = "dark"
        self.rust_binary = self.find_rust_binary()

        # Setup
        self.setup_page()
        asyncio.create_task(self.load_tracks())

    def find_rust_binary(self) -> str:
        """Find the Rust binary path"""
        # Try multiple possible locations
        possible_paths = [
            "../target/release/wolfplayer",  # Relative from flet_app
            "./target/release/wolfplayer",   # Relative from project root
            "target/release/wolfplayer",     # Same directory
        ]

        current_dir = os.path.dirname(os.path.abspath(__file__))

        for path in possible_paths:
            full_path = os.path.join(current_dir, path)
            if os.path.exists(full_path):
                print(f"Found Rust binary at: {full_path}")
                return full_path

        # If not found, return the most likely path
        return os.path.join(current_dir, "../target/release/wolfplayer")

    def setup_page(self):
        """Setup page configuration"""
        self.page.title = f"{APP_NAME} v{APP_VERSION}"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 0
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_min_width = 800
        self.page.window_min_height = 600

        # Create UI
        self.create_app_bar()
        self.create_main_content()
        self.create_player_bar()

        # Layout
        self.page.add(
            ft.Column([
                self.app_bar,
                ft.Divider(height=1),
                self.main_content,
                ft.Divider(height=1),
                self.player_bar,
            ], spacing=0, expand=True)
        )

    def create_app_bar(self):
        """Create application bar"""
        self.theme_toggle = ft.IconButton(
            icon=ft.icons.DARK_MODE_OUTLINED,
            on_click=self.toggle_theme,
            tooltip="Toggle theme"
        )

        self.app_bar = ft.AppBar(
            title=ft.Text(APP_NAME, size=24, weight=ft.FontWeight.BOLD),
            center_title=False,
            bgcolor=ft.colors.SURFACE,
            actions=[
                ft.IconButton(
                    icon=ft.icons.REFRESH,
                    on_click=self.refresh_tracks,
                    tooltip="Refresh tracks"
                ),
                self.theme_toggle,
                ft.PopupMenuButton(
                    icon=ft.icons.MORE_VERT,
                    items=[
                        ft.PopupMenuItem(text="Settings"),
                        ft.PopupMenuItem(text="About"),
                    ]
                ),
            ],
        )

    def create_main_content(self):
        """Create main content area"""
        # YouTube download section
        self.youtube_url_field = ft.TextField(
            hint_text="Enter YouTube URL...",
            prefix_icon=ft.icons.LINK,
            expand=True,
            border_radius=8,
        )

        self.download_btn = ft.ElevatedButton(
            text="Download",
            icon=ft.icons.DOWNLOAD,
            on_click=self.download_youtube,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            )
        )

        self.download_progress = ft.ProgressBar(value=0, visible=False)
        self.download_status = ft.Text("", size=12)

        download_section = ft.Container(
            content=ft.Column([
                ft.Text("Download from YouTube", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.youtube_url_field,
                    self.download_btn,
                ]),
                self.download_progress,
                self.download_status,
            ], spacing=10),
            padding=20,
            bgcolor=ft.colors.SURFACE_CONTAINER,
            border_radius=12,
            margin=ft.margin.all(10),
        )

        # Tracks list
        self.search_field = ft.TextField(
            hint_text="Search tracks...",
            prefix_icon=ft.icons.SEARCH,
            on_change=self.search_tracks,
            border_radius=8,
            filled=True,
            expand=True,
        )

        self.tracks_list = ft.Column(spacing=1, scroll=ft.ScrollMode.AUTO, expand=True)

        tracks_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Your Music Library", size=20, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon=ft.icons.PLAYLIST_ADD,
                        on_click=self.create_playlist,
                        tooltip="Create playlist"
                    ),
                ]),
                ft.Row([self.search_field]),
                ft.Divider(),
                ft.Container(
                    content=self.tracks_list,
                    expand=True,
                ),
            ], spacing=15),
            padding=20,
            expand=True,
        )

        # Main layout
        self.main_content = ft.Row([
            ft.Container(
                content=ft.Column([
                    download_section,
                    tracks_section,
                ], spacing=20, expand=True),
                expand=2,
            ),
            ft.VerticalDivider(width=1),
            ft.Container(
                content=ft.Column([
                    ft.Text("Now Playing", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.icons.MUSIC_NOTE, size=80, color=ft.colors.PRIMARY),
                            ft.Text("No track selected", size=16, weight=ft.FontWeight.W_500),
                            ft.Text("Select a track to play", size=14, color=ft.colors.OUTLINE),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                        padding=40,
                        alignment=ft.alignment.center,
                        border_radius=12,
                        bgcolor=ft.colors.SURFACE_CONTAINER,
                    ),
                    ft.Text("Playlists", size=18, weight=ft.FontWeight.BOLD, margin=ft.margin.only(top=30)),
                    ft.Column([
                        ft.ListTile(
                            title=ft.Text("Favorites"),
                            leading=ft.Icon(ft.icons.FAVORITE, color=ft.colors.RED),
                            on_click=lambda e: print("Favorites clicked"),
                        ),
                        ft.ListTile(
                            title=ft.Text("Recently Added"),
                            leading=ft.Icon(ft.icons.HISTORY),
                            on_click=lambda e: print("Recently Added clicked"),
                        ),
                    ]),
                ], spacing=20),
                width=300,
                padding=20,
            ),
        ], expand=True)

    def create_player_bar(self):
        """Create player control bar"""
        self.current_track_title = ft.Text("No track selected", size=14, weight=ft.FontWeight.W_500)
        self.current_track_artist = ft.Text("", size=12, color=ft.colors.OUTLINE)

        self.play_button = ft.IconButton(
            icon=ft.icons.PLAY_ARROW,
            on_click=self.toggle_playback,
            icon_size=30,
        )

        self.prev_button = ft.IconButton(
            icon=ft.icons.SKIP_PREVIOUS,
            on_click=self.previous_track,
        )

        self.next_button = ft.IconButton(
            icon=ft.icons.SKIP_NEXT,
            on_click=self.next_track,
        )

        self.progress_bar = ft.Slider(
            min=0,
            max=100,
            value=0,
            on_change=self.seek_track,
            expand=True,
        )

        self.current_time = ft.Text("0:00", size=12)
        self.total_time = ft.Text("0:00", size=12)

        self.volume_slider = ft.Slider(
            min=0,
            max=100,
            value=80,
            divisions=10,
            on_change=self.change_volume,
            width=100,
        )

        self.player_bar = ft.Container(
            content=ft.Column([
                ft.Row([
                    self.current_time,
                    self.progress_bar,
                    self.total_time,
                ]),
                ft.Row([
                    ft.Column([
                        self.current_track_title,
                        self.current_track_artist,
                    ], spacing=0, tight=True),

                    ft.Row([
                        self.prev_button,
                        self.play_button,
                        self.next_button,
                    ]),

                    ft.Row([
                        ft.Icon(ft.icons.VOLUME_UP, size=20),
                        self.volume_slider,
                    ], spacing=5, tight=True),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            bgcolor=ft.colors.SURFACE_CONTAINER,
        )

    async def load_tracks(self):
        """Load tracks from Rust backend"""
        try:
            # Check if Rust binary exists
            if not os.path.exists(self.rust_binary):
                # Try to build it
                await self.build_rust_binary()

            print(f"Using Rust binary: {self.rust_binary}")

            result = subprocess.run(
                [self.rust_binary, "list"],
                capture_output=True,
                text=True,
                check=True
            )

            self.tracks = self.parse_tracks_output(result.stdout)
            await self.update_tracks_list()

        except FileNotFoundError:
            await self.show_snackbar("Rust binary not found. Please build it first.", ft.colors.ERROR)
        except subprocess.CalledProcessError as e:
            print(f"Error loading tracks: {e.stderr}")
            # Try running without tracks in database
            self.tracks = []
            await self.update_tracks_list()
            await self.show_snackbar("No tracks found in database", ft.colors.INFO)
        except Exception as e:
            print(f"Unexpected error: {e}")
            await self.show_snackbar("Failed to load tracks", ft.colors.ERROR)

    async def build_rust_binary(self):
        """Build the Rust binary if it doesn't exist"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        rust_dir = os.path.join(current_dir, "..")
        cargo_toml = os.path.join(rust_dir, "Cargo.toml")

        if os.path.exists(cargo_toml):
            print("Building Rust binary...")
            result = subprocess.run(
                ["cargo", "build", "--release"],
                cwd=rust_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.rust_binary = os.path.join(rust_dir, "target/release/wolfplayer")
                print(f"Built Rust binary at: {self.rust_binary}")
            else:
                print(f"Build failed: {result.stderr}")
                raise Exception("Failed to build Rust binary")
        else:
            raise FileNotFoundError("Cargo.toml not found")

    def parse_tracks_output(self, output: str) -> List[Dict]:
        """Parse Rust CLI output into track list"""
        tracks = []
        lines = output.strip().split('\n')

        # Simple parsing for now
        for line in lines:
            if line.strip() and not line.startswith('-') and "ID" not in line and "Tracks" not in line:
                # Try to split by common separators
                if ' - ' in line:
                    parts = line.split(' - ', 3)
                    if len(parts) >= 3:
                        track = {
                            'id': parts[0][:12] if len(parts[0]) > 12 else parts[0],
                            'title': parts[1],
                            'artist': parts[2],
                            'duration': parts[3] if len(parts) > 3 else "0:00",
                        }
                        tracks.append(track)
                else:
                    # Simple space-based parsing
                    parts = line.split(maxsplit=3)
                    if len(parts) >= 1:
                        track = {
                            'id': parts[0][:12] if len(parts[0]) > 12 else parts[0],
                            'title': parts[1] if len(parts) > 1 else "Unknown",
                            'artist': parts[2] if len(parts) > 2 else "Unknown",
                            'duration': parts[3] if len(parts) > 3 else "0:00",
                        }
                        tracks.append(track)

        return tracks

    async def update_tracks_list(self):
        """Update tracks list display"""
        self.tracks_list.controls.clear()

        for track in self.tracks:
            # Create track item
            item = ft.Container(
                content=ft.ListTile(
                    title=ft.Text(track.get('title', 'Unknown'),
                                 weight=ft.FontWeight.W_500,
                                 max_lines=1,
                                 overflow=ft.TextOverflow.ELLIPSIS),
                    subtitle=ft.Text(
                        f"{track.get('artist', 'Unknown')} • {track.get('duration', '0:00')}",
                        size=12,
                        color=ft.colors.OUTLINE,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    leading=ft.Icon(ft.icons.MUSIC_NOTE),
                    trailing=ft.PopupMenuButton(
                        icon=ft.icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(
                                text="Play",
                                icon=ft.icons.PLAY_ARROW,
                                on_click=lambda e, t=track: self.play_track(t)
                            ),
                            ft.PopupMenuItem(
                                text="Delete",
                                icon=ft.icons.DELETE,
                                on_click=lambda e, t=track: self.delete_track(t)
                            ),
                        ]
                    ),
                    on_click=lambda e, t=track: self.play_track(t),
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                border_radius=8,
                on_hover=lambda e: self.on_track_hover(e),
            )
            self.tracks_list.controls.append(item)

        if not self.tracks:
            self.tracks_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.MUSIC_OFF, size=64, color=ft.colors.OUTLINE),
                        ft.Text("No tracks yet", size=18, color=ft.colors.OUTLINE),
                        ft.Text("Download some music from YouTube to get started",
                               size=14, color=ft.colors.OUTLINE),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
                    padding=80,
                    alignment=ft.alignment.center,
                )
            )

        await self.page.update_async()

    def on_track_hover(self, e):
        """Handle track hover effect"""
        e.control.bgcolor = ft.colors.SURFACE_CONTAINER if e.data == "true" else None
        self.page.update()

    async def toggle_theme(self, e):
        """Toggle between dark and light theme"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.page.theme_mode = (
            ft.ThemeMode.LIGHT if self.current_theme == "light"
            else ft.ThemeMode.DARK
        )
        self.theme_toggle.icon = (
            ft.icons.LIGHT_MODE if self.current_theme == "dark"
            else ft.icons.DARK_MODE_OUTLINED
        )
        await self.page.update_async()

    async def download_youtube(self, e):
        """Download from YouTube using Rust backend"""
        url = self.youtube_url_field.value.strip()
        if not url:
            await self.show_snackbar("Please enter a YouTube URL", ft.colors.ERROR)
            return

        # Show progress
        self.download_btn.disabled = True
        self.download_progress.visible = True
        self.download_progress.value = None  # Indeterminate
        self.download_status.value = "Fetching metadata..."
        await self.page.update_async()

        try:
            # Check if binary exists
            if not os.path.exists(self.rust_binary):
                await self.build_rust_binary()

            # Run Rust download command
            output_dir = "music"
            os.makedirs(output_dir, exist_ok=True)

            print(f"Downloading: {url}")
            self.download_status.value = "Starting download..."

            process = subprocess.Popen(
                [self.rust_binary, "download", url, "--output", output_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Read output
            stdout, stderr = process.communicate()

            # Check result
            if process.returncode == 0:
                self.download_status.value = "Download completed!"
                await self.page.update_async()
                await asyncio.sleep(1)  # Show completion message briefly

                await self.show_snackbar("Download completed successfully!", ft.colors.GREEN)
                self.youtube_url_field.value = ""

                # Refresh tracks
                await self.load_tracks()
            else:
                error_msg = stderr if stderr else stdout if stdout else "Unknown error"
                print(f"Download error: {error_msg}")
                await self.show_snackbar(f"Download failed: {error_msg[:50]}...", ft.colors.ERROR)

        except FileNotFoundError:
            await self.show_snackbar("Rust binary not found. Please build it first.", ft.colors.ERROR)
        except Exception as ex:
            print(f"Error: {ex}")
            await self.show_snackbar(f"Error: {str(ex)}", ft.colors.ERROR)
        finally:
            # Reset UI
            self.download_btn.disabled = False
            self.download_progress.visible = False
            self.download_status.value = ""
            await self.page.update_async()

    async def play_track(self, track):
        """Play a track"""
        self.current_track = track
        self.current_track_title.value = track.get('title', 'Unknown')
        self.current_track_artist.value = track.get('artist', 'Unknown')
        self.play_button.icon = ft.icons.PAUSE

        # Update player UI
        duration = track.get('duration', '0:00')
        self.total_time.value = duration

        await self.page.update_async()

        # Show notification
        await self.show_snackbar(f"Now playing: {track.get('title', 'Unknown')}", ft.colors.PRIMARY)

    async def toggle_playback(self, e):
        """Toggle play/pause"""
        if self.current_track:
            if self.play_button.icon == ft.icons.PLAY_ARROW:
                self.play_button.icon = ft.icons.PAUSE
                await self.show_snackbar("Playing", ft.colors.PRIMARY)
            else:
                self.play_button.icon = ft.icons.PLAY_ARROW
                await self.show_snackbar("Paused", ft.colors.OUTLINE)
            await self.page.update_async()
        else:
            await self.show_snackbar("No track selected", ft.colors.WARNING)

    async def previous_track(self, e):
        """Play previous track"""
        if self.current_track and self.tracks:
            current_index = next(
                (i for i, t in enumerate(self.tracks)
                 if t.get('id') == self.current_track.get('id')),
                -1
            )
            if current_index > 0:
                await self.play_track(self.tracks[current_index - 1])

    async def next_track(self, e):
        """Play next track"""
        if self.current_track and self.tracks:
            current_index = next(
                (i for i, t in enumerate(self.tracks)
                 if t.get('id') == self.current_track.get('id')),
                -1
            )
            if current_index < len(self.tracks) - 1:
                await self.play_track(self.tracks[current_index + 1])

    async def seek_track(self, e):
        """Seek to position in track"""
        # Placeholder for seek functionality
        pass

    async def change_volume(self, e):
        """Change volume"""
        # Placeholder for volume control
        pass

    async def search_tracks(self, e):
        """Search tracks"""
        query = e.control.value.lower()
        if query:
            filtered = [t for t in self.tracks
                       if query in t.get('title', '').lower()
                       or query in t.get('artist', '').lower()]
            # For now, just highlight matching tracks
            pass

    async def refresh_tracks(self, e):
        """Refresh tracks list"""
        await self.load_tracks()
        await self.show_snackbar("Tracks refreshed", ft.colors.PRIMARY)

    async def create_playlist(self, e):
        """Create new playlist dialog"""
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        def save_playlist(e):
            name = name_field.value.strip()
            if name:
                # Save playlist logic here
                print(f"Creating playlist: {name}")
                close_dlg(e)

        name_field = ft.TextField(label="Playlist name", autofocus=True)
        desc_field = ft.TextField(label="Description (optional)", multiline=True)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Create Playlist"),
            content=ft.Column([
                name_field,
                desc_field,
            ], tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Create", on_click=save_playlist),
            ],
        )

        self.page.dialog = dlg
        dlg.open = True
        await self.page.update_async()

    async def delete_track(self, track):
        """Delete a track"""
        def close_dlg(e):
            dlg.open = False
            self.page.update()

        def confirm_delete(e):
            try:
                # Call Rust backend to delete track
                result = subprocess.run(
                    [self.rust_binary, "delete", track['id']],
                    check=True,
                    capture_output=True,
                    text=True
                )
                # Remove from local list
                self.tracks = [t for t in self.tracks if t['id'] != track['id']]
                self.update_tracks_list()
                self.show_snackbar("Track deleted", ft.colors.GREEN)
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if e.stderr else "Unknown error"
                self.show_snackbar(f"Failed to delete track: {error_msg[:50]}", ft.colors.ERROR)
            close_dlg(e)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Track"),
            content=ft.Text(f"Are you sure you want to delete '{track.get('title', 'Unknown')}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=close_dlg),
                ft.TextButton("Delete", on_click=confirm_delete),
            ],
        )

        self.page.dialog = dlg
        dlg.open = True
        await self.page.update_async()

    async def show_snackbar(self, message: str, color):
        """Show a snackbar notification"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color,
            show_close_icon=True,
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        await self.page.update_async()


def main(page: ft.Page):
    app = WolfPlayer(page)


# Run the app
if __name__ == "__main__":
    ft.app(target=main)
