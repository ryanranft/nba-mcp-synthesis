#!/usr/bin/env python3
"""
Extract real recommendations from ML Systems book analysis and update master recommendations.
"""

import json
import os
import re
from datetime import datetime


def extract_ml_systems_recommendations():
    """Extract recommendations from the ML Systems book analysis."""

    # Read the final recommendations document
    recommendations_file = (
        "/Users/ryanranft/nba-mcp-synthesis/MCP_FINAL_RECOMMENDATIONS_COMPLETE.md"
    )

    if not os.path.exists(recommendations_file):
        print(f"❌ Recommendations file not found: {recommendations_file}")
        return []

    with open(recommendations_file, "r") as f:
        content = f.read()

    recommendations = []

    # Extract Critical recommendations (lines 32-100)
    critical_section = content.split("### **🔴 CRITICAL PRIORITY**")[1].split(
        "### **🟡 IMPORTANT PRIORITY**"
    )[0]

    # Find all numbered recommendations
    critical_pattern = r"(\d+)\. \*\*(.*?)\*\* ⭐"
    critical_matches = re.findall(critical_pattern, critical_section)

    for num, title in critical_matches:
        # Extract details for this recommendation
        start_idx = critical_section.find(f"{num}. **{title}** ⭐")
        if start_idx != -1:
            # Find the next recommendation or end of section
            next_num = int(num) + 1
            next_pattern = f"{next_num}. **"
            end_idx = critical_section.find(next_pattern, start_idx)
            if end_idx == -1:
                end_idx = len(critical_section)

            rec_text = critical_section[start_idx:end_idx]

            # Extract book reference
            book_match = re.search(r"- \*\*Book:\*\* (.*)", rec_text)
            book_ref = book_match.group(1) if book_match else ""

            # Extract time estimate
            time_match = re.search(r"- \*\*Time:\*\* (.*)", rec_text)
            time_est = time_match.group(1) if time_match else ""

            # Extract impact
            impact_match = re.search(r"- \*\*Impact:\*\* (.*)", rec_text)
            impact = impact_match.group(1) if impact_match else ""

            # Extract status
            status_match = re.search(r"- \*\*Status:\*\* (.*)", rec_text)
            status = status_match.group(1) if status_match else ""

            recommendations.append(
                {
                    "title": title.strip(),
                    "category": "critical",
                    "reasoning": f"From ML Systems book: {book_ref}",
                    "book_reference": book_ref,
                    "time_estimate": time_est,
                    "impact": impact,
                    "status": status,
                }
            )

    # Extract Important recommendations
    important_section = content.split("### **🟡 IMPORTANT PRIORITY**")[1].split(
        "### **🟢 NICE-TO-HAVE**"
    )[0]

    important_pattern = r"(\d+)\. \*\*(.*?)\*\* ⭐"
    important_matches = re.findall(important_pattern, important_section)

    for num, title in important_matches:
        # Extract details for this recommendation
        start_idx = important_section.find(f"{num}. **{title}** ⭐")
        if start_idx != -1:
            # Find the next recommendation or end of section
            next_num = int(num) + 1
            next_pattern = f"{next_num}. **"
            end_idx = important_section.find(next_pattern, start_idx)
            if end_idx == -1:
                end_idx = len(important_section)

            rec_text = important_section[start_idx:end_idx]

            # Extract book reference
            book_match = re.search(r"- \*\*Book:\*\* (.*)", rec_text)
            book_ref = book_match.group(1) if book_match else ""

            # Extract time estimate
            time_match = re.search(r"- \*\*Time:\*\* (.*)", rec_text)
            time_est = time_match.group(1) if time_match else ""

            # Extract impact
            impact_match = re.search(r"- \*\*Impact:\*\* (.*)", rec_text)
            impact = impact_match.group(1) if impact_match else ""

            # Extract status
            status_match = re.search(r"- \*\*Status:\*\* (.*)", rec_text)
            status = status_match.group(1) if status_match else ""

            recommendations.append(
                {
                    "title": title.strip(),
                    "category": "important",
                    "reasoning": f"From ML Systems book: {book_ref}",
                    "book_reference": book_ref,
                    "time_estimate": time_est,
                    "impact": impact,
                    "status": status,
                }
            )

    # Extract Nice-to-Have recommendations
    nice_section = content.split("### **🟢 NICE-TO-HAVE**")[1].split("---")[0]

    nice_pattern = r"(\d+)\. \*\*(.*?)\*\* ⭐"
    nice_matches = re.findall(nice_pattern, nice_section)

    for num, title in nice_matches:
        # Extract details for this recommendation
        start_idx = nice_section.find(f"{num}. **{title}** ⭐")
        if start_idx != -1:
            # Find the next recommendation or end of section
            next_num = int(num) + 1
            next_pattern = f"{next_num}. **"
            end_idx = nice_section.find(next_pattern, start_idx)
            if end_idx == -1:
                end_idx = len(nice_section)

            rec_text = nice_section[start_idx:end_idx]

            # Extract book reference
            book_match = re.search(r"- \*\*Book:\*\* (.*)", rec_text)
            book_ref = book_match.group(1) if book_match else ""

            # Extract time estimate
            time_match = re.search(r"- \*\*Time:\*\* (.*)", rec_text)
            time_est = time_match.group(1) if time_match else ""

            # Extract impact
            impact_match = re.search(r"- \*\*Impact:\*\* (.*)", rec_text)
            impact = impact_match.group(1) if impact_match else ""

            # Extract status
            status_match = re.search(r"- \*\*Status:\*\* (.*)", rec_text)
            status = status_match.group(1) if status_match else ""

            recommendations.append(
                {
                    "title": title.strip(),
                    "category": "nice_to_have",
                    "reasoning": f"From ML Systems book: {book_ref}",
                    "book_reference": book_ref,
                    "time_estimate": time_est,
                    "impact": impact,
                    "status": status,
                }
            )

    # Count by category
    critical_count = len([r for r in recommendations if r["category"] == "critical"])
    important_count = len([r for r in recommendations if r["category"] == "important"])
    nice_count = len([r for r in recommendations if r["category"] == "nice_to_have"])

    print(f"📖 Extracted {len(recommendations)} recommendations from ML Systems book:")
    print(f"   - Critical: {critical_count}")
    print(f"   - Important: {important_count}")
    print(f"   - Nice-to-Have: {nice_count}")

    return recommendations


