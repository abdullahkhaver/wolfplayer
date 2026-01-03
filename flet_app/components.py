import flet as ft
from typing import Callable, Any

class ModernComponents:
    """Reusable modern UI components"""

    @staticmethod
    def create_card(content: ft.Control, padding: int = 16, elevation: int = 1) -> ft.Card:
        """Create a modern card"""
        return ft.Card(
            content=ft.Container(
                content=content,
                padding=padding,
                border_radius=12,
            ),
            elevation=elevation,
            surface_tint_color=ft.colors.TRANSPARENT,
        )

    @staticmethod
    def create_icon_button(
        icon: str,
        on_click: Callable,
        size: int = 40,
        bgcolor = None,
        icon_color = None,
        tooltip: str = None
    ) -> ft.IconButton:
        """Create a modern icon button"""
        return ft.IconButton(
            icon=icon,
            on_click=on_click,
            icon_size=size,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.all(8),
                bgcolor=bgcolor,
                overlay_color=ft.colors.with_opacity(0.1, ft.colors.PRIMARY),
            ),
            icon_color=icon_color,
            tooltip=tooltip,
        )

    @staticmethod
    def create_track_item(
        title: str,
        artist: str,
        duration: str,
        on_play: Callable = None,
        on_menu: Callable = None,
    ) -> ft.Container:
        """Create a track list item"""
        return ft.Container(
            content=ft.ListTile(
                title=ft.Text(title, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(f"{artist} • {duration}",
                               size=12, color=ft.colors.OUTLINE),
                leading=ft.Icon(ft.icons.MUSIC_NOTE),
                trailing=ModernComponents.create_icon_button(
                    icon=ft.icons.MORE_VERT,
                    on_click=on_menu,
                    size=24,
                ) if on_menu else None,
                on_click=on_play,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
            border_radius=8,
            on_hover=lambda e: ModernComponents.on_item_hover(e),
        )

    @staticmethod
    def on_item_hover(e):
        """Handle item hover effect"""
        e.control.bgcolor = ft.colors.SURFACE_CONTAINER if e.data == "true" else None
        e.control.update()

    @staticmethod
    def create_progress_dialog(title: str, message: str) -> ft.AlertDialog:
        """Create a progress dialog"""
        return ft.AlertDialog(
            modal=True,
            title=ft.Text(title),
            content=ft.Column([
                ft.ProgressRing(width=30, height=30),
                ft.Text(message, size=14),
            ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
