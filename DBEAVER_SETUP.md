# DBeaver Setup for Databricks PostgreSQL

Quick guide to connect DBeaver to your Databricks PostgreSQL instance.

---

## Prerequisites

- **DBeaver**: Download from https://dbeaver.io/download/
  - Use **DBeaver Community Edition** (free) or Ultimate
- **PostgreSQL password**: Your Databricks PostgreSQL password

---

## Connection Setup (5 Minutes)

### Step 1: Create New Connection

1. Open DBeaver
2. Click **Database** → **New Database Connection**
3. Select **PostgreSQL**
4. Click **Next**

### Step 2: Enter Connection Details

```
Host:     instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com
Port:     5432
Database: databricks_postgres
Username: suryasai.turaga@databricks.com
Password: [Your Databricks PostgreSQL password]
```

**Important**: Make sure to **Save password** checkbox is checked.

### Step 3: Configure SSL

1. Click on **SSL** tab
2. Set **SSL Mode**: `require`
3. Leave other SSL fields empty (Databricks uses default SSL)

### Step 4: Test Connection

1. Click **Test Connection**
2. If prompted to download PostgreSQL driver, click **Download**
3. Should see: ✅ **Connected (PostgreSQL 15.x)**

### Step 5: Advanced Settings (Optional but Recommended)

**Connection Settings Tab:**
- **Connection name**: `Voyce - Databricks PostgreSQL`
- **Connection folder**: Create folder "Databricks"

**Driver Properties Tab:**
- `ApplicationName`: DBeaver-Voyce
- `connectTimeout`: 30
- `socketTimeout`: 60

### Step 6: Finish

Click **Finish** to save the connection.

---

## Verifying the Connection

### 1. Expand Connection Tree

```
Voyce - Databricks PostgreSQL
├── Databases
│   └── databricks_postgres
│       └── Schemas
│           └── public
│               ├── Tables
│               │   ├── users
│               │   ├── voice_submissions
│               │   ├── transcriptions
│               │   ├── ai_analysis
│               │   ├── sync_metadata
│               │   ├── processing_costs
│               │   └── audit_log
│               └── Views
```

### 2. Test Queries

Right-click on connection → **SQL Editor** → **New SQL Script**

```sql
-- Test connection
SELECT version();

-- List all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Check voice submissions
SELECT
    COUNT(*) as total_submissions,
    COUNT(DISTINCT user_id) as unique_users,
    MAX(created_at) as latest_submission
FROM voice_submissions;

-- Check transcriptions
SELECT
    engine,
    COUNT(*) as count,
    AVG(confidence) as avg_confidence
FROM transcriptions
GROUP BY engine;
```

---

## Using .pgpass for Passwordless Connection

If you set up `.pgpass` file (recommended), DBeaver can read it:

### Option 1: Reference .pgpass

1. In connection settings, leave **Password** field empty
2. DBeaver will automatically use `~/.pgpass` if it exists

### Option 2: Store Password in DBeaver

1. Check **Save password** in connection settings
2. DBeaver encrypts and stores password securely

---

## Useful DBeaver Features for Voyce

### 1. ER Diagram

View database schema visually:

1. Right-click on `public` schema
2. Select **View Diagram**
3. See relationships between tables

### 2. Data Export

Export voice submissions to CSV/JSON:

1. Right-click on `voice_submissions` table
2. Select **Export Data**
3. Choose format (CSV, JSON, Excel, etc.)

### 3. SQL Templates

Create reusable queries:

1. **Window** → **SQL Templates**
2. Add common queries:

```sql
-- Get recent submissions
SELECT
    vs.id,
    vs.created_at,
    u.email,
    t.text as transcription,
    ai.sentiment,
    ai.score
FROM voice_submissions vs
JOIN users u ON vs.user_id = u.id
LEFT JOIN transcriptions t ON vs.id = t.submission_id
LEFT JOIN ai_analysis ai ON vs.id = ai.submission_id
WHERE vs.created_at > NOW() - INTERVAL '24 hours'
ORDER BY vs.created_at DESC;
```

### 4. Data Editor

Edit data directly:

1. Double-click on table
2. Edit cells inline
3. **Ctrl+S** (Cmd+S) to save changes

### 5. Query History

View past queries:

1. **Window** → **Show View** → **Query Manager**
2. See all executed queries
3. Re-run or edit previous queries

---

## Troubleshooting

### Issue: "Connection refused"

**Cause**: Wrong host or port

**Solution**:
- Verify host: `instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com`
- Verify port: `5432`

### Issue: "SSL required"

**Cause**: SSL not enabled

**Solution**:
1. Go to **SSL** tab
2. Set **SSL Mode**: `require`

