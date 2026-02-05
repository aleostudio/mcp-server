#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NOCOLOR='\033[0m'

# Init .venv if not exists
if [ ! -d ".venv" ]; then
    echo "${YELLOW}Creating virtualenv...${NOCOLOR}"
    uv venv
    NEEDS_SYNC=true
else
    # Check if the marker file exists
    if [ ! -f ".venv/.synced" ]; then
        NEEDS_SYNC=true
    else
        NEEDS_SYNC=false
    fi
fi

# Activate virtualenv
source .venv/bin/activate

# Sync dependencies
if [ "$NEEDS_SYNC" = true ]; then
    echo "${YELLOW}Synchronizing dependencies...${NOCOLOR}"
    uv sync
    # Create marker file
    touch .venv/.synced 
fi

# Run server
echo "${GREEN}Running server...${NOCOLOR}"
uv run python -m app.main --sse --port ${APP_PORT:-8000}
