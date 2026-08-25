#!/usr/bin/env bash
# Install this icon theme into Zed.
#
#   ./install.sh            rebuild, then patch Zed's installed Symbols pack
#   ./install.sh --restore  put Zed's Symbols pack back to stock
#
# The patch route exists because Zed has no CLI for installing dev extensions.
# It works immediately with "icon_theme": "Symbols Icon Theme", but Zed's
# updater will overwrite it when upstream Symbols publishes a new version --
# just re-run this script if that happens.
#
# The durable route is `zed: install dev extension` from the command palette,
# pointed at this folder. Dev extensions are never auto-updated. See README.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYMBOLS="$HOME/Library/Application Support/Zed/extensions/installed/symbols"

if [[ "${1:-}" == "--restore" ]]; then
  python3 "$ROOT/build/apply.py" --restore
  echo "Zed's Symbols pack is back to stock."
  exit 0
fi

if [[ ! -d "$SYMBOLS" ]]; then
  echo "error: Symbols is not installed in Zed." >&2
  echo "Install the Symbols extension first, or use the dev-extension route." >&2
  exit 1
fi

echo "==> rebuilding theme from build/upstream"
python3 "$ROOT/build/build_extension.py"

echo
echo "==> patching Zed's installed Symbols pack"
python3 "$ROOT/build/apply.py"

echo
echo "Done. Restart Zed."
echo "Your settings should read:  \"icon_theme\": \"Symbols Icon Theme\""
