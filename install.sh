#!/usr/bin/env bash
# ===============================================================================
# VIZ TERMINAL MEDIA PLAYER - AUTOMATED ONE-LINE INSTALLER
# ===============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/pixel-library/viz/main/install.sh | bash
# ===============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
cat << "EOF"
██╗   ██╗██╗███████╗
██║   ██║██║╚══███╔╝
██║   ██║██║  ███╔╝ 
╚██╗ ██╔╝██║ ███╔╝  
 ╚████╔╝ ██║███████╗
  ╚═══╝  ╚═╝╚══════╝
EOF
echo -e "${RESET}"
echo -e "${BOLD}Viz Terminal Media Player - Installer${RESET}"
echo -e "--------------------------------------------------"

# 1. Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[Error] Python 3 is required but not installed.${RESET}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${RESET}"

# 2. Install System Media Dependencies (libmpv)
echo -e "${CYAN} Checking system media dependencies (libmpv)...${RESET}"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v apt-get &> /dev/null; then
        echo -e "Detected Debian/Ubuntu system..."
        sudo -n apt-get update -qq 2>/dev/null && sudo -n apt-get install -y -qq mpv libmpv-dev python3-pip python3-venv 2>/dev/null || true
    elif command -v pacman &> /dev/null; then
        echo -e "Detected Arch Linux system..."
        sudo -n pacman -Sy --noconfirm mpv python-pip 2>/dev/null || true
    elif command -v dnf &> /dev/null; then
        echo -e "Detected Fedora system..."
        sudo -n dnf install -y mpv mpv-devel python3-pip 2>/dev/null || true
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &> /dev/null; then
        echo -e "Detected macOS system..."
        brew install mpv || true
    else
        echo -e "${YELLOW}[Notice] Homebrew not found. Please install mpv manually using 'brew install mpv'${RESET}"
    fi
fi

# 3. Install Viz Python Package
echo -e "${CYAN} Installing Viz Python Package via Pip...${RESET}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null || echo ".")" && pwd)"
if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    python3 -m pip install --upgrade --user "$SCRIPT_DIR"
else
    python3 -m pip install --upgrade --user git+https://github.com/pixel-library/viz.git
fi

# Determine active Python interpreter to ensure launcher points to the correct environment
PYTHON_EXEC=$(python3 -c "import sys; print(sys.executable)" 2>/dev/null || command -v python3 || echo "python3")

# 4. Create robust launcher wrapper to prevent environment/path conflicts
USER_BIN="$HOME/.local/bin"
mkdir -p "$USER_BIN"

cat << EOF > "$USER_BIN/viz"
#!/usr/bin/env bash
if "$PYTHON_EXEC" -c "import viz.cli" &>/dev/null; then
    exec "$PYTHON_EXEC" -m viz.cli "\$@"
elif python3 -c "import viz.cli" &>/dev/null; then
    exec python3 -m viz.cli "\$@"
elif /usr/bin/python3 -c "import viz.cli" &>/dev/null; then
    exec /usr/bin/python3 -m viz.cli "\$@"
else
    exec python3 -m viz.cli "\$@"
fi
EOF
chmod +x "$USER_BIN/viz"

# Copy to conda bin if active to override conda entrypoint
if [ -n "$CONDA_PREFIX" ] && [ -d "$CONDA_PREFIX/bin" ]; then
    cp "$USER_BIN/viz" "$CONDA_PREFIX/bin/viz" 2>/dev/null || true
fi

sudo -n ln -sf "$USER_BIN/viz" /usr/local/bin/viz 2>/dev/null || true

if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
    echo -e "${YELLOW} Adding $USER_BIN to your PATH...${RESET}"
    for PROFILE in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$PROFILE" ]; then
            if ! grep -q '.local/bin' "$PROFILE"; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$PROFILE"
                echo -e "${GREEN}✓ Added PATH export to $PROFILE${RESET}"
            fi
        fi
    done
    export PATH="$HOME/.local/bin:$PATH"
fi

echo -e ""
echo -e "${GREEN}${BOLD}=================================================="
echo -e " 🎉 Viz has been successfully installed!"
echo -e "==================================================${RESET}"
echo -e "If 'viz' command is not recognized in your current shell session, run:"
echo -e "  ${CYAN}${BOLD}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
echo -e ""
echo -e "To launch the player, type:"
echo -e "  ${CYAN}${BOLD}viz${RESET}"
echo -e ""
echo -e "To open a specific directory:"
echo -e "  ${CYAN}${BOLD}viz --path ~/Videos${RESET}"
echo -e ""
