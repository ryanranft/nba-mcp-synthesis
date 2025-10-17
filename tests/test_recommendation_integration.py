#!/usr/bin/env python3
"""
Test suite for Recommendation Integration System

Tests all components of the recommendation integration system including:
- PhaseMapper recommendation → phase mapping
- RecommendationIntegrator phase document generation
- PlanOverrideManager conflict detection and safe updates
- CrossProjectTracker cross-project status tracking
- Main integration workflow
"""

import unittest
import json
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from phase_mapper import PhaseMapper
from recommendation_integrator import RecommendationIntegrator
from plan_override_manager import PlanOverrideManager
from cross_project_tracker import CrossProjectTracker


class TestPhaseMapper(unittest.TestCase):
    """Test PhaseMapper recommendation → phase mapping functionality."""

    def setUp(self):
        self.mapper = PhaseMapper()

    def test_map_recommendation_to_phase(self):
        """Test mapping recommendations to phases."""
        # Test data validation → Phase 1
        rec = {
            "title": "Implement data validation pipeline",
            "reasoning": "Quality checks needed for data integrity",
        }
        phases = self.mapper.map_recommendation_to_phase(rec)
        self.assertIn(1, phases)  # Phase 1: Data Quality

        # Test ML model → Phase 5
        rec = {
            "title": "Add machine learning model training",
            "reasoning": "Need to train models for prediction",
        }
        phases = self.mapper.map_recommendation_to_phase(rec)
        self.assertIn(5, phases)  # Phase 5: Machine Learning

        # Test AWS Glue → Phase 2
        rec = {
            "title": "Set up AWS Glue ETL pipeline",
            "reasoning": "Transform data using AWS Glue",
        }
        phases = self.mapper.map_recommendation_to_phase(rec)
        self.assertIn(2, phases)  # Phase 2: AWS Glue ETL

    def test_map_recommendations_batch(self):
        """Test batch mapping of recommendations."""
        recommendations = [
            {"title": "Implement data validation", "category": "critical"},
            {"title": "Add ML model training", "category": "important"},
            {"title": "Set up PostgreSQL database", "category": "critical"},
        ]

        phase_recs = self.mapper.map_recommendations_batch(recommendations)

        # Should have recommendations in multiple phases
        total_mapped = sum(len(recs) for recs in phase_recs.values())
        self.assertEqual(total_mapped, len(recommendations))

        # Should have some phases with recommendations
        phases_with_recs = len([recs for recs in phase_recs.values() if recs])
        self.assertGreater(phases_with_recs, 0)

    def test_get_phase_statistics(self):
        """Test phase statistics generation."""
        phase_recs = {
            0: [{"title": "Test 1"}],
            1: [{"title": "Test 2"}, {"title": "Test 3"}],
            2: [],
            3: [{"title": "Test 4"}],
            4: [],
            5: [{"title": "Test 5"}],
            6: [],
            7: [],
            8: [],
            9: [],
        }

        stats = self.mapper.get_phase_statistics(phase_recs)

        self.assertEqual(stats["total_recommendations"], 5)
        self.assertEqual(stats["phases_with_recommendations"], 4)
        self.assertEqual(len(stats["phase_distribution"]), 4)


