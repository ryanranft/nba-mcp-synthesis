#!/usr/bin/env python3
"""
UserPromptSubmit Hook - Automatic Task Extraction with Master Task Inference

This hook runs before Claude processes each user prompt.
It extracts potential tasks, detects master tasks (large initiatives),
and matches to existing projects.

Part of: Automatic Task Tracking System (Phase 2 + Phase 3 Enhancement)
"""

import sys
import re
import json
from typing import List, Dict, Optional


# Action verbs that indicate tasks
TASK_VERBS = [
    "research",
    "analyze",
    "build",
    "create",
    "fix",
    "implement",
    "investigate",
    "compare",
    "test",
    "deploy",
    "update",
    "refactor",
    "add",
    "remove",
    "delete",
    "modify",
    "write",
    "read",
    "review",
    "setup",
    "configure",
    "install",
    "debug",
    "optimize",
    "migrate",
    "integrate",
    "document",
    "verify",
    "validate",
    "monitor",
    "track",
]

# Patterns that indicate multi-step work
MULTI_STEP_PATTERNS = [
    r"can you .*? and .*?",  # "can you X and Y"
    r"please .*? and .*?",  # "please X and Y"
    r"\d+\.",  # Numbered lists (1., 2., 3.)
    r"- ",  # Bullet points
    r"first.*then",  # Sequential instructions
    r"after.*then",  # Sequential instructions
]

# Complexity indicators
COMPLEXITY_INDICATORS = [
    "complex",
    "comprehensive",
    "detailed",
    "complete",
    "full",
    "entire",
    "all",
    "every",
    "multiple",
    "several",
]

# Master task indicators (large initiatives)
MASTER_TASK_INDICATORS = {
    "scope_words": [
        "complete",
        "comprehensive",
        "full",
        "entire",
        "all",
        "end-to-end",
        "overall",
        "system",
        "platform",
        "framework",
    ],
    "project_verbs": [
        "build",
        "create",
        "implement",
        "develop",
        "design",
        "establish",
        "setup",
        "architect",
        "deploy",
        "launch",
    ],
    "domain_words": [
        "system",
        "platform",
        "service",
        "application",
        "module",
        "component",
        "feature",
        "integration",
        "pipeline",
        "workflow",
    ],
    "time_words": [
        "phase",
        "sprint",
        "milestone",
        "roadmap",
        "initiative",
        "project",
        "campaign",
        "program",
        "plan",
    ],
    "phase_patterns": [r"phase \d+", r"step \d+ of \d+", r"part \d+", r"stage \d+"],
}


def extract_tasks_from_prompt(prompt: str) -> tuple:
    """Extract potential tasks from user prompt."""
    tasks = []

    # Check for action verbs
    prompt_lower = prompt.lower()
    found_verbs = [verb for verb in TASK_VERBS if verb in prompt_lower]

    # Check for multi-step indicators
    has_multi_step = any(
        re.search(pattern, prompt_lower) for pattern in MULTI_STEP_PATTERNS
    )

    # Check for complexity indicators
    has_complexity = any(
        indicator in prompt_lower for indicator in COMPLEXITY_INDICATORS
    )

    # Check for numbered lists
    numbered_items = re.findall(r"^\d+\.\s*(.+)$", prompt, re.MULTILINE)
    if numbered_items:
        for idx, item in enumerate(numbered_items, 1):
            tasks.append(
                {"number": idx, "description": item.strip(), "source": "numbered_list"}
            )

    # Check for bullet points
    bullet_items = re.findall(r"^[-*]\s*(.+)$", prompt, re.MULTILINE)
    if bullet_items and not numbered_items:  # Only if no numbered list
        for idx, item in enumerate(bullet_items, 1):
            tasks.append(
                {"number": idx, "description": item.strip(), "source": "bullet_list"}
            )

    # If no explicit list but has task indicators, extract main task
    if not tasks and (found_verbs or has_multi_step):
        # Try to extract main action
        main_task = extract_main_action(prompt, found_verbs)
        if main_task:
            tasks.append({"number": 1, "description": main_task, "source": "implicit"})

    # Add metadata
    task_metadata = {
        "has_action_verbs": bool(found_verbs),
        "action_verbs_found": found_verbs[:3],  # First 3 verbs
        "is_multi_step": has_multi_step,
        "is_complex": has_complexity,
        "task_count": len(tasks),
    }

    return tasks, task_metadata


