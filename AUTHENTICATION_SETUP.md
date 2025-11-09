# 🔐 Authentication & Token Management Setup

Complete guide for setting up PostgreSQL authentication and OAuth token rotation for Voyce platform.

---

## Overview

Your Voyce deployment uses two authentication systems:

1. **PostgreSQL** (Databricks-hosted)
   - Connection: Username/password
   - Password stored in: `.pgpass` file (optional, for convenience)
   - Used by: Backend API, DBeaver, psql

2. **Databricks OAuth** (Workspace API)
   - Token type: JWT (JSON Web Token)
   - Expiry: 1 hour
   - Auto-rotation: Every 50 minutes
   - Used by: Unity Catalog, ML pipelines, data sync

---

## Quick Start (5 Minutes)

### 1. Set PostgreSQL Password

```bash
# Set password as environment variable
export PGPASSWORD="your-databricks-postgres-password"

# Verify it's set
echo $PGPASSWORD
```

### 2. Setup .pgpass for Passwordless Access (Optional)

```bash
# Run setup script
./scripts/setup_pgpass.sh

# This creates ~/.pgpass with your credentials
# Now you can connect without typing password:
# psql "postgresql://suryasai.turaga@databricks.com@instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require"
```

**Benefits**:
- No need to type password for psql commands
- DBeaver can read from .pgpass
- Scripts can run without manual password entry

### 3. Setup Automatic OAuth Token Rotation

```bash
# Install Databricks CLI (if not already installed)
pip install databricks-cli

# Login to Databricks
databricks auth login --host https://fe-vm-hls-amer.cloud.databricks.com

# Setup automatic rotation (runs every 50 minutes)
./scripts/setup_auto_token_rotation.sh
```

**What this does**:
- Creates LaunchAgent (macOS) or systemd timer (Linux)
- Checks token expiry every 50 minutes
- Automatically refreshes token via Databricks CLI
- Updates `.env` file with new token
- Logs rotation to `logs/oauth-rotation.log`

---

## Manual Token Rotation

If you need to manually rotate the OAuth token:

```bash
# Run rotation script
python3 scripts/rotate_oauth_token.py
```

**Output**:
```
🔐 Databricks OAuth Token Rotation
==========================================

📊 Current Token Status:
   expires_in_minutes: 45
   is_expired: False

🔄 Token expired or expiring soon. Rotating...
✅ New token valid until: 2025-11-09T08:30:00
✅ Updated .env

🎉 Token rotation successful!

⚠️  IMPORTANT: Restart your backend server
   pkill -f 'python main.py' && python main.py
```

**Note**: After token rotation, you must restart the backend server for the new token to take effect.

---

## PostgreSQL Connection Details

### For psql (Command Line)

```bash
# With .pgpass setup (no password needed)
psql "postgresql://suryasai.turaga@databricks.com@instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require"

# With password prompt
PGPASSWORD="your-password" psql \
  "postgresql://suryasai.turaga@databricks.com@instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require"
```

### For DBeaver

See `DBEAVER_SETUP.md` for complete guide.

**Quick settings**:
```
Host:     instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com
Port:     5432
Database: databricks_postgres
Username: suryasai.turaga@databricks.com
Password: [your-password]
SSL Mode: require
```

### For Backend (.env)

Already configured in `.env`:
```bash
POSTGRES_HOST=instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com
POSTGRES_PORT=5432
POSTGRES_DB=databricks_postgres
POSTGRES_USER=suryasai.turaga@databricks.com
POSTGRES_PASSWORD=${PGPASSWORD}
DATABASE_URL=postgresql+asyncpg://suryasai.turaga%40databricks.com:${PGPASSWORD}@instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require
```

---

## OAuth Token Details

### Current Token Info

Check token status:
```bash
python3 -c "
from backend.services.databricks_oauth import get_oauth_manager

manager = get_oauth_manager()
info = manager.get_token_info()

print('Token Info:')
for key, value in info.items():
    print(f'  {key}: {value}')
"
```

**Output**:
```
Token Info:
  subject: suryasai.turaga@databricks.com
  client_id: databricks-session
  scopes: ['iam.current-user:read', 'iam.groups:read', ...]
  issuer: https://fe-vm-hls-amer.cloud.databricks.com/oidc
  expires_at: 2025-11-09T07:45:00
  expires_in_minutes: 52
  is_valid: True
```

### Token Scopes

Your OAuth token has these scopes:
- `iam.current-user:read` - Read current user info
- `iam.groups:read` - Read group memberships
- `iam.service-principals:read` - Read service principals
- `iam.users:read` - Read user information

These scopes allow:
- Unity Catalog access
- Workspace API calls
- SQL Warehouse queries
- Volume access (audio files)

---

## Monitoring

### Check Token Rotation Logs

```bash
# View rotation logs
tail -f logs/oauth-rotation.log

# On macOS with LaunchAgent
launchctl list | grep oauth-rotation

# On Linux with systemd
systemctl --user status voyce-oauth-rotation.timer
```

### Test PostgreSQL Connection

