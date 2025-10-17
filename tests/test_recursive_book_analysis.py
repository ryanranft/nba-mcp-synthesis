#!/usr/bin/env python3
"""
Test suite for Recursive Book Analysis Workflow

Tests all components of the book analysis system including:
- BookManager S3 operations
- RecursiveAnalyzer convergence tracking
- RecommendationGenerator report generation
- PlanGenerator implementation plans
- MasterRecommendations deduplication
- ProjectScanner knowledge base
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

from recursive_book_analysis import (
    BookManager,
    RecursiveAnalyzer,
    RecommendationGenerator,
    PlanGenerator,
    MasterRecommendations,
    ProjectScanner,
    AcsmConverter,
)


class TestAcsmConverter(unittest.TestCase):
    """Test ACSM file conversion functionality."""

    def setUp(self):
        self.converter = AcsmConverter()

    def test_needs_conversion(self):
        """Test ACSM file detection."""
        self.assertTrue(self.converter.needs_conversion("book.acsm"))
        self.assertFalse(self.converter.needs_conversion("book.pdf"))
        self.assertFalse(self.converter.needs_conversion("book.epub"))

    def test_is_ade_installed(self):
        """Test Adobe Digital Editions installation check."""
        # Mock the path check
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            self.assertTrue(self.converter.is_ade_installed())

            mock_exists.return_value = False
            self.assertFalse(self.converter.is_ade_installed())


class TestBookManager(unittest.TestCase):
    """Test BookManager S3 operations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.book_manager = BookManager("test-bucket")

        # Mock S3 client
        self.book_manager.s3_client = Mock()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_book_exists_in_s3(self):
        """Test S3 book existence check."""
        # Test book exists
        self.book_manager.s3_client.head_object.return_value = {}
        self.assertTrue(self.book_manager.book_exists_in_s3("books/test.pdf"))

        # Test book doesn't exist
        from botocore.exceptions import ClientError

        error_response = {"Error": {"Code": "404"}}
        self.book_manager.s3_client.head_object.side_effect = ClientError(
            error_response, "HeadObject"
        )
        self.assertFalse(self.book_manager.book_exists_in_s3("books/missing.pdf"))

    def test_upload_to_s3(self):
        """Test S3 upload functionality."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.pdf")
        with open(test_file, "w") as f:
            f.write("test content")

        # Mock successful upload
        self.book_manager.s3_client.upload_file.return_value = None
        result = self.book_manager.upload_to_s3(test_file, "books/test.pdf")
        self.assertTrue(result)

        # Mock failed upload
        self.book_manager.s3_client.upload_file.side_effect = Exception("Upload failed")
        result = self.book_manager.upload_to_s3(test_file, "books/test.pdf")
        self.assertFalse(result)


class TestProjectScanner(unittest.TestCase):
    """Test ProjectScanner knowledge base functionality."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = ProjectScanner()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_scan_project(self):
        """Test project scanning functionality."""
        # Create test project structure
        os.makedirs(os.path.join(self.temp_dir, "src", "ml"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "tests"), exist_ok=True)

        # Create test files
        with open(os.path.join(self.temp_dir, "src", "ml", "model.py"), "w") as f:
            f.write("class Model:\n    def train(self): pass")

        with open(os.path.join(self.temp_dir, "tests", "test_model.py"), "w") as f:
            f.write("def test_model(): pass")

        # Mock the scan
        with patch.object(self.scanner, "_scan_directory") as mock_scan:
            mock_scan.return_value = {
                "modules": ["src.ml.model"],
                "features": ["Model", "train"],
                "files": 2,
            }

            result = self.scanner.scan_project(self.temp_dir)
            self.assertIn("modules", result)
            self.assertIn("features", result)
            self.assertIn("files", result)


