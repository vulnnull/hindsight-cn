#!/usr/bin/env bash
# Hindsight memory integration for OpenAI Codex CLI
#
# This script installs the Hindsight hooks into ~/.codex/ and copies
# the hook scripts to ~/.hindsight/codex/scripts/.
#
# Usage:
#   ./install.sh              # Install (or update)
#   ./install.sh --uninstall  # Remove Hindsight hooks

set -euo pipefail

INTEGRATION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${HOME}/.hindsight/codex"
SCRIPTS_DIR="${INSTALL_DIR}/scripts"
CODEX_DIR="${HOME}/.codex"
HOOKS_FILE="${CODEX_DIR}/hooks.json"
CONFIG_FILE="${CODEX_DIR}/config.toml"

# ──────────────────────────────────────────────────────────────────────────────
# Uninstall
# ──────────────────────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--uninstall" ]]; then
    echo "Uninstalling Hindsight Codex integration..."

    # Remove scripts directory
    if [[ -d "${SCRIPTS_DIR}" ]]; then
        rm -rf "${SCRIPTS_DIR}"
        echo "  Removed ${SCRIPTS_DIR}"
    fi

    # Remove hooks.json
    if [[ -f "${HOOKS_FILE}" ]]; then
        rm -f "${HOOKS_FILE}"
        echo "  Removed ${HOOKS_FILE}"
    fi

    # Remove codex_hooks feature flag from config.toml (if present)
    if [[ -f "${CONFIG_FILE}" ]]; then
        # Remove the [features] block line for codex_hooks
        sed -i.bak '/^codex_hooks *= *true/d' "${CONFIG_FILE}" && rm -f "${CONFIG_FILE}.bak"
        echo "  Removed codex_hooks from ${CONFIG_FILE}"
    fi

    echo "Uninstall complete."
    exit 0
fi

# ──────────────────────────────────────────────────────────────────────────────
# Install
# ──────────────────────────────────────────────────────────────────────────────
echo "Installing Hindsight Codex integration..."

# 1. Copy scripts to ~/.hindsight/codex/scripts/
mkdir -p "${SCRIPTS_DIR}"
cp -r "${INTEGRATION_DIR}/scripts/." "${SCRIPTS_DIR}/"
chmod +x "${SCRIPTS_DIR}/session_start.py"
chmod +x "${SCRIPTS_DIR}/recall.py"
chmod +x "${SCRIPTS_DIR}/retain.py"
echo "  Scripts installed to ${SCRIPTS_DIR}"

# 2. Copy default settings (don't overwrite user's existing settings)
SETTINGS_DST="${INSTALL_DIR}/settings.json"
if [[ ! -f "${SETTINGS_DST}" ]]; then
    cp "${INTEGRATION_DIR}/settings.json" "${SETTINGS_DST}"
    echo "  Default settings written to ${SETTINGS_DST}"
else
    echo "  Keeping existing settings at ${SETTINGS_DST}"
fi

# 3. Write ~/.codex/hooks.json with absolute paths
mkdir -p "${CODEX_DIR}"
cat > "${HOOKS_FILE}" <<EOF
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${SCRIPTS_DIR}/session_start.py\"",
            "timeout": 5
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${SCRIPTS_DIR}/recall.py\"",
            "timeout": 12
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${SCRIPTS_DIR}/retain.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
EOF
echo "  Hooks written to ${HOOKS_FILE}"

# 4. Enable codex_hooks in ~/.codex/config.toml
if [[ ! -f "${CONFIG_FILE}" ]]; then
    touch "${CONFIG_FILE}"
fi

# Check if [features] section exists
if grep -q '^\[features\]' "${CONFIG_FILE}" 2>/dev/null; then
    # Section exists — add codex_hooks under it if not already present
    if ! grep -q '^codex_hooks' "${CONFIG_FILE}"; then
        # Insert codex_hooks after [features]
        sed -i.bak '/^\[features\]/a codex_hooks = true' "${CONFIG_FILE}" && rm -f "${CONFIG_FILE}.bak"
        echo "  Added codex_hooks = true to [features] in ${CONFIG_FILE}"
    else
        echo "  codex_hooks already enabled in ${CONFIG_FILE}"
    fi
else
    # No [features] section — append it
    printf '\n[features]\ncodex_hooks = true\n' >> "${CONFIG_FILE}"
    echo "  Added [features] codex_hooks = true to ${CONFIG_FILE}"
fi

echo ""
echo "Hindsight is installed for Codex."
echo ""
echo "Configuration:"
echo "  Edit ${SETTINGS_DST} to customize settings."
echo "  Or create ~/.hindsight/codex.json for personal overrides."
echo ""
echo "For Hindsight Cloud, set:"
echo "  \"hindsightApiUrl\": \"https://api.hindsight.vectorize.io\""
echo "  \"hindsightApiToken\": \"your-api-key\""
echo ""
echo "For local daemon mode, set an LLM API key:"
echo "  export OPENAI_API_KEY=sk-your-key"
echo ""
echo "Start a new Codex session to activate."
