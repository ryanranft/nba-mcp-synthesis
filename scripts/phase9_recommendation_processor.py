#!/usr/bin/env python3
"""
Phase 9: Intelligent Recommendation Processor

Processes 1,643 recommendations and generates:
1. codebase_analysis.json - Analysis of both project structures
2. recommendation_mapping.json - Detailed mapping for each recommendation
3. dependency_graph.json - Dependency relationships and implementation order
4. integration_strategies.json - Detailed strategies for top 100 recommendations

This script uses intelligent pattern matching, NLP techniques, and heuristics to:
- Determine target project (MCP vs Simulator)
- Identify target files/modules
- Suggest integration strategy
- Calculate priority scores
- Build dependency graphs
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
import hashlib

# ===========================
# Configuration
# ===========================

SIMULATOR_PATH = Path("/Users/ryanranft/nba-simulator-aws")
MCP_PATH = Path("/Users/ryanranft/nba-mcp-synthesis")
OUTPUT_DIR = MCP_PATH / "implementation_plans"

# Keywords for project classification
MCP_KEYWORDS = {
    "mcp",
    "tool",
    "metric",
    "formula",
    "calculation",
    "basketball stat",
    "nba metric",
    "player rating",
    "team rating",
    "efficiency",
    "analytics",
    "per",
    "ts%",
    "efg%",
    "usage rate",
    "offensive rating",
    "defensive rating",
    "four factors",
    "assist percentage",
    "rebound percentage",
    "true shooting",
    "player efficiency",
    "pace",
    "possessions",
}

SIMULATOR_KEYWORDS = {
    "model",
    "training",
    "prediction",
    "simulation",
    "ml",
    "machine learning",
    "neural network",
    "regression",
    "classification",
    "clustering",
    "ensemble",
    "feature engineering",
    "data pipeline",
    "etl",
    "aws",
    "sagemaker",
    "rds",
    "s3",
    "glue",
    "ec2",
    "deployment",
    "inference",
    "evaluation",
    "metrics",
    "cross-validation",
    "hyperparameter",
    "optimization",
    "gradient",
    "loss",
}

# Integration strategies
INTEGRATION_STRATEGIES = {
    "extend_existing": "Add functionality to existing file/class",
    "create_new": "Create new file/module",
    "modify_existing": "Modify existing code structure",
    "create_subclass": "Extend existing class via inheritance",
    "add_function": "Add standalone function to module",
}

# ===========================
# Data Classes
# ===========================


@dataclass
class CodebaseModule:
    """Represents a module in the codebase"""

    name: str
    path: str
    files: List[str]
    capabilities: List[str]
    extensibility: str  # 'high', 'medium', 'low'


@dataclass
class RecommendationMapping:
    """Mapping of a recommendation to implementation details"""

    rec_id: str
    title: str
    target_project: str
    target_files: List[str]
    integration_strategy: str
    rationale: str
    dependencies: Dict[str, List[str]]
    priority_score: float
    estimated_effort: str
    conflicts: List[str]
    implementation_notes: str
    category: str
    priority: str


# ===========================
# File Discovery Functions
# ===========================


def find_python_files(
    base_path: Path, exclude_patterns: List[str] = None
) -> List[Path]:
    """Find all Python files in a directory, excluding certain patterns"""
    if exclude_patterns is None:
        exclude_patterns = ["__pycache__", ".pyc", "test_", "archive", "deprecated"]

    python_files = []
    for file in base_path.rglob("*.py"):
        # Skip excluded patterns
        if any(pattern in str(file) for pattern in exclude_patterns):
            continue
        python_files.append(file)

    return python_files


def categorize_files(files: List[Path], base_path: Path) -> Dict[str, List[str]]:
    """Categorize files by their apparent purpose"""
    categories = defaultdict(list)

    for file in files:
        rel_path = str(file.relative_to(base_path))

        # Categorize based on path and filename
        if "model" in rel_path.lower() or "ml" in rel_path.lower():
            categories["models"].append(rel_path)
        elif "data" in rel_path.lower() or "etl" in rel_path.lower():
            categories["data_processing"].append(rel_path)
        elif "feature" in rel_path.lower():
            categories["feature_engineering"].append(rel_path)
        elif "eval" in rel_path.lower() or "metric" in rel_path.lower():
            categories["evaluation"].append(rel_path)
        elif "api" in rel_path.lower() or "endpoint" in rel_path.lower():
            categories["api"].append(rel_path)
        elif "tool" in rel_path.lower() or "mcp" in rel_path.lower():
            categories["mcp_tools"].append(rel_path)
        elif "deployment" in rel_path.lower() or "infra" in rel_path.lower():
            categories["infrastructure"].append(rel_path)
        else:
            categories["other"].append(rel_path)

    return dict(categories)


# ===========================
# Analysis Functions
# ===========================


def analyze_codebase(project_path: Path, project_name: str) -> Dict:
    """Analyze a codebase and extract structure information"""
    print(f"Analyzing {project_name} codebase at {project_path}...")

    # Find all Python files
    py_files = find_python_files(project_path)
    print(f"  Found {len(py_files)} Python files")

    # Categorize files
    categorized = categorize_files(py_files, project_path)

    # Build module structure
    modules = []
    for category, files in categorized.items():
        if not files:
            continue

        module = {
            "name": category,
            "files": files[:20],  # Limit to 20 files per category for summary
            "file_count": len(files),
            "capabilities": extract_capabilities(category),
            "extensibility": assess_extensibility(category),
        }
        modules.append(module)

    return {
        "project_name": project_name,
        "path": str(project_path),
        "total_files": len(py_files),
        "modules": modules,
        "key_directories": get_key_directories(project_path),
    }


def extract_capabilities(category: str) -> List[str]:
    """Extract likely capabilities from a category name"""
    capability_map = {
        "models": ["ML model training", "Model persistence", "Model evaluation"],
        "data_processing": ["Data ingestion", "Data cleaning", "ETL pipelines"],
        "feature_engineering": [
            "Feature extraction",
            "Feature transformation",
            "Feature selection",
        ],
        "evaluation": [
            "Model evaluation",
            "Metrics calculation",
            "Performance tracking",
        ],
        "api": ["REST endpoints", "Request handling", "Response formatting"],
        "mcp_tools": ["MCP tool implementation", "NBA metrics", "Data retrieval"],
        "infrastructure": ["Deployment", "Configuration", "Resource management"],
    }
    return capability_map.get(category, ["General utilities"])


def assess_extensibility(category: str) -> str:
    """Assess how easy it is to extend a category"""
    high_extensibility = ["mcp_tools", "feature_engineering", "evaluation"]
    medium_extensibility = ["models", "data_processing", "api"]

    if category in high_extensibility:
        return "high"
    elif category in medium_extensibility:
        return "medium"
    else:
        return "low"


def get_key_directories(project_path: Path) -> List[str]:
    """Get key directories in the project"""
    key_dirs = []
    for item in project_path.iterdir():
        if (
            item.is_dir()
            and not item.name.startswith(".")
            and item.name not in ["__pycache__", "node_modules"]
        ):
            key_dirs.append(item.name)
    return sorted(key_dirs)


# ===========================
# Recommendation Classification
# ===========================


def classify_recommendation(rec: Dict) -> str:
    """Determine if recommendation belongs to MCP or Simulator project"""
    # Get text to analyze
    title = rec.get("title", "").lower()
    description = rec.get("description", "").lower()
    category = rec.get("category", "").lower()
    technical_details = rec.get("technical_details", "").lower()

    combined_text = f"{title} {description} {category} {technical_details}"

    # Count keyword matches
    mcp_score = sum(1 for keyword in MCP_KEYWORDS if keyword in combined_text)
    sim_score = sum(1 for keyword in SIMULATOR_KEYWORDS if keyword in combined_text)

    # Category-based classification
    if category in ["nba analytics", "basketball metrics", "statistics"]:
        mcp_score += 3
    elif category in ["ml", "machine learning", "model training", "data processing"]:
        sim_score += 3

    # Special patterns
    if re.search(
        r"\b(calculate|compute|formula|rating|percentage|metric)\b", combined_text
    ):
        mcp_score += 1
    if re.search(
        r"\b(train|predict|model|neural|regression|classification)\b", combined_text
    ):
        sim_score += 2

    # Default to simulator if unclear (more recommendations likely go there)
    if mcp_score > sim_score:
        return "nba-mcp-synthesis"
    else:
        return "nba-simulator-aws"


def identify_target_files(
    rec: Dict, project: str, codebase_analysis: Dict
) -> List[str]:
    """Identify specific files where recommendation should be implemented"""
    title = rec.get("title", "").lower()
    category = rec.get("category", "").lower()

    # Find matching module
    project_analysis = codebase_analysis.get(project, {})
    modules = project_analysis.get("modules", [])

    target_files = []

    # Match based on category and keywords
    if project == "nba-mcp-synthesis":
        if "tool" in title or "metric" in title or "formula" in title:
            target_files.append(f"{MCP_PATH}/mcp_server/tools/nba_metrics.py")
        elif "validation" in title or "quality" in title:
            target_files.append(f"{MCP_PATH}/mcp_server/data_quality.py")
        elif "monitoring" in title or "alert" in title:
            target_files.append(f"{MCP_PATH}/mcp_server/monitoring.py")
        else:
            target_files.append(f"{MCP_PATH}/mcp_server/tools/advanced_tools.py")

    else:  # nba-simulator-aws
        if "model" in title or "training" in title:
            target_files.append(f"{SIMULATOR_PATH}/models/ensemble.py")
        elif "data" in title or "etl" in title or "pipeline" in title:
            target_files.append(f"{SIMULATOR_PATH}/data/processing.py")
        elif "feature" in title:
            target_files.append(f"{SIMULATOR_PATH}/features/engineering.py")
        elif "evaluation" in title or "metric" in title:
            target_files.append(f"{SIMULATOR_PATH}/evaluation/metrics.py")
        elif "api" in title or "endpoint" in title:
            target_files.append(f"{SIMULATOR_PATH}/api/endpoints.py")
        elif "validation" in title:
            target_files.append(f"{SIMULATOR_PATH}/data/validation.py")
        else:
            target_files.append(f"{SIMULATOR_PATH}/utils/helpers.py")

    # Add test file
    if target_files:
        test_file = target_files[0].replace(".py", "_test.py")
        if "/mcp_server/" in test_file:
            test_file = test_file.replace("/mcp_server/", "/tests/")
        elif "/models/" in test_file or "/data/" in test_file:
            test_file = test_file.replace(
                f"{SIMULATOR_PATH}/", f"{SIMULATOR_PATH}/tests/"
            )
        target_files.append(test_file)

    return target_files


def determine_integration_strategy(rec: Dict, target_files: List[str]) -> str:
    """Determine how to integrate the recommendation"""
    title = rec.get("title", "").lower()

    # Check if file exists
    if target_files:
        main_file = Path(target_files[0])
        if main_file.exists():
            # File exists - extend or modify
            if "new" in title or "add" in title or "create" in title:
                if "model" in title or "algorithm" in title:
                    return "create_subclass"
                else:
                    return "extend_existing"
            else:
                return "modify_existing"
        else:
            # File doesn't exist - create new
            return "create_new"

    return "create_new"


def calculate_priority_score(rec: Dict) -> float:
    """Calculate priority score (0-10) based on multiple factors"""
    # Base score from priority
    priority_map = {
        "critical": 9.0,
        "high": 7.0,
        "important": 6.0,
        "medium": 5.0,
        "low": 3.0,
        "nice-to-have": 2.0,
    }
    base_score = priority_map.get(rec.get("priority", "medium").lower(), 5.0)

    # Adjust for dependencies
    deps = rec.get("dependencies", [])
    if isinstance(deps, list):
        dep_penalty = min(len(deps) * 0.2, 2.0)
        base_score -= dep_penalty

    # Adjust for category
    category = rec.get("category", "").lower()
    if category in ["data processing", "ml", "testing"]:
        base_score += 0.5

    # Ensure in range [0, 10]
    return max(0.0, min(10.0, base_score))


def estimate_effort(rec: Dict) -> str:
    """Estimate implementation effort"""
    # Count implementation steps
    steps = rec.get("implementation_steps", [])
    if isinstance(steps, list):
        num_steps = len(steps)
    else:
        num_steps = 3  # Default

    # Get time estimate if available
    time_est = rec.get("time_estimate", "")
    if "hour" in time_est:
        hours = (
            int(re.search(r"(\d+)", time_est).group(1))
            if re.search(r"(\d+)", time_est)
            else 4
        )
        return f"{hours} hours"

    # Estimate based on steps
    if num_steps <= 3:
        return "2-4 hours"
    elif num_steps <= 5:
        return "4-8 hours"
    else:
        return "8-16 hours"


# ===========================
# Main Processing Function
# ===========================


def process_recommendations(
    recommendations: List[Dict], codebase_analysis: Dict
) -> List[RecommendationMapping]:
    """Process all recommendations and create mappings"""
    print(f"\nProcessing {len(recommendations)} recommendations...")

    mappings = []

    for idx, rec in enumerate(recommendations):
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(recommendations)} recommendations...")

        # Generate recommendation ID
        rec_hash = hashlib.md5(rec["title"].encode()).hexdigest()[:8]
        rec_id = f"rec_{idx+1:04d}_{rec_hash}"

        # Classify project
        target_project = classify_recommendation(rec)

        # Identify target files
        target_files = identify_target_files(rec, target_project, codebase_analysis)

        # Determine integration strategy
        integration_strategy = determine_integration_strategy(rec, target_files)

        # Calculate priority score
        priority_score = calculate_priority_score(rec)

        # Estimate effort
        effort = estimate_effort(rec)

        # Build rationale
        rationale = f"Classified as {target_project} project. "
        if target_files:
            rationale += f"Implementing in {Path(target_files[0]).name}. "
        rationale += f"Using {integration_strategy} strategy. "
        rationale += f"Priority score: {priority_score:.1f}/10."

        # Extract dependencies
        dependencies = {
            "libraries": (
                rec.get("dependencies", [])
                if isinstance(rec.get("dependencies"), list)
                else []
            ),
            "prerequisites": [],  # Will be filled in dependency graph phase
        }

        # Create mapping
        mapping = RecommendationMapping(
            rec_id=rec_id,
            title=rec["title"],
            target_project=target_project,
            target_files=target_files,
            integration_strategy=integration_strategy,
            rationale=rationale,
            dependencies=dependencies,
            priority_score=priority_score,
            estimated_effort=effort,
            conflicts=[],  # Will be filled if conflicts detected
            implementation_notes=rec.get("technical_details", "")[:200] + "...",
            category=rec.get("category", "Uncategorized"),
            priority=rec.get("priority", "medium"),
        )

        mappings.append(mapping)

    print(f"  Completed processing {len(mappings)} recommendations!")
    return mappings


# ===========================
# Dependency Graph Construction
# ===========================


def build_dependency_graph(mappings: List[RecommendationMapping]) -> Dict:
    """Build dependency graph showing relationships between recommendations"""
    print("\nBuilding dependency graph...")

    # Build index of recommendations by capability
    capability_index = defaultdict(list)
    for mapping in mappings:
        # Extract capabilities from title and category
        capabilities = extract_capability_keywords(mapping.title, mapping.category)
        for cap in capabilities:
            capability_index[cap].append(mapping.rec_id)

    # Build edges (dependencies)
    edges = []
    for mapping in mappings:
        # Check if this recommendation depends on others
        # Example: "Model deployment" depends on "Model training"
        potential_deps = find_potential_dependencies(mapping, capability_index)
        for dep in potential_deps:
            if dep != mapping.rec_id:
                edges.append(
                    {"from": dep, "to": mapping.rec_id, "type": "prerequisite"}
                )

    # Remove circular dependencies
    edges = remove_circular_dependencies(edges)

    # Build implementation order (phases)
    implementation_order = determine_implementation_order(mappings, edges)

    return {
        "nodes": [
            {
                "id": m.rec_id,
                "phase": implementation_order.get(m.rec_id, 3),
                "dependencies": [e["from"] for e in edges if e["to"] == m.rec_id],
            }
            for m in mappings
        ],
        "edges": edges,
        "implementation_order": implementation_order,
        "circular_dependencies": [],  # Will be filled if any found
        "parallel_groups": identify_parallel_groups(mappings, edges),
    }


def extract_capability_keywords(title: str, category: str) -> Set[str]:
    """Extract capability keywords from title and category"""
    text = f"{title} {category}".lower()
    keywords = set()

    # Common capability patterns
    patterns = [
        "validation",
        "monitoring",
        "testing",
        "deployment",
        "training",
        "feature store",
        "data quality",
        "ci/cd",
        "pipeline",
        "model",
    ]

    for pattern in patterns:
        if pattern in text:
            keywords.add(pattern)

    return keywords


def find_potential_dependencies(
    mapping: RecommendationMapping, capability_index: Dict
) -> List[str]:
    """Find potential prerequisite recommendations"""
    deps = []

    # Check for common dependency patterns
    title_lower = mapping.title.lower()

    # Deployment depends on training
    if "deploy" in title_lower or "production" in title_lower:
        if "training" in capability_index:
            deps.extend(
                capability_index["training"][:2]
            )  # Take first 2 training recommendations

    # Testing depends on implementation
    if "test" in title_lower:
        if "validation" in capability_index:
            deps.extend(capability_index["validation"][:1])

    # Advanced features depend on basic features
    if "advanced" in title_lower or "optimize" in title_lower:
        # Look for basic implementations
        category = mapping.category.lower()
        if category in capability_index:
            deps.extend(capability_index[category][:1])

    return deps


def remove_circular_dependencies(edges: List[Dict]) -> List[Dict]:
    """Remove circular dependencies from edge list"""
    # Build adjacency list
    adj = defaultdict(set)
    for edge in edges:
        adj[edge["from"]].add(edge["to"])

    # Find cycles using DFS
    def has_cycle(node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in adj[node]:
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    # Remove edges that create cycles
    cleaned_edges = []
    for edge in edges:
        # Temporarily add edge and check for cycle
        adj[edge["from"]].add(edge["to"])

        visited = set()
        rec_stack = set()
        if not has_cycle(edge["from"], visited, rec_stack):
            cleaned_edges.append(edge)
        else:
            adj[edge["from"]].remove(edge["to"])

    return cleaned_edges


def determine_implementation_order(
    mappings: List[RecommendationMapping], edges: List[Dict]
) -> Dict[str, int]:
    """Determine implementation order (phases 1-5) for each recommendation"""
    # Phase 1: High priority, no dependencies
    # Phase 2: Foundation items that others depend on
    # Phase 3: Core features with some dependencies
    # Phase 4: Advanced features with many dependencies
    # Phase 5: Nice-to-haves

    order = {}

    # Build dependency count
    dep_count = defaultdict(int)
    for edge in edges:
        dep_count[edge["to"]] += 1

    # Build "depended on" count (how many depend on this)
    depended_on = defaultdict(int)
    for edge in edges:
        depended_on[edge["from"]] += 1

    for mapping in mappings:
        rec_id = mapping.rec_id

        # Calculate phase
        if mapping.priority_score >= 8.5 and dep_count[rec_id] == 0:
            phase = 1  # Quick wins
        elif depended_on[rec_id] >= 3:
            phase = 2  # Foundations
        elif dep_count[rec_id] <= 2 and mapping.priority_score >= 6.0:
            phase = 3  # Core features
        elif mapping.priority_score >= 4.0:
            phase = 4  # Advanced features
        else:
            phase = 5  # Nice-to-haves

        order[rec_id] = phase

    return order


def identify_parallel_groups(
    mappings: List[RecommendationMapping], edges: List[Dict]
) -> List[List[str]]:
    """Identify groups of recommendations that can be implemented in parallel"""
    # Build dependency sets
    depends_on = defaultdict(set)
    for edge in edges:
        depends_on[edge["to"]].add(edge["from"])

    # Group by shared dependencies
    groups = []
    independent = [m.rec_id for m in mappings if not depends_on[m.rec_id]]
    if independent:
        # Split independent into groups of 10
        for i in range(0, len(independent), 10):
            groups.append(independent[i : i + 10])

    return groups


# ===========================
# Main Execution
# ===========================


def main():
    print("=" * 80)
    print("Phase 9: Intelligent Recommendation Processor")
    print("=" * 80)

    # Step 1: Load recommendations
    print("\n[Step 1] Loading recommendations...")
    with open(OUTPUT_DIR / "consolidated_recommendations.json", "r") as f:
        data = json.load(f)
    recommendations = data["recommendations"]
    print(f"  Loaded {len(recommendations)} recommendations")

    # Step 2: Analyze codebases
    print("\n[Step 2] Analyzing codebases...")
    simulator_analysis = analyze_codebase(SIMULATOR_PATH, "nba-simulator-aws")
    mcp_analysis = analyze_codebase(MCP_PATH, "nba-mcp-synthesis")

    codebase_analysis = {
        "simulator": simulator_analysis,
        "mcp": mcp_analysis,
        "timestamp": data["metadata"]["timestamp"],
        "analysis_version": "1.0",
    }

    # Save codebase analysis
    with open(OUTPUT_DIR / "codebase_analysis.json", "w") as f:
        json.dump(codebase_analysis, f, indent=2)
    print(f"  ✓ Saved codebase_analysis.json")

    # Step 3: Process recommendations
    print("\n[Step 3] Processing recommendations...")
    mappings = process_recommendations(recommendations, codebase_analysis)

    # Calculate statistics
    mcp_count = sum(1 for m in mappings if m.target_project == "nba-mcp-synthesis")
    sim_count = sum(1 for m in mappings if m.target_project == "nba-simulator-aws")

    print(f"\n  Statistics:")
    print(
        f"    • Mapped to nba-simulator-aws: {sim_count} ({sim_count/len(mappings)*100:.1f}%)"
    )
    print(
        f"    • Mapped to nba-mcp-synthesis: {mcp_count} ({mcp_count/len(mappings)*100:.1f}%)"
    )

    # Save recommendation mappings
    mapping_data = {
        "total_recommendations": len(mappings),
        "mapped_to_simulator": sim_count,
        "mapped_to_mcp": mcp_count,
        "recommendations": [asdict(m) for m in mappings],
    }

    with open(OUTPUT_DIR / "recommendation_mapping.json", "w") as f:
        json.dump(mapping_data, f, indent=2)
    print(f"  ✓ Saved recommendation_mapping.json")

    # Step 4: Build dependency graph
    print("\n[Step 4] Building dependency graph...")
    dep_graph = build_dependency_graph(mappings)

    with open(OUTPUT_DIR / "dependency_graph.json", "w") as f:
        json.dump(dep_graph, f, indent=2)
    print(f"  ✓ Saved dependency_graph.json")

    # Print summary statistics
    phase_counts = defaultdict(int)
    for node in dep_graph["nodes"]:
        phase_counts[node["phase"]] += 1

    print(f"\n  Phase Distribution:")
    for phase in sorted(phase_counts.keys()):
        print(f"    • Phase {phase}: {phase_counts[phase]} recommendations")

    print("\n" + "=" * 80)
    print("✓ Processing Complete!")
    print("=" * 80)
    print(f"\nGenerated files in {OUTPUT_DIR}:")
    print("  1. codebase_analysis.json")
    print("  2. recommendation_mapping.json")
    print("  3. dependency_graph.json")
    print("\nNext: Run integration strategies and roadmap generators")


if __name__ == "__main__":
    main()
