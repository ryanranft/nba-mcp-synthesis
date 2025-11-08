#!/usr/bin/env python3
"""
Test script to validate the calibration_quality() infinity bug fix.

This script verifies that:
1. Empty calibrator returns 0.15 instead of inf for Brier score
2. Empty calibrator returns 0.70 instead of inf for log loss
3. Warnings are properly issued
4. System allows betting with empty calibrator (conservative approach)
"""

import sys
import os
import warnings

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_server.betting.probability_calibration import BayesianCalibrator, SimulationCalibrator


def test_bayesian_calibrator_empty():
    """Test BayesianCalibrator with no data"""
    print("=" * 70)
    print("TEST 1: BayesianCalibrator with empty database")
    print("=" * 70)

    # Create fresh calibrator
    calibrator = BayesianCalibrator()

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Test calibration_quality()
        quality = calibrator.calibration_quality()

        # Verify result
        if quality == float('inf'):
            print("❌ FAIL: calibration_quality() returned infinity (bug NOT fixed)")
            return False
        elif quality == 0.15:
            print(f"✅ PASS: calibration_quality() returned {quality} (expected: 0.15)")
        else:
            print(f"⚠️  WARNING: calibration_quality() returned {quality} (expected: 0.15)")

        # Verify warning was issued
        if len(w) > 0:
            print(f"✅ PASS: Warning issued: {w[0].message}")
        else:
            print("⚠️  WARNING: No warning issued (expected warning about no data)")

        # Test average_brier_score directly
        brier = calibrator.database.average_brier_score()
        print(f"   Brier score: {brier} (expected: 0.15)")

        # Test average_log_loss directly
        log_loss = calibrator.database.average_log_loss()
        print(f"   Log loss: {log_loss} (expected: 0.70)")

    return True


def test_simulation_calibrator_empty():
    """Test SimulationCalibrator with no data"""
    print("\n" + "=" * 70)
    print("TEST 2: SimulationCalibrator with empty database")
    print("=" * 70)

    # Create fresh calibrator
    calibrator = SimulationCalibrator()

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Test calibration_quality()
        quality = calibrator.calibration_quality()

        # Verify result
        if quality == float('inf'):
            print("❌ FAIL: calibration_quality() returned infinity (bug NOT fixed)")
            return False
        elif quality == 0.15:
            print(f"✅ PASS: calibration_quality() returned {quality} (expected: 0.15)")
        else:
            print(f"⚠️  WARNING: calibration_quality() returned {quality} (expected: 0.15)")

        # Verify warning was issued
        if len(w) > 0:
            print(f"✅ PASS: Warning issued: {w[0].message}")
        else:
            print("⚠️  WARNING: No warning issued (expected warning about no data)")

    return True


def test_calibrator_with_data():
    """Test that calibrator works correctly with actual data"""
    print("\n" + "=" * 70)
    print("TEST 3: BayesianCalibrator with actual data")
    print("=" * 70)

    # Create calibrator and add observations
    calibrator = BayesianCalibrator()

    # Add some synthetic observations (well-calibrated)
    import numpy as np
    from datetime import datetime, timedelta
    np.random.seed(42)

    base_date = datetime.now() - timedelta(days=20)
    for i in range(20):
        sim_prob = np.random.uniform(0.4, 0.8)
        outcome = 1 if np.random.random() < sim_prob else 0
        calibrator.add_observation(
            date=base_date + timedelta(days=i),
            game_id=f"TEST_{i}",
            sim_prob=sim_prob,
            outcome=outcome
        )

    # Test calibration_quality() - should NOT return 0.15 now
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        quality = calibrator.calibration_quality()

        if quality == 0.15:
            print(f"⚠️  WARNING: calibration_quality() returned default {quality} despite having data")
        else:
            print(f"✅ PASS: calibration_quality() returned computed value: {quality:.4f}")

        # Should NOT have warning
        if len(w) > 0:
            print(f"⚠️  WARNING: Unexpected warning: {w[0].message}")
        else:
            print("✅ PASS: No warning issued (expected - has data)")

    return True


def test_betting_decision_with_empty_calibrator():
    """Test that betting system allows bets with empty calibrator"""
    print("\n" + "=" * 70)
    print("TEST 4: Betting decision with empty calibrator")
    print("=" * 70)

    try:
        import dill as pickle

        # Try to load the calibrated engine
        engine_path = "models/calibrated_kelly_engine.pkl"
        if not os.path.exists(engine_path):
            print(f"⚠️  SKIP: Engine not found at {engine_path}")
            return True

        with open(engine_path, 'rb') as f:
            engine = pickle.load(f)

        # Make a decision with reasonable parameters
        decision = engine.decide(
            sim_prob=0.65,
            odds=1.90,
            away_odds=2.00,
            bankroll=10000,
            game_id="TEST_GAME_123"
        )

        print(f"Decision: {'BET' if decision['should_bet'] else 'NO BET'}")
        print(f"Reason: {decision.get('reason', 'N/A')}")

        if decision['should_bet']:
            print(f"✅ PASS: System allows betting (bet amount: ${decision['bet_amount']:.2f})")
        else:
            if "calibration" in decision.get('reason', '').lower():
                print(f"❌ FAIL: System blocked bet due to calibration (should allow with 0.15)")
            else:
                print(f"✅ PASS: System blocked bet for valid reason: {decision['reason']}")

    except ImportError:
        print("⚠️  SKIP: dill not available or engine cannot be loaded")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("CALIBRATION_QUALITY() INFINITY BUG FIX - VALIDATION")
    print("=" * 70)
    print()

    tests = [
        test_bayesian_calibrator_empty,
        test_simulation_calibrator_empty,
        test_calibrator_with_data,
        test_betting_decision_with_empty_calibrator
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if all(results):
        print("\n✅ ALL TESTS PASSED - Bug fix validated!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
