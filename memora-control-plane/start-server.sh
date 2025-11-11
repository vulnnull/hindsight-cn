#!/bin/bash
# Wrapper script to map MEMORA_CP_* environment variables to Next.js standard variables

# Map prefixed env vars to standard Next.js env vars
export HOSTNAME="${MEMORA_CP_HOSTNAME:-0.0.0.0}"
export PORT="${MEMORA_CP_PORT:-3000}"

# Start the Next.js server
# The server.js is in the standalone output at the root
exec node server.js
