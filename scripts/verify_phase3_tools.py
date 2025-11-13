#!/usr/bin/env python3
"""
Phase 3 Tools Verification Script

Quick verification that all Phase 3 tools are functional.
Run with: python scripts/verify_phase3_tools.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".claude", "task_tracker"),
)

from task_tracker_mcp import (
    create_task,
    bulk_update_status,
    bulk_update_priority,
    bulk_add_tags,
    list_templates,
    get_template_details,
    get_velocity_metrics,
    get_bottlenecks,
    list_tasks,
    get_db_connection,
)


def print_header(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def verify_bulk_operations():
    """Verify bulk operation tools."""
    print_header("BULK OPERATIONS VERIFICATION")

    # Create test tasks
    print("Creating 3 test tasks...")
    task_ids = []
    for i in range(3):
        result = create_task(
            content=f"VERIFY: Test task {i+1}",
            active_form=f"Verifying task {i+1}",
            priority="low",
        )
        if result["success"]:
            task_ids.append(result["task"]["id"])
            print(f"  ✅ Created task #{result['task']['id']}")
        else:
            print(f"  ❌ Failed to create task {i+1}")
            return False

    # Test bulk status update
    print("\nTesting bulk_update_status...")
    result = bulk_update_status(task_ids, "completed")
    if result["success"]:
        print(f"  ✅ Updated {result['updated_count']} tasks to 'completed'")
    else:
        print(f"  ❌ Bulk status update failed: {result.get('error', 'Unknown error')}")
        return False

    # Test bulk priority update
    print("\nTesting bulk_update_priority...")
    result = bulk_update_priority(task_ids, "high")
    if result["success"]:
        print(f"  ✅ Updated {result['updated_count']} tasks to 'high' priority")
    else:
        print(f"  ❌ Bulk priority update failed")
        return False

    # Test bulk add tags
    print("\nTesting bulk_add_tags...")
    result = bulk_add_tags(task_ids, ["verification", "automated"])
    if result["success"]:
        print(f"  ✅ Added tags to {result['updated_count']} tasks")
    else:
        print(f"  ❌ Bulk add tags failed")
        return False

    # Cleanup
    print("\nCleaning up test tasks...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE content LIKE 'VERIFY:%'")
    conn.commit()
    print("  ✅ Cleanup complete")

    return True


def verify_templates():
    """Verify template system."""
    print_header("TEMPLATE SYSTEM VERIFICATION")

    # List templates
    print("Testing list_templates...")
    result = list_templates()
    if result["success"]:
        count = len(result["templates"])
        print(f"  ✅ Found {count} templates")
        print("\n  Available templates:")
        for template in result["templates"][:3]:  # Show first 3
            print(f"    - {template['name']} ({template['usage_count']} uses)")
        if count > 3:
            print(f"    ... and {count - 3} more")
    else:
        print(f"  ❌ List templates failed")
        return False

    # Get template details
    print("\nTesting get_template_details...")
    result = get_template_details("Bug Fix")
    if result["success"]:
        template = result["template"]
        task_count = (
            len(template["task_definitions"]) if "task_definitions" in template else 0
        )
        print(f"  ✅ Retrieved template: {template['name']}")
        print(f"    Description: {template['description']}")
        print(f"    Tasks in template: {task_count}")
        print(f"    Usage count: {template['usage_count']}")
    else:
        print(f"  ❌ Get template details failed")
        return False

    return True


def verify_analytics():
    """Verify analytics tools."""
    print_header("ANALYTICS TOOLS VERIFICATION")

    # Test velocity metrics
    print("Testing get_velocity_metrics...")
    result = get_velocity_metrics(days=30)
    if result["success"]:
        velocity = result["velocity"]
        trend = result["trend"]
        print(f"  ✅ Velocity metrics calculated")
        print(f"    Tasks/day: {velocity['tasks_per_day']}")
        print(f"    Tasks/week: {velocity['tasks_per_week']}")
        print(f"    Trend: {trend['direction']} ({trend['percentage_change']:+.1f}%)")
    else:
        print(f"  ❌ Velocity metrics failed")
        return False

    # Test bottleneck detection
    print("\nTesting get_bottlenecks...")
    result = get_bottlenecks(min_days_stale=7)
    if result["success"]:
        bottlenecks = result["bottlenecks"]
        print(f"  ✅ Bottleneck analysis complete")
        print(f"    Severity: {result['severity']}")
        print(f"    Stale tasks: {bottlenecks['stale_tasks']['count']}")
        print(f"    Blocked tasks: {bottlenecks['blocked_tasks']['count']}")
        print(f"    Complex tasks: {bottlenecks['complex_tasks']['count']}")
    else:
        print(f"  ❌ Bottleneck detection failed")
        return False

    return True


def verify_smart_filters():
    """Verify smart filtering."""
    print_header("SMART FILTERS VERIFICATION")

    # Test basic listing
    print("Testing list_tasks (basic)...")
    result = list_tasks()
    if result["success"]:
        print(f"  ✅ Retrieved {result['pagination']['total_count']} tasks")
    else:
        print(f"  ❌ List tasks failed")
        return False

    # Test with priority filter
    print("\nTesting list_tasks (with priority filter)...")
    result = list_tasks(priority="high")
    if result["success"]:
        print(f"  ✅ Found {result['pagination']['total_count']} high-priority tasks")
    else:
        print(f"  ❌ Priority filter failed")
        return False

    # Test with status filter
    print("\nTesting list_tasks (with status filter)...")
    result = list_tasks(status="pending")
    if result["success"]:
        print(f"  ✅ Found {result['pagination']['total_count']} pending tasks")
    else:
        print(f"  ❌ Status filter failed")
        return False

    return True


def main():
    """Run all verifications."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "PHASE 3 TOOLS VERIFICATION" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")

    results = {}

    # Run verifications
    results["bulk_ops"] = verify_bulk_operations()
    results["templates"] = verify_templates()
    results["analytics"] = verify_analytics()
    results["filters"] = verify_smart_filters()

    # Print summary
    print_header("VERIFICATION SUMMARY")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for category, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {category.replace('_', ' ').title()}")

    print(f"\n  Total: {passed}/{total} checks passed ({(passed/total)*100:.0f}%)")

    if failed == 0:
        print("\n  🎉 ALL PHASE 3 TOOLS VERIFIED FUNCTIONAL! 🎉")
        return 0
    else:
        print(f"\n  ⚠️  {failed} verification(s) failed")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Verification error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
