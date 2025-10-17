#!/usr/bin/env python3
"""
Recommendation Integrator for Recommendation Organization & Integration System

Integrates recommendations from books into NBA_SIMULATOR_AWS project.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from phase_mapper import PhaseMapper

logger = logging.getLogger(__name__)


class RecommendationIntegrator:
    """
    Integrates recommendations from books into NBA_SIMULATOR_AWS project.
    """

    def __init__(self, simulator_path: str, synthesis_path: str):
        self.simulator_path = simulator_path
        self.synthesis_path = synthesis_path
        self.phase_mapper = PhaseMapper()

        # Ensure paths exist
        if not os.path.exists(simulator_path):
            raise ValueError(f"Simulator path does not exist: {simulator_path}")
        if not os.path.exists(synthesis_path):
            raise ValueError(f"Synthesis path does not exist: {synthesis_path}")

    def load_master_recommendations(self) -> Dict[str, Any]:
        """Load all recommendations from master DB."""
        master_file = os.path.join(
            self.synthesis_path, "analysis_results/master_recommendations.json"
        )

        if not os.path.exists(master_file):
            logger.warning(f"Master recommendations file not found: {master_file}")
            return {"recommendations": [], "by_category": {}, "by_book": {}}

        try:
            with open(master_file, "r") as f:
                data = json.load(f)
            logger.info(
                f"Loaded {len(data.get('recommendations', []))} recommendations from master DB"
            )
            return data
        except Exception as e:
            logger.error(f"Error loading master recommendations: {e}")
            return {"recommendations": [], "by_category": {}, "by_book": {}}

    def create_phase_recommendations(
        self, recommendations: Dict[str, Any]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Organize recommendations by phase.

        Args:
            recommendations: Master recommendations dictionary

        Returns:
            dict: {phase_num: [recommendations]}
        """
        phase_recs = {i: [] for i in range(10)}

        for rec in recommendations.get("recommendations", []):
            phases = self.phase_mapper.map_recommendation_to_phase(rec)
            for phase in phases:
                phase_recs[phase].append(rec)

        # Log phase distribution
        total_mapped = sum(len(recs) for recs in phase_recs.values())
        logger.info(f"Mapped {total_mapped} recommendations across phases")

        for phase, recs in phase_recs.items():
            if recs:
                logger.info(f"  Phase {phase}: {len(recs)} recommendations")

        return phase_recs

    def generate_phase_enhancement_docs(
        self, phase_recs: Dict[int, List[Dict[str, Any]]]
    ) -> List[str]:
        """
        Generate enhancement documents for each phase.

        Args:
            phase_recs: Phase recommendations dictionary

        Returns:
            list: List of generated file paths
        """
        generated_files = []

        for phase_num, recs in phase_recs.items():
            if not recs:
                continue

            output_path = os.path.join(
                self.simulator_path,
                f"docs/phases/phase_{phase_num}/RECOMMENDATIONS_FROM_BOOKS.md",
            )

            content = self._format_phase_recommendations(phase_num, recs)

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w") as f:
                f.write(content)

            generated_files.append(output_path)
            logger.info(f"Generated phase {phase_num} recommendations: {output_path}")

        return generated_files

    def _format_phase_recommendations(
        self, phase_num: int, recs: List[Dict[str, Any]]
    ) -> str:
        """Format recommendations for phase document."""
        critical = [r for r in recs if r.get("category") == "critical"]
        important = [r for r in recs if r.get("category") == "important"]
        nice = [r for r in recs if r.get("category") == "nice_to_have"]

        phase_desc = self.phase_mapper.get_phase_description(phase_num)

        content = f"""# Phase {phase_num} - Book Recommendations

**Generated:** {datetime.now().isoformat()}
**Source:** Technical book analysis ({len(set(r.get('source_books', ['Unknown'])[0] if r.get('source_books') else 'Unknown' for r in recs))} books)
**Total Recommendations:** {len(recs)}
**Phase Description:** {phase_desc}

---

## Overview

This document contains recommendations from technical book analysis that are relevant to Phase {phase_num} of the NBA Simulator AWS project.

**Phase Focus:** {phase_desc}

**Key Areas:**
{self._get_phase_keywords(phase_num)}

---

"""

        if critical:
            content += f"""## Critical Recommendations ({len(critical)})

{self._format_rec_list(critical)}

---
"""

        if important:
            content += f"""## Important Recommendations ({len(important)})

{self._format_rec_list(important)}

---
"""

        if nice:
            content += f"""## Nice-to-Have Recommendations ({len(nice)})

{self._format_rec_list(nice)}

---
"""

        content += f"""## Implementation Priority

1. **Address all Critical items first** - These are essential for project success
2. **Then Important items** - These provide significant value
3. **Finally Nice-to-Have items** - These enhance the project but aren't essential

---

## Source Books

The following books contributed recommendations to this phase:

{self._get_source_books(recs)}

---

## Next Steps

1. Review each recommendation carefully
2. Check for conflicts with existing Phase {phase_num} plans
3. Prioritize based on project timeline and resources
4. Create implementation tasks for approved recommendations
5. Update Phase {phase_num} documentation as needed

---

## Related Documentation

- [Phase {phase_num} Main Documentation](../phase_{phase_num}/)
- [Implementation Plans](../../../implementation_plans/)
- [Cross-Project Status](../../../CROSS_PROJECT_IMPLEMENTATION_STATUS.md)

---

*This document was automatically generated by the Recommendation Integration System.*
"""

        return content

    def _format_rec_list(self, recs: List[Dict[str, Any]]) -> str:
        """Format a list of recommendations."""
        if not recs:
            return "No recommendations in this category."

        formatted = []
        for i, rec in enumerate(recs, 1):
            title = rec.get("title", "Untitled Recommendation")
            source_books = rec.get("source_books", ["Unknown"])
            added_date = rec.get("added_date", "Unknown")
            rec_id = rec.get("id", f"rec_{i}")
            reasoning = rec.get("reasoning", "")

            formatted.append(
                f"""### {i}. {title}

**Source Books:** {', '.join(source_books)}
**Added:** {added_date}
**ID:** {rec_id}

{reasoning if reasoning else 'No additional reasoning provided.'}

"""
            )

        return "\n".join(formatted)

    def _get_phase_keywords(self, phase_num: int) -> str:
        """Get keywords for a phase as formatted list."""
        keywords = self.phase_mapper.phase_keywords.get(phase_num, [])
        if not keywords:
            return "- No specific keywords defined"

        # Format as bullet list, limiting to first 10 keywords
        limited_keywords = keywords[:10]
        return "\n".join(f"- {keyword}" for keyword in limited_keywords)

    def _get_source_books(self, recs: List[Dict[str, Any]]) -> str:
        """Get unique source books from recommendations."""
        books = set()
        for rec in recs:
            source_books = rec.get("source_books", [])
            if isinstance(source_books, list):
                books.update(source_books)
            else:
                books.add(str(source_books))

        if not books:
            return "- No source books identified"

        return "\n".join(f"- {book}" for book in sorted(books))

    def generate_integration_summary(
        self, phase_recs: Dict[int, List[Dict[str, Any]]]
    ) -> str:
        """
        Generate a summary of the integration process.

        Args:
            phase_recs: Phase recommendations dictionary

        Returns:
            str: Integration summary content
        """
        stats = self.phase_mapper.get_phase_statistics(phase_recs)

        content = f"""# Recommendation Integration Summary

**Generated:** {datetime.now().isoformat()}
**Integration Status:** Complete

---

## Overview

This summary reports the results of integrating book recommendations into the NBA Simulator AWS project.

### Key Metrics

- **Total Recommendations Processed:** {stats['total_recommendations']}
- **Phases with Recommendations:** {stats['phases_with_recommendations']}/10
- **Phase Documents Generated:** {stats['phases_with_recommendations']}
- **Safe Updates Applied:** TBD
- **Conflicts Pending Review:** TBD

---

## Recommendations by Category

| Category | Count | Percentage |
|----------|-------|------------|
| Critical | {stats['category_distribution']['critical']} | {(stats['category_distribution']['critical'] / max(1, stats['total_recommendations']) * 100):.1f}% |
| Important | {stats['category_distribution']['important']} | {(stats['category_distribution']['important'] / max(1, stats['total_recommendations']) * 100):.1f}% |
| Nice-to-Have | {stats['category_distribution']['nice_to_have']} | {(stats['category_distribution']['nice_to_have'] / max(1, stats['total_recommendations']) * 100):.1f}% |

---

## Phase Distribution

| Phase | Count | Status |
|-------|-------|--------|
"""

        for phase_num in range(10):
            count = stats["phase_distribution"].get(phase_num, 0)
            status = "✅ Generated" if count > 0 else "⏸️ No recommendations"
            phase_desc = self.phase_mapper.get_phase_description(phase_num)
            content += f"| {phase_num} | {count} | {status} |\n"

        content += f"""
---

## Generated Files

### Phase Enhancement Documents

"""

        for phase_num, count in stats["phase_distribution"].items():
            if count > 0:
                content += f"- **Phase {phase_num}:** `docs/phases/phase_{phase_num}/RECOMMENDATIONS_FROM_BOOKS.md`\n"

        content += f"""
---

## Integration Results

### Safe Updates Applied (TBD)

These recommendations were automatically integrated without conflicts:
- Enhancements to existing plans
- New additions that don't conflict with current approaches
- Non-conflicting improvements

### Conflicts Pending Review (TBD)

These recommendations require manual review:
- Conflicting approaches or technologies
- Contradictory requirements
- Major architectural changes

**Action Required:** Review PROPOSED_UPDATES.md files in phase directories

---

## Next Steps

### Immediate Actions

1. **Review Conflicts** (TBD items)
   - Check PROPOSED_UPDATES.md files
   - Resolve conflicts manually
   - Update phase plans as needed

2. **Verify Applied Updates** (TBD items)
   - Review automatically applied enhancements
   - Ensure they align with project goals
   - Adjust implementation details if needed

3. **Update Project Documentation**
   - Reflect changes in phase documentation
   - Update project timelines if needed
   - Communicate changes to team

### Long-term Actions

1. **Monitor Implementation Progress**
   - Track recommendation completion
   - Update cross-project status regularly
   - Identify new integration opportunities

2. **Refine Integration Process**
   - Improve conflict detection
   - Enhance automatic integration
   - Optimize phase mapping

---

## Files Generated

- **Phase Enhancement Docs:** {stats['phases_with_recommendations']} files in `docs/phases/phase_X/`
- **Cross-Project Status:** `CROSS_PROJECT_IMPLEMENTATION_STATUS.md`
- **Integration Summary:** `integration_summary.md`
- **Proposed Updates:** `docs/phases/phase_X/PROPOSED_UPDATES.md` (if conflicts exist)

---

*This summary was generated by the Recommendation Integration System.*
"""

        return content


