#!/bin/bash
#
# Setup Automatic OAuth Token Rotation
# Runs every 50 minutes to refresh Databricks OAuth token before expiry
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROTATION_SCRIPT="$SCRIPT_DIR/rotate_oauth_token.py"
LOG_DIR="$PROJECT_DIR/logs"

echo "🔐 Setting up Automatic OAuth Token Rotation"
echo ""

# Create logs directory
mkdir -p "$LOG_DIR"

# Detect OS
OS="$(uname -s)"

case "$OS" in
    Darwin)
        echo "📱 Detected: macOS"
        echo "   Setting up LaunchAgent for automatic rotation..."
        echo ""

        # Create LaunchAgent plist
        PLIST_NAME="com.voyce.oauth-rotation"
        PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

        cat > "$PLIST_FILE" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>

    <key>ProgramArguments</key>
    <array>
        <string>$(which python3)</string>
        <string>${ROTATION_SCRIPT}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>

    <key>StandardOutPath</key>
    <string>${LOG_DIR}/oauth-rotation.log</string>

    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/oauth-rotation-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
        <key>PYTHONPATH</key>
        <string>${PROJECT_DIR}</string>
    </dict>

    <key>StartInterval</key>
    <integer>3000</integer>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

        chmod 644 "$PLIST_FILE"

        # Load LaunchAgent
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        launchctl load "$PLIST_FILE"

        echo "✅ LaunchAgent created: $PLIST_FILE"
        echo "   • Runs every 50 minutes (3000 seconds)"
        echo "   • Logs: $LOG_DIR/oauth-rotation.log"
        echo ""
        echo "Commands:"
        echo "   • Check status: launchctl list | grep oauth-rotation"
        echo "   • View logs: tail -f $LOG_DIR/oauth-rotation.log"
        echo "   • Stop: launchctl unload $PLIST_FILE"
        echo "   • Start: launchctl load $PLIST_FILE"
        ;;

    Linux)
        echo "🐧 Detected: Linux"

        # Check if systemd is available
        if command -v systemctl &> /dev/null; then
            echo "   Setting up systemd timer..."
            echo ""

            # Create systemd service
            SERVICE_FILE="$HOME/.config/systemd/user/voyce-oauth-rotation.service"
            TIMER_FILE="$HOME/.config/systemd/user/voyce-oauth-rotation.timer"

            mkdir -p "$HOME/.config/systemd/user"

            cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Voyce OAuth Token Rotation
After=network.target

[Service]
Type=oneshot
WorkingDirectory=${PROJECT_DIR}
ExecStart=$(which python3) ${ROTATION_SCRIPT}
StandardOutput=append:${LOG_DIR}/oauth-rotation.log
StandardError=append:${LOG_DIR}/oauth-rotation-error.log
Environment="PYTHONPATH=${PROJECT_DIR}"

[Install]
WantedBy=default.target
EOF

            cat > "$TIMER_FILE" <<EOF
[Unit]
Description=Voyce OAuth Token Rotation Timer
Requires=voyce-oauth-rotation.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=50min
Persistent=true

[Install]
WantedBy=timers.target
EOF

            # Reload systemd and enable timer
            systemctl --user daemon-reload
            systemctl --user enable voyce-oauth-rotation.timer
            systemctl --user start voyce-oauth-rotation.timer

            echo "✅ Systemd timer created"
            echo "   • Runs every 50 minutes"
            echo "   • Logs: $LOG_DIR/oauth-rotation.log"
            echo ""
            echo "Commands:"
            echo "   • Check status: systemctl --user status voyce-oauth-rotation.timer"
            echo "   • View logs: journalctl --user -u voyce-oauth-rotation.service -f"
            echo "   • Stop: systemctl --user stop voyce-oauth-rotation.timer"
            echo "   • Start: systemctl --user start voyce-oauth-rotation.timer"
        else
            # Fallback to crontab
            echo "   Setting up cron job..."
            echo ""

            CRON_CMD="*/50 * * * * cd $PROJECT_DIR && $(which python3) $ROTATION_SCRIPT >> $LOG_DIR/oauth-rotation.log 2>&1"

            # Add to crontab if not already present
            (crontab -l 2>/dev/null | grep -v "rotate_oauth_token.py"; echo "$CRON_CMD") | crontab -

            echo "✅ Cron job added"
            echo "   • Runs every 50 minutes"
            echo "   • Logs: $LOG_DIR/oauth-rotation.log"
            echo ""
            echo "Commands:"
            echo "   • View cron jobs: crontab -l"
            echo "   • View logs: tail -f $LOG_DIR/oauth-rotation.log"
            echo "   • Remove: crontab -e (delete the line)"
        fi
        ;;

    *)
        echo "❌ Unsupported OS: $OS"
        echo "   Please manually set up a cron job to run:"
        echo "   $ROTATION_SCRIPT"
        exit 1
        ;;
esac

echo ""
echo "🎉 Automatic token rotation setup complete!"
echo ""
echo "📋 What happens now:"
echo "   1. Script runs every 50 minutes"
echo "   2. Checks if OAuth token expires within 5 minutes"
echo "   3. If yes, gets new token via Databricks CLI"
echo "   4. Updates .env file with new token"
echo "   5. Logs rotation to $LOG_DIR/oauth-rotation.log"
echo ""
echo "⚠️  IMPORTANT:"
echo "   • Make sure Databricks CLI is installed: pip install databricks-cli"
echo "   • Make sure you're logged in: databricks auth login"
echo "   • Backend server will need restart after token rotation"
echo ""
echo "🔍 Monitor rotation:"
echo "   tail -f $LOG_DIR/oauth-rotation.log"
