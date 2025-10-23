#!/usr/bin/env python3
"""
Test Phase Skip Fix

Verifies that phases 5-8 can be properly skipped and phase 8.5
can start with skipped prerequisites.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phase_status_manager import PhaseStatusManager, PhaseState

def test_phase_skip_fix():
    """Test that skipped phases satisfy prerequisites."""

    print("🧪 Testing Phase Skip Fix\n")
    print("="*60)

    # Create a temporary status manager
    status_mgr = PhaseStatusManager()

    # Simulate completed phases up to phase 4
    print("1. Setting up phases 0-4 as completed...")
    for phase_id in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_3_5", "phase_4"]:
        if phase_id in status_mgr.phases:
            status_mgr.phases[phase_id].state = PhaseState.COMPLETED
            print(f"   ✅ {phase_id} = COMPLETED")

    print("\n2. Skipping manual phases 5-8...")
    status_mgr.skip_phase("phase_5", "Test: Dry-run validation - manual phase")
    status_mgr.skip_phase("phase_6", "Test: Conflict resolution - manual phase")
    status_mgr.skip_phase("phase_7", "Test: Manual review - manual phase")
    status_mgr.skip_phase("phase_8", "Test: Implementation - manual phase")

    # Verify phases are marked as skipped
    print("\n3. Verifying phases are marked as SKIPPED...")
    all_skipped = True
    for phase_id in ["phase_5", "phase_6", "phase_7", "phase_8"]:
        phase = status_mgr.phases.get(phase_id)
        if phase and phase.state == PhaseState.SKIPPED:
            print(f"   ✅ {phase_id} = SKIPPED")
        else:
            print(f"   ❌ {phase_id} = {phase.state if phase else 'NOT FOUND'}")
            all_skipped = False

    # Try to start phase 8.5 (should work now)
    print("\n4. Testing phase 8.5 can start with skipped prerequisites...")
    try:
        status_mgr.start_phase("phase_8_5", "Phase 8.5: Pre-Integration Validation")
        print("   ✅ Phase 8.5 started successfully!")

        # Check prerequisites
        unmet_prereqs = status_mgr._check_prerequisites("phase_8_5")
        if not unmet_prereqs:
            print("   ✅ All prerequisites satisfied (skipped phases count as satisfied)")
        else:
            print(f"   ❌ Unmet prerequisites: {unmet_prereqs}")
            return False

    except ValueError as e:
        print(f"   ❌ Failed to start phase 8.5: {e}")
        return False

    print("\n" + "="*60)
    if all_skipped:
        print("✅ TEST PASSED: Phase skip fix is working correctly!")
        print("\nKey findings:")
        print("- Phases 5-8 can be marked as SKIPPED")
        print("- SKIPPED phases satisfy prerequisites")
        print("- Phase 8.5 can start after phases 5-8 are skipped")
        return True
    else:
        print("❌ TEST FAILED: Some phases were not properly skipped")
        return False

if __name__ == "__main__":
    success = test_phase_skip_fix()
    sys.exit(0 if success else 1)







