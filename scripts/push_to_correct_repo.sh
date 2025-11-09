#!/bin/bash
#
# Push Voyce code to correct GitHub repository
# Target: https://github.com/suryasai87/voyce
#

set -e

echo "🔄 Pushing Voyce to Correct Repository"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the voyce project root directory"
    exit 1
fi

# Target repository
TARGET_REPO="https://github.com/suryasai87/voyce.git"
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "none")

echo "Current remote: $CURRENT_REMOTE"
echo "Target remote:  $TARGET_REPO"
echo ""

# Check if repository exists
echo "🔍 Checking if target repository exists..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://github.com/suryasai87/voyce)

if [ "$HTTP_CODE" = "404" ]; then
    echo ""
    echo "❌ Repository does not exist yet!"
    echo ""
    echo "Please create it first:"
    echo ""
    echo "Option 1: Via GitHub Web Interface"
    echo "  1. Go to: https://github.com/new"
    echo "  2. Login as: suryasai87"
    echo "  3. Repository name: voyce"
    echo "  4. Visibility: Public"
    echo "  5. Do NOT initialize with README"
    echo "  6. Click 'Create repository'"
    echo ""
    echo "Option 2: Via GitHub CLI"
    echo "  gh auth login  # Login as suryasai87"
    echo "  gh repo create suryasai87/voyce --public"
    echo ""
    echo "After creating the repository, run this script again!"
    exit 1
fi

echo "✅ Repository exists!"
echo ""

# Update remote
echo "🔧 Updating git remote..."
if [ "$CURRENT_REMOTE" = "$TARGET_REPO" ]; then
    echo "✅ Remote already set to correct repository"
else
    git remote remove origin 2>/dev/null || true
    git remote add origin "$TARGET_REPO"
    echo "✅ Remote updated to: $TARGET_REPO"
fi

echo ""
git remote -v
echo ""

# Check git status
echo "📊 Git status:"
git status --short
echo ""

# Push to repository
echo "🚀 Pushing code to GitHub..."
echo ""

if git push -u origin main; then
    echo ""
    echo "🎉 Success! Code pushed to: $TARGET_REPO"
    echo ""
    echo "🔗 View repository: https://github.com/suryasai87/voyce"
    echo ""
    echo "✅ Next steps:"
    echo "  1. Verify code at: https://github.com/suryasai87/voyce"
    echo "  2. Share with collaborators"
    echo "  3. Continue with deployment (see AUTHENTICATION_SETUP.md)"
else
    echo ""
    echo "❌ Push failed!"
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. Authentication failed"
    echo "   Solution: Make sure you're authenticated as 'suryasai87'"
    echo "   gh auth login"
    echo ""
    echo "2. Permission denied"
    echo "   Solution: Check that 'suryasai87' owns the repository"
    echo ""
    echo "3. Repository not empty"
    echo "   Solution: If repo was initialized with README, force push:"
    echo "   git push -u origin main --force"
    echo ""
    exit 1
fi