### Issue: "Authentication failed"

**Cause**: Wrong username or password

**Solution**:
- Username must be: `suryasai.turaga@databricks.com` (include @databricks.com)
- Check password is correct

### Issue: "Timeout"

**Cause**: Network latency or firewall

**Solution**:
1. Check internet connection
2. Increase timeout in **Driver Properties**:
   - `connectTimeout`: 60
   - `socketTimeout`: 120

### Issue: "Too many connections"

**Cause**: Connection pool exhausted

**Solution**:
1. Close unused DBeaver windows
2. Right-click connection → **Disconnect**
3. Reconnect

---

## Connection String (For Reference)

If needed elsewhere, here's the full connection string:

```
postgresql://suryasai.turaga%40databricks.com:${PGPASSWORD}@instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require
```

**Note**: `%40` is URL-encoded `@` character.

---

## Best Practices

### 1. Use Read-Only Connection for Analysis

Create a second connection with read-only access:

```sql
-- As admin, create read-only role
CREATE ROLE voyce_readonly;
GRANT CONNECT ON DATABASE databricks_postgres TO voyce_readonly;
GRANT USAGE ON SCHEMA public TO voyce_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO voyce_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO voyce_readonly;

-- Create read-only user
CREATE USER analyst WITH PASSWORD 'secure_password';
GRANT voyce_readonly TO analyst;
```

### 2. Use Transactions for Bulk Updates

```sql
BEGIN;

-- Make changes
UPDATE voice_submissions
SET status = 'processed'
WHERE id IN (1, 2, 3);

-- Verify
SELECT * FROM voice_submissions WHERE id IN (1, 2, 3);

-- Commit or rollback
COMMIT;  -- or ROLLBACK;
```

### 3. Set Query Timeout

Prevent long-running queries:

1. **Preferences** → **Editors** → **SQL Editor**
2. Set **Query timeout**: 60 seconds

### 4. Enable Auto-Commit (Careful!)

For quick testing only:

1. **Database** → **Transaction Mode** → **Auto-commit**

⚠️ **Warning**: Changes are immediately saved!

---

## Useful SQL Queries

### Voice Submission Analytics

```sql
-- Daily submission counts
SELECT
    DATE(created_at) as date,
    COUNT(*) as submissions,
    COUNT(DISTINCT user_id) as unique_users
FROM voice_submissions
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Sentiment distribution
SELECT
    sentiment,
    COUNT(*) as count,
    ROUND(AVG(score), 2) as avg_score
FROM ai_analysis
GROUP BY sentiment;

-- Processing costs
SELECT
    DATE(created_at) as date,
    SUM(whisper_cost + claude_cost + databricks_cost) as total_cost,
    COUNT(*) as submissions,
    ROUND(SUM(whisper_cost + claude_cost + databricks_cost) / COUNT(*), 4) as cost_per_submission
FROM processing_costs
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Data Quality Checks

```sql
-- Find submissions without transcriptions
SELECT vs.id, vs.created_at, vs.status
FROM voice_submissions vs
LEFT JOIN transcriptions t ON vs.id = t.submission_id
WHERE t.id IS NULL
AND vs.created_at < NOW() - INTERVAL '1 hour';

-- Find transcriptions with low confidence
SELECT
    t.submission_id,
    t.engine,
    t.confidence,
    t.text
FROM transcriptions t
WHERE t.confidence < 0.7
ORDER BY t.confidence ASC;

-- Check for duplicate submissions
SELECT
    user_id,
    DATE_TRUNC('minute', created_at) as minute,
    COUNT(*) as count
FROM voice_submissions
GROUP BY user_id, DATE_TRUNC('minute', created_at)
HAVING COUNT(*) > 1;
```

---

## DBeaver Extensions (Optional)

### 1. ER Diagram Plugin

For better visualizations:

1. **Help** → **Install New Software**
2. Search for "ERD"
3. Install ER Diagram plugin

### 2. Git Integration

Version control for SQL scripts:

1. **Help** → **Install New Software**
2. Search for "Git"
3. Install Git integration

---

## Summary

**Setup Time**: 5 minutes
**Connection Type**: SSL-required PostgreSQL
**Authentication**: Username/password (can use .pgpass)
**Database**: Databricks-hosted PostgreSQL 15

**Connection Details**:
```
Host: instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com
Port: 5432
Database: databricks_postgres
SSL Mode: require
```

**Next Steps**:
1. ✅ Connect DBeaver
2. Explore schema and tables
3. Run analytics queries
4. Set up data export jobs (optional)
5. Create SQL templates for common queries

---

**Enjoy querying your voice feedback data!** 📊
