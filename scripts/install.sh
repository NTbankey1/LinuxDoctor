#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────
# Linux Doctor — One-liner Installer
# ──────────────────────────────────────────────────────────
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/NTbankey1/linux-doctor/main/scripts/install.sh | bash
# ──────────────────────────────────────────────────────────

REPO="NTbankey1/linux-doctor"
BRANCH="main"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.linux-doctor}"
PYTHON="${PYTHON:-python3}"

# ── Colors ────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

info()  { echo -e "${CYAN}::${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
err()   { echo -e "${RED}✗${NC} $1"; exit 1; }

# ── Check prerequisites ───────────────────────────────────
info "Checking prerequisites..."

command -v git  >/dev/null 2>&1 || err "git is required. Install it first."
command -v curl >/dev/null 2>&1 || err "curl is required. Install it first."

# Check Python version
PYTHON_BIN=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
        VER=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
        if [ -n "$VER" ] && [ "$(echo "$VER" | cut -d. -f1)" -ge 3 ] && [ "$(echo "$VER" | cut -d. -f2)" -ge 10 ]; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

[ -z "$PYTHON_BIN" ] && err "Python 3.10+ is required. Install it from https://www.python.org/downloads/"
ok "Python: $("$PYTHON_BIN" --version 2>&1)"

# Check uv
if command -v uv >/dev/null 2>&1; then
    UV_BIN="uv"
    ok "uv: $(uv --version 2>&1)"
else
    warn "uv not found — installing via pip..."
    "$PYTHON_BIN" -m pip install --user uv 2>/dev/null || {
        info "Trying official uv installer..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
        command -v uv >/dev/null 2>&1 || err "uv installation failed. Install manually: https://docs.astral.sh/uv/#installation"
    fi
    UV_BIN="uv"
    ok "uv installed"
fi

# ── Clone / update repository ─────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    info "Updating existing installation at $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git fetch origin "$BRANCH"
    git reset --hard "origin/$BRANCH"
    ok "Repository updated"
else
    info "Cloning linux-doctor to $INSTALL_DIR..."
    git clone --depth=1 --branch "$BRANCH" "https://github.com/$REPO.git" "$INSTALL_DIR"
    ok "Repository cloned"
fi

cd "$INSTALL_DIR"

# ── Install dependencies ──────────────────────────────────
info "Installing Python dependencies..."
"$UV_BIN" sync 2>&1 | tail -1
ok "Dependencies installed"

# ── Train models (only if not already present) ────────────
MODEL_DIR="$INSTALL_DIR/models"
if [ -d "$MODEL_DIR" ] && [ "$(find "$MODEL_DIR" -maxdepth 1 -name '*.pkl' 2>/dev/null | wc -l)" -gt 0 ]; then
    ok "ML models already trained — skipping training"
else
    info "Training ML models (this may take a minute)..."
    "$UV_BIN" run python scripts/train.py
    ok "ML models trained"
fi

# ── Ensure dataset exists ─────────────────────────────────
if [ ! -f "$INSTALL_DIR/data/raw/linux_issues.jsonl" ]; then
    info "Generating synthetic dataset..."
    "$UV_BIN" run python scripts/generate_dataset.py
    ok "Dataset generated"
fi

# ── Create symlink ────────────────────────────────────────
SYMLINK_TARGET="/usr/local/bin/linux-doctor"
WRAPPER="$INSTALL_DIR/linux-doctor"

# Create a wrapper script that cd's to the install dir first
cat > "$WRAPPER" << 'SCRIPT'
#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$0")"
exec uv run python -m linux_doctor.cli.app "$@"
SCRIPT
chmod +x "$WRAPPER"

# Install to PATH
if [ -w "/usr/local/bin" ]; then
    ln -sf "$WRAPPER" "$SYMLINK_TARGET"
    ok "Installed to $SYMLINK_TARGET"
else
    mkdir -p "$HOME/.local/bin"
    ln -sf "$WRAPPER" "$HOME/.local/bin/linux-doctor"
    warn "Could not write to /usr/local/bin — installed to $HOME/.local/bin/linux-doctor"
    warn "Make sure \$HOME/.local/bin is in your PATH"
    export PATH="$HOME/.local/bin:$PATH"
fi

# ── Verify ─────────────────────────────────────────────────
if command -v linux-doctor >/dev/null 2>&1; then
    ok "Installation complete! Run: linux-doctor \"your linux issue\""
else
    warn "Installation done but 'linux-doctor' not in PATH yet."
    warn "Add to your shell config: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "  linux-doctor \"nginx failed to start\""
fi
