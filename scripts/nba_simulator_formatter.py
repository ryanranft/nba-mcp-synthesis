#!/usr/bin/env python3
"""
NBA Simulator Formatter

Transforms recommendations from basic format to nba-simulator-aws directory structure.
Maps recommendations to phases, generates complete file sets, and maintains indices.

Usage:
    python3 scripts/nba_simulator_formatter.py \\
        --synthesis implementation_plans/consolidated_recommendations.json \\
        --output /Users/ryanranft/nba-simulator-aws/docs/phases \\
        --update-indices
"""

import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NBASimulatorFormatter:
    """Format recommendations for nba-simulator-aws project structure."""

    # Phase mapping keywords
    PHASE_KEYWORDS = {
        0: ['data collection', 'extraction', 'ingestion', 'scraping', 'api', 'raw data', 'source'],
        1: ['data quality', 'validation', 'cleaning', 'preprocessing', 'data integrity', 'quality check'],
        2: ['feature engineering', 'etl', 'transformation', 'feature', 'preprocessing pipeline'],
        3: ['database', 'storage', 'infrastructure', 'postgres', 'sql', 'data warehouse', 'schema'],
        4: ['simulation', 'game engine', 'game logic', 'monte carlo', 'simulator'],
        5: ['ml', 'machine learning', 'model', 'training', 'prediction', 'classifier', 'regression', 'neural network', 'deep learning'],
        6: ['api', 'serving', 'deployment', 'endpoint', 'rest api', 'prediction service'],
        7: ['betting', 'odds', 'bookmaker', 'wagering', 'line', 'spread'],
        8: ['analytics', 'real-time', 'streaming', 'advanced analytics', 'dashboard'],
        9: ['monitoring', 'observability', 'logging', 'metrics', 'alerting', 'drift detection']
    }

    def __init__(self, synthesis_file: str, output_base: str):
        """
        Initialize formatter.

        Args:
            synthesis_file: Path to consolidated_recommendations.json
            output_base: Base output directory (/path/to/nba-simulator-aws/docs/phases)
        """
        self.synthesis_file = Path(synthesis_file)
        self.output_base = Path(output_base)
        self.recommendations = []
        self.phase_mapping = {}  # rec_id -> phase
        self.phase_counters = {i: 1 for i in range(10)}  # Track subdirectory numbers per phase

        logger.info(f"📂 Synthesis file: {self.synthesis_file}")
        logger.info(f"📂 Output base: {self.output_base}")

    def load_recommendations(self):
        """Load recommendations from synthesis file."""
        logger.info(f"📖 Loading recommendations from {self.synthesis_file}")

        with open(self.synthesis_file, 'r') as f:
            data = json.load(f)

        self.recommendations = data.get('recommendations', [])
        logger.info(f"✅ Loaded {len(self.recommendations)} recommendations")

    def map_recommendation_to_phase(self, rec: Dict) -> int:
        """
        Map recommendation to appropriate phase based on keywords.

        Args:
            rec: Recommendation dictionary

        Returns:
            Phase number (0-9)
        """
        title = rec.get('title', '').lower()
        description = rec.get('description', '').lower()
        category = rec.get('category', '').lower()
        text = f"{title} {description} {category}"

        # Score each phase
        scores = {}
        for phase, keywords in self.PHASE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[phase] = score

        # Return phase with highest score, default to 5 (ML) if no match
        if not scores:
            logger.warning(f"⚠️  No phase match for: {title[:50]}... -> Defaulting to Phase 5")
            return 5

        best_phase = max(scores, key=scores.get)
        return best_phase

    def sanitize_dirname(self, text: str) -> str:
        """
        Sanitize text for directory name.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized directory name
        """
        # Convert to lowercase, replace spaces with underscores
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '_', text)
        text = text[:60]  # Limit length
        return text

    def create_subdirectory(self, phase: int, rec: Dict, rec_idx: int) -> Path:
        """
        Create subdirectory for recommendation.

        Args:
            phase: Phase number
            rec: Recommendation dictionary
            rec_idx: Recommendation index (1-based)

        Returns:
            Path to created subdirectory
        """
        # Create subdirectory name: {phase}.{counter}_{topic}
        counter = self.phase_counters[phase]
        self.phase_counters[phase] += 1

        topic = self.sanitize_dirname(rec['title'])
        dirname = f"{phase}.{counter}_{topic}"

        # Create full path
        phase_dir = self.output_base / f"phase_{phase}"
        subdir = phase_dir / dirname
        subdir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📁 Created: phase_{phase}/{dirname}")
        return subdir

    def generate_readme(self, rec: Dict, phase: int, subdir: Path, rec_idx: int):
        """Generate README.md for recommendation."""
        priority_emoji = {
            'critical': '⭐ CRITICAL',
            'important': '🟡 IMPORTANT',
            'nice-to-have': '🟢 NICE-TO-HAVE'
        }

        priority = rec.get('priority', 'important')
        priority_display = priority_emoji.get(priority, '🟡 IMPORTANT')

        # Extract subdirectory name
        subdir_name = subdir.name
        subdir_num = subdir_name.split('_')[0]

        readme_content = f"""# {subdir_num}: {rec['title']}

**Sub-Phase:** {subdir_num} ({rec.get('category', 'General')})
**Parent Phase:** [Phase {phase}: {self._get_phase_name(phase)}](../PHASE_{phase}_INDEX.md)
**Status:** 🔵 PLANNED
**Priority:** {priority_display}
**Implementation ID:** rec_{rec_idx:03d}

---

## Overview

{rec.get('description', 'No description provided.')}

**Key Capabilities:**
{self._format_list_from_text(rec.get('technical_details', ''))}

**Impact:**
{rec.get('expected_impact', 'Enhances system capabilities and reliability.')}

---

## Quick Start

```python
from implement_rec_{rec_idx:03d} import Implement{self._to_class_name(rec['title'])}

# Initialize implementation
impl = Implement{self._to_class_name(rec['title'])}()
impl.setup()

# Execute implementation
results = impl.execute()

print(f"Implementation complete: {{results}}")
```

---

## Architecture

### Implementation Steps

{self._format_implementation_steps(rec.get('implementation_steps', []))}

---

## Implementation Files

| File | Purpose |
|------|---------|
| **implement_rec_{rec_idx:03d}.py** | Main implementation |
| **test_rec_{rec_idx:03d}.py** | Test suite |
| **STATUS.md** | Implementation status |
| **RECOMMENDATIONS_FROM_BOOKS.md** | Source book recommendations |
| **IMPLEMENTATION_GUIDE.md** | Detailed implementation guide |

---

## Configuration

```python
# Configuration example
config = {{
    "enabled": True,
    "mode": "production",
    # Add specific configuration parameters
}}

impl = Implement{self._to_class_name(rec['title'])}(config=config)
```

---

## Performance Characteristics

**Estimated Time:** {rec.get('time_estimate', '8-16 hours')}

---

## Dependencies

**Prerequisites:**
{self._format_dependencies(rec.get('dependencies', []))}

**Enables:**
- Enhanced system capabilities
- Improved prediction accuracy
- Better maintainability

---

## Usage Examples

### Example 1: Basic Usage

```python
# Basic implementation
from implement_rec_{rec_idx:03d} import Implement{self._to_class_name(rec['title'])}

impl = Implement{self._to_class_name(rec['title'])}()
impl.setup()
results = impl.execute()
```

---

## Integration with Other Sub-Phases

This recommendation integrates with:
- Phase {phase} components
- Cross-phase dependencies as specified

---

## Testing

```bash
# Run test suite
cd {subdir}
python test_rec_{rec_idx:03d}.py -v
```

---

## Troubleshooting

**Common Issues:**
- See IMPLEMENTATION_GUIDE.md for detailed troubleshooting

---

## Related Documentation

- **[STATUS.md](STATUS.md)** - Implementation status
- **[RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md)** - Source recommendations
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Detailed guide
- **[Phase {phase} Index](../PHASE_{phase}_INDEX.md)** - Parent phase overview

---

## Navigation

**Return to:** [Phase {phase}: {self._get_phase_name(phase)}](../PHASE_{phase}_INDEX.md)

---

**Last Updated:** {datetime.now().strftime('%B %d, %Y')}
**Maintained By:** NBA Simulator AWS Team
**Source:** {rec.get('source_book', 'Book recommendations')}
"""

        readme_path = subdir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)

    def generate_status(self, rec: Dict, subdir: Path, rec_idx: int):
        """Generate STATUS.md for recommendation."""
        priority_display = rec.get('priority', 'important').upper()

        status_content = f"""# Recommendation Status: {rec['title']}

**ID:** rec_{rec_idx:03d}
**Name:** {rec['title']}
**Phase:** {self.phase_mapping.get(f'rec_{rec_idx:03d}', 0)} ({rec.get('category', 'General')})
**Source Books:** {rec.get('source_book', 'Various technical books')}
**Priority:** {priority_display}
**Status:** 🔵 **PLANNED**

---

## Implementation Summary

**Estimated Time:** {rec.get('time_estimate', '8-16 hours')}
**Dependencies:** {len(rec.get('dependencies', []))} dependencies

---

## Description

{rec.get('description', 'No description provided.')}

---

## Expected Impact

{rec.get('expected_impact', 'Enhances system capabilities.')}

---

## Implementation Checklist

### Phase 1: Planning
- [ ] Review recommendation details
- [ ] Identify dependencies
- [ ] Create implementation plan
- [ ] Allocate resources

### Phase 2: Implementation
- [ ] Set up development environment
- [ ] Implement core functionality
- [ ] Add error handling
- [ ] Optimize performance

### Phase 3: Testing
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Perform manual testing
- [ ] Validate edge cases

### Phase 4: Documentation
- [ ] Update README.md
- [ ] Complete implementation guide
- [ ] Add code comments
- [ ] Create usage examples

### Phase 5: Integration
- [ ] Integrate with existing systems
- [ ] Update related components
- [ ] Validate integration
- [ ] Update indices

### Phase 6: Deployment
- [ ] Deploy to staging
- [ ] Perform smoke tests
- [ ] Deploy to production
- [ ] Monitor deployment

---

## Dependencies

{self._format_dependencies_detailed(rec.get('dependencies', []))}

---

## Files

| File | Status | Purpose |
|------|--------|---------|
| implement_rec_{rec_idx:03d}.py | 🔵 Planned | Main implementation |
| test_rec_{rec_idx:03d}.py | 🔵 Planned | Test suite |
| README.md | ✅ Complete | Documentation |
| STATUS.md | ✅ Complete | This file |
| RECOMMENDATIONS_FROM_BOOKS.md | ✅ Complete | Source references |
| IMPLEMENTATION_GUIDE.md | 🔵 Planned | Detailed guide |

---

## Related Documentation

- [README.md](README.md) - Overview and quick start
- [RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md) - Source recommendations
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Detailed implementation guide

---

**Last Updated:** {datetime.now().strftime('%B %d, %Y')}
**Maintained By:** NBA Simulator AWS Team
"""

        status_path = subdir / "STATUS.md"
        with open(status_path, 'w') as f:
            f.write(status_content)

    def generate_recommendations_from_books(self, rec: Dict, subdir: Path, rec_idx: int):
        """Generate RECOMMENDATIONS_FROM_BOOKS.md."""
        priority_display = rec.get('priority', 'important').upper()

        content = f"""# Book Recommendations - rec_{rec_idx:03d}

**Recommendation:** {rec['title']}
**Source Book:** {rec.get('source_book', 'Various technical books')}
**Priority:** {priority_display}
**Added:** {datetime.now().strftime('%Y-%m-%d')}

---

## Source Information

**Book:** {rec.get('source_book', 'Unknown')}
**Chapter:** {rec.get('source_chapter', 'N/A')}
**Category:** {rec.get('category', 'General')}

---

## Recommendation Details

{rec.get('description', 'No description provided.')}

---

## Technical Details

{rec.get('technical_details', 'No technical details provided.')}

---

## Expected Impact

{rec.get('expected_impact', 'Enhances system capabilities.')}

---

## Implementation Priority

**Priority Level:** {priority_display}
**Estimated Time:** {rec.get('time_estimate', '8-16 hours')}

---

## Dependencies

{self._format_dependencies_detailed(rec.get('dependencies', []))}

---

## Related Recommendations

- See Phase index for related recommendations in this category
- Check IMPLEMENTATION_GUIDE.md for integration details

---

**Generated:** {datetime.now().strftime('%B %d, %Y')}
**Source:** Book Analysis System
"""

        path = subdir / "RECOMMENDATIONS_FROM_BOOKS.md"
        with open(path, 'w') as f:
            f.write(content)

    def generate_implementation_guide(self, rec: Dict, subdir: Path, rec_idx: int):
        """Generate detailed implementation guide."""
        content = f"""# Implementation Guide: {rec['title']}

**Recommendation ID:** rec_{rec_idx:03d}
**Priority:** {rec.get('priority', 'important').upper()}
**Estimated Time:** {rec.get('time_estimate', '8-16 hours')}

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Implementation Steps](#implementation-steps)
4. [Testing Strategy](#testing-strategy)
5. [Integration Points](#integration-points)
6. [Troubleshooting](#troubleshooting)
7. [Performance Considerations](#performance-considerations)

---

## Overview

### Purpose

{rec.get('description', 'No description provided.')}

### Expected Outcomes

{rec.get('expected_impact', 'Enhances system capabilities.')}

### Technical Approach

{rec.get('technical_details', 'No technical details provided.')}

---

## Prerequisites

### System Requirements

- Python 3.9+
- Required libraries (see requirements.txt)
- Database access (if applicable)
- API credentials (if applicable)

### Dependencies

{self._format_dependencies_detailed(rec.get('dependencies', []))}

### Knowledge Requirements

- Understanding of NBA simulator architecture
- Familiarity with the specific domain area
- Python programming experience

---

## Implementation Steps

{self._format_implementation_steps_detailed(rec.get('implementation_steps', []))}

---

## Testing Strategy

### Unit Tests

```python
# Test individual components
import unittest
from implement_rec_{rec_idx:03d} import Implement{self._to_class_name(rec['title'])}

class TestRec{rec_idx:03d}(unittest.TestCase):
    def test_setup(self):
        impl = Implement{self._to_class_name(rec['title'])}()
        result = impl.setup()
        self.assertIsNotNone(result)

    def test_execution(self):
        impl = Implement{self._to_class_name(rec['title'])}()
        impl.setup()
        result = impl.execute()
        self.assertTrue(result['success'])
```

### Integration Tests

- Test interaction with existing components
- Validate data flow
- Verify error handling

### Performance Tests

- Measure execution time
- Monitor memory usage
- Validate scalability

---

## Integration Points

### Input Dependencies

{self._format_dependencies_detailed(rec.get('dependencies', []))}

### Output Consumers

- Components that will use the output of this implementation
- Downstream processes that depend on this functionality

### Data Flow

1. Input data sources
2. Processing steps
3. Output destinations
4. Error handling paths

---

## Troubleshooting

### Common Issues

#### Issue 1: Setup Failures

**Symptom:** Setup fails with error message
**Cause:** Missing dependencies or incorrect configuration
**Solution:** Verify all prerequisites are met

#### Issue 2: Performance Issues

**Symptom:** Slow execution
**Cause:** Inefficient algorithms or data structures
**Solution:** Profile code and optimize bottlenecks

#### Issue 3: Integration Failures

**Symptom:** Errors when integrating with other components
**Cause:** API mismatches or data format issues
**Solution:** Verify interface contracts and data schemas

---

## Performance Considerations

### Optimization Strategies

- Use efficient algorithms and data structures
- Implement caching where appropriate
- Batch operations when possible
- Monitor resource usage

### Scalability

- Design for horizontal scaling
- Use asynchronous processing where appropriate
- Implement proper error handling and retries

---

## Related Documentation

- [README.md](README.md) - Overview and quick start
- [STATUS.md](STATUS.md) - Implementation status
- [RECOMMENDATIONS_FROM_BOOKS.md](RECOMMENDATIONS_FROM_BOOKS.md) - Source references

---

**Last Updated:** {datetime.now().strftime('%B %d, %Y')}
**Author:** NBA Simulator AWS Team
"""

        path = subdir / "IMPLEMENTATION_GUIDE.md"
        with open(path, 'w') as f:
            f.write(content)

    def generate_implementation_skeleton(self, rec: Dict, subdir: Path, rec_idx: int):
        """Generate implement_rec_XXX.py skeleton."""
        class_name = self._to_class_name(rec['title'])

        content = f'''#!/usr/bin/env python3
"""
Implementation: {rec['title']}

Recommendation ID: rec_{rec_idx:03d}
Source: {rec.get('source_book', 'Book recommendations')}
Priority: {rec.get('priority', 'important').upper()}

Description:
{rec.get('description', 'No description provided.')}

Expected Impact:
{rec.get('expected_impact', 'Enhances system capabilities.')}
"""

import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class {class_name}:
    """
    {rec['title']}.

    Based on recommendation from: {rec.get('source_book', 'Book analysis')}
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize {rec['title']} implementation.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {{}}
        self.initialized = False
        logger.info(f"Initialized {{self.__class__.__name__}}")

    def setup(self) -> Dict[str, Any]:
        """
        Set up the implementation.

        Returns:
            Setup results
        """
        logger.info("Setting up implementation...")

        # TODO: Implement setup logic
        # - Initialize resources
        # - Validate configuration
        # - Prepare dependencies

        self.initialized = True
        logger.info("✅ Setup complete")

        return {{
            "success": True,
            "message": "Setup completed successfully"
        }}

    def execute(self) -> Dict[str, Any]:
        """
        Execute the main implementation.

        Returns:
            Execution results
        """
        if not self.initialized:
            raise RuntimeError("Must call setup() before execute()")

        logger.info("Executing implementation...")

        # TODO: Implement core logic
        # Implementation steps:
{self._format_steps_as_comments(rec.get('implementation_steps', []))}

        logger.info("✅ Execution complete")

        return {{
            "success": True,
            "message": "Execution completed successfully"
        }}

    def validate(self) -> bool:
        """
        Validate the implementation results.

        Returns:
            True if validation passes
        """
        logger.info("Validating implementation...")

        # TODO: Implement validation logic
        # - Verify outputs
        # - Check data quality
        # - Validate integration points

        logger.info("✅ Validation complete")
        return True

    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up resources...")
        # TODO: Implement cleanup logic
        self.initialized = False


def main():
    """Main execution function."""
    print(f"=" * 80)
    print(f"{rec['title']}")
    print(f"=" * 80)

    # Initialize
    impl = {class_name}()

    # Setup
    setup_result = impl.setup()
    print(f"\\nSetup: {{setup_result['message']}}")

    # Execute
    exec_result = impl.execute()
    print(f"Execution: {{exec_result['message']}}")

    # Validate
    is_valid = impl.validate()
    print(f"Validation: {{'✅ Passed' if is_valid else '❌ Failed'}}")

    # Cleanup
    impl.cleanup()
    print(f"\\n✅ Implementation complete!")


if __name__ == "__main__":
    main()
'''

        path = subdir / f"implement_rec_{rec_idx:03d}.py"
        with open(path, 'w') as f:
            f.write(content)

    def generate_test_skeleton(self, rec: Dict, subdir: Path, rec_idx: int):
        """Generate test_rec_XXX.py skeleton."""
        class_name = self._to_class_name(rec['title'])

        content = f'''#!/usr/bin/env python3
"""
Test Suite: {rec['title']}

Tests for rec_{rec_idx:03d} implementation.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from implement_rec_{rec_idx:03d} import {class_name}


class TestRec{rec_idx:03d}(unittest.TestCase):
    """Test suite for {rec['title']}."""

    def setUp(self):
        """Set up test fixtures."""
        self.impl = {class_name}()

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.impl, 'cleanup'):
            self.impl.cleanup()

    def test_initialization(self):
        """Test that implementation initializes correctly."""
        self.assertIsNotNone(self.impl)
        self.assertFalse(self.impl.initialized)

    def test_setup(self):
        """Test setup method."""
        result = self.impl.setup()
        self.assertTrue(result['success'])
        self.assertTrue(self.impl.initialized)

    def test_execute_without_setup(self):
        """Test that execute fails without setup."""
        with self.assertRaises(RuntimeError):
            self.impl.execute()

    def test_execute_with_setup(self):
        """Test successful execution."""
        self.impl.setup()
        result = self.impl.execute()
        self.assertTrue(result['success'])

    def test_validate(self):
        """Test validation method."""
        self.impl.setup()
        self.impl.execute()
        is_valid = self.impl.validate()
        self.assertTrue(is_valid)

    def test_cleanup(self):
        """Test cleanup method."""
        self.impl.setup()
        self.impl.cleanup()
        self.assertFalse(self.impl.initialized)

    # TODO: Add more specific tests
    # - Test edge cases
    # - Test error handling
    # - Test integration points
    # - Test performance


def run_tests():
    """Run test suite."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRec{rec_idx:03d})
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
'''

        path = subdir / f"test_rec_{rec_idx:03d}.py"
        with open(path, 'w') as f:
            f.write(content)

    def format_all_recommendations(self):
        """Format all recommendations."""
        logger.info(f"\n🚀 Starting formatting of {len(self.recommendations)} recommendations\n")

        for idx, rec in enumerate(self.recommendations, 1):
            try:
                # Map to phase
                phase = self.map_recommendation_to_phase(rec)
                rec_id = f"rec_{idx:03d}"
                self.phase_mapping[rec_id] = phase

                logger.info(f"[{idx}/{len(self.recommendations)}] {rec['title'][:50]}... -> Phase {phase}")

                # Create subdirectory
                subdir = self.create_subdirectory(phase, rec, idx)

                # Generate all files
                self.generate_readme(rec, phase, subdir, idx)
                self.generate_status(rec, subdir, idx)
                self.generate_recommendations_from_books(rec, subdir, idx)
                self.generate_implementation_guide(rec, subdir, idx)
                self.generate_implementation_skeleton(rec, subdir, idx)
                self.generate_test_skeleton(rec, subdir, idx)

            except Exception as e:
                logger.error(f"❌ Error formatting rec_{idx:03d}: {e}")
                continue

        logger.info(f"\n✅ Formatted {len(self.recommendations)} recommendations")

    def update_phase_indices(self):
        """Update phase index files."""
        logger.info("\n📝 Updating phase indices...")

        for phase in range(10):
            phase_dir = self.output_base / f"phase_{phase}"
            if not phase_dir.exists():
                continue

            # Count recommendations in this phase
            rec_count = sum(1 for p in self.phase_mapping.values() if p == phase)
            if rec_count == 0:
                continue

            # Create/update phase index
            index_path = phase_dir / f"PHASE_{phase}_INDEX.md"
            index_content = f"""# Phase {phase}: {self._get_phase_name(phase)}

**Total Recommendations:** {rec_count}
**Status:** 🔵 PLANNED
**Last Updated:** {datetime.now().strftime('%B %d, %Y')}

---

## Overview

Phase {phase} focuses on: {self._get_phase_description(phase)}

---

## Sub-Phases

"""

            # List all subdirectories in this phase
            subdirs = sorted([d for d in phase_dir.iterdir() if d.is_dir() and d.name.startswith(f"{phase}.")])
            for subdir in subdirs:
                index_content += f"- [{subdir.name}]({subdir.name}/README.md)\n"

            index_content += f"""

---

## Navigation

**Previous Phase:** [Phase {phase - 1}](../phase_{phase - 1}/PHASE_{phase - 1}_INDEX.md) (if {phase} > 0)
**Next Phase:** [Phase {phase + 1}](../phase_{phase + 1}/PHASE_{phase + 1}_INDEX.md) (if {phase} < 9)

---

**Generated:** {datetime.now().strftime('%B %d, %Y')}
"""

            with open(index_path, 'w') as f:
                f.write(index_content)

            logger.info(f"  ✅ Updated PHASE_{phase}_INDEX.md ({rec_count} recommendations)")

    # Helper methods
    def _get_phase_name(self, phase: int) -> str:
        """Get human-readable phase name."""
        names = {
            0: "Data Collection",
            1: "Data Quality",
            2: "Feature Engineering",
            3: "Database & Infrastructure",
            4: "Simulation Engine",
            5: "Machine Learning",
            6: "Prediction API",
            7: "Betting Integration",
            8: "Advanced Analytics",
            9: "Monitoring & Observability"
        }
        return names.get(phase, f"Phase {phase}")

    def _get_phase_description(self, phase: int) -> str:
        """Get phase description."""
        descriptions = {
            0: "data collection, scraping, and ingestion from various sources",
            1: "data quality, validation, cleaning, and preprocessing",
            2: "feature engineering, transformation, and ETL pipelines",
            3: "database design, storage infrastructure, and schema management",
            4: "simulation engine, game logic, and Monte Carlo simulations",
            5: "machine learning models, training pipelines, and predictions",
            6: "prediction serving, REST API, and deployment",
            7: "betting odds integration and wagering systems",
            8: "advanced analytics, real-time processing, and dashboards",
            9: "monitoring, observability, logging, and drift detection"
        }
        return descriptions.get(phase, f"phase {phase} implementation")

    def _to_class_name(self, text: str) -> str:
        """Convert text to PascalCase class name."""
        words = re.sub(r'[^\w\s]', '', text).split()
        return ''.join(word.capitalize() for word in words)

    def _format_list_from_text(self, text: str) -> str:
        """Format text as bullet list."""
        if not text:
            return "- No details provided"
        sentences = text.split('. ')
        return '\n'.join(f"- {s.strip()}" for s in sentences if s.strip())

    def _format_implementation_steps(self, steps: List[str]) -> str:
        """Format implementation steps."""
        if not steps:
            return "1. Review requirements\n2. Implement solution\n3. Test thoroughly\n4. Deploy to production"
        return '\n'.join(f"{i}. {step}" for i, step in enumerate(steps, 1))

    def _format_implementation_steps_detailed(self, steps: List[str]) -> str:
        """Format implementation steps with detailed sections."""
        if not steps:
            return "### Step 1: Review Requirements\n\nAnalyze the requirements and plan the implementation.\n"

        content = ""
        for i, step in enumerate(steps, 1):
            content += f"### Step {i}: {step}\n\n"
            content += "**Actions:**\n- TODO: Detail actions for this step\n\n"
            content += "**Expected Outcome:**\n- TODO: Define expected outcome\n\n"
        return content

    def _format_dependencies(self, deps: List[str]) -> str:
        """Format dependencies as bullet list."""
        if not deps:
            return "- No dependencies"
        return '\n'.join(f"- {dep}" for dep in deps)

    def _format_dependencies_detailed(self, deps: List[str]) -> str:
        """Format dependencies with details."""
        if not deps:
            return "**No dependencies identified.**"

        content = "**Required Prerequisites:**\n\n"
        for dep in deps:
            content += f"- {dep}\n"
        return content

    def _format_steps_as_comments(self, steps: List[str]) -> str:
        """Format steps as code comments."""
        if not steps:
            return "        # Step 1: Implement core functionality"
        return '\n'.join(f"        # {step}" for step in steps)


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Format recommendations for nba-simulator-aws")
    parser.add_argument('--synthesis', required=True, help='Path to consolidated_recommendations.json')
    parser.add_argument('--output', required=True, help='Output base directory')
    parser.add_argument('--update-indices', action='store_true', help='Update phase indices')

    args = parser.parse_args()

    formatter = NBASimulatorFormatter(args.synthesis, args.output)

    # Load recommendations
    formatter.load_recommendations()

    # Format all recommendations
    formatter.format_all_recommendations()

    # Update indices if requested
    if args.update_indices:
        formatter.update_phase_indices()

    # Print summary
    print(f"\n" + "=" * 80)
    print(f"✅ FORMATTING COMPLETE")
    print(f"=" * 80)
    print(f"Total recommendations: {len(formatter.recommendations)}")
    print(f"\nRecommendations by phase:")
    for phase in range(10):
        count = sum(1 for p in formatter.phase_mapping.values() if p == phase)
        if count > 0:
            print(f"  Phase {phase} ({formatter._get_phase_name(phase)}): {count} recommendations")
    print(f"\nOutput directory: {formatter.output_base}")
    print(f"=" * 80)


if __name__ == "__main__":
    main()