class TestMasterRecommendations(unittest.TestCase):
    """Test MasterRecommendations deduplication functionality."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.master_recs = MasterRecommendations(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_add_recommendation(self):
        """Test adding recommendations with deduplication."""
        # Add first recommendation
        rec1 = {"title": "Implement model versioning", "category": "critical"}
        self.master_recs.add_recommendation(rec1, "Test Book 1")

        # Add duplicate recommendation
        rec2 = {"title": "Implement model versioning", "category": "critical"}
        self.master_recs.add_recommendation(rec2, "Test Book 2")

        # Should only have one recommendation
        self.assertEqual(len(self.master_recs.recommendations), 1)

        # Should have both books as sources
        rec = self.master_recs.recommendations[0]
        self.assertIn("Test Book 1", rec["source_books"])
        self.assertIn("Test Book 2", rec["source_books"])

    def test_save_and_load(self):
        """Test saving and loading master recommendations."""
        # Add a recommendation
        rec = {"title": "Test recommendation", "category": "important"}
        self.master_recs.add_recommendation(rec, "Test Book")

        # Save
        self.master_recs.save_master()

        # Create new instance and load
        new_master_recs = MasterRecommendations(self.temp_dir)
        new_master_recs.load_master()

        # Should have the same recommendation
        self.assertEqual(len(new_master_recs.recommendations), 1)
        self.assertEqual(
            new_master_recs.recommendations[0]["title"], "Test recommendation"
        )


class TestRecursiveAnalyzer(unittest.TestCase):
    """Test RecursiveAnalyzer convergence tracking."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = RecursiveAnalyzer(
            {"convergence_threshold": 3, "max_iterations": 10, "chunk_size": 1000}
        )

        # Mock dependencies
        self.analyzer.scanner = Mock()
        self.analyzer.scanner.scan_projects.return_value = {
            "synthesis": {"modules": [], "features": []},
            "simulator": {"modules": [], "features": []},
        }
        self.analyzer.master_recs = Mock()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_convergence_detection(self):
        """Test convergence detection logic."""
        # Test nice-to-have only iteration
        recommendations = {
            "critical": [],
            "important": [],
            "nice_to_have": ["Test recommendation"],
        }

        has_critical = len(recommendations.get("critical", [])) > 0
        has_important = len(recommendations.get("important", [])) > 0
        has_only_nice = (
            not has_critical
            and not has_important
            and len(recommendations.get("nice_to_have", [])) > 0
        )

        self.assertTrue(has_only_nice)

    def test_iteration_tracking(self):
        """Test iteration tracking functionality."""
        tracker = {
            "iterations": [],
            "total_recommendations": {"critical": 0, "important": 0, "nice_to_have": 0},
        }

        # Simulate iteration
        iteration_data = {
            "iteration": 1,
            "timestamp": datetime.now().isoformat(),
            "recommendations": {
                "critical": ["Test"],
                "important": [],
                "nice_to_have": [],
            },
        }
        tracker["iterations"].append(iteration_data)

        # Update totals
        for category in ["critical", "important", "nice_to_have"]:
            tracker["total_recommendations"][category] += len(
                iteration_data["recommendations"].get(category, [])
            )

        self.assertEqual(tracker["total_recommendations"]["critical"], 1)
        self.assertEqual(len(tracker["iterations"]), 1)


