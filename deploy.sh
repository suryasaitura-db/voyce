#!/bin/bash
# Deployment script for Voyce application

set -e

echo "Voyce Deployment Script"
echo "======================="

# Check if Databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "Error: Databricks CLI is not installed"
    echo "Install with: pip install databricks-cli"
    exit 1
fi

# Verify DEFAULT profile exists
if ! databricks configure --token --profile DEFAULT 2>/dev/null; then
    echo "Warning: DEFAULT profile may not be configured"
    echo "Please ensure ~/.databrickscfg has [DEFAULT] profile"
fi

# Parse arguments
ENVIRONMENT=${1:-dev}

echo ""
echo "Deploying to environment: $ENVIRONMENT"
echo "Using Databricks profile: DEFAULT"
echo ""

# Validate bundle configuration
echo "Validating Databricks bundle..."
databricks bundle validate -t $ENVIRONMENT

# Deploy to Databricks
echo "Deploying to Databricks..."
databricks bundle deploy -t $ENVIRONMENT

echo ""
echo "Deployment completed successfully!"
echo "Environment: $ENVIRONMENT"
echo ""
