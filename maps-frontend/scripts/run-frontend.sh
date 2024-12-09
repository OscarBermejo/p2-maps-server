#!/bin/bash
cd "$(dirname "$0")/.."  # Navigate to frontend directory
npm run build
nohup npx serve -s build -l 3000 > frontend-nohup.out 2>&1 &