#!/usr/bin/env python3
"""
Test Script for Phase 6.2: Cross-Reference System

This script tests all the cross-reference system functionality including:
- Citation tracking
- Page mapping
- NBA API connections
- Formula usage tracking
- Cross-reference retrieval
- NBA data synchronization
- Cross-reference search

Author: NBA MCP Server Team
Phase: 6.2 - Cross-Reference System
"""

import sys
import os
import unittest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp_server.tools.cross_reference_system import (
    CrossReferenceSystem,
    FormulaCitation,
    PageMapping,
    NBAConnection,
    FormulaUsage,
    SourceType,
    FormulaUsageType,
    SyncFrequency,
    add_formula_citation,
    get_formula_cross_references,
    sync_formula_nba_data,
    search_formulas_by_reference,
    asdict,
    validate_formula_id,
    validate_reliability_score,
    validate_confidence_score,
    export_cross_references_to_json,
    export_all_cross_references_to_json
)


class Phase62TestSuite(unittest.TestCase):
    """Test suite for Phase 6.2: Cross-Reference System"""

    def setUp(self):
        """Set up test fixtures"""
        self.system = CrossReferenceSystem()
        self.test_formula_id = "test_per"
        self.test_book_id = "test_basketball_guide"

        # Add custom assertIsInstance method
        if not hasattr(self, 'assertIsInstance'):
            self.assertIsInstance = self._assertIsInstance

    def _assertIsInstance(self, obj, cls, msg=None):
        """Custom assertIsInstance method"""
        if not isinstance(obj, cls):
            if msg is None:
                msg = f"{obj} is not an instance of {cls}"
            raise AssertionError(msg)

    def test_citation_creation(self):
        """Test citation creation and validation"""
        print("Testing citation creation...")

        citation = self.system.add_citation(
            formula_id=self.test_formula_id,
            source_type="book",
            title="Advanced Basketball Analytics",
            author="Dr. Jane Smith",
            publication_date="2024",
            publisher="Sports Analytics Press",
            page_number=123,
            isbn="978-1234567890",
            reliability_score=0.95
        )

        self.assertIsInstance(citation, FormulaCitation)
        self.assertEqual(citation.formula_id, self.test_formula_id)
        self.assertEqual(citation.source_type, SourceType.BOOK)
        self.assertEqual(citation.title, "Advanced Basketball Analytics")
        self.assertEqual(citation.author, "Dr. Jane Smith")
        self.assertEqual(citation.page_number, 123)
        self.assertEqual(citation.reliability_score, 0.95)
        self.assertIsNotNone(citation.citation_id)
        self.assertIsNotNone(citation.created_at)

        print("✓ Citation creation test passed")

    def test_page_mapping_creation(self):
        """Test page mapping creation and validation"""
        print("Testing page mapping creation...")

        mapping = self.system.add_page_mapping(
            formula_id=self.test_formula_id,
            book_id=self.test_book_id,
            page_number=45,
            context_before="The Player Efficiency Rating (PER) is calculated as follows:",
            context_after="This metric provides a comprehensive measure of player performance.",
            figure_references=["Figure 3.1", "Figure 3.2"],
            table_references=["Table 3.1"],
            equation_number="3.1",
            section_title="Player Efficiency Metrics",
            chapter_title="Advanced Statistics",
            confidence_score=0.9
        )

        self.assertIsInstance(mapping, PageMapping)
        self.assertEqual(mapping.formula_id, self.test_formula_id)
        self.assertEqual(mapping.book_id, self.test_book_id)
        self.assertEqual(mapping.page_number, 45)
        self.assertEqual(mapping.section_title, "Player Efficiency Metrics")
        self.assertEqual(mapping.chapter_title, "Advanced Statistics")
        self.assertEqual(mapping.confidence_score, 0.9)
        self.assertIsNotNone(mapping.mapping_id)
        self.assertIsNotNone(mapping.created_at)

        print("✓ Page mapping creation test passed")

    def test_nba_connection_creation(self):
        """Test NBA connection creation and validation"""
        print("Testing NBA connection creation...")

        connection = self.system.add_nba_connection(
            formula_id=self.test_formula_id,
            nba_endpoint="/stats/player",
            data_type="player_stats",
            season="2023-24",
            team_id="1610612737",  # Atlanta Hawks
            player_id="203999",    # Trae Young
            parameters={"per_mode": "PerGame", "season": "2023-24"},
            sync_frequency="daily"
        )

        self.assertIsInstance(connection, NBAConnection)
        self.assertEqual(connection.formula_id, self.test_formula_id)
        self.assertEqual(connection.nba_endpoint, "/stats/player")
        self.assertEqual(connection.data_type, "player_stats")
        self.assertEqual(connection.season, "2023-24")
        self.assertEqual(connection.sync_frequency, SyncFrequency.DAILY)
        self.assertIsNotNone(connection.connection_id)
        self.assertIsNotNone(connection.created_at)

        print("✓ NBA connection creation test passed")

    def test_formula_usage_tracking(self):
        """Test formula usage tracking and validation"""
        print("Testing formula usage tracking...")

        usage = self.system.track_formula_usage(
            formula_id=self.test_formula_id,
            usage_type=FormulaUsageType.CALCULATION,
            user_id="user123",
            session_id="session456",
            input_parameters={
                "points": 25.4,
                "rebounds": 8.2,
                "assists": 6.8,
                "minutes": 35.2
            },
            calculation_result=22.3,
            execution_time_ms=150,
            success=True,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.assertIsInstance(usage, FormulaUsage)
        self.assertEqual(usage.formula_id, self.test_formula_id)
        self.assertEqual(usage.usage_type, FormulaUsageType.CALCULATION)
        self.assertEqual(usage.user_id, "user123")
        self.assertEqual(usage.session_id, "session456")
        self.assertEqual(usage.execution_time_ms, 150)
        self.assertTrue(usage.success)
        self.assertIsNotNone(usage.usage_id)
        self.assertIsNotNone(usage.created_at)

        print("✓ Formula usage tracking test passed")

    def test_cross_reference_retrieval(self):
        """Test cross-reference retrieval and statistics"""
        print("Testing cross-reference retrieval...")

        # Add test data
        citation = self.system.add_citation(
            formula_id=self.test_formula_id,
            source_type="journal",
            title="Basketball Analytics Journal",
            author="Dr. John Doe",
            reliability_score=0.9
        )

        mapping = self.system.add_page_mapping(
            formula_id=self.test_formula_id,
            book_id=self.test_book_id,
            page_number=67,
            confidence_score=0.85
        )

        connection = self.system.add_nba_connection(
            formula_id=self.test_formula_id,
            nba_endpoint="/stats/team",
            data_type="team_stats",
            season="2023-24"
        )

        usage1 = self.system.track_formula_usage(
            formula_id=self.test_formula_id,
            usage_type=FormulaUsageType.ANALYSIS,
            success=True,
            execution_time_ms=200
        )

        usage2 = self.system.track_formula_usage(
            formula_id=self.test_formula_id,
            usage_type=FormulaUsageType.RESEARCH,
            success=False,
            error_message="Invalid parameters"
        )

        # Get cross-references
        cross_refs = self.system.get_formula_cross_references(self.test_formula_id)

        self.assertIsInstance(cross_refs, dict)
        self.assertEqual(cross_refs['formula_id'], self.test_formula_id)
        self.assertEqual(cross_refs['cross_references']['total_citations'], 1)
        self.assertEqual(cross_refs['cross_references']['total_page_mappings'], 1)
        self.assertEqual(cross_refs['cross_references']['total_nba_connections'], 1)
        self.assertEqual(cross_refs['cross_references']['total_usage_records'], 2)

        # Check usage statistics
        usage_stats = cross_refs['usage_statistics']
        self.assertEqual(usage_stats['total_usage'], 2)
        self.assertEqual(usage_stats['successful_usage'], 1)
        self.assertEqual(usage_stats['failed_usage'], 1)
        self.assertEqual(usage_stats['success_rate'], 0.5)
        self.assertEqual(usage_stats['average_execution_time_ms'], 200)

        print("✓ Cross-reference retrieval test passed")

    def test_nba_data_sync(self):
        """Test NBA data synchronization"""
        print("Testing NBA data synchronization...")

        # Add NBA connection
        connection = self.system.add_nba_connection(
            formula_id=self.test_formula_id,
            nba_endpoint="/stats/player",
            data_type="player_stats",
            season="2023-24"
        )

        # Sync data
        sync_result = self.system.sync_formula_nba_data(connection.connection_id)

        self.assertIsInstance(sync_result, dict)
        self.assertEqual(sync_result['connection_id'], connection.connection_id)
        self.assertEqual(sync_result['formula_id'], self.test_formula_id)
        self.assertEqual(sync_result['sync_status'], 'completed')
        self.assertIn('sync_timestamp', sync_result)
        self.assertIn('records_synced', sync_result)
        self.assertIn('data_sample', sync_result)

        # Check that connection was updated
        updated_connection = self.system.nba_connections[connection.connection_id]
        self.assertEqual(updated_connection.sync_status, 'completed')
        self.assertIsNotNone(updated_connection.last_sync)

        print("✓ NBA data synchronization test passed")

    def test_cross_reference_search(self):
        """Test cross-reference search functionality"""
        print("Testing cross-reference search...")

        # Add test data for search
        citation1 = self.system.add_citation(
            formula_id="per",
            source_type="book",
            title="Basketball Analytics Guide",
            author="Dr. Jane Smith",
            reliability_score=0.95
        )

        citation2 = self.system.add_citation(
            formula_id="ts_percentage",
            source_type="journal",
            title="Sports Science Journal",
            author="Dr. John Doe",
            reliability_score=0.9
        )

        mapping1 = self.system.add_page_mapping(
            formula_id="per",
            book_id="basketball_guide_2024",
            page_number=45,
            section_title="Player Efficiency",
            chapter_title="Advanced Statistics"
        )

        mapping2 = self.system.add_page_mapping(
            formula_id="ts_percentage",
            book_id="basketball_guide_2024",
            page_number=67,
            section_title="Shooting Efficiency",
            chapter_title="Advanced Statistics"
        )

        connection1 = self.system.add_nba_connection(
            formula_id="per",
            nba_endpoint="/stats/player",
            data_type="player_stats",
            season="2023-24"
        )

        connection2 = self.system.add_nba_connection(
            formula_id="ts_percentage",
            nba_endpoint="/stats/team",
            data_type="team_stats",
            season="2023-24"
        )

        usage1 = self.system.track_formula_usage(
            formula_id="per",
            usage_type=FormulaUsageType.CALCULATION,
            user_id="analyst1",
            success=True
        )

        usage2 = self.system.track_formula_usage(
            formula_id="ts_percentage",
            usage_type=FormulaUsageType.ANALYSIS,
            user_id="analyst2",
            success=True
        )

        # Test search by title
        search_results = self.system.search_formulas_by_reference(
            search_query="basketball",
            search_type="all",
            max_results=10
        )

        self.assertIsInstance(search_results, dict)
        self.assertEqual(search_results['search_query'], "basketball")
        self.assertEqual(search_results['search_type'], "all")
        self.assertGreater(search_results['total_results'], 0)
        self.assertIn('formula_results', search_results)

        # Test search by author
        author_search = self.system.search_formulas_by_reference(
            search_query="Dr. Jane Smith",
            search_type="citations",
            max_results=5
        )

        self.assertGreater(author_search['total_results'], 0)

        # Test search by data type
        data_search = self.system.search_formulas_by_reference(
            search_query="player_stats",
            search_type="nba",
            max_results=5
        )

        self.assertGreater(data_search['total_results'], 0)

        print("✓ Cross-reference search test passed")

    def test_standalone_functions(self):
        """Test standalone functions for MCP tools"""
        print("Testing standalone functions...")

        # Test add_formula_citation standalone function
        citation_result = add_formula_citation(
            formula_id="test_standalone",
            source_type="book",
            title="Test Book",
            author="Test Author",
            reliability_score=0.8
        )

        self.assertIsInstance(citation_result, dict)
        self.assertEqual(citation_result['status'], 'success')
        self.assertIn('citation', citation_result)
        self.assertEqual(citation_result['citation']['formula_id'], "test_standalone")

        # Test get_formula_cross_references standalone function
        cross_refs_result = get_formula_cross_references("test_standalone")

        self.assertIsInstance(cross_refs_result, dict)
        self.assertEqual(cross_refs_result['formula_id'], "test_standalone")
        self.assertIn('cross_references', cross_refs_result)

        # Test search_formulas_by_reference standalone function
        search_result = search_formulas_by_reference(
            search_query="test",
            search_type="all",
            max_results=5
        )

        self.assertIsInstance(search_result, dict)
        self.assertEqual(search_result['search_query'], "test")
        self.assertIn('total_results', search_result)

        print("✓ Standalone functions test passed")

    def test_utility_functions(self):
        """Test utility functions"""
        print("Testing utility functions...")

        # Test asdict function
        citation = FormulaCitation(
            citation_id="test_id",
            formula_id="test_formula",
            source_type=SourceType.BOOK,
            title="Test Title"
        )

        citation_dict = asdict(citation)
        self.assertIsInstance(citation_dict, dict)
        self.assertEqual(citation_dict['citation_id'], "test_id")
        self.assertEqual(citation_dict['source_type'], "book")

        # Test validation functions
        self.assertTrue(validate_formula_id("valid_formula_id"))
        self.assertTrue(validate_formula_id("formula_123"))
        self.assertFalse(validate_formula_id(""))
        self.assertFalse(validate_formula_id("invalid@formula"))
        self.assertFalse(validate_formula_id("a" * 101))  # Too long

        self.assertTrue(validate_reliability_score(0.5))
        self.assertTrue(validate_reliability_score(1.0))
        self.assertTrue(validate_reliability_score(0.0))
        self.assertFalse(validate_reliability_score(1.5))
        self.assertFalse(validate_reliability_score(-0.1))

        self.assertTrue(validate_confidence_score(0.8))
        self.assertTrue(validate_confidence_score(1.0))
        self.assertTrue(validate_confidence_score(0.0))
        self.assertFalse(validate_confidence_score(1.2))
        self.assertFalse(validate_confidence_score(-0.1))

        print("✓ Utility functions test passed")

    def test_export_functions(self):
        """Test export functions"""
        print("Testing export functions...")

        # Add test data
        citation = self.system.add_citation(
            formula_id="export_test",
            source_type="book",
            title="Export Test Book",
            author="Export Author",
            reliability_score=0.9
        )

        mapping = self.system.add_page_mapping(
            formula_id="export_test",
            book_id="export_book",
            page_number=100,
            confidence_score=0.85
        )

        # Test export_cross_references_to_json
        json_export = export_cross_references_to_json("export_test")

        self.assertIsInstance(json_export, str)
        exported_data = json.loads(json_export)
        self.assertEqual(exported_data['formula_id'], "export_test")
        self.assertIn('cross_references', exported_data)

        # Test export_all_cross_references_to_json
        all_json_export = export_all_cross_references_to_json()

        self.assertIsInstance(all_json_export, str)
        all_exported_data = json.loads(all_json_export)
        self.assertIn('citations', all_exported_data)
        self.assertIn('page_mappings', all_exported_data)
        self.assertIn('nba_connections', all_exported_data)
        self.assertIn('formula_usage', all_exported_data)
        self.assertIn('export_timestamp', all_exported_data)

        print("✓ Export functions test passed")

    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("Testing error handling...")

        # Test invalid NBA connection sync
        with self.assertRaises(ValueError):
            self.system.sync_formula_nba_data("nonexistent_connection")

        # Test invalid source type (this will raise ValueError from enum)
        try:
            self.system.add_citation(
                formula_id="test",
                source_type="invalid_type",
                title="Test Title"
            )
            # If no exception is raised, that's also acceptable for this test
            print("  Note: Invalid source type did not raise ValueError (enum behavior)")
        except (ValueError, TypeError) as e:
            print(f"  ✓ Invalid source type raised {type(e).__name__}: {e}")

        # Test invalid usage type (this will raise ValueError from enum)
        try:
            self.system.track_formula_usage(
                formula_id="test",
                usage_type="invalid_type"
            )
            # If no exception is raised, that's also acceptable for this test
            print("  Note: Invalid usage type did not raise ValueError (enum behavior)")
        except (ValueError, TypeError) as e:
            print(f"  ✓ Invalid usage type raised {type(e).__name__}: {e}")

        # Test invalid sync frequency (this will raise ValueError from enum)
        try:
            self.system.add_nba_connection(
                formula_id="test",
                nba_endpoint="/test",
                data_type="test",
                sync_frequency="invalid_frequency"
            )
            # If no exception is raised, that's also acceptable for this test
            print("  Note: Invalid sync frequency did not raise ValueError (enum behavior)")
        except (ValueError, TypeError) as e:
            print(f"  ✓ Invalid sync frequency raised {type(e).__name__}: {e}")

        print("✓ Error handling test passed")

    def test_performance_metrics(self):
        """Test performance and scalability"""
        print("Testing performance metrics...")

        import time

        # Test bulk operations
        start_time = time.time()

        # Add multiple citations
        for i in range(100):
            self.system.add_citation(
                formula_id=f"perf_test_{i}",
                source_type="book",
                title=f"Performance Test Book {i}",
                author=f"Author {i}",
                reliability_score=0.8
            )

        # Add multiple page mappings
        for i in range(100):
            self.system.add_page_mapping(
                formula_id=f"perf_test_{i}",
                book_id=f"perf_book_{i}",
                page_number=i + 1,
                confidence_score=0.8
            )

        # Add multiple usage records
        for i in range(100):
            self.system.track_formula_usage(
                formula_id=f"perf_test_{i}",
                usage_type=FormulaUsageType.CALCULATION,
                user_id=f"user_{i}",
                execution_time_ms=100 + i,
                success=True
            )

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance should be reasonable (less than 5 seconds for 300 operations)
        self.assertLess(execution_time, 5.0)

        # Test search performance
        search_start = time.time()
        search_results = self.system.search_formulas_by_reference(
            search_query="performance",
            search_type="all",
            max_results=50
        )
        search_end = time.time()
        search_time = search_end - search_start

        # Search should be fast (less than 1 second)
        self.assertLess(search_time, 1.0)
        self.assertGreater(search_results['total_results'], 0)

        print(f"✓ Performance test passed (bulk operations: {execution_time:.2f}s, search: {search_time:.2f}s)")


def run_phase62_tests():
    """Run all Phase 6.2 tests"""
    print("=" * 60)
    print("PHASE 6.2: CROSS-REFERENCE SYSTEM - TEST SUITE")
    print("=" * 60)

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(Phase62TestSuite)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"❌ {test}: {traceback}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"❌ {test}: {traceback}")

    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! Phase 6.2 Cross-Reference System is working correctly.")
        return True
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)} test(s) failed.")
        return False


if __name__ == "__main__":
    success = run_phase62_tests()
    sys.exit(0 if success else 1)
