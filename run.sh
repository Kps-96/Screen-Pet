#!/usr/bin/env bash
# Startup script for Deckpet

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Ensure XCB cursor libraries are discoverable
if [ -d "$DIR/libs/usr/lib/x86_64-linux-gnu" ]; then
    export LD_LIBRARY_PATH="$DIR/libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
fi

# Force XCB (XWayland) for strict Always-On-Top and exact screen positioning
export QT_QPA_PLATFORM=xcb

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

exec ./venv/bin/python3 main.py "$@"
