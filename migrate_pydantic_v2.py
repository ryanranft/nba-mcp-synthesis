#!/usr/bin/env python3
"""
Pydantic V2 Migration Script
Migrates class Config to model_config = ConfigDict(...) pattern
"""

import re
import sys


def migrate_config_blocks(content):
    """
    Find and replace all class Config blocks with model_config = ConfigDict(...)
    """

    # Pattern to match class Config blocks with json_schema_extra
    # This handles multiline examples with proper indentation

    lines = content.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a "class Config:" line
        if re.match(r"^(\s{4})class Config:$", line):
            indent = "    "  # 4 spaces

            # Found a Config class, now find its content
            # Skip the "class Config:" line
            i += 1

            # Collect all content until we hit non-indented code or end
            config_lines = []
            while i < len(lines):
                next_line = lines[i]

                # If line starts with 8 spaces (Config class body) or is empty
                if next_line.startswith("        ") or next_line.strip() == "":
                    config_lines.append(next_line)
                    i += 1
                else:
                    # Hit the end of Config class
                    break

            # Now reconstruct as model_config
            if config_lines:
                # Find json_schema_extra line
                result.append(f"{indent}model_config = ConfigDict(")

                # Add the config content with adjusted indentation
                for config_line in config_lines:
                    if config_line.strip():
                        # Remove 4 spaces from indentation (was 8, now 4 inside ConfigDict)
                        if config_line.startswith("        "):
                            result.append("    " + config_line[4:])
                        else:
                            result.append(config_line)
                    else:
                        result.append(config_line)

                result.append(f"{indent})")
                result.append("")  # Empty line after model_config

        else:
            result.append(line)
            i += 1

    return "\n".join(result)


def main():
    input_file = "mcp_server/tools/params.py"
    output_file = "mcp_server/tools/params.py"

    print(f"Reading {input_file}...")
    with open(input_file, "r") as f:
        content = f.read()

    print("Migrating Config blocks...")
    new_content = migrate_config_blocks(content)

    print(f"Writing to {output_file}...")
    with open(output_file, "w") as f:
        f.write(new_content)

    print("✅ Migration complete!")
    print("\nValidating syntax...")

    import py_compile

    try:
        py_compile.compile(output_file, doraise=True)
        print("✅ Syntax valid!")
        return 0
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error: {e}")
        print("\nRestoring backup...")
        import shutil

        shutil.copy(f"{output_file}.backup", output_file)
        print("✅ Backup restored")
        return 1


if __name__ == "__main__":
    sys.exit(main())