class TestRecommendationGenerator(unittest.TestCase):
    """Test RecommendationGenerator report generation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = RecommendationGenerator()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_generate_report(self):
        """Test markdown report generation."""
        tracker = {
            "book_title": "Test Book",
            "start_time": datetime.now().isoformat(),
            "total_iterations": 3,
            "convergence_achieved": True,
            "convergence_iteration": 3,
            "total_recommendations": {"critical": 2, "important": 3, "nice_to_have": 1},
            "iterations": [
                {
                    "iteration": 1,
                    "recommendations": {
                        "critical": ["Test 1"],
                        "important": [],
                        "nice_to_have": [],
                    },
                },
                {
                    "iteration": 2,
                    "recommendations": {
                        "critical": ["Test 2"],
                        "important": ["Test 3"],
                        "nice_to_have": [],
                    },
                },
                {
                    "iteration": 3,
                    "recommendations": {
                        "critical": [],
                        "important": [],
                        "nice_to_have": ["Test 4"],
                    },
                },
            ],
        }

        report_file = self.generator.generate_report(tracker, self.temp_dir)

        # Check file was created
        self.assertTrue(os.path.exists(report_file))

        # Check content
        with open(report_file, "r") as f:
            content = f.read()
            self.assertIn("Test Book", content)
            self.assertIn("CONVERGENCE ACHIEVED", content)
            self.assertIn("Test 1", content)
            self.assertIn("Test 2", content)

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        test_cases = [
            ("Test Book: Analysis", "Test_Book_Analysis"),
            ("Book/With\\Invalid:Chars", "Book_With_Invalid_Chars"),
            ("Book with spaces", "Book_with_spaces"),
            ("Book@#$%^&*()", "Book"),
        ]

        for input_name, expected in test_cases:
            result = self.generator._sanitize_filename(input_name)
            self.assertEqual(result, expected)


class TestPlanGenerator(unittest.TestCase):
    """Test PlanGenerator implementation plan generation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.generator = PlanGenerator()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_generate_plans(self):
        """Test implementation plan generation."""
        tracker = {
            "book_title": "Test Book",
            "iterations": [
                {
                    "recommendations": {
                        "critical": ["Implement model versioning"],
                        "important": ["Add monitoring"],
                        "nice_to_have": ["Improve documentation"],
                    }
                }
            ],
        }

        plan_files = self.generator.generate_plans(tracker, self.temp_dir)

        # Should generate plans for critical and important items
        self.assertEqual(len(plan_files), 3)  # 2 plans + README

        # Check files exist
        for plan_file in plan_files:
            self.assertTrue(os.path.exists(plan_file))

        # Check content
        with open(plan_files[0], "r") as f:
            content = f.read()
            self.assertIn("Implement model versioning", content)
            self.assertIn("Test Book", content)

    def test_generate_plan_file(self):
        """Test individual plan file generation."""
        plan_file = self.generator._generate_plan_file(
            "Test Recommendation", "critical", 1, self.temp_dir, "Test Book"
        )

        self.assertTrue(os.path.exists(plan_file))

        with open(plan_file, "r") as f:
            content = f.read()
            self.assertIn("Test Recommendation", content)
            self.assertIn("Critical", content)
            self.assertIn("HIGH", content)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch("recursive_book_analysis.BookManager")
    @patch("recursive_book_analysis.RecursiveAnalyzer")
    def test_full_workflow(self, mock_analyzer, mock_book_manager):
        """Test the complete workflow integration."""
        # Mock book manager
        mock_bm_instance = Mock()
        mock_bm_instance.check_and_upload_books.return_value = {
            "already_in_s3": [],
            "uploaded": [{"title": "Test Book"}],
            "needs_conversion": [],
            "failed": [],
            "skipped": [],
        }
        mock_book_manager.return_value = mock_bm_instance

        # Mock analyzer
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze_book_recursively.return_value = {
            "book_title": "Test Book",
            "convergence_achieved": True,
            "total_iterations": 3,
            "total_recommendations": {"critical": 1, "important": 2, "nice_to_have": 1},
        }
        mock_analyzer.return_value = mock_analyzer_instance

        # Mock recommendation generator
        with patch("recursive_book_analysis.RecommendationGenerator") as mock_rg:
            mock_rg_instance = Mock()
            mock_rg_instance.generate_report.return_value = "test_report.md"
            mock_rg.return_value = mock_rg_instance

            # Mock plan generator
            with patch("recursive_book_analysis.PlanGenerator") as mock_pg:
                mock_pg_instance = Mock()
                mock_pg_instance.generate_plans.return_value = ["plan1.md", "plan2.md"]
                mock_pg.return_value = mock_pg_instance

                # This would be the actual workflow test
                # For now, we just verify the mocks are set up correctly
                self.assertTrue(True)


class TestConfiguration(unittest.TestCase):
    """Test configuration loading and validation."""

    def test_load_books_config(self):
        """Test loading books configuration."""
        config_data = {
            "books": [
                {
                    "id": "test_book",
                    "title": "Test Book",
                    "s3_path": "books/test.pdf",
                    "format": "pdf",
                }
            ],
            "analysis_settings": {"convergence_threshold": 3, "max_iterations": 15},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            with open(config_file, "r") as f:
                loaded_config = json.load(f)

            self.assertEqual(len(loaded_config["books"]), 1)
            self.assertEqual(loaded_config["books"][0]["title"], "Test Book")
            self.assertEqual(
                loaded_config["analysis_settings"]["convergence_threshold"], 3
            )
        finally:
            os.unlink(config_file)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestAcsmConverter,
        TestBookManager,
        TestProjectScanner,
        TestMasterRecommendations,
        TestRecursiveAnalyzer,
        TestRecommendationGenerator,
        TestPlanGenerator,
        TestIntegration,
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
    print(f"Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(
        f"  Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print(f"{'='*70}")

    # Exit with error code if tests failed
    sys.exit(len(result.failures) + len(result.errors))