def extract_main_action(prompt: str, verbs: List[str]) -> str:
    """Extract the main action from prompt."""
    # Find first sentence with action verb
    sentences = re.split(r"[.!?]", prompt)
    for sentence in sentences:
        sentence = sentence.strip()
        if any(verb in sentence.lower() for verb in verbs):
            # Clean up the sentence
            sentence = re.sub(
                r"^(can you|could you|please|would you)\s+",
                "",
                sentence,
                flags=re.IGNORECASE,
            )
            return sentence

    # Fallback: return first sentence
    return sentences[0].strip() if sentences else ""


def infer_master_task(prompt: str, extracted_tasks: List[Dict]) -> Optional[Dict]:
    """
    Infer if prompt describes a master task (large initiative).

    Returns master task metadata if detected, None otherwise.
    """
    prompt_lower = prompt.lower()

    # Score accumulation
    score = 0
    reasons = []

    # 1. Check scope indicators
    scope_matches = [
        w for w in MASTER_TASK_INDICATORS["scope_words"] if w in prompt_lower
    ]
    if len(scope_matches) >= 2:
        score += 3
        reasons.append(f"broad scope: {', '.join(scope_matches[:3])}")

    # 2. Check project-level verbs
    project_verbs = [
        v for v in MASTER_TASK_INDICATORS["project_verbs"] if v in prompt_lower
    ]
    if project_verbs:
        score += 2
        reasons.append(f"project-level work: {project_verbs[0]}")

    # 3. Check domain words
    domain_matches = [
        w for w in MASTER_TASK_INDICATORS["domain_words"] if w in prompt_lower
    ]
    if domain_matches:
        score += 1
        reasons.append(f"system component: {domain_matches[0]}")

    # 4. Check for multi-phase indicators
    phase_detected = any(
        re.search(p, prompt_lower) for p in MASTER_TASK_INDICATORS["phase_patterns"]
    )
    if phase_detected:
        score += 3
        reasons.append("multi-phase work detected")

    # 5. Check number of subtasks
    if len(extracted_tasks) >= 3:
        score += 2
        reasons.append(f"{len(extracted_tasks)} subtasks identified")

    # 6. Check for explicit breakdown structure
    has_numbered_list = any(t["source"] == "numbered_list" for t in extracted_tasks)
    if has_numbered_list:
        score += 2
        reasons.append("explicit numbered breakdown")

    # 7. Check prompt length (complex requests tend to be longer)
    if len(prompt) > 500:
        score += 1
        reasons.append("detailed request")

    # Decision threshold
    if score >= 5:
        # Extract master task title
        title = extract_master_task_title(prompt, extracted_tasks)

        return {
            "is_master_task": True,
            "title": title,
            "score": score,
            "confidence": min(score / 12.0, 1.0),  # Normalize to 0-1
            "reasons": reasons,
            "estimated_subtasks": len(extracted_tasks) or "unknown",
            "context_summary": generate_context_summary(prompt, extracted_tasks),
        }

    return None


def extract_master_task_title(prompt: str, tasks: List[Dict]) -> str:
    """Extract concise title for master task."""
    # Try to find first sentence with project verb
    sentences = re.split(r"[.!?]", prompt)
    for sentence in sentences:
        sentence = sentence.strip()
        if any(
            verb in sentence.lower() for verb in MASTER_TASK_INDICATORS["project_verbs"]
        ):
            # Clean up
            sentence = re.sub(
                r"^(can you|could you|please|would you|i want to|i need to)\s+",
                "",
                sentence,
                flags=re.IGNORECASE,
            )
            # Capitalize first letter
            return (
                sentence[0].upper() + sentence[1:]
                if sentence
                else "Untitled Initiative"
            )

    # Fallback: use first task if available
    if tasks:
        return tasks[0]["description"]

    # Ultimate fallback
    return "Untitled Initiative"


def generate_context_summary(prompt: str, tasks: List[Dict]) -> str:
    """Generate brief context summary for master task."""
    # Extract key phrases (first 200 chars + task count)
    summary = prompt[:200].strip()
    if len(prompt) > 200:
        summary += "..."

    if tasks:
        summary += f"\n\nIncludes {len(tasks)} major tasks."

    return summary


def match_to_existing_master_task(
    prompt: str, extracted_tasks: List[Dict]
) -> Optional[int]:
    """
    Match current prompt to existing master task.

    Returns master_task_id if match found, None otherwise.

    Note: This is a simplified version. In production, would query
    the Task Tracker MCP to get existing masters.
    """
    # For now, return None (no matching)
    # In a full implementation, this would:
    # 1. Get existing master tasks via MCP query
    # 2. Calculate similarity scores (Jaccard, keywords)
    # 3. Return best match if score > threshold
    return None


