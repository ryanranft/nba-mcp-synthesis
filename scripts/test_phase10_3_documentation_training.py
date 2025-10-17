#!/usr/bin/env python3
"""
Test script for Phase 10.3: Documentation & Training

This script tests the comprehensive documentation and training system including:
- User guide generation
- API documentation generation
- Tutorial creation
- Quick start guide generation
- Training module creation
- Comprehensive documentation projects
- Documentation export
- Documentation status tracking

Usage:
    python3 scripts/test_phase10_3_documentation_training.py
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp_server.tools.documentation_training import (
    DocumentationGenerator,
    generate_user_guide,
    generate_api_documentation,
    generate_tutorial,
    generate_quick_start_guide,
    create_training_module,
    generate_comprehensive_documentation,
    export_documentation,
    get_documentation_status,
)


def test_documentation_system():
    """Test the documentation training system"""
    print("=" * 80)
    print("Phase 10.3: Documentation & Training System Test")
    print("=" * 80)

    # Test system initialization
    print("\n1. Testing Documentation Training System Initialization")
    print("-" * 60)

    try:
        system = DocumentationGenerator()
        print("✓ Documentation training system initialized successfully")
        print(f"  - Generated documents: {len(system.generated_docs)}")
        print(f"  - Training modules: {len(system.training_modules)}")
        print(f"  - Output directory: {system.output_dir}")
    except Exception as e:
        print(f"✗ System initialization failed: {e}")
        return False

    # Test user guide generation
    print("\n2. Testing User Guide Generation")
    print("-" * 60)

    try:
        result = generate_user_guide(
            title="NBA Analytics User Guide",
            description="Comprehensive guide for NBA analytics tools and formulas",
        )

        print("✓ User guide generated successfully")
        print(f"  - Guide ID: {result.get('guide_id', 'N/A')}")
        print(f"  - Content length: {result.get('content_length', 0)} characters")
        print(f"  - Sections: {result.get('sections', 0)}")
        print(f"  - Status: {result.get('status', 'N/A')}")
    except Exception as e:
        print(f"✗ User guide generation failed: {e}")

    # Test API documentation generation
    print("\n3. Testing API Documentation Generation")
    print("-" * 60)

    try:
        result = generate_api_documentation(
            title="NBA MCP Server API Reference",
            description="Complete API reference for NBA MCP Server",
        )

        print("✓ API documentation generated successfully")
        print(f"  - API ID: {result.get('api_id', 'N/A')}")
        print(f"  - Endpoints: {result.get('endpoints_count', 0)}")
        print(f"  - Content length: {result.get('content_length', 0)} characters")
        print(f"  - Status: {result.get('status', 'N/A')}")
    except Exception as e:
        print(f"✗ API documentation generation failed: {e}")

    # Test tutorial generation
    print("\n4. Testing Tutorial Generation")
    print("-" * 60)

    try:
        result = generate_tutorial(
            title="Getting Started with NBA Analytics",
            level="beginner",
            objectives=[
                "Understand basic NBA statistics",
                "Learn to use formula tools",
                "Create your first analysis",
            ],
        )

        print("✓ Tutorial generated successfully")
        print(f"  - Tutorial ID: {result.get('tutorial_id', 'N/A')}")
        print(f"  - Steps: {result.get('steps_count', 0)}")
        print(f"  - Level: {result.get('level', 'N/A')}")
        print(f"  - Objectives: {result.get('objectives_count', 0)}")
    except Exception as e:
        print(f"✗ Tutorial generation failed: {e}")

    # Test quick start guide generation
    print("\n5. Testing Quick Start Guide Generation")
    print("-" * 60)

    try:
        result = generate_quick_start_guide(title="NBA Analytics Quick Start")

        print("✓ Quick start guide generated successfully")
        print(f"  - QuickStart ID: {result.get('quickstart_id', 'N/A')}")
        print(f"  - Sections: {result.get('sections', 0)}")
        print(f"  - Content length: {result.get('content_length', 0)} characters")
        print(f"  - Status: {result.get('status', 'N/A')}")
    except Exception as e:
        print(f"✗ Quick start guide generation failed: {e}")

    # Test training module creation
    print("\n6. Testing Training Module Creation")
    print("-" * 60)

    try:
        result = create_training_module(
            title="Advanced NBA Analytics",
            description="Comprehensive training on advanced NBA analytics techniques",
            level="advanced",
        )

        print("✓ Training module created successfully")
        print(f"  - Module ID: {result.get('module_id', 'N/A')}")
        print(f"  - Duration: {result.get('duration_minutes', 0)} minutes")
        print(f"  - Objectives: {result.get('objectives_count', 0)}")
        print(f"  - Assessment questions: {result.get('assessment_questions', 0)}")
    except Exception as e:
        print(f"✗ Training module creation failed: {e}")

    # Test comprehensive documentation generation
    print("\n7. Testing Comprehensive Documentation Generation")
    print("-" * 60)

    try:
        result = generate_comprehensive_documentation(
            project_title="NBA MCP Server Complete Documentation"
        )

        print("✓ Comprehensive documentation generated successfully")
        print(f"  - Project ID: {result.get('project_id', 'N/A')}")
        print(f"  - Total files: {result.get('total_files', 0)}")
        print(f"  - Components: {len(result.get('components', {}))}")
        print(f"  - Status: {result.get('status', 'N/A')}")
    except Exception as e:
        print(f"✗ Comprehensive documentation generation failed: {e}")

    # Test documentation export
    print("\n8. Testing Documentation Export")
    print("-" * 60)

    try:
        result = export_documentation(format_type="html", doc_id="test_doc_001")

        print("✓ Documentation export successful")
        print(f"  - Status: {result.get('status', 'N/A')}")
        print(f"  - Output file: {result.get('output_file', 'N/A')}")
        print(f"  - Format: {result.get('format', 'N/A')}")
        print(f"  - Content length: {result.get('content_length', 0)} characters")
    except Exception as e:
        print(f"✗ Documentation export failed: {e}")

    # Test documentation status
    print("\n9. Testing Documentation Status")
    print("-" * 60)

    try:
        result = get_documentation_status()

        print("✓ Documentation status retrieved successfully")
        print(f"  - Total docs: {result.get('total_docs', 0)}")
        print(f"  - Training modules: {result.get('total_modules', 0)}")
        print(f"  - Available formats: {len(result.get('available_formats', []))}")
        print(f"  - Status: {result.get('status', 'N/A')}")
    except Exception as e:
        print(f"✗ Documentation status retrieval failed: {e}")

    return True


def test_standalone_functions():
    """Test standalone documentation functions"""
    print("\n10. Testing Standalone Functions")
    print("-" * 60)

    # Test various documentation types
    doc_types = [
        ("user_guide", "User Guide"),
        ("api_documentation", "API Documentation"),
        ("tutorial", "Tutorial"),
        ("reference_guide", "Reference Guide"),
        ("training_material", "Training Material"),
        ("quick_start", "Quick Start"),
        ("troubleshooting", "Troubleshooting"),
        ("examples", "Examples"),
    ]

    for doc_type, doc_name in doc_types:
        try:
            if doc_type == "user_guide":
                result = generate_user_guide(
                    title=f"Test {doc_name}",
                    description=f"Test {doc_name} for NBA analytics",
                )
            elif doc_type == "api_documentation":
                result = generate_api_documentation(
                    title=f"Test {doc_name}",
                    description=f"Test {doc_name} for NBA analytics",
                )
            elif doc_type == "tutorial":
                result = generate_tutorial(
                    title=f"Test {doc_name}",
                    level="beginner",
                    objectives=["Learn basics", "Practice examples"],
                )
            elif doc_type == "quick_start":
                result = generate_quick_start_guide(title=f"Test {doc_name}")
            else:
                result = generate_user_guide(
                    title=f"Test {doc_name}",
                    description=f"Test {doc_name} for NBA analytics",
                )

            print(
                f"✓ {doc_name} generated: {result.get('guide_id', result.get('api_id', result.get('tutorial_id', result.get('quickstart_id', 'N/A'))))}"
            )
        except Exception as e:
            print(f"✗ {doc_name} generation failed: {e}")


def test_error_handling():
    """Test error handling scenarios"""
    print("\n11. Testing Error Handling")
    print("-" * 60)

    # Test invalid parameters
    test_cases = [
        ("Empty title", lambda: generate_user_guide("", "Test")),
        (
            "Invalid level",
            lambda: generate_tutorial("Test Tutorial", "invalid", ["test"]),
        ),
        ("Invalid format", lambda: export_documentation("invalid", "test")),
    ]

    for test_name, test_func in test_cases:
        try:
            result = test_func()
            if result.get("status") == "error":
                print(f"✓ {test_name}: Handled error correctly")
            else:
                print(f"✗ {test_name}: Should have failed but didn't")
        except Exception as e:
            print(f"✓ {test_name}: Handled error correctly - {str(e)[:50]}...")


def test_integration_scenarios():
    """Test integration scenarios"""
    print("\n12. Testing Integration Scenarios")
    print("-" * 60)

    # Scenario 1: Complete documentation workflow
    print("Scenario 1: Complete Documentation Workflow")
    try:
        # Generate user guide
        user_guide = generate_user_guide(
            title="NBA Analytics Complete Guide",
            description="Complete guide for NBA analytics",
        )

        # Generate API docs
        api_docs = generate_api_documentation(
            title="NBA MCP API Reference",
            description="API reference for NBA MCP Server",
        )

        # Create tutorial
        tutorial = generate_tutorial(
            title="NBA Analytics Tutorial",
            level="intermediate",
            objectives=["Learn NBA metrics", "Use analytics tools"],
        )

        # Generate comprehensive documentation
        comprehensive = generate_comprehensive_documentation(
            project_title="NBA Analytics Suite"
        )

        print("✓ Complete workflow executed successfully")
        print(f"  - User guide: {user_guide.get('guide_id', 'N/A')}")
        print(f"  - API docs: {api_docs.get('api_id', 'N/A')}")
        print(f"  - Tutorial: {tutorial.get('tutorial_id', 'N/A')}")
        print(f"  - Comprehensive: {comprehensive.get('project_id', 'N/A')}")

    except Exception as e:
        print(f"✗ Complete workflow failed: {e}")

    # Scenario 2: Multi-format export
    print("\nScenario 2: Multi-Format Export")
    try:
        formats = ["html", "json", "rst"]

        for fmt in formats:
            result = export_documentation(format_type=fmt, doc_id="test_multi_format")
            print(f"✓ {fmt.upper()} export: {result.get('status', 'N/A')}")

    except Exception as e:
        print(f"✗ Multi-format export failed: {e}")


def test_performance_benchmarks():
    """Test performance benchmarks"""
    print("\n13. Testing Performance Benchmarks")
    print("-" * 60)

    # Benchmark documentation generation
    start_time = datetime.now()

    try:
        # Generate multiple documents
        results = []
        for i in range(5):
            result = generate_user_guide(
                title=f"Performance Test Guide {i+1}",
                description=f"Performance test guide {i+1}",
            )
            results.append(result)

        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()
        print(f"✓ Generated {len(results)} documents in {duration:.2f} seconds")
        print(f"  - Average time per document: {duration/len(results):.2f} seconds")

    except Exception as e:
        print(f"✗ Performance benchmark failed: {e}")


def main():
    """Main test function"""
    print("Starting Phase 10.3: Documentation & Training System Tests")
    print(f"Test started at: {datetime.now()}")

    try:
        # Run all tests
        test_documentation_system()
        test_standalone_functions()
        test_error_handling()
        test_integration_scenarios()
        test_performance_benchmarks()

        print("\n" + "=" * 80)
        print("Phase 10.3: Documentation & Training System Tests Completed")
        print("=" * 80)
        print(f"Test completed at: {datetime.now()}")

    except Exception as e:
        print(f"\nTest suite failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