def test_recommendation_integrator():
    """Test the RecommendationIntegrator functionality."""
    # Create test directories
    test_simulator = "/tmp/test_simulator"
    test_synthesis = "/tmp/test_synthesis"

    os.makedirs(test_simulator, exist_ok=True)
    os.makedirs(test_synthesis, exist_ok=True)
    os.makedirs(os.path.join(test_synthesis, "analysis_results"), exist_ok=True)

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
        test_synthesis, "analysis_results", "master_recommendations.json"
    )
    with open(master_file, "w") as f:
        json.dump(test_recommendations, f, indent=2)

    # Test integrator
    integrator = RecommendationIntegrator(test_simulator, test_synthesis)

    print("🧪 Testing RecommendationIntegrator...")

    # Load recommendations
    master_recs = integrator.load_master_recommendations()
    print(f"  Loaded {len(master_recs['recommendations'])} recommendations")

    # Map to phases
    phase_recs = integrator.create_phase_recommendations(master_recs)
    print(f"  Mapped to {len([r for r in phase_recs.values() if r])} phases")

    # Generate phase docs
    generated_files = integrator.generate_phase_enhancement_docs(phase_recs)
    print(f"  Generated {len(generated_files)} phase documents")

    # Generate summary
    summary = integrator.generate_integration_summary(phase_recs)
    print(f"  Generated integration summary ({len(summary)} chars)")

    # Cleanup
    import shutil

    shutil.rmtree(test_simulator)
    shutil.rmtree(test_synthesis)

    print("✅ RecommendationIntegrator test completed!")


if __name__ == "__main__":
    test_recommendation_integrator()
