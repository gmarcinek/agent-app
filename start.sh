#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p output/logs

echo -e "${BLUE}🎯 Starting Agent App Orchestrator${NC}"
echo -e "${BLUE}=================================${NC}"

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down processes...${NC}"
    
    # Kill background jobs
    jobs -p | xargs -r kill
    
    # Wait a bit for graceful shutdown
    sleep 2
    
    # Force kill if still running
    jobs -p | xargs -r kill -9 2>/dev/null
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start analyser in background
echo -e "${BLUE}🔧 Starting analyser...${NC}"
poetry run analyser-watch --mode watch > output/logs/analyser.log 2>&1 &
ANALYSER_PID=$!
echo -e "${GREEN}✅ Analyser started (PID: $ANALYSER_PID) - logs: output/logs/analyser.log${NC}"

# Short delay between starts
sleep 1

# Start synthetiser in background  
echo -e "${BLUE}🔧 Starting synthetiser...${NC}"
poetry run synthetiser --mode watch > output/logs/synthetiser.log 2>&1 &
SYNTHETISER_PID=$!
echo -e "${GREEN}✅ Synthetiser started (PID: $SYNTHETISER_PID) - logs: output/logs/synthetiser.log${NC}"

# Short delay before starting main process
sleep 1

echo -e "${BLUE}🚀 Starting agent in foreground...${NC}"
echo -e "${YELLOW}💡 Background processes running. Use Ctrl+C to stop all.${NC}"
echo -e "${YELLOW}📝 Check logs: tail -f output/logs/analyser.log${NC}"
echo -e "${YELLOW}📝 Check logs: tail -f output/logs/synthetiser.log${NC}"
echo -e "${BLUE}=================================${NC}"

# Start agent in foreground (interactive mode)
poetry run agent

# If agent exits normally, cleanup background processes
cleanup