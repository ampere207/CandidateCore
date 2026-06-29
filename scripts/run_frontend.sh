#!/bin/bash
# Script to run Next.js frontend

set -e

echo "=== Launching Next.js Frontend on http://localhost:3000 ==="
cd frontend
npm run dev
