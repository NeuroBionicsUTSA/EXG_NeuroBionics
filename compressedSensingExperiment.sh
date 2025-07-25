#!/bin/bash
# Compressed Sensing Experiment Script
# Runs streaming services, then records data for 10 minutes

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Path to the virtual environment's Python
PYTHON=".venv/bin/python"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Compressed Sensing Experiment ===${NC}"
echo -e "${YELLOW}Starting streaming services...${NC}"

# Start brainflow streaming (server and client)
echo -e "${YELLOW}Starting EXG streaming...${NC}"
bash "$SCRIPT_DIR/stream_brainflow.sh" &
BRAINFLOW_PID=$!

# Wait 5 seconds for brainflow to initialize
sleep 5

# Start prompt streaming
echo -e "${YELLOW}Starting prompt streaming...${NC}"
bash "$SCRIPT_DIR/stream_prompt.sh" &
PROMPT_PID=$!

# Wait 15 seconds total for all streams to initialize
echo -e "${YELLOW}Waiting 15 seconds for streams to initialize...${NC}"
sleep 10

# Check if streams are ready (optional - can be enhanced)
echo -e "${YELLOW}Checking stream status...${NC}"

# Start data recording for 10 minutes (600 seconds)
echo -e "${GREEN}Starting data recording for 3 minutes...${NC}"
cd "$SCRIPT_DIR"

# Run the recording script with timeout (using built-in bash timeout alternative)
# Record for 5 minutes (300 seconds) - using background process with sleep
$PYTHON src/record_lsl_csv.py &
RECORD_PID=$!

# Wait for 5 minutes
sleep 180

# Kill the recording process
kill $RECORD_PID 2>/dev/null

# Recording finished
echo -e "${GREEN}Data recording completed!${NC}"

# Clean up: Kill background processes
echo -e "${YELLOW}Cleaning up background processes...${NC}"

# Kill the streaming processes
kill $BRAINFLOW_PID 2>/dev/null
kill $PROMPT_PID 2>/dev/null

# Also kill any remaining Python processes related to our scripts
pkill -f "brainflow_server.py" 2>/dev/null
pkill -f "brainflow_client.py" 2>/dev/null
pkill -f "prompt_server.py" 2>/dev/null
pkill -f "prompt_client.py" 2>/dev/null

echo -e "${GREEN}Experiment completed successfully!${NC}"
echo -e "${YELLOW}Data saved to: $($PYTHON -c "from src.record_lsl_csv import SESSION_DIR; print(SESSION_DIR)")${NC}"
