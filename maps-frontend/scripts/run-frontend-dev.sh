#!/bin/bash
cd "$(dirname "$0")/.."  # Navigate to frontend directory

# First, let's try to kill any existing process on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Run frontend in development mode
npm start