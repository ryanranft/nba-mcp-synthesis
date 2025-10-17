#!/usr/bin/env python3
"""
Test Workflow Automation System
Verifies all components work correctly
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

print("=" * 70)
print("NBA MCP Synthesis - Workflow System Test")
print("=" * 70)
print()

# Test 1: Import all modules
print("1. Testing module imports...")
try:
    from monitoring.slack_notifier import (
        SlackNotifier,
        ProcessEvent,
        ProcessStatus,
        ProcessSource,
        get_notifier,
        notify_process_started,
        notify_process_completed,
    )

    print("   ✅ slack_notifier imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import slack_notifier: {e}")
    sys.exit(1)

try:
    from workflow.engine import (
        WorkflowEngine,
        Workflow,
        WorkflowStep,
        StepStatus,
        WorkflowStatus,
        get_engine,
    )

    print("   ✅ workflow.engine imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import workflow.engine: {e}")
    sys.exit(1)

try:
    from workflow.triggers import (
        WorkflowTrigger,
        TriggerType,
        TriggerEvent,
        get_trigger_manager,
    )

    print("   ✅ workflow.triggers imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import workflow.triggers: {e}")
    sys.exit(1)

try:
    from synthesis.workflow_hooks import (
        with_workflow_notifications,
        notify_synthesis_complete,
        notify_mcp_tool_complete,
        notify_test_complete,
    )

    print("   ✅ workflow_hooks imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import workflow_hooks: {e}")
    sys.exit(1)

print()

# Test 2: Create notifier (without webhook, should use fallback)
print("2. Testing Slack notifier creation...")
try:
    notifier = SlackNotifier()  # Should work even without webhook URL
    print(
        f"   ✅ Notifier created (webhook configured: {notifier.webhook_url is not None})"
    )
except Exception as e:
    print(f"   ❌ Failed to create notifier: {e}")
    sys.exit(1)

print()

# Test 3: Create workflow engine
print("3. Testing workflow engine creation...")
try:
    engine = WorkflowEngine()
    print(f"   ✅ Engine created (state dir: {engine.state_dir})")
    print(f"   ✅ Built-in actions registered: {len(engine.action_registry)}")
except Exception as e:
    print(f"   ❌ Failed to create engine: {e}")
    sys.exit(1)

print()

# Test 4: Create trigger manager
print("4. Testing trigger manager...")
try:
    trigger_mgr = get_trigger_manager()
    print(f"   ✅ Trigger manager created")
    print(f"   ✅ Trigger handlers: {len(trigger_mgr.trigger_handlers)}")
except Exception as e:
    print(f"   ❌ Failed to create trigger manager: {e}")
    sys.exit(1)

print()

# Test 5: Load YAML workflows
print("5. Testing YAML workflow loading...")
yaml_files = [
    "workflows/automated_testing_pipeline.yaml",
    "workflows/nba_data_synthesis.yaml",
    "workflows/cross_chat_coordination.yaml",
]

for yaml_file in yaml_files:
    try:
        if os.path.exists(yaml_file):
            workflow = engine.load_workflow_from_yaml(yaml_file)
            print(
                f"   ✅ Loaded {os.path.basename(yaml_file)}: {len(workflow.steps)} steps"
            )
        else:
            print(f"   ⚠️  File not found: {yaml_file}")
    except Exception as e:
        print(f"   ❌ Failed to load {yaml_file}: {e}")

print()

# Test 6: Create and execute simple workflow
print("6. Testing workflow execution...")


async def test_workflow_execution():
    try:
        # Register test action
        async def test_action(message: str):
            await asyncio.sleep(0.1)  # Simulate work
            return {"status": "success", "message": message}

        engine.register_action("test_action", test_action)

        # Create simple workflow
        workflow = Workflow(
            workflow_id="test-workflow",
            name="Test Workflow",
            description="Simple test workflow",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    description="First test step",
                    action="test_action",
                    params={"message": "Hello from step 1"},
                    timeout_seconds=10,
                ),
                WorkflowStep(
                    name="Step 2",
                    description="Second test step",
                    action="test_action",
                    params={"message": "Hello from step 2"},
                    timeout_seconds=10,
                ),
                WorkflowStep(
                    name="Step 3 (with delay)",
                    description="Built-in delay action",
                    action="delay",
                    params={"seconds": 0.5},
                    timeout_seconds=10,
                ),
            ],
            source=ProcessSource.WORKFLOW_ENGINE,
            notify_slack=False,  # Disable Slack for test
            save_state=False,  # Disable state saving for test
        )

        # Execute workflow
        success = await engine.execute_workflow(workflow)

        if success:
            print(f"   ✅ Workflow executed successfully")
            print(f"   ✅ All {len(workflow.steps)} steps completed")

            # Verify step results
            for step in workflow.steps:
                if step.status == StepStatus.COMPLETED:
                    print(f"      - {step.name}: {step.status.value}")
                else:
                    print(f"      - {step.name}: {step.status.value} (unexpected)")
            return True
        else:
            print(f"   ❌ Workflow execution failed")
            return False

    except Exception as e:
        print(f"   ❌ Workflow execution error: {e}")
        import traceback

        traceback.print_exc()
        return False


# Run async test
workflow_success = asyncio.run(test_workflow_execution())
print()

# Test 7: Test trigger events
print("7. Testing trigger events...")
try:
    trigger_mgr = get_trigger_manager()

    # Register test handler
    events_received = []

    def test_handler(event):
        events_received.append(event)

    trigger_mgr.register_trigger(TriggerType.PROCESS_COMPLETE, test_handler)

    # Emit test event
    trigger_mgr.emit_process_complete("Test Process", "test_source", {"test": "data"})

    if len(events_received) == 1:
        print(f"   ✅ Event emitted and received successfully")
        print(f"   ✅ Event type: {events_received[0].event_type.value}")
    else:
        print(f"   ❌ Expected 1 event, received {len(events_received)}")

except Exception as e:
    print(f"   ❌ Trigger event test failed: {e}")

print()

# Test 8: Test decorator
print("8. Testing workflow decorator...")


async def test_decorator():
    try:

        @with_workflow_notifications(
            "Test Process",
            ProcessSource.WORKFLOW_ENGINE,
            notify_slack=False,
            emit_events=True,
        )
        async def test_function(value: int):
            await asyncio.sleep(0.1)
            return {"result": value * 2}

        result = await test_function(value=5)

        if result["result"] == 10:
            print(f"   ✅ Decorator executed successfully")
            print(f"   ✅ Function result: {result}")
            return True
        else:
            print(f"   ❌ Unexpected result: {result}")
            return False

    except Exception as e:
        print(f"   ❌ Decorator test failed: {e}")
        return False


decorator_success = asyncio.run(test_decorator())
print()

# Summary
print("=" * 70)
print("Test Summary")
print("=" * 70)
print()

all_tests_passed = workflow_success and decorator_success

if all_tests_passed:
    print("✅ All tests passed!")
    print()
    print("Workflow automation system is ready to use.")
    print()
    print("Next steps:")
    print("1. Set SLACK_WEBHOOK_URL environment variable for Slack integration")
    print("2. Register custom actions with WorkflowEngine")
    print("3. Create workflow YAML definitions")
    print("4. Execute workflows with: python -m workflow.cli run <workflow.yaml>")
    sys.exit(0)
else:
    print("❌ Some tests failed")
    print()
    print("Please review the errors above and fix any issues.")
    sys.exit(1)
