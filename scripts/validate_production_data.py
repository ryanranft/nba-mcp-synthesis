#!/usr/bin/env python3
"""
NBA MCP Synthesis - Production Data Quality Validation CLI
Command-line tool for validating NBA database data quality
"""

import asyncio
import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_quality.workflows import (
    validate_nba_database,
    validate_recent_data,
    get_data_quality_report,
    ProductionDataQualityWorkflow
)
from data_quality.validator import DataValidator
from data_quality.expectations import (
    create_game_expectations,
    create_player_expectations,
    create_team_expectations
)


def print_banner():
    """Print CLI banner"""
    print("=" * 80)
    print("NBA MCP Synthesis - Data Quality Validation Tool")
    print("=" * 80)
    print("")


def print_validation_summary(summary: Dict[str, Any]):
    """Print formatted validation summary"""
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    if "tables_validated" in summary:
        # Full database validation
        print(f"\nTimestamp: {summary.get('timestamp', 'N/A')}")
        print(f"Tables Validated: {summary.get('tables_validated', 0)}")
        print(f"Tables Passed: {summary.get('tables_passed', 0)}")
        print(f"Tables Failed: {summary.get('tables_failed', 0)}")
        print(f"Overall Pass Rate: {summary.get('overall_pass_rate', 0)*100:.1f}%")

        if summary.get('failed_tables'):
            print("\n⚠️  TABLES WITH ISSUES:")
            for failure in summary['failed_tables']:
                table = failure['table']
                if 'pass_rate' in failure:
                    print(f"  • {table}: {failure['pass_rate']*100:.1f}% pass rate "
                          f"({failure['failed_count']} failed expectations)")
                else:
                    print(f"  • {table}: Error - {failure.get('error', 'Unknown')}")
        else:
            print("\n✅ All tables passed validation!")

    else:
        # Single table validation
        print(f"\nTable: {summary.get('table_name', 'N/A')}")
        print(f"Rows Validated: {summary.get('rows_validated', 0)}")
        print(f"Validation Time: {summary.get('validation_time', 'N/A')}")

        if 'summary' in summary:
            s = summary['summary']
            print(f"\nExpectations:")
            print(f"  Total: {s.get('total_expectations', 0)}")
            print(f"  Passed: {s.get('passed', 0)}")
            print(f"  Failed: {s.get('failed', 0)}")
            print(f"  Pass Rate: {s.get('pass_rate', 0)*100:.1f}%")

        if summary.get('failed_expectations'):
            print("\n⚠️  FAILED EXPECTATIONS:")
            for failure in summary['failed_expectations']:
                print(f"  • {failure.get('expectation', 'Unknown')} on column '{failure.get('column', 'N/A')}'")
                if 'error' in failure:
                    print(f"    Error: {failure['error']}")

    print("\n" + "=" * 80)


async def cmd_validate_all(args):
    """Validate entire database"""
    print("Running full database validation...")
    print("This may take a few minutes...\n")

    summary = await validate_nba_database()
    print_validation_summary(summary)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n✅ Results saved to: {output_path}")

    # Exit with error code if validations failed
    if summary.get('tables_failed', 0) > 0:
        return 1
    return 0


async def cmd_validate_table(args):
    """Validate specific table"""
    print(f"Validating table: {args.table}...")

    workflow = ProductionDataQualityWorkflow()
    result = await workflow.validator.validate_table(args.table)

    print_validation_summary(result)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\n✅ Results saved to: {output_path}")

    # Exit with error code if validation failed
    if result.get('summary', {}).get('failed', 0) > 0:
        return 1
    return 0


async def cmd_validate_incremental(args):
    """Validate only recent data"""
    print(f"Running incremental validation for: {args.table}")
    print(f"Filter: {args.where}\n")

    result = await validate_recent_data(args.table, args.where)
    print_validation_summary(result)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\n✅ Results saved to: {output_path}")

    # Exit with error code if validation failed
    if result.get('summary', {}).get('failed', 0) > 0:
        return 1
    return 0


async def cmd_report(args):
    """Get data quality report"""
    print(f"Retrieving data quality report (last {args.days} days)...\n")

    report = await get_data_quality_report(days=args.days)

    print(json.dumps(report, indent=2, default=str))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n✅ Report saved to: {output_path}")

    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NBA MCP Synthesis - Data Quality Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate entire database
  %(prog)s all

  # Validate specific table
  %(prog)s table games

  # Validate recent data only
  %(prog)s incremental games --where "game_date > '2024-01-01'"

  # Get data quality report
  %(prog)s report --days 7

  # Save results to file
  %(prog)s all --output validation_results.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Validate all command
    parser_all = subparsers.add_parser('all', help='Validate entire database')
    parser_all.add_argument('-o', '--output', help='Save results to JSON file')
    parser_all.set_defaults(func=cmd_validate_all)

    # Validate table command
    parser_table = subparsers.add_parser('table', help='Validate specific table')
    parser_table.add_argument('table', help='Table name to validate')
    parser_table.add_argument('-o', '--output', help='Save results to JSON file')
    parser_table.set_defaults(func=cmd_validate_table)

    # Incremental validation command
    parser_incr = subparsers.add_parser('incremental', help='Validate recent data only')
    parser_incr.add_argument('table', help='Table name to validate')
    parser_incr.add_argument('-w', '--where', required=True,
                            help='SQL WHERE clause for filtering data')
    parser_incr.add_argument('-o', '--output', help='Save results to JSON file')
    parser_incr.set_defaults(func=cmd_validate_incremental)

    # Report command
    parser_report = subparsers.add_parser('report', help='Get data quality report')
    parser_report.add_argument('-d', '--days', type=int, default=7,
                               help='Number of days of history (default: 7)')
    parser_report.add_argument('-o', '--output', help='Save report to JSON file')
    parser_report.set_defaults(func=cmd_report)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Print banner
    print_banner()

    # Run command
    try:
        exit_code = asyncio.run(args.func(args))
        return exit_code

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
