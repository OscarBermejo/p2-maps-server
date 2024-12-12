#!/bin/bash
cd "$(dirname "$0")/.."  # Navigate to frontend directory

# First, let's try to kill any existing process on port 3001
lsof -ti:3001 | xargs kill -9 2>/dev/null || true

# Set the development port to 3001
export PORT=3001

# Run frontend in development mode
npm start