#!/bin/bash
# Git Sync Verification Script
# Usage: ./verify_sync.sh <filename>

FILE=$1
if [ -z "$FILE" ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

echo "🔍 Verifying git sync for: $FILE"
echo ""

# Check if file exists
if [ ! -f "$FILE" ]; then
    echo "❌ File does not exist: $FILE"
    exit 1
fi

# Get hashes
LOCAL_HASH=$(git hash-object "$FILE")
GIT_HASH=$(git ls-files --stage "$FILE" | cut -d' ' -f2)

echo "Local file hash:     $LOCAL_HASH"
echo "Git repository hash: $GIT_HASH"
echo ""

if [ "$LOCAL_HASH" = "$GIT_HASH" ]; then
    echo "✅ File is in sync with git repository"
else
    echo "❌ File is NOT in sync with git repository"
    echo "   This means your working file differs from what's committed"
    echo "   You need to: git add $FILE && git commit -m 'Update $FILE'"
fi

echo ""
echo "📊 Git status:"
git status --porcelain "$FILE"
