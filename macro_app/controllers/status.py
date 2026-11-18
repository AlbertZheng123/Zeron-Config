"""UI status indicator controller."""

from __future__ import annotations


class StatusController:
    """Keep the overlay and main-menu run indicators in sync."""

    def __init__(self, overlay_status_label, main_status_label) -> None:
        self.overlay_status_label = overlay_status_label
        self.main_status_label = main_status_label
        self.set_running(False)

    def set_running(self, running: bool) -> None:
        if running:
            overlay_text = "ACTIVE"
            overlay_style = (
                "color: #10B981; font-size: 15px; font-weight: 800; background: transparent;"
                "font-family: 'Space Mono', 'Menlo', monospace; border: none; padding: 0px; margin: 0px;"
            )
            main_text = "\u25cf  RUNNING"
            main_style = (
                "color: #22C55E; font-size: 15px; font-weight: 700; background: transparent;"
                "font-family: 'Space Mono', 'Menlo', monospace; letter-spacing: 0.5px;"
            )
        else:
            overlay_text = "IDLE"
            overlay_style = (
                "color: #10B981; font-size: 15px; font-weight: 800; background: transparent;"
                "font-family: 'Space Mono', 'Menlo', monospace; border: none; padding: 0px; margin: 0px;"
            )
            main_text = "\u25cb  IDLE"
            main_style = (
                "color: #666666; font-size: 15px; font-weight: 700; background: transparent;"
                "font-family: 'Space Mono', 'Menlo', monospace; letter-spacing: 0.5px;"
            )
        self.overlay_status_label.setText(overlay_text)
        self.overlay_status_label.setStyleSheet(overlay_style)
        self.main_status_label.setText(main_text)
        self.main_status_label.setStyleSheet(main_style)
