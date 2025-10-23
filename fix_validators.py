#!/usr/bin/env python3
"""
Fix Pydantic V1 @validator to V2 @field_validator
Adds @classmethod decorator where needed
"""

import re


def fix_validators(file_path):
    with open(file_path, "r") as f:
        content = f.read()

    # Replace @validator with @field_validator
    content = content.replace("@validator(", "@field_validator(")

    # Find all field_validator definitions and add @classmethod if not present
    # Pattern: @field_validator(...)\n    def method_name(cls, ...)
    pattern = r"(@field_validator\([^)]+\))\n(    def \w+\(cls,)"

    def add_classmethod(match):
        validator_line = match.group(1)
        def_line = match.group(2)
        # Check if @classmethod is already there
        return f"{validator_line}\n    @classmethod\n{def_line}"

    # Only add @classmethod if it's not already there
    lines = content.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is a @field_validator line
        if "@field_validator(" in line:
            new_lines.append(line)
            i += 1
            # Check next line - should it be @classmethod?
            if i < len(lines) and lines[i].strip().startswith("def "):
                # Add @classmethod before the def
                indent = len(lines[i]) - len(lines[i].lstrip())
                new_lines.append(" " * indent + "@classmethod")
                new_lines.append(lines[i])
                i += 1
            elif i < len(lines) and "@classmethod" in lines[i]:
                # Already has @classmethod, keep it
                new_lines.append(lines[i])
                i += 1
        else:
            new_lines.append(line)
            i += 1

    content = "\n".join(new_lines)

    with open(file_path, "w") as f:
        f.write(content)

    print(f"✅ Fixed @validator → @field_validator in {file_path}")


if __name__ == "__main__":
    fix_validators("mcp_server/tools/params.py")
