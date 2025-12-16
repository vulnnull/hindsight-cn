#!/bin/bash
# Regenerate llms-full.txt when docs change

LOG_PREFIX="       "

# Check if any docs files are staged
DOCS_CHANGED=$(git diff --cached --name-only -- 'hindsight-docs/docs/**/*.md' 'hindsight-docs/docs/**/*.mdx' 2>/dev/null || true)

if [ -z "$DOCS_CHANGED" ]; then
    echo "${LOG_PREFIX}No docs changes, skipping"
    exit 0
fi

echo "${LOG_PREFIX}Docs changed, regenerating llms-full.txt..."

# Check if npm is available and hindsight-docs exists
if [ ! -d "hindsight-docs" ] || ! command -v npm &> /dev/null; then
    echo "${LOG_PREFIX}Warning: Cannot regenerate llms-full.txt (missing hindsight-docs or npm)"
    exit 0
fi

cd hindsight-docs

# Run the generate script
if npm run generate-llms --silent 2>/dev/null; then
    # Check if llms-full.txt changed
    if [ -n "$(git diff --name-only -- static/llms-full.txt 2>/dev/null)" ]; then
        echo "${LOG_PREFIX}llms-full.txt updated, staging..."
        git add static/llms-full.txt
    else
        echo "${LOG_PREFIX}llms-full.txt unchanged"
    fi
else
    echo "${LOG_PREFIX}Warning: Failed to regenerate llms-full.txt"
fi
