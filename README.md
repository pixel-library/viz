# Viz — Offline Terminal Media Player

```
██╗   ██╗██╗███████╗
██║   ██║██║╚══███╔╝
██║   ██║██║  ███╔╝ 
╚██╗ ██╔╝██║ ███╔╝  
 ╚████╔╝ ██║███████╗
  ╚═══╝  ╚═╝╚══════╝
```

**Viz** is an offline, highly stylized, terminal-based audio and video media player built with Python, Textual, and python-mpv.

---

## ⚡ Features

- **Hacker / VCR Terminal Aesthetic**: Responsive CSS-styled TUI with custom ASCII branding.
- **50/50 Navigation Box**: Split layout featuring discover categories and a dynamic file browser.
- **Real-Time Media Filtering**: Search bar filtering files as you type.
- **Non-Blocking MPV Media Engine**: Async architecture running audio decoding & native video window overlay without freezing the terminal UI.
- **Resilient Fallback Mode**: Gracefully handles missing `libmpv` with simulated playback previews.

---

## 🚀 Quick Start

### 1. Requirements & System Dependencies

- **Python**: 3.10 or higher
- **System Media Engine (`libmpv`)**:
  - **Ubuntu / Debian**: `sudo apt update && sudo apt install -y mpv libmpv-dev`
  - **Arch Linux**: `sudo pacman -S mpv`
  - **Fedora**: `sudo dnf install mpv mpv-devel`
  - **macOS**: `brew install mpv`

### 2. Installation

```bash
git clone https://github.com/pixel-library/viz.git
cd viz
pip install textual python-mpv
```

### 3. Usage

```bash
python main.py
```

---

## ⌨️ Hotkeys & Keybindings

| Key | Description |
| --- | --- |
| `Enter` | Trigger playback for selected file in browser |
| `Spacebar` | Toggle Play / Pause |
| `M` | Toggle Mute / Unmute |
| `Left Arrow` | Seek backward 10 seconds |
| `Right Arrow` | Seek forward 10 seconds |
| `Ctrl + T` | Toggle TV Mode info |
| `?` | Show Help Screen |
| `Q` | Quit Viz Media Player |

---

## 📄 License

MIT License
