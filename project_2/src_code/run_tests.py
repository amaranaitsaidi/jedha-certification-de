"""
Test Runner Script
==================
Script pour exécuter facilement les tests avec différentes options.

Usage:
    python run_tests.py                  # Tous les tests
    python run_tests.py --quality        # Tests de qualité uniquement
    python run_tests.py --unit           # Tests unitaires uniquement
    python run_tests.py --report         # Générer rapport HTML
    python run_tests.py --coverage       # Avec couverture de code
    python run_tests.py --fast           # Tests rapides uniquement
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, description: str):
    """
    Exécuter une commande et afficher le résultat.

    Args:
        cmd: Liste des arguments de la commande
        description: Description de la commande
    """
    print(f"\n{'=' * 70}")
    print(f"{description}")
    print(f"{'=' * 70}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    return result.returncode


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Run tests for Amazon Reviews ETL Pipeline"
    )

    parser.add_argument(
        '--quality',
        action='store_true',
        help='Run data quality tests only'
    )

    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run unit tests only'
    )

    parser.add_argument(
        '--fast',
        action='store_true',
        help='Run fast tests only (exclude slow tests)'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate HTML report'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run tests in parallel'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Base pytest command
    cmd = ['pytest', 'tests/']

    # Add markers
    if args.quality:
        cmd.extend(['-m', 'quality'])
    elif args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.fast:
        cmd.extend(['-m', 'not slow'])

    # Add verbosity
    if args.verbose:
        cmd.append('-v')

    # Add HTML report
    if args.report:
        cmd.extend(['--html=reports/pytest_report.html', '--self-contained-html'])

    # Add coverage
    if args.coverage:
        cmd.extend([
            '--cov=scripts',
            '--cov-report=html',
            '--cov-report=term'
        ])

    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', 'auto'])

    # Determine description
    if args.quality:
        description = "Running Data Quality Tests"
    elif args.unit:
        description = "Running Unit Tests"
    elif args.fast:
        description = "Running Fast Tests"
    else:
        description = "Running All Tests"

    # Run tests
    return_code = run_command(cmd, description)

    # Print summary
    print(f"\n{'=' * 70}")
    if return_code == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print(f"{'=' * 70}\n")

    if args.report:
        report_path = Path(__file__).parent / 'reports' / 'pytest_report.html'
        if report_path.exists():
            print(f"HTML Report: {report_path}")

    if args.coverage:
        coverage_path = Path(__file__).parent / 'htmlcov' / 'index.html'
        if coverage_path.exists():
            print(f"Coverage Report: {coverage_path}")

    return return_code


if __name__ == "__main__":
    sys.exit(main())
