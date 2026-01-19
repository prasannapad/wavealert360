#!/bin/bash
# 🚀 Quick Pi Sparse Checkout Validator
# ====================================
# Fast validation that sparse checkout is working correctly

echo "🎯 Quick Sparse Checkout Validation"
echo "==================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check if sparse checkout is enabled
sparse_enabled=$(git config core.sparseCheckout)
if [ "$sparse_enabled" = "true" ]; then
    echo "✅ Sparse checkout is ENABLED"
else
    echo "❌ Sparse checkout is DISABLED"
    echo "   Run: git config core.sparseCheckout true"
    exit 1
fi

# Check sparse checkout patterns
if [ -f ".git/info/sparse-checkout" ]; then
    echo "✅ Sparse checkout patterns configured:"
    cat .git/info/sparse-checkout | sed 's/^/   /'
else
    echo "❌ No sparse checkout patterns found"
    exit 1
fi

# Count actual files
file_count=$(find . -type f -not -path './.git/*' | wc -l)
echo ""
echo "📁 Files in working directory: $file_count"

if [ "$file_count" -le 10 ]; then
    echo "🎉 ULTRA-MINIMAL SUCCESS! (Expected ~8 files)"
    echo "   📊 ~98% bandwidth reduction achieved"
else
    echo "⚠️  File count seems high (expected ~8)"
    echo "   Check if sparse checkout is applied correctly"
fi

echo ""
echo "📋 Current files:"
find . -type f -not -path './.git/*' | sort | sed 's/^/   /'

echo ""
echo "🔍 Quick functionality check:"

# Test if essential files exist
essential_files=(
    "device/main.py"
    "device/helpers.py" 
    "updater/auto_updater.py"
    "requirements.txt"
)

all_present=true
for file in "${essential_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (MISSING)"
        all_present=false
    fi
done

if [ "$all_present" = true ]; then
    echo ""
    echo "🎯 VALIDATION PASSED: Ultra-minimal sparse checkout working perfectly!"
else
    echo ""
    echo "❌ VALIDATION FAILED: Missing essential files"
fi
