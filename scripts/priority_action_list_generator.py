#!/usr/bin/env python3
"""
Priority Action List Generator

Generates dependency-aware implementation order for NBA simulator recommendations.
Provides estimated times, risk assessment, and prerequisites for background agent.

Usage:
    python3 scripts/priority_action_list_generator.py \\
        --synthesis implementation_plans/consolidated_recommendations.json \\
        --dependency-graph DEPENDENCY_GRAPH.md \\
        --output PRIORITY_ACTION_LIST.md
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PriorityActionListGenerator:
    """Generate priority action list for implementation."""

    PRIORITY_WEIGHTS = {
        'critical': 3,
        'important': 2,
        'nice-to-have': 1
    }

    RISK_LEVELS = {
        'low': 'Low risk - straightforward implementation',
        'medium': 'Medium risk - requires coordination',
        'high': 'High risk - complex integration'
    }

    def __init__(self, recommendations: List[Dict], dependency_order: List[str]):
        """
        Initialize generator.

        Args:
            recommendations: List of recommendation dictionaries
            dependency_order: Ordered list of rec_ids from dependency tracker
        """
        self.recommendations = recommendations
        self.dependency_order = dependency_order
        self.rec_index = {f"rec_{i:03d}": i - 1 for i in range(1, len(recommendations) + 1)}

        logger.info(f"Initialized generator with {len(recommendations)} recommendations")

    def parse_time_estimate(self, time_str: str) -> float:
        """
        Parse time estimate string to hours.

        Args:
            time_str: Time estimate (e.g., "24 hours", "2-4 days", "1 week")

        Returns:
            Estimated hours (float)
        """
        if not time_str:
            return 8.0  # Default

        time_str = time_str.lower()

        # Extract numbers
        numbers = re.findall(r'\d+', time_str)
        if not numbers:
            return 8.0

        # Parse based on unit
        if 'hour' in time_str:
            if len(numbers) == 1:
                return float(numbers[0])
            else:
                # Range: take average
                return sum(float(n) for n in numbers) / len(numbers)
        elif 'day' in time_str:
            if len(numbers) == 1:
                return float(numbers[0]) * 8  # 8 hours per day
            else:
                return sum(float(n) for n in numbers) / len(numbers) * 8
        elif 'week' in time_str:
            if len(numbers) == 1:
                return float(numbers[0]) * 40  # 40 hours per week
            else:
                return sum(float(n) for n in numbers) / len(numbers) * 40
        else:
            # Assume hours
            if len(numbers) == 1:
                return float(numbers[0])
            else:
                return sum(float(n) for n in numbers) / len(numbers)

    def assess_risk(self, rec: Dict) -> str:
        """
        Assess implementation risk level.

        Args:
            rec: Recommendation dictionary

        Returns:
            Risk level ('low', 'medium', 'high')
        """
        # Factors that increase risk:
        # 1. Number of dependencies
        # 2. Estimated time
        # 3. Keywords indicating complexity

        deps_count = len(rec.get('dependencies', []))
        time_hours = self.parse_time_estimate(rec.get('time_estimate', ''))
        text = f"{rec.get('title', '')} {rec.get('description', '')} {rec.get('technical_details', '')}".lower()

        risk_score = 0

        # Dependencies
        if deps_count > 3:
            risk_score += 2
        elif deps_count > 1:
            risk_score += 1

        # Time
        if time_hours > 40:
            risk_score += 2
        elif time_hours > 16:
            risk_score += 1

        # Complexity keywords
        complex_keywords = ['integration', 'migration', 'refactor', 'architecture', 'distributed', 'real-time', 'streaming']
        for keyword in complex_keywords:
            if keyword in text:
                risk_score += 1
                break

        # Database/infrastructure
        if any(k in text for k in ['database', 'infrastructure', 'deployment', 'production']):
            risk_score += 1

        # Determine risk level
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'

    def estimate_impact(self, rec: Dict) -> Tuple[str, int]:
        """
        Estimate expected impact.

        Args:
            rec: Recommendation dictionary

        Returns:
            Tuple of (description, score)
        """
        priority = rec.get('priority', 'important')
        category = rec.get('category', '').lower()
        
        impact_text = rec.get('expected_impact', '').lower()

        # Base score from priority
        score = self.PRIORITY_WEIGHTS.get(priority, 2)

        # Adjust based on keywords
        high_impact_keywords = ['accuracy', 'performance', 'reliability', 'critical', 'essential']
        for keyword in high_impact_keywords:
            if keyword in impact_text:
                score += 1
                break

        # Category impact
        high_impact_categories = ['ml', 'prediction', 'model', 'core']
        if any(cat in category for cat in high_impact_categories):
            score += 1

        # Generate description
        if score >= 4:
            desc = "🔴 High Impact - Critical for prediction accuracy"
        elif score >= 3:
            desc = "🟡 Medium Impact - Significant improvement"
        else:
            desc = "🟢 Low Impact - Enhancement"

        return desc, score

    def generate_action_list(self, output_file: str):
        """
        Generate priority action list.

        Args:
            output_file: Path to output markdown file
        """
        logger.info("Generating priority action list...")

        # Group by priority
        by_priority = {'critical': [], 'important': [], 'nice-to-have': []}
        
        for rec_id in self.dependency_order:
            idx = self.rec_index.get(rec_id)
            if idx is None:
                continue
            
            rec = self.recommendations[idx]
            priority = rec.get('priority', 'important')
            by_priority[priority].append((rec_id, rec))

        # Calculate statistics
        total_time = sum(self.parse_time_estimate(rec.get('time_estimate', '')) 
                        for rec in self.recommendations)
        total_critical = len(by_priority['critical'])
        total_important = len(by_priority['important'])
        total_nice = len(by_priority['nice-to-have'])

        # Generate markdown
        markdown = f"""# Priority Action List

**Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
**Total Recommendations:** {len(self.recommendations)}
**Estimated Total Time:** {total_time:.1f} hours (~{total_time/40:.1f} weeks)

---

## Overview

This document provides a dependency-aware implementation order for all {len(self.recommendations)} recommendations from the book analysis system.

**Priority Breakdown:**
- ⭐ **Critical:** {total_critical} recommendations (~{sum(self.parse_time_estimate(r.get('time_estimate', '')) for _, r in by_priority['critical']):.1f} hours)
- 🟡 **Important:** {total_important} recommendations (~{sum(self.parse_time_estimate(r.get('time_estimate', '')) for _, r in by_priority['important']):.1f} hours)
- 🟢 **Nice-to-Have:** {total_nice} recommendations (~{sum(self.parse_time_estimate(r.get('time_estimate', '')) for _, r in by_priority['nice-to-have']):.1f} hours)

---

## Implementation Strategy

### Phase 1: Critical Foundations ({total_critical} items)

Implement all critical recommendations first. These are essential for core functionality.

### Phase 2: Important Enhancements ({total_important} items)

Implement important recommendations to enhance capabilities significantly.

### Phase 3: Nice-to-Have Features ({total_nice} items)

Implement nice-to-have recommendations for additional enhancements.

---

## Detailed Action List

"""

        # Generate detailed list
        global_counter = 1
        
        for priority_name in ['critical', 'important', 'nice-to-have']:
            priority_recs = by_priority[priority_name]
            if not priority_recs:
                continue

            priority_emoji = {'critical': '⭐', 'important': '🟡', 'nice-to-have': '🟢'}[priority_name]
            priority_display = priority_name.replace('-', ' ').title()

            markdown += f"### {priority_emoji} {priority_display} Priority\n\n"

            for rec_id, rec in priority_recs:
                # Calculate details
                time_hours = self.parse_time_estimate(rec.get('time_estimate', ''))
                risk = self.assess_risk(rec)
                impact_desc, impact_score = self.estimate_impact(rec)
                deps = rec.get('dependencies', [])

                markdown += f"""---

#### {global_counter}. {rec['title']}

**ID:** {rec_id}
**Priority:** {priority_emoji} {priority_display}
**Estimated Time:** {time_hours:.1f} hours
**Risk Level:** {risk.capitalize()}
**Expected Impact:** {impact_desc}

**Description:**
{rec.get('description', 'No description provided.')}

**Prerequisites:**
"""

                if deps:
                    for dep in deps:
                        markdown += f"- {dep}\n"
                else:
                    markdown += "- None (can start immediately)\n"

                markdown += f"""
**Implementation Steps:**
"""

                steps = rec.get('implementation_steps', [])
                if steps:
                    for i, step in enumerate(steps, 1):
                        markdown += f"{i}. {step}\n"
                else:
                    markdown += "1. Review requirements\n2. Implement solution\n3. Test thoroughly\n4. Deploy to production\n"

                markdown += f"""
**Expected Outcome:**
{rec.get('expected_impact', 'Enhances system capabilities.')}

**Files:**
- `implement_{rec_id}.py` - Main implementation
- `test_{rec_id}.py` - Test suite
- `README.md` - Documentation

"""

                global_counter += 1

        # Add summary
        markdown += f"""
---

## Implementation Timeline

### Week 1-2: Critical Items ({total_critical} items)

