"""
Header Widget displaying the original VIZ ASCII logo and system capability status.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label

from viz.constants import __version__
from viz.terminal import TerminalCapabilities


VIZ_ASCII_LOGO = """██╗   ██╗██╗███████╗
██║   ██║██║╚══███╔╝
██║   ██║██║  ███╔╝ 
╚██╗ ██╔╝██║ ███╔╝  
 ╚████╔╝ ██║███████╗
  ╚═══╝  ╚═╝╚══════╝"""


class HeaderWidget(Widget):
    """Header Widget featuring the original VIZ ASCII logo and capability status."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.is_compact: bool = False

    def compose(self) -> ComposeResult:
        caps = []
        if TerminalCapabilities.has_display():
            caps.append("GPU")
        if TerminalCapabilities.has_kitty_graphics():
            caps.append("KITTY")
        if TerminalCapabilities.has_truecolor():
            caps.append("24BIT")
        cap_str = " | ".join(caps) if caps else "BASIC"

        if self.is_compact:
            header_text = (
                f"[bold orange]VIZ[/bold orange]  [bold #CC6600]OFFLINE MEDIA TERMINAL v{__version__}[/bold #CC6600]   "
                f"[bold #888888]|[/bold #888888]   [bold orange]{cap_str}[/bold orange]  ●  [bold green]READY[/bold green]"
            )
        else:
            header_text = (
                f"[bold orange]{VIZ_ASCII_LOGO}[/bold orange]\n"
                f"[bold #CC6600]OFFLINE MEDIA TERMINAL v{__version__}[/bold #CC6600]   "
                f"[bold #888888]|[/bold #888888]   [bold orange]{cap_str}[/bold orange]  ●  [bold green]READY[/bold green]"
            )
        yield Label(header_text, id="top-status-line")

    def set_compact_mode(self, compact: bool) -> None:
        if self.is_compact == compact:
            return
        self.is_compact = compact
        try:
            lbl = self.query_one("#top-status-line", Label)
            caps = []
            if TerminalCapabilities.has_display():
                caps.append("GPU")
            if TerminalCapabilities.has_kitty_graphics():
                caps.append("KITTY")
            if TerminalCapabilities.has_truecolor():
                caps.append("24BIT")
            cap_str = " | ".join(caps) if caps else "BASIC"

            if compact:
                header_text = (
                    f"[bold orange]VIZ[/bold orange]  [bold #CC6600]OFFLINE MEDIA TERMINAL v{__version__}[/bold #CC6600]   "
                    f"[bold #888888]|[/bold #888888]   [bold orange]{cap_str}[/bold orange]  ●  [bold green]READY[/bold green]"
                )
            else:
                header_text = (
                    f"[bold orange]{VIZ_ASCII_LOGO}[/bold orange]\n"
                    f"[bold #CC6600]OFFLINE MEDIA TERMINAL v{__version__}[/bold #CC6600]   "
                    f"[bold #888888]|[/bold #888888]   [bold orange]{cap_str}[/bold orange]  ●  [bold green]READY[/bold green]"
                )
            lbl.update(header_text)
        except Exception:
            pass

    def set_status(self, status_str: str) -> None:
        try:
            lbl = self.query_one("#top-status-line", Label)
            caps = []
            if TerminalCapabilities.has_display():
                caps.append("GPU")
            if TerminalCapabilities.has_kitty_graphics():
                caps.append("KITTY")
            if TerminalCapabilities.has_truecolor():
                caps.append("24BIT")
            cap_str = " | ".join(caps) if caps else "BASIC"

            if self.is_compact:
                header_text = (
                    f"[bold orange]VIZ[/bold orange]  [bold #CC6600]OFFLINE MEDIA TERMINAL v{__version__}[/bold #CC6600]   "
                    f"[bold #888888]|[/bold #888888]   [bold orange]{cap_str}[/bold orange]  ●  [bold green]{status_str.upper()}[/bold green]"
                )
            else:
                header_text = (
                    f"[bold orange]{VIZ_ASCII_LOGO}[/bold orange]\n"
                    f"[bold #CC6600]OFFLINE MEDIA TERMINAL v{__version__}[/bold #CC6600]   "
                    f"[bold #888888]|[/bold #888888]   [bold orange]{cap_str}[/bold orange]  ●  [bold green]{status_str.upper()}[/bold green]"
                )
            lbl.update(header_text)
        except Exception:
            pass
