#!/bin/bash
# Run a command with dev server, starting it if needed

set -e

URL="http://localhost:3000"
COMMAND="$@"

# Check if server is running
check_server() {
    curl -s --head --request GET "$URL" --max-time 2 > /dev/null 2>&1
}

# If server is already running, just execute the command
if check_server; then
    echo "✓ Server already running at $URL"
    eval "$COMMAND"
    exit 0
fi

# Start server in background
echo "Starting dev server..."
pnpm dev > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to be ready (max 30 seconds)
echo -n "Waiting for server"
for i in {1..30}; do
    if check_server; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 1
done

if ! check_server; then
    echo " ✗ Failed to start server"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Run the command
eval "$COMMAND"
EXIT_CODE=$?

# Stop the server we started
echo "Stopping dev server..."
kill $SERVER_PID 2>/dev/null || true

exit $EXIT_CODE