```bash
# Test with psql
psql "postgresql://suryasai.turaga@databricks.com@instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require" -c "SELECT version();"

# Test with Python
python3 -c "
import asyncio
import asyncpg
import os

async def test():
    conn = await asyncpg.connect(
        host='instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com',
        port=5432,
        database='databricks_postgres',
        user='suryasai.turaga@databricks.com',
        password=os.getenv('PGPASSWORD'),
        ssl='require'
    )
    version = await conn.fetchval('SELECT version()')
    print(f'✅ Connected: {version}')
    await conn.close()

asyncio.run(test())
"
```

### Test OAuth Token

```bash
# Test token validity
curl -H "Authorization: Bearer $(grep DATABRICKS_OAUTH_TOKEN .env | cut -d'=' -f2)" \
     https://fe-vm-hls-amer.cloud.databricks.com/api/2.0/preview/scim/v2/Me
```

---

## Troubleshooting

### Issue: "PGPASSWORD not set"

**Solution**:
```bash
export PGPASSWORD="your-password"

# Add to your shell profile for persistence
echo 'export PGPASSWORD="your-password"' >> ~/.zshrc  # or ~/.bashrc
```

### Issue: "OAuth token expired"

**Solution**:
```bash
# Manually rotate token
python3 scripts/rotate_oauth_token.py

# Or refresh via CLI
databricks auth token --host https://fe-vm-hls-amer.cloud.databricks.com

# Update .env with new token
# DATABRICKS_OAUTH_TOKEN=eyJraWQiOi...new-token...
```

### Issue: "Connection refused" (PostgreSQL)

**Solution**:
- Check PGPASSWORD is set: `echo $PGPASSWORD`
- Verify host is reachable: `ping instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com`
- Check SSL mode: Must be `sslmode=require`

### Issue: "Automatic rotation not working"

**macOS**:
```bash
# Check LaunchAgent status
launchctl list | grep oauth-rotation

# View logs
tail -f logs/oauth-rotation.log

# Restart
launchctl unload ~/Library/LaunchAgents/com.voyce.oauth-rotation.plist
launchctl load ~/Library/LaunchAgents/com.voyce.oauth-rotation.plist
```

**Linux**:
```bash
# Check timer status
systemctl --user status voyce-oauth-rotation.timer

# View logs
journalctl --user -u voyce-oauth-rotation.service -f

# Restart
systemctl --user restart voyce-oauth-rotation.timer
```

### Issue: ".pgpass not working"

**Solution**:
```bash
# Check file exists and has correct permissions
ls -la ~/.pgpass
# Should show: -rw------- (600)

# Fix permissions
chmod 600 ~/.pgpass

# Verify format (no spaces around colons)
cat ~/.pgpass
# Should be: host:port:database:username:password
```

---

## Security Best Practices

### 1. Protect .pgpass

```bash
# .pgpass must have 600 permissions
chmod 600 ~/.pgpass

# Never commit .pgpass to git
echo '.pgpass' >> .gitignore
```

### 2. Rotate Passwords Regularly

For PostgreSQL:
1. Change password in Databricks admin console
2. Update `PGPASSWORD` environment variable
3. Update `~/.pgpass` file
4. Update `.env` file

For OAuth tokens:
- Tokens auto-expire after 1 hour
- Automatic rotation handles this
- Manual rotation: `python3 scripts/rotate_oauth_token.py`

### 3. Use Environment Variables

Never hardcode credentials:
```bash
# ✅ Good
PGPASSWORD=${PGPASSWORD}

# ❌ Bad
PGPASSWORD=my-actual-password
```

### 4. Audit Access

Check who accessed the database:
```sql
-- View PostgreSQL access logs (if enabled)
SELECT * FROM pg_stat_activity WHERE datname = 'databricks_postgres';

-- View Databricks audit logs
SELECT * FROM audit_log ORDER BY created_at DESC LIMIT 100;
```

---

## Summary

### What You Have Now

✅ **PostgreSQL Authentication**
- Direct password authentication via PGPASSWORD
- Optional .pgpass for passwordless access
- DBeaver-compatible configuration
- SSL-encrypted connections

✅ **OAuth Token Management**
- Current token valid for ~1 hour
- Automatic rotation every 50 minutes
- Manual rotation script available
- Backend integration with auto-refresh checking

✅ **Tools Setup**
- psql command-line access
- DBeaver GUI access (see DBEAVER_SETUP.md)
- Python backend integration
- Monitoring and logging

### Next Steps

1. **Set PGPASSWORD**:
   ```bash
   export PGPASSWORD="your-password"
   ```

2. **Setup .pgpass** (optional):
   ```bash
   ./scripts/setup_pgpass.sh
   ```

3. **Setup auto token rotation**:
   ```bash
   ./scripts/setup_auto_token_rotation.sh
   ```

4. **Initialize database schema**:
   ```bash
   python scripts/init_db.py
   ```

5. **Start backend**:
   ```bash
   python main.py
   ```

6. **Connect DBeaver** (optional):
   - Follow `DBEAVER_SETUP.md`

---

## Related Documentation

- **DATABRICKS_SETUP.md** - Databricks-only deployment guide
- **DBEAVER_SETUP.md** - DBeaver connection setup
- **UPSTASH_SETUP.md** - Upstash Redis setup (if needed)
- **QUICK_START.md** - Overall platform quick start

---

**Authentication configured!** 🔐
**Token rotation automated!** 🔄
**Ready to deploy!** 🚀
