"""
Amazon Review Data Pipeline
============================
Main orchestrator that executes the complete ETL pipeline step by step.

Usage:
    python scripts/pipeline.py --all                    # Execute all steps
    python scripts/pipeline.py --step extract          # Only extract from PostgreSQL to S3
    python scripts/pipeline.py --step setup-mongo      # Only setup MongoDB
    python scripts/pipeline.py --step setup-snowflake # Only setup Snowflake
    python scripts/pipeline.py --step process          # Only process and store data
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger(name='pipeline', log_dir='logs', level='INFO')


class PipelineOrchestrator:
    """Orchestrates the complete data pipeline."""

    def __init__(self, dry_run: bool = False):
        """
        Initialize pipeline orchestrator.

        Args:
            dry_run: If True, only simulate execution
        """
        self.dry_run = dry_run
        self.scripts_dir = Path(__file__).parent
        self.start_time = datetime.now()

        if dry_run:
            logger.info("=" * 80)
            logger.info("DRY-RUN MODE ENABLED")
            logger.info("=" * 80)

    def _run_script(self, script_name: str, description: str) -> bool:
        """
        Execute a Python script.

        Args:
            script_name: Name of the script file
            description: Human-readable description

        Returns:
            True if successful, False otherwise
        """
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return False

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"EXECUTING: {description}")
        logger.info("=" * 80)
        logger.info(f"Script: {script_name}")

        if self.dry_run:
            logger.info("[DRY-RUN] Would execute: python {script_path}")
            return True

        try:
            # Execute script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                check=False
            )

            # Log output
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(line)

            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        logger.error(line)

            # Check result
            if result.returncode == 0:
                logger.info(f"[OK] {description} completed successfully")
                return True
            else:
                logger.error(f"[FAIL] {description} failed with exit code {result.returncode}")
                return False

        except Exception as e:
            logger.error(f"[FAIL] Failed to execute {script_name}: {e}")
            return False

    def step_extract(self) -> bool:
        """Step 1: Extract data from PostgreSQL to S3."""
        return self._run_script(
            #'extract_to_s3.py',
            'extract_postgres_to_s3.py',
            'Extract raw data from PostgreSQL to S3 Data Lake'
        )

    def step_setup_mongodb(self) -> bool:
        """Step 2: Setup MongoDB collections and indexes."""
        return self._run_script(
            'setup_mongodb.py',
            'Initialize MongoDB (collections, indexes, validation)'
        )

    def step_setup_snowflake(self) -> bool:
        """Step 3: Setup Snowflake warehouse, database, and tables."""
        return self._run_script(
            'setup_snowflake.py',
            'Initialize Snowflake (database, schema, tables, views)'
        )

    def step_process(self) -> bool:
        """Step 4: Process data and store to Snowflake + MongoDB."""
        return self._run_script(
            'process_and_store.py',
            'Process reviews from S3 and store to Snowflake + MongoDB'
        )

    def run_all(self) -> bool:
        """Execute all pipeline steps in order."""
        logger.info("")
        logger.info("=" * 80)
        logger.info("         AMAZON REVIEW DATA PIPELINE")
        logger.info("=" * 80)
        logger.info("")

        steps = [
            ("extract", self.step_extract),
            ("setup-mongo", self.step_setup_mongodb),
            ("setup-snowflake", self.step_setup_snowflake),
            ("process", self.step_process)
        ]

        results = {}

        for step_name, step_func in steps:
            logger.info(f"\n[STEP {steps.index((step_name, step_func)) + 1}/{len(steps)}]")
            success = step_func()
            results[step_name] = success

            if not success:
                logger.error(f"Pipeline stopped at step: {step_name}")
                self._print_summary(results, failed_at=step_name)
                return False

        self._print_summary(results)
        return all(results.values())

    def _print_summary(self, results: dict, failed_at: str = None):
        """
        Print pipeline execution summary.

        Args:
            results: Dictionary of step results
            failed_at: Name of the step where pipeline failed
        """
        duration = datetime.now() - self.start_time
        total_steps = len(results)
        successful_steps = sum(1 for v in results.values() if v)

        logger.info("")
        logger.info("=" * 80)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration}")
        logger.info(f"Steps completed: {successful_steps}/{total_steps}")
        logger.info("")

        for step_name, success in results.items():
            status = "[OK] SUCCESS" if success else "[FAIL] FAILED"
            logger.info(f"  {step_name:20s} {status}")

        logger.info("")

        if failed_at:
            logger.info("=" * 80)
            logger.error(f"[!] PIPELINE FAILED AT: {failed_at}")
            logger.info("=" * 80)
        elif all(results.values()):
            logger.info("=" * 80)
            logger.info("[OK] PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Amazon Review Data Pipeline - Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python scripts/pipeline.py --all

  # Run specific step only
  python scripts/pipeline.py --step extract
  python scripts/pipeline.py --step setup-mongo
  python scripts/pipeline.py --step setup-snowflake
  python scripts/pipeline.py --step process

  # Dry-run mode (simulate execution)
  python scripts/pipeline.py --all --dry-run
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Execute all pipeline steps in order'
    )

    parser.add_argument(
        '--step',
        type=str,
        choices=['extract', 'setup-mongo', 'setup-snowflake', 'process'],
        help='Execute a specific step only'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate execution without running scripts'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.step:
        parser.print_help()
        logger.error("\nError: You must specify either --all or --step")
        sys.exit(1)

    if args.all and args.step:
        parser.print_help()
        logger.error("\nError: Cannot use --all and --step together")
        sys.exit(1)

    # Initialize orchestrator
    orchestrator = PipelineOrchestrator(dry_run=args.dry_run)

    # Execute
    try:
        if args.all:
            success = orchestrator.run_all()
        else:
            # Execute specific step
            step_map = {
                'extract': orchestrator.step_extract,
                'setup-mongo': orchestrator.step_setup_mongodb,
                'setup-snowflake': orchestrator.step_setup_snowflake,
                'process': orchestrator.step_process
            }

            step_func = step_map[args.step]
            success = step_func()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
