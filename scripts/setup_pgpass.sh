#!/bin/bash
#
# Setup .pgpass file for Databricks PostgreSQL authentication
# This allows passwordless connection to PostgreSQL instance
#

set -e

echo "🔐 Setting up .pgpass for Databricks PostgreSQL"
echo ""

# Check if PGPASSWORD is set
if [ -z "$PGPASSWORD" ]; then
    echo "⚠️  PGPASSWORD environment variable is not set"
    echo ""
    echo "Please enter your Databricks PostgreSQL password:"
    read -s PGPASSWORD
    echo ""
fi

# Databricks PostgreSQL instance details
PG_HOST="instance-099dd8fa-7b2c-4a8f-b255-3d1534bcc58b.database.cloud.databricks.com"
PG_PORT="5432"
PG_DATABASE="databricks_postgres"
PG_USER="suryasai.turaga@databricks.com"

# Create .pgpass file
PGPASS_FILE="$HOME/.pgpass"
BACKUP_FILE="$HOME/.pgpass.backup.$(date +%Y%m%d_%H%M%S)"

# Backup existing .pgpass if it exists
if [ -f "$PGPASS_FILE" ]; then
    echo "📋 Backing up existing .pgpass to $BACKUP_FILE"
    cp "$PGPASS_FILE" "$BACKUP_FILE"
fi

# Create new .pgpass entry
echo "✍️  Writing .pgpass file..."
echo "${PG_HOST}:${PG_PORT}:${PG_DATABASE}:${PG_USER}:${PGPASSWORD}" > "$PGPASS_FILE"

# Set correct permissions (required by PostgreSQL)
chmod 600 "$PGPASS_FILE"

echo "✅ .pgpass file created successfully"
echo ""
echo "File location: $PGPASS_FILE"
echo "Permissions: $(ls -l $PGPASS_FILE | awk '{print $1}')"
echo ""

# Test connection
echo "🔍 Testing connection..."
if command -v psql &> /dev/null; then
    if psql "postgresql://${PG_USER}@${PG_HOST}:${PG_PORT}/${PG_DATABASE}?sslmode=require" -c "SELECT version();" &> /dev/null; then
        echo "✅ Connection successful!"
        psql "postgresql://${PG_USER}@${PG_HOST}:${PG_PORT}/${PG_DATABASE}?sslmode=require" -c "SELECT version();" | head -3
    else
        echo "❌ Connection failed. Please check your password."
        exit 1
    fi
else
    echo "⚠️  psql not found. Install PostgreSQL client to test connection:"
    echo "   brew install postgresql@15"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "You can now connect without password:"
echo "   psql \"postgresql://${PG_USER}@${PG_HOST}:${PG_PORT}/${PG_DATABASE}?sslmode=require\""
