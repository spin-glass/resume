#!/bin/bash
# Run a command with Python simple HTTP server, starting it if needed

set -e

PORT=8080
URL="http://localhost:$PORT/resume-ja.html"
COMMAND="$@"
SERVER_DIR="resume"

# Check if server is running
check_server() {
    curl -s --head --request GET "$URL" --max-time 1 > /dev/null 2>&1
}

# If server is already running, just execute the command
if check_server; then
    echo "✓ Python server already running at http://localhost:$PORT"
    eval "$COMMAND"
    exit 0
fi

# Start server in background
echo "Starting Python HTTP server on port $PORT..."
cd $SERVER_DIR && python3 -m http.server $PORT > /dev/null 2>&1 &
SERVER_PID=$!


# Wait for server to be ready (max 10 seconds)
echo -n "Waiting for server"
for i in {1..10}; do
    if check_server; then
        echo " ✓"
        break
    fi
    echo -n "."
    sleep 1
done

if ! check_server; then
    echo " ✗ Failed to start Python server"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Run the command
echo "Executing: $COMMAND"
eval "$COMMAND"
EXIT_CODE=$?

# Stop the server we started
echo "Stopping Python server..."
kill $SERVER_PID 2>/dev/null || true

exit $EXIT_CODE