Focus on critical recommendations that provide foundational capabilities.

**Estimated Time:** {sum(self.parse_time_estimate(r.get('time_estimate', '')) for _, r in by_priority['critical']):.1f} hours

### Week 3-6: Important Items ({total_important} items)

Implement important enhancements that significantly improve system capabilities.

**Estimated Time:** {sum(self.parse_time_estimate(r.get('time_estimate', '')) for _, r in by_priority['important']):.1f} hours

### Week 7+: Nice-to-Have Items ({total_nice} items)

Add nice-to-have features for additional enhancements.

**Estimated Time:** {sum(self.parse_time_estimate(r.get('time_estimate', '')) for _, r in by_priority['nice-to-have']):.1f} hours

---

## Risk Management

### High-Risk Recommendations

"""

        # List high-risk recommendations
        high_risk_count = 0
        for rec_id in self.dependency_order:
            idx = self.rec_index.get(rec_id)
            if idx is None:
                continue
            rec = self.recommendations[idx]
            if self.assess_risk(rec) == 'high':
                high_risk_count += 1
                markdown += f"- **{rec_id}:** {rec.get('title', '')} - {self.RISK_LEVELS['high']}\n"

        if high_risk_count == 0:
            markdown += "✅ No high-risk recommendations identified.\n"

        markdown += f"""

### Mitigation Strategies

1. **Start with low-risk items** to build momentum
2. **Implement high-risk items early** when resources are fresh
3. **Allocate extra time** for high-risk items
4. **Implement thorough testing** for all recommendations
5. **Document lessons learned** for future improvements

---

## Background Agent Instructions

### Execution Mode

The background agent should:

1. **Follow the implementation order** specified in this document
2. **Check prerequisites** before starting each recommendation
3. **Run tests** after implementing each recommendation
4. **Commit changes** with descriptive messages
5. **Document issues** encountered during implementation
6. **Skip failed items** and continue with the next one

### Success Criteria

Each recommendation is considered complete when:

- [ ] All implementation steps are executed
- [ ] Tests pass successfully
- [ ] Documentation is updated
- [ ] Code is committed to version control
- [ ] Integration points are validated

### Error Handling

If implementation fails:

1. Log the error in `IMPLEMENTATION_LOG.md`
2. Mark the recommendation as "FAILED" in STATUS.md
3. Continue with the next recommendation
4. Notify maintainers of failures

---

## Statistics

**Total Recommendations:** {len(self.recommendations)}
**Total Estimated Time:** {total_time:.1f} hours (~{total_time/40:.1f} weeks)

**By Priority:**
- Critical: {total_critical} ({total_critical/len(self.recommendations)*100:.1f}%)
- Important: {total_important} ({total_important/len(self.recommendations)*100:.1f}%)
- Nice-to-Have: {total_nice} ({total_nice/len(self.recommendations)*100:.1f}%)

**By Risk Level:**
"""

        # Calculate risk distribution
        risk_counts = {'low': 0, 'medium': 0, 'high': 0}
        for rec in self.recommendations:
            risk = self.assess_risk(rec)
            risk_counts[risk] += 1

        for risk, count in risk_counts.items():
            percentage = count / len(self.recommendations) * 100
            markdown += f"- {risk.capitalize()}: {count} ({percentage:.1f}%)\n"

        markdown += f"""

---

**Generated by:** Priority Action List Generator
**Last Updated:** {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}
**Source:** NBA Simulator AWS Book Analysis
"""

        # Write to file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            f.write(markdown)

        logger.info(f"✅ Saved priority action list to {output_file}")


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate priority action list")
    parser.add_argument('--synthesis', required=True, help='Path to consolidated_recommendations.json')
    parser.add_argument('--output', default='PRIORITY_ACTION_LIST.md', help='Output markdown file')

    args = parser.parse_args()

    # Load recommendations
    with open(args.synthesis, 'r') as f:
        data = json.load(f)
    recommendations = data.get('recommendations', [])

    # Load dependency order (simplified - just use sequential order if no dependency file)
    dependency_order = [f"rec_{i:03d}" for i in range(1, len(recommendations) + 1)]

    # Build generator
    generator = PriorityActionListGenerator(recommendations, dependency_order)
    
    # Generate action list
    generator.generate_action_list(args.output)
    
    # Print summary
    print(f"\n" + "=" * 80)
    print(f"✅ PRIORITY ACTION LIST GENERATED")
    print(f"=" * 80)
    print(f"Total recommendations: {len(recommendations)}")
    print(f"Output: {args.output}")
    print(f"=" * 80)


if __name__ == "__main__":
    main()

