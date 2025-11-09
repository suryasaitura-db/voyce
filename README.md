# Voyce

A Databricks-powered application.

## Prerequisites

- Python 3.9+
- Databricks CLI configured with [DEFAULT] profile
- Access to Databricks workspace

## Configuration

This project uses the Databricks [DEFAULT] profile for all operations. Ensure your `~/.databrickscfg` is configured:

```ini
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = your-token-here
```

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/suryasai87/voyce.git
   cd voyce
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

5. Update `.env` with your configuration

6. Run locally:
   ```bash
   python main.py
   ```

   The application will be available at `http://localhost:8000`

## Databricks Deployment

The project uses Databricks Asset Bundles with serverless compute and SQL serverless where possible.

### Deploy to Databricks:

```bash
databricks bundle deploy -t dev
```

### Run jobs:

```bash
databricks bundle run -t dev
```

## Project Structure

```
voyce/
├── src/                    # Source code
├── notebooks/              # Databricks notebooks
├── config/                 # Configuration files
├── tests/                  # Test files
├── databricks.yml          # Databricks Asset Bundle config
├── requirements.txt        # Python dependencies
└── main.py                # Application entry point
```

## Technology Stack

- Databricks Runtime: Latest (15.4.x+)
- Serverless Compute: Enabled
- SQL Serverless: Enabled for analytics workloads
- Python: 3.9+

## Development Workflow

1. Develop and test locally on `http://localhost:8000`
2. Commit changes to Git
3. Deploy to Databricks dev environment
4. Test in Databricks
5. Promote to production

## License

MIT
