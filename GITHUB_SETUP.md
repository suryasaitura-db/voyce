# 📦 GitHub Repository Setup

The Voyce repository needs to be created on GitHub before pushing code.

---

## Option 1: Create via GitHub CLI (Fastest)

```bash
# Install GitHub CLI (if not installed)
brew install gh

# Authenticate
gh auth login

# Create repository
cd /Users/suryasai.turaga/voyce
gh repo create suryasai87/voyce --public --source=. --remote=origin

# Push code
git push -u origin main
```

---

## Option 2: Create via GitHub Website

### Step 1: Create Repository on GitHub

1. Go to: https://github.com/new
2. **Repository name**: `voyce`
3. **Description**: `🎙️ AI-powered voice feedback platform with multi-language support, sentiment analysis, and real-time analytics`
4. **Visibility**: Public
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### Step 2: Push Local Code

```bash
cd /Users/suryasai.turaga/voyce

# Verify remote
git remote -v

# If remote doesn't exist, add it:
git remote add origin https://github.com/suryasai87/voyce.git

# Push code
git push -u origin main
```

### Step 3: Verify Upload

1. Go to: https://github.com/suryasai87/voyce
2. You should see all files
3. Check that README.md displays correctly

---

## Option 3: Create with Personal Access Token

If you have authentication issues:

### Step 1: Create Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. **Note**: "Voyce deployment"
4. **Expiration**: 90 days
5. **Scopes**: Select `repo` (full control of private repositories)
6. Click "Generate token"
7. **Copy the token** (you won't see it again!)

### Step 2: Push with Token

```bash
cd /Users/suryasai.turaga/voyce

# Use token in URL (replace YOUR_TOKEN)
git remote set-url origin https://YOUR_TOKEN@github.com/suryasai87/voyce.git

# Push
git push -u origin main
```

---

## After Successful Push

### Verify Repository

Visit: https://github.com/suryasai87/voyce

You should see:
- ✅ All 125+ files
- ✅ README.md displayed
- ✅ Folder structure
- ✅ Documentation in /docs/
- ✅ Latest commit: "Add custom UI branding and deployment guides"

### Configure Repository Settings

1. **About Section**:
   - Description: `🎙️ AI-powered voice feedback platform`
   - Website: (deployment URL when ready)
   - Topics: `voice-recognition`, `sentiment-analysis`, `fastapi`, `react`, `databricks`, `ai`, `ml`

2. **Enable GitHub Pages** (optional):
   - Settings → Pages
   - Source: Deploy from branch
   - Branch: main, /docs
   - This will host documentation

3. **Configure Branch Protection** (recommended for teams):
   - Settings → Branches → Add rule
   - Branch name pattern: `main`
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging

4. **Add Collaborators**:
   - Settings → Collaborators and teams
   - Add team members

---

## Share with Collaborators

Once pushed, share this link with your team:

```
Repository: https://github.com/suryasai87/voyce

Clone command:
git clone https://github.com/suryasai87/voyce.git
cd voyce

Follow setup guide:
See COLLABORATOR_GUIDE.md
```

---

## Troubleshooting

### Issue: "Permission denied"

**Solution**:
```bash
# Use HTTPS instead of SSH
git remote set-url origin https://github.com/suryasai87/voyce.git

# Or set up SSH keys
# Follow: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
```

### Issue: "Repository not found"

**Solution**:
1. Verify repository exists at: https://github.com/suryasai87/voyce
2. Check you're logged into correct GitHub account
3. Verify repository name spelling

### Issue: "Authentication failed"

**Solution**:
```bash
# Clear credentials
git credential-osxkeychain erase
host=github.com
protocol=https
[Press Ctrl+D]

# Try push again - will prompt for credentials
git push -u origin main
```

---

## Current Status

```bash
# Check git status
cd /Users/suryasai.turaga/voyce
git status

# Check remote
git remote -v

# Check commits
git log --oneline -5
```

**Expected**:
- Branch: main
- Commits: 4
- Remote: origin → https://github.com/suryasai87/voyce.git
- Status: Up to date

**All files committed**: ✅
**Ready to push**: ✅
**Waiting for**: GitHub repository creation

---

## Next Steps

1. Create GitHub repository (choose option above)
2. Push code: `git push -u origin main`
3. Verify at: https://github.com/suryasai87/voyce
4. Share with collaborators
5. Deploy (see `DEPLOYMENT_STATUS.md`)

---

**Note**: All code is committed locally and ready. Just need to create the GitHub repository and push!
