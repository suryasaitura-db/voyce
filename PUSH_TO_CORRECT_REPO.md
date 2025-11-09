# Push Code to Correct Repository

The code is currently at: https://github.com/suryasaitura-db/voyce
You want it at: https://github.com/suryasai87/voyce

---

## Quick Fix (2 Minutes)

### Step 1: Create Repository on GitHub

Go to: https://github.com/new

**Settings**:
- **Owner**: suryasai87 (make sure you're logged in as this user)
- **Repository name**: `voyce`
- **Description**: `Voyce - AI-Powered Voice Feedback Platform with Databricks Integration`
- **Visibility**: Public
- **Do NOT check**: Initialize with README, .gitignore, or license

Click **Create repository**

### Step 2: Update Git Remote and Push

Run these commands in your terminal:

```bash
# Navigate to project directory
cd /Users/suryasai.turaga/voyce

# Remove current remote
git remote remove origin

# Add correct remote
git remote add origin https://github.com/suryasai87/voyce.git

# Verify
git remote -v
# Should show: https://github.com/suryasai87/voyce.git

# Push all code
git push -u origin main

# You may be prompted to authenticate
# Use your GitHub credentials for suryasai87 account
```

### Step 3: Verify

Open: https://github.com/suryasai87/voyce

You should see:
- README.md
- All project files
- Documentation files (DATABRICKS_SETUP.md, AUTHENTICATION_SETUP.md, etc.)
- Backend, frontend, chrome-extension folders
- All commits

---

## Alternative: Use GitHub CLI

If you have GitHub CLI and are logged in as `suryasai87`:

```bash
# Create repository
gh repo create suryasai87/voyce \
  --public \
  --description "Voyce - AI-Powered Voice Feedback Platform with Databricks Integration" \
  --source=. \
  --remote=origin \
  --push
```

This creates the repo and pushes in one command!

---

## Troubleshooting

### Issue: "Repository already exists"

**Solution**: The repository was created. Just push:
```bash
git remote set-url origin https://github.com/suryasai87/voyce.git
git push -u origin main
```

### Issue: "Authentication failed"

**Solution**: Make sure you're authenticated as `suryasai87`:

```bash
# Via GitHub CLI
gh auth login

# Or use Personal Access Token
# 1. Go to: https://github.com/settings/tokens
# 2. Generate new token (classic)
# 3. Scopes: repo (all)
# 4. Use token as password when pushing
```

### Issue: "Permission denied"

**Cause**: You're authenticated as wrong user

**Solution**:
```bash
# Check current GitHub user
gh auth status

# Or check git config
git config user.name
git config user.email

# Login as correct user
gh auth login
```

---

## Current Status

**Code location**: https://github.com/suryasaitura-db/voyce ✅
**Desired location**: https://github.com/suryasai87/voyce ⏳

**Action needed**: Create repository at `suryasai87/voyce` then push

---

## Need Help?

If you're having trouble, here's what I can see:

**Current remote**:
```bash
origin  https://github.com/suryasaitura-db/voyce.git (fetch)
origin  https://github.com/suryasaitura-db/voyce.git (push)
```

**Authenticated as**: `suryasaitura-db`

**To switch to suryasai87**:
1. Create repo at https://github.com/suryasai87/voyce
2. Run the commands in Step 2 above
3. You may need to authenticate as `suryasai87` when pushing

Let me know if you need more help!
