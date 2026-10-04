#!/usr/bin/env bash
# Installs the app launcher (and optionally login autostart) for the current user. Linux and macOS.
#   ./install.sh                 launcher + autostart
#   ./install.sh --no-autostart  launcher only
#   ./install.sh --uninstall     remove both
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
os="${SYSTEMMANAGER_OS:-$(uname -s)}"   # override only for testing

ensure_venv() {
    if [[ ! -x "$here/.venv/bin/python" ]]; then
        echo "Creating virtualenv..."
        python3 -m venv "$here/.venv"
        "$here/.venv/bin/pip" install -q -r "$here/requirements.txt"
    fi
}

# ---------------------------------------------------------------- Linux
linux_paths() {
    apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    icons="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
    autostart="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
}

linux_uninstall() {
    linux_paths
    rm -fv "$apps/systemmanager.desktop" "$autostart/systemmanager.desktop" "$icons/systemmanager.svg"
}

linux_install() {
    linux_paths
    local entry="[Desktop Entry]
Type=Application
Name=System Manager
Comment=Disk, CPU, memory and service dashboard
Exec=$here/run.sh
Icon=systemmanager
Terminal=false
Categories=System;Monitor;
StartupWMClass=systemmanager"
    mkdir -p "$apps" "$icons"
    cp "$here/assets/systemmanager.svg" "$icons/"
    printf '%s\n' "$entry" > "$apps/systemmanager.desktop"
    echo "Installed launcher: $apps/systemmanager.desktop"
    if [[ "${1:-}" != "--no-autostart" ]]; then
        mkdir -p "$autostart"
        printf '%s\nX-GNOME-Autostart-enabled=true\n' "$entry" > "$autostart/systemmanager.desktop"
        echo "Enabled autostart: $autostart/systemmanager.desktop"
    fi
    if command -v update-desktop-database >/dev/null; then update-desktop-database "$apps" || true; fi
}

# ---------------------------------------------------------------- macOS
mac_paths() {
    app="$HOME/Applications/System Manager.app"
    agent="$HOME/Library/LaunchAgents/com.systemmanager.dashboard.plist"
}

mac_uninstall() {
    mac_paths
    if command -v launchctl >/dev/null; then
        launchctl bootout "gui/$(id -u)/com.systemmanager.dashboard" 2>/dev/null || true
    fi
    rm -rfv "$app" "$agent"
}

mac_install() {
    mac_paths
    # A tiny .app bundle so it shows up in Launchpad / Spotlight / the Dock.
    mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
    printf '#!/bin/bash\nexec "%s/run.sh"\n' "$here" > "$app/Contents/MacOS/system-manager"
    chmod +x "$app/Contents/MacOS/system-manager"
    cat > "$app/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>System Manager</string>
    <key>CFBundleDisplayName</key><string>System Manager</string>
    <key>CFBundleIdentifier</key><string>com.systemmanager.dashboard</string>
    <key>CFBundleExecutable</key><string>system-manager</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleVersion</key><string>1</string>
    <key>CFBundleIconFile</key><string>systemmanager</string>
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
PLIST
    # Icon is best-effort: needs iconutil (ships with macOS) and the venv's PySide6.
    if command -v iconutil >/dev/null; then
        local iconset
        iconset="$(mktemp -d)/systemmanager.iconset"
        if "$here/.venv/bin/python" "$here/tools/make_icns.py" "$here/assets/systemmanager.svg" "$iconset" \
            && iconutil -c icns "$iconset" -o "$app/Contents/Resources/systemmanager.icns"; then
            :
        else
            echo "Note: could not build the app icon; the app will use the default icon."
        fi
    fi
    echo "Installed app: $app"

    if [[ "${1:-}" != "--no-autostart" ]]; then
        mkdir -p "$(dirname "$agent")"
        cat > "$agent" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.systemmanager.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-a</string>
        <string>$app</string>
    </array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
PLIST
        echo "Enabled autostart (starts at next login): $agent"
    fi
}

# ---------------------------------------------------------------- main
case "$os" in
    Linux)  prefix=linux ;;
    Darwin) prefix=mac ;;
    *) echo "Unsupported OS: $os (Linux and macOS only)" >&2; exit 1 ;;
esac

if [[ "${1:-}" == "--uninstall" ]]; then
    "${prefix}_uninstall"
    exit 0
fi

ensure_venv
"${prefix}_install" "${1:-}"
