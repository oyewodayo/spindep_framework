#!/usr/bin/env bash
# ============================================================
# SPINDEP — One-Line Installer
# ============================================================
# Run this script to install the 'spin' command globally.
#
# Usage:
#   bash install.sh
#
# What it does:
#   1. Checks Python >= 3.9
#   2. Creates a virtual environment (optional)
#   3. Installs all dependencies
#   4. Registers 'spin' as a global terminal command
#   5. Verifies the install with 'spin info'
# ============================================================

set -e

BOLD="\033[1m"
GREEN="\033[92m"
BLUE="\033[94m"
YELLOW="\033[93m"
RED="\033[91m"
CYAN="\033[96m"
RESET="\033[0m"

ok()   { echo -e "  ${GREEN}✓${RESET}  $1"; }
info() { echo -e "  ${BLUE}●${RESET}  $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
err()  { echo -e "  ${RED}✗${RESET}  $1"; exit 1; }
head() { echo -e "\n${BOLD}${CYAN}$1${RESET}\n$(printf '─%.0s' {1..60})"; }

head "SPINDEP Installer"

# ── 1. Check Python version ──────────────────────────────────
info "Checking Python version..."
PY=$(python3 --version 2>&1 | awk '{print $2}')
MAJOR=$(echo $PY | cut -d. -f1)
MINOR=$(echo $PY | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
    err "Python 3.9+ required. Found: $PY"
fi
ok "Python $PY"

# ── 2. Locate setup.py ──────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "$SCRIPT_DIR/setup.py" ]; then
    err "setup.py not found in $SCRIPT_DIR. Run this script from the spindep_framework folder."
fi
info "Framework directory: $SCRIPT_DIR"

# ── 3. Optional: create venv ────────────────────────────────
echo ""
read -p "  Create a virtual environment? (recommended) [Y/n]: " USE_VENV
USE_VENV=${USE_VENV:-Y}

if [[ "$USE_VENV" =~ ^[Yy]$ ]]; then
    VENV_DIR="$SCRIPT_DIR/.venv"
    if [ ! -d "$VENV_DIR" ]; then
        info "Creating virtual environment at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
        ok "Virtual environment created"
    else
        ok "Using existing virtual environment at $VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    info "Virtual environment activated"
else
    warn "Installing into system Python (may require sudo on some systems)"
fi

# ── 4. Install ───────────────────────────────────────────────
echo ""
info "Installing SPINDEP and dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -e "$SCRIPT_DIR[full]"
ok "Installation complete"

# ── 5. Verify ────────────────────────────────────────────────
echo ""
info "Verifying installation..."
if command -v spin &>/dev/null; then
    ok "'spin' command is available"
    echo ""
    spin info
else
    warn "'spin' not found in PATH."
    echo ""
    echo -e "  Add this to your shell profile (${BOLD}~/.bashrc${RESET} or ${BOLD}~/.zshrc${RESET}):"
    if [[ "$USE_VENV" =~ ^[Yy]$ ]]; then
        echo -e "    ${CYAN}source $VENV_DIR/bin/activate${RESET}"
    else
        SPIN_PATH=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))")
        echo -e "    ${CYAN}export PATH=\"$SPIN_PATH:\$PATH\"${RESET}"
    fi
    echo ""
    echo -e "  Then reload your shell:  ${CYAN}source ~/.bashrc${RESET}"
fi

# ── 6. Usage reminder ────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}Quick start:${RESET}"
echo -e "  ${CYAN}spin run      --data ./datasets${RESET}              # Full analysis"
echo -e "  ${CYAN}spin test     matter.csv anti.csv --plot${RESET}     # Quick CPT test"
echo -e "  ${CYAN}spin validate --data ./datasets${RESET}              # Pre-flight check"
echo -e "  ${CYAN}spin import   --from /data --coupling gAgA ...${RESET}"
echo -e "  ${CYAN}spin config   myrun.yaml${RESET}                     # Config file run"
echo -e "  ${CYAN}spin --help${RESET}                                  # All commands"
echo ""
ok "SPINDEP is ready."