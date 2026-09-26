# Viz — Premium Offline Terminal Media Player

```
██╗   ██╗██╗███████╗
██║   ██║██║╚══███╔╝
██║   ██║██║  ███╔╝ 
╚██╗ ██╔╝██║ ███╔╝  
 ╚████╔╝ ██║███████╗
  ╚═══╝  ╚═╝╚══════╝
```

**Viz** is an offline, highly stylized, commercial-grade terminal media player and pipeline engine built with Python, Textual, and `python-mpv`.

---

## 🌟 Commercial Features

- **Hacker & VCR Aesthetics**: Custom terminal typography, border styles, and 4 theme modes (**Cyberpunk Cyan**, **Retro Synthwave**, **Amber CRT**, and **Monokai Dark**).
- **Live ASCII Audio Equalizer**: Dynamic animated audio spectrum bars (`▅ █ ▇ ▅ ▄ ▅ █ ▇`) active during playback.
- **Visual Progress Bar Scrubber**: Real-time progress timeline `[██████████░░░░░░░░░░] 50%` with minute/second duration counter.
- **Interactive Category System**: Discover categories including *All Media*, *Movies & Videos*, *Music & Audio*, *Favorites ★*, *Recently Played*, and *Directory Browser*.
- **Dynamic Folder Explorer**: Navigate subdirectories and external drives directly within the TUI.
- **JSON Settings & State Persistence**: Volume levels, color themes, favorites, and recent history persist automatically across app sessions in `~/.config/viz/config.json`.
- **Non-Blocking Thread Engine**: Asynchronous playback management using worker threads (`@work(thread=True)`) ensuring zero terminal freezing during IO or playback operations.
- **Resilient Fallback Mode**: Gracefully handles missing `libmpv` with simulated playback previews and UI timers.

---

## ⚡ Quick Start & Installation

### 1. System Dependencies (libmpv)

- **Ubuntu / Debian**: `sudo apt update && sudo apt install -y mpv libmpv-dev`
- **Arch Linux**: `sudo pacman -S mpv`
- **Fedora**: `sudo dnf install mpv mpv-devel`
- **macOS**: `brew install mpv`

### 2. Package Installation

Install directly via `pip` locally or as an editable package:

```bash
git clone https://github.com/pixel-library/viz.git
cd viz
pip install .
```

After installation, run Viz from anywhere using the `viz` command:

```bash
viz --path ~/Videos
```

Or run standalone without installation:

```bash
python main.py
```

---

## 🔄 Updating & Uninstalling

### How to Update Viz to the Latest Version

If you installed Viz via git clone, pull the latest changes and upgrade the package:

```bash
cd viz
git pull origin main
pip install --upgrade .
```

Or update directly from GitHub:

```bash
pip install --upgrade git+https://github.com/pixel-library/viz.git
```

### How to Uninstall Viz

To remove Viz from your system:

```bash
pip uninstall viz-player
```

*(Optional)* To clear all saved configuration, themes, and favorites data:

```bash
rm -rf ~/.config/viz
```

---

## ⌨️ Complete Keybinding Reference

| Key | Description |
| --- | --- |
| `Enter` | Trigger playback / Open directory |
| `Spacebar` | Toggle Play / Pause |
| `M` | Toggle Mute / Unmute |
| `Up Arrow` / `Down Arrow` | Adjust Volume (+ / - 5%) |
| `Left Arrow` / `Right Arrow` | Seek relative (-10s / +10s) |
| `T` | Cycle Color Themes (*Cyberpunk*, *Synthwave*, *Amber*, *Monokai*) |
| `B` | Toggle Favorite / Bookmark (★) |
| `A` | Cycle Audio Stream |
| `S` | Cycle Subtitles |
| `Ctrl + T` | Toggle TV Mode info |
| `?` | Show Help Screen |
| `Q` | Quit Viz |

---

## 📦 Project Architecture

```
viz/
├── main.py             # Single-file entry point
├── pyproject.toml      # Package & distribution specification
├── LICENSE             # MIT License
├── README.md           # Documentation
└── viz/
    ├── __init__.py     # Package initialization
    ├── app.py          # Textual UI, themes, ASCII layout & handlers
    ├── cli.py          # Command-line argument parser
    ├── config.py       # Persistent JSON settings & favorites store
    └── engine.py       # Asynchronous MPV wrapper & fallback engine
```

---

## 📄 License

Distributed under the **MIT License**.