def should_create_tasks(prompt: str, tasks: List[Dict], metadata: Dict) -> bool:
    """Determine if tasks should be created for this prompt."""

    # Don't create tasks for simple questions
    simple_question_patterns = [
        r"^what is ",
        r"^what\'s ",
        r"^how do ",
        r"^can you explain ",
        r"^tell me about ",
    ]

    prompt_lower = prompt.lower().strip()

    # Check if it's a simple question
    if any(re.match(pattern, prompt_lower) for pattern in simple_question_patterns):
        # Unless it has multi-step or complexity indicators
        if not metadata["is_multi_step"] and not metadata["is_complex"]:
            return False

    # Create tasks if:
    # 1. Explicit task list (numbered or bullets)
    # 2. Multi-step work indicated
    # 3. Action verbs + complexity indicators
    # 4. Multiple action verbs (>2)

    if tasks and any(t["source"] in ["numbered_list", "bullet_list"] for t in tasks):
        return True

    if metadata["is_multi_step"]:
        return True

    if metadata["has_action_verbs"] and metadata["is_complex"]:
        return True

    if len(metadata["action_verbs_found"]) >= 2:
        return True

    return False


def format_enhanced_task_context(
    prompt: str,
    tasks: List[Dict],
    metadata: Dict,
    master_task_info: Optional[Dict],
    matched_master: Optional[int],
) -> str:
    """Format enhanced task context with master task guidance."""

    if not should_create_tasks(prompt, tasks, metadata):
        return ""  # No task context needed

    context = "\n\n---\n\n**AUTOMATIC TASK EXTRACTION & MASTER TASK DETECTION:**\n\n"

    # Master task detection
    if master_task_info:
        context += "🎯 **MASTER TASK DETECTED:**\n"
        context += f"- Title: {master_task_info['title']}\n"
        context += f"- Confidence: {master_task_info['confidence']*100:.0f}%\n"
        context += f"- Reasons: {', '.join(master_task_info['reasons'])}\n"
        context += f"- Estimated subtasks: {master_task_info['estimated_subtasks']}\n\n"

        if matched_master:
            context += f"✅ **MATCHES EXISTING PROJECT:** ID {matched_master}\n"
            context += "**Recommended Action:** Add tasks to existing master task\n\n"
        else:
            context += "**Recommended Action:** Create new master task\n\n"

    # Show extracted tasks
    if tasks:
        context += "**Tasks Detected:**\n"
        for task in tasks:
            context += f"{task['number']}. {task['description']}\n"
        context += "\n"

    # Instructions
    context += "**Instructions:**\n"
    if master_task_info and not matched_master:
        context += "1. Use `create_master_task` MCP tool to create master task with all subtasks\n"
        context += "2. Or use TodoWrite for session-level tracking\n"
        context += "3. Mark first subtask as 'in_progress' before starting\n"
    elif master_task_info and matched_master:
        context += f"1. Add tasks to existing master task (ID {matched_master})\n"
        context += "2. Use `create_task` MCP tool with master_task_id parameter\n"
        context += "3. Or use TodoWrite for session-level tracking\n"
    else:
        context += "1. Use TodoWrite tool immediately to create task list\n"
        context += "2. Or use `create_task` MCP tool for persistent storage\n"

    context += "4. Update status immediately after completing each task\n"
    context += "5. Have exactly ONE task 'in_progress' at a time\n"

    context += "\n---\n"

    return context


def main():
    """Main hook execution with master task inference."""

    # Read user prompt from stdin
    prompt = sys.stdin.read().strip()

    if not prompt:
        # No prompt, nothing to do
        sys.exit(0)

    # Extract tasks
    tasks, metadata = extract_tasks_from_prompt(prompt)

    # Infer master task
    master_task_info = infer_master_task(prompt, tasks)

    # Check for existing master tasks (simplified for now)
    matched_master = match_to_existing_master_task(prompt, tasks)

    # Format context with master task guidance
    task_context = format_enhanced_task_context(
        prompt, tasks, metadata, master_task_info, matched_master
    )

    # Output task context if any
    if task_context:
        print(
            task_context, file=sys.stderr
        )  # Send to stderr so it appears in hook output

    # For debugging (optional)
    debug_info = {
        "tasks_extracted": len(tasks),
        "should_create_tasks": should_create_tasks(prompt, tasks, metadata),
        "is_master_task": master_task_info is not None,
        "master_task_score": master_task_info["score"] if master_task_info else 0,
        "metadata": metadata,
    }

    # Write debug info to file (optional - uncomment for debugging)
    # with open('/tmp/claude_task_extraction.log', 'a') as f:
    #     f.write(json.dumps(debug_info) + '\n')

    sys.exit(0)


if __name__ == "__main__":
    main()
