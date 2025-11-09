#!/usr/bin/env python3
"""
Utility script for running data synchronization operations.
Can be used for manual sync, testing, or maintenance tasks.
"""
import asyncio
import argparse
import logging
from datetime import datetime
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_sync(
    sync_type: str = "bidirectional",
    incremental: bool = True,
    force_full: bool = False,
    batch_size: int = 1000
):
    """
    Run data synchronization.

    Args:
        sync_type: Type of sync ('submissions', 'analyses', 'bidirectional')
        incremental: Only sync new/updated records
        force_full: Force full sync
        batch_size: Number of records per batch
    """
    from services.sync_service import get_sync_service

    logger.info(f"Starting sync: type={sync_type}, incremental={incremental}")

    # Get sync service
    sync_service = await get_sync_service(batch_size=batch_size)

    try:
        if sync_type == "submissions":
            # Sync submissions to Databricks
            result = await sync_service.sync_submissions_to_databricks(
                incremental=incremental,
                force_full_sync=force_full
            )
            logger.info(f"Submissions sync completed: {result}")

        elif sync_type == "analyses":
            # Sync analyses to PostgreSQL
            result = await sync_service.sync_analyses_to_postgres(
                incremental=incremental,
                force_full_sync=force_full
            )
            logger.info(f"Analyses sync completed: {result}")

        elif sync_type == "bidirectional":
            # Full bidirectional sync
            result = await sync_service.full_bidirectional_sync()
            logger.info(f"Bidirectional sync completed: {result}")

        else:
            raise ValueError(f"Invalid sync_type: {sync_type}")

        return result

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise


async def validate_sync():
    """Validate sync by comparing record counts."""
    from services.sync_service import get_sync_service

    logger.info("Running sync validation")

    sync_service = await get_sync_service()
    validation = await sync_service.validate_sync()

    logger.info("Validation results:")
    for table, result in validation.items():
        if isinstance(result, dict):
            in_sync = result.get("in_sync", False)
            pg_count = result.get("postgresql_count", 0)
            db_count = result.get("databricks_count", 0)

            status = "✓ IN SYNC" if in_sync else "✗ OUT OF SYNC"
            logger.info(f"{table}: {status}")
            logger.info(f"  PostgreSQL: {pg_count:,} records")
            logger.info(f"  Databricks: {db_count:,} records")

            if not in_sync:
                logger.warning(f"  Difference: {abs(pg_count - db_count):,} records")

    return validation


async def get_sync_status():
    """Get current sync status and statistics."""
    from services.sync_service import get_sync_service

    logger.info("Getting sync status")

    sync_service = await get_sync_service()
    status = await sync_service.get_sync_status()

    logger.info("Current stats:")
    for key, value in status.get("current_stats", {}).items():
        logger.info(f"  {key}: {value}")

    logger.info("\nRecent sync history:")
    for sync in status.get("sync_history", [])[:5]:
        logger.info(
            f"  {sync['sync_type']:20s} | {sync['table_name']:20s} | "
            f"{sync['sync_status']:10s} | {sync['records_synced']:6d} records | "
            f"{sync['sync_duration_seconds']:.2f}s"
        )

    return status


async def initialize_tables():
    """Initialize Databricks tables."""
    from services.sync_service import get_sync_service

    logger.info("Initializing Databricks tables")

    sync_service = await get_sync_service()
    await sync_service.initialize()

    logger.info("Tables initialized successfully")


async def optimize_tables():
    """Optimize Databricks Delta tables."""
    from services.databricks_client import get_databricks_client

    logger.info("Optimizing Databricks tables")

    client = get_databricks_client()

    # Optimize voice_submissions
    logger.info("Optimizing voice_submissions")
    client.optimize_table(
        "voice_submissions",
        z_order_by=["user_id", "created_at"]
    )

    # Optimize ai_analyses
    logger.info("Optimizing ai_analyses")
    client.optimize_table(
        "ai_analyses",
        z_order_by=["submission_id", "created_at"]
    )

    logger.info("Tables optimized successfully")


async def vacuum_tables(retention_hours: int = 168):
    """Vacuum Databricks Delta tables to remove old files."""
    from services.databricks_client import get_databricks_client

    logger.info(f"Vacuuming tables (retention: {retention_hours}h)")

    client = get_databricks_client()

    # Vacuum voice_submissions
    logger.info("Vacuuming voice_submissions")
    client.vacuum_table("voice_submissions", retention_hours=retention_hours)

    # Vacuum ai_analyses
    logger.info("Vacuuming ai_analyses")
    client.vacuum_table("ai_analyses", retention_hours=retention_hours)

    logger.info("Tables vacuumed successfully")


async def get_table_stats():
    """Get statistics for Databricks tables."""
    from services.databricks_client import get_databricks_client

    logger.info("Getting table statistics")

    client = get_databricks_client()

    # Get voice_submissions stats
    logger.info("\nvoice_submissions:")
    stats = client.get_table_stats("voice_submissions")
    logger.info(f"  Row count: {stats['row_count']:,}")

    # Get ai_analyses stats
    logger.info("\nai_analyses:")
    stats = client.get_table_stats("ai_analyses")
    logger.info(f"  Row count: {stats['row_count']:,}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Data Synchronization Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run incremental bidirectional sync
  python run_sync.py sync --type bidirectional

  # Run full sync of submissions to Databricks
  python run_sync.py sync --type submissions --full

  # Validate sync
  python run_sync.py validate

  # Get sync status
  python run_sync.py status

  # Initialize tables
  python run_sync.py init

  # Optimize Delta tables
  python run_sync.py optimize

  # Get table statistics
  python run_sync.py stats
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Run data synchronization")
    sync_parser.add_argument(
        "--type",
        choices=["submissions", "analyses", "bidirectional"],
        default="bidirectional",
        help="Type of sync to run"
    )
    sync_parser.add_argument(
        "--full",
        action="store_true",
        help="Force full sync (non-incremental)"
    )
    sync_parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for processing"
    )

    # Validate command
    subparsers.add_parser("validate", help="Validate sync status")

    # Status command
    subparsers.add_parser("status", help="Get sync status and statistics")

    # Initialize command
    subparsers.add_parser("init", help="Initialize Databricks tables")

    # Optimize command
    subparsers.add_parser("optimize", help="Optimize Delta tables")

    # Vacuum command
    vacuum_parser = subparsers.add_parser("vacuum", help="Vacuum Delta tables")
    vacuum_parser.add_argument(
        "--retention-hours",
        type=int,
        default=168,
        help="Retention period in hours (default: 168 = 7 days)"
    )

    # Stats command
    subparsers.add_parser("stats", help="Get table statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Run command
    try:
        if args.command == "sync":
            asyncio.run(run_sync(
                sync_type=args.type,
                incremental=not args.full,
                force_full=args.full,
                batch_size=args.batch_size
            ))

        elif args.command == "validate":
            asyncio.run(validate_sync())

        elif args.command == "status":
            asyncio.run(get_sync_status())

        elif args.command == "init":
            asyncio.run(initialize_tables())

        elif args.command == "optimize":
            asyncio.run(optimize_tables())

        elif args.command == "vacuum":
            asyncio.run(vacuum_tables(retention_hours=args.retention_hours))

        elif args.command == "stats":
            asyncio.run(get_table_stats())

        logger.info("\n✓ Command completed successfully")

    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"\n✗ Command failed: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