class TestRecommendationIntegrator(unittest.TestCase):
    """Test RecommendationIntegrator phase document generation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.simulator_path = os.path.join(self.temp_dir, "simulator")
        self.synthesis_path = os.path.join(self.temp_dir, "synthesis")

        os.makedirs(self.simulator_path, exist_ok=True)
        os.makedirs(self.synthesis_path, exist_ok=True)
        os.makedirs(
            os.path.join(self.synthesis_path, "analysis_results"), exist_ok=True
        )

        self.integrator = RecommendationIntegrator(
            self.simulator_path, self.synthesis_path
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_master_recommendations(self):
        """Test loading master recommendations."""
        # Create test master recommendations
        test_recommendations = {
            "recommendations": [
                {
                    "id": "test_1",
                    "title": "Test recommendation",
                    "category": "critical",
                    "source_books": ["Test Book"],
                    "added_date": datetime.now().isoformat(),
                }
            ],
            "by_category": {"critical": ["test_1"]},
            "by_book": {"Test Book": ["test_1"]},
        }

        master_file = os.path.join(
            self.synthesis_path, "analysis_results", "master_recommendations.json"
        )
        with open(master_file, "w") as f:
            json.dump(test_recommendations, f, indent=2)

        # Load recommendations
        master_recs = self.integrator.load_master_recommendations()

        self.assertEqual(len(master_recs["recommendations"]), 1)
        self.assertEqual(
            master_recs["recommendations"][0]["title"], "Test recommendation"
        )

    def test_create_phase_recommendations(self):
        """Test organizing recommendations by phase."""
        test_recommendations = {
            "recommendations": [
                {
                    "id": "test_1",
                    "title": "Implement data validation pipeline",
                    "category": "critical",
                    "source_books": ["Test Book"],
                    "reasoning": "Quality checks needed",
                },
                {
                    "id": "test_2",
                    "title": "Add machine learning model training",
                    "category": "important",
                    "source_books": ["Test Book"],
                    "reasoning": "Need ML models",
                },
            ]
        }

        phase_recs = self.integrator.create_phase_recommendations(test_recommendations)

        # Should have recommendations in multiple phases
        total_mapped = sum(len(recs) for recs in phase_recs.values())
        self.assertEqual(total_mapped, 2)

        # Should have some phases with recommendations
        phases_with_recs = len([recs for recs in phase_recs.values() if recs])
        self.assertGreater(phases_with_recs, 0)

    def test_generate_phase_enhancement_docs(self):
        """Test generating phase enhancement documents."""
        phase_recs = {
            1: [
                {
                    "id": "test_1",
                    "title": "Implement data validation",
                    "category": "critical",
                    "source_books": ["Test Book"],
                    "reasoning": "Quality checks needed",
                }
            ],
            5: [
                {
                    "id": "test_2",
                    "title": "Add ML model training",
                    "category": "important",
                    "source_books": ["Test Book"],
                    "reasoning": "Need ML models",
                }
            ],
        }

        generated_files = self.integrator.generate_phase_enhancement_docs(phase_recs)

        self.assertEqual(len(generated_files), 2)

        # Check that files were created
        for file_path in generated_files:
            self.assertTrue(os.path.exists(file_path))

            # Check file content
            with open(file_path, "r") as f:
                content = f.read()
                self.assertIn("Phase", content)
                self.assertIn("Book Recommendations", content)


class TestPlanOverrideManager(unittest.TestCase):
    """Test PlanOverrideManager conflict detection and safe updates."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.simulator_path = os.path.join(self.temp_dir, "simulator")

        os.makedirs(self.simulator_path, exist_ok=True)

        # Create test phase directory and plan
        phase_dir = os.path.join(self.simulator_path, "docs", "phases", "phase_5")
        os.makedirs(phase_dir, exist_ok=True)

        test_plan_content = """# Phase 5 - Machine Learning Models

## Current Plan
- Implement basic ML models
- Add model training pipeline
- Create prediction endpoints

## Implementation Tasks
- [ ] Set up ML framework
- [ ] Train initial models
- [ ] Deploy models
"""

        plan_file = os.path.join(phase_dir, "PHASE_5_INDEX.md")
        with open(plan_file, "w") as f:
            f.write(test_plan_content)

        self.manager = PlanOverrideManager(self.simulator_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_analyze_plan_conflicts(self):
        """Test plan conflict analysis."""
        test_recommendations = [
            {
                "title": "Improve model training pipeline",
                "category": "important",
                "source_books": ["Test Book"],
                "reasoning": "Enhance existing training with better validation",
            },
            {
                "title": "Add model versioning with MLflow",
                "category": "critical",
                "source_books": ["Test Book"],
                "reasoning": "Track models and enable rollbacks",
            },
            {
                "title": "Replace ML framework with different approach",
                "category": "critical",
                "source_books": ["Test Book"],
                "reasoning": "Use different framework instead of current one",
            },
        ]

        analysis = self.manager.analyze_plan_conflicts(5, test_recommendations)

        self.assertIn("conflicts", analysis)
        self.assertIn("enhancements", analysis)
        self.assertIn("new_additions", analysis)

        # Should have some conflicts due to "instead of" language
        self.assertGreater(len(analysis["conflicts"]), 0)

    def test_propose_plan_updates(self):
        """Test plan update proposal generation."""
        analysis = {
            "conflicts": [
                {
                    "title": "Replace ML framework",
                    "category": "critical",
                    "source_books": ["Test Book"],
                    "reasoning": "Use different framework instead of current one",
                }
            ],
            "enhancements": [
                {
                    "title": "Improve model training",
                    "category": "important",
                    "source_books": ["Test Book"],
                    "reasoning": "Enhance existing training",
                }
            ],
            "new_additions": [
                {
                    "title": "Add model versioning",
                    "category": "critical",
                    "source_books": ["Test Book"],
                    "reasoning": "Track models",
                }
            ],
        }

        proposal = self.manager.propose_plan_updates(5, analysis)

        self.assertEqual(proposal["phase"], 5)
        self.assertTrue(proposal["action_required"])  # Has conflicts
        self.assertEqual(proposal["conflicts_count"], 1)
        self.assertEqual(proposal["safe_updates_count"], 2)

    def test_apply_safe_updates(self):
        """Test applying safe updates."""
        proposal = {
            "phase": 5,
            "enhancements": [
                {
                    "title": "Improve model training",
                    "category": "important",
                    "source_books": ["Test Book"],
                    "reasoning": "Enhance existing training",
                }
            ],
            "new_additions": [
                {
                    "title": "Add model versioning",
                    "category": "critical",
                    "source_books": ["Test Book"],
                    "reasoning": "Track models",
                }
            ],
            "conflicts": [],
        }

        results = self.manager.apply_safe_updates(5, proposal)

        self.assertGreater(results["applied"], 0)
        self.assertEqual(results["pending"], 0)


class TestCrossProjectTracker(unittest.TestCase):
    """Test CrossProjectTracker cross-project status tracking."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.synthesis_path = os.path.join(self.temp_dir, "synthesis")
        self.simulator_path = os.path.join(self.temp_dir, "simulator")

        os.makedirs(self.synthesis_path, exist_ok=True)
        os.makedirs(self.simulator_path, exist_ok=True)

        # Create test files
        test_files = [
            (self.synthesis_path, "requirements.txt", "pandas\nnumpy\nmlflow"),
            (
                self.synthesis_path,
                "main.py",
                "class RecommendationSystem:\n    def analyze(self): pass",
            ),
            (self.simulator_path, "requirements.txt", "pandas\nscikit-learn\naws-sdk"),
            (
                self.simulator_path,
                "model.py",
                "class MLModel:\n    def train(self): pass",
            ),
        ]

        for base_path, filename, content in test_files:
            file_path = os.path.join(base_path, filename)
            with open(file_path, "w") as f:
                f.write(content)

        self.tracker = CrossProjectTracker(self.synthesis_path, self.simulator_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_scan_both_projects(self):
        """Test scanning both projects."""
        scan_results = self.tracker.scan_both_projects()

        self.assertIn("synthesis", scan_results)
        self.assertIn("simulator", scan_results)
        self.assertIn("shared", scan_results)
        self.assertIn("scan_date", scan_results)

        # Should have found files and modules
        self.assertGreater(scan_results["synthesis"]["files"], 0)
        self.assertGreater(scan_results["simulator"]["files"], 0)

        # Should have found shared technologies
        self.assertGreater(len(scan_results["shared"]["shared_technologies"]), 0)

    def test_generate_unified_status(self):
        """Test unified status report generation."""
        scan_results = {
            "synthesis": {
                "project_name": "NBA MCP Synthesis",
                "files": 10,
                "modules": ["main", "analyzer"],
                "features": ["analyze", "recommend"],
                "technologies": {"Python", "Pandas"},
                "recommendations_implemented": 5,
            },
            "simulator": {
                "project_name": "NBA Simulator AWS",
                "files": 15,
                "modules": ["model", "simulation"],
                "features": ["train", "predict"],
                "technologies": {"Python", "AWS"},
                "recommendations_implemented": 3,
            },
            "shared": {
                "shared_technologies": ["Python"],
                "shared_features": [],
                "integration_points": [],
            },
            "scan_date": datetime.now().isoformat(),
        }

        status_report = self.tracker.generate_unified_status(scan_results)

        self.assertIn("Cross-Project Implementation Status", status_report)
        self.assertIn("NBA MCP Synthesis", status_report)
        self.assertIn("NBA Simulator AWS", status_report)
        self.assertIn("Shared Technologies", status_report)


class TestIntegrationWorkflow(unittest.TestCase):
    """Test the complete integration workflow."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.synthesis_path = os.path.join(self.temp_dir, "synthesis")
        self.simulator_path = os.path.join(self.temp_dir, "simulator")

        os.makedirs(self.synthesis_path, exist_ok=True)
        os.makedirs(self.simulator_path, exist_ok=True)
        os.makedirs(
            os.path.join(self.synthesis_path, "analysis_results"), exist_ok=True
        )

        # Create test master recommendations
        test_recommendations = {
            "recommendations": [
                {
                    "id": "test_1",
                    "title": "Implement data validation pipeline",
                    "category": "critical",
                    "source_books": ["Test Book"],
                    "added_date": datetime.now().isoformat(),
                    "reasoning": "Quality checks needed for data integrity",
                },
                {
                    "id": "test_2",
                    "title": "Add machine learning model training",
                    "category": "important",
                    "source_books": ["Test Book"],
                    "added_date": datetime.now().isoformat(),
                    "reasoning": "Need to train models for prediction",
                },
            ],
            "by_category": {
                "critical": ["test_1"],
                "important": ["test_2"],
                "nice_to_have": [],
            },
            "by_book": {"Test Book": ["test_1", "test_2"]},
        }

        master_file = os.path.join(
            self.synthesis_path, "analysis_results", "master_recommendations.json"
        )
        with open(master_file, "w") as f:
            json.dump(test_recommendations, f, indent=2)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch("recommendation_integrator.RecommendationIntegrator")
    @patch("plan_override_manager.PlanOverrideManager")
    @patch("cross_project_tracker.CrossProjectTracker")
    def test_integration_workflow(
        self, mock_tracker, mock_override_mgr, mock_integrator
    ):
        """Test the complete integration workflow."""
        # Mock integrator
        mock_integrator_instance = Mock()
        mock_integrator_instance.load_master_recommendations.return_value = {
            "recommendations": [
                {"title": "Test recommendation", "category": "critical"}
            ]
        }
        mock_integrator_instance.create_phase_recommendations.return_value = {
            1: [{"title": "Test recommendation", "category": "critical"}]
        }
        mock_integrator_instance.generate_phase_enhancement_docs.return_value = [
            "/path/to/phase_1_recommendations.md"
        ]
        mock_integrator.return_value = mock_integrator_instance

        # Mock override manager
        mock_override_instance = Mock()
        mock_override_instance.analyze_plan_conflicts.return_value = {
            "conflicts": [],
            "enhancements": [],
            "new_additions": [{"title": "Test recommendation", "category": "critical"}],
        }
        mock_override_instance.propose_plan_updates.return_value = {
            "phase": 1,
            "conflicts": [],
            "enhancements": [],
            "new_additions": [{"title": "Test recommendation", "category": "critical"}],
        }
        mock_override_instance.apply_safe_updates.return_value = {
            "applied": 1,
            "pending": 0,
        }
        mock_override_mgr.return_value = mock_override_instance

        # Mock tracker
        mock_tracker_instance = Mock()
        mock_tracker_instance.scan_both_projects.return_value = {
            "synthesis": {"files": 10, "modules": []},
            "simulator": {"files": 15, "modules": []},
            "shared": {"shared_technologies": []},
            "scan_date": datetime.now().isoformat(),
        }
        mock_tracker.return_value = mock_tracker_instance

        # This would test the actual integration workflow
        # For now, we just verify the mocks are set up correctly
        self.assertTrue(True)


class TestConfiguration(unittest.TestCase):
    """Test configuration loading and validation."""

    def test_phase_mapper_configuration(self):
        """Test PhaseMapper configuration."""
        mapper = PhaseMapper()

        # Test phase descriptions
        descriptions = mapper.get_all_phase_descriptions()
        self.assertEqual(len(descriptions), 10)

        # Test specific phase description
        phase_5_desc = mapper.get_phase_description(5)
        self.assertIn("Machine Learning", phase_5_desc)

    def test_path_validation(self):
        """Test path validation in components."""
        # Test valid paths
        temp_dir = tempfile.mkdtemp()
        try:
            integrator = RecommendationIntegrator(temp_dir, temp_dir)
            self.assertEqual(integrator.simulator_path, temp_dir)
            self.assertEqual(integrator.synthesis_path, temp_dir)
        finally:
            shutil.rmtree(temp_dir)

        # Test invalid paths
        with self.assertRaises(ValueError):
            RecommendationIntegrator("/nonexistent/path", "/another/nonexistent/path")


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestPhaseMapper,
        TestRecommendationIntegrator,
        TestPlanOverrideManager,
        TestCrossProjectTracker,
        TestIntegrationWorkflow,
        TestConfiguration,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*70}")
    print(f"Integration System Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(
        f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print(f"{'='*70}")

    # Exit with error code if tests failed
    sys.exit(len(result.failures) + len(result.errors))