def update_master_recommendations(new_recommendations):
    """Update the master recommendations database."""

    master_file = "/Users/ryanranft/nba-mcp-synthesis/analysis_results/master_recommendations.json"

    # Load existing recommendations
    if os.path.exists(master_file):
        with open(master_file, "r") as f:
            master_data = json.load(f)
    else:
        master_data = {
            "recommendations": [],
            "by_category": {"critical": [], "important": [], "nice_to_have": []},
            "by_book": {},
            "last_updated": datetime.now().isoformat(),
        }

    # Clear existing test recommendations
    master_data["recommendations"] = []
    master_data["by_category"] = {"critical": [], "important": [], "nice_to_have": []}
    master_data["by_book"] = {"Designing Machine Learning Systems": []}

    # Add new recommendations
    for i, rec in enumerate(new_recommendations):
        rec_id = f"ml_systems_{i+1}"

        recommendation = {
            "id": rec_id,
            "title": rec["title"],
            "category": rec["category"],
            "source_books": ["Designing Machine Learning Systems"],
            "added_date": datetime.now().isoformat(),
            "reasoning": rec.get("reasoning", ""),
            "book_reference": rec.get("book_reference", ""),
            "time_estimate": rec.get("time_estimate", ""),
            "impact": rec.get("impact", ""),
            "status": rec.get("status", ""),
        }

        master_data["recommendations"].append(recommendation)
        master_data["by_category"][rec["category"]].append(rec_id)
        master_data["by_book"]["Designing Machine Learning Systems"].append(rec_id)

    # Update timestamp
    master_data["last_updated"] = datetime.now().isoformat()

    # Save updated master recommendations
    os.makedirs(os.path.dirname(master_file), exist_ok=True)
    with open(master_file, "w") as f:
        json.dump(master_data, f, indent=2)

    print(f"💾 Updated master recommendations with {len(new_recommendations)} items")
    return master_data


def main():
    """Main function to extract and update recommendations."""

    print("🚀 Extracting ML Systems book recommendations...")

    # Extract recommendations
    recommendations = extract_ml_systems_recommendations()

    if not recommendations:
        print("❌ No recommendations found")
        return

    # Update master recommendations
    master_data = update_master_recommendations(recommendations)

    print("✅ ML Systems recommendations extracted and updated!")
    print(f"   Total recommendations: {len(master_data['recommendations'])}")
    print(f"   Critical: {len(master_data['by_category']['critical'])}")
    print(f"   Important: {len(master_data['by_category']['important'])}")
    print(f"   Nice-to-Have: {len(master_data['by_category']['nice_to_have'])}")


if __name__ == "__main__":
    main()
