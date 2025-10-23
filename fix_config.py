#!/usr/bin/env python3
"""
Convert Pydantic V1 `class Config` to V2 `model_config = ConfigDict(...)`
"""

import re

def fix_config_classes(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line starts a Config class
        if line.strip() == 'class Config:':
            indent = len(line) - len(line.lstrip())
            base_indent = ' ' * indent

            # Collect all config options
            config_opts = []
            i += 1

            # Read config body
            while i < len(lines):
                config_line = lines[i]
                config_stripped = config_line.strip()

                # Check if we've left the config block
                if config_stripped and not config_line.startswith(base_indent + '    ') and config_stripped != '':
                    # We've left the config class
                    break

                # Skip empty lines within config
                if not config_stripped:
                    i += 1
                    continue

                # Extract config option
                if '=' in config_stripped:
                    config_opts.append(config_stripped)

                i += 1

            # Generate model_config line
            if config_opts:
                # Format as ConfigDict
                config_dict_content = ', '.join(config_opts)
                new_lines.append(f"{base_indent}model_config = ConfigDict({config_dict_content})\n")
            else:
                # Empty config
                new_lines.append(f"{base_indent}model_config = ConfigDict()\n")

            # Add blank line after model_config
            if i < len(lines) and lines[i].strip():
                new_lines.append('\n')

            continue

        new_lines.append(line)
        i += 1

    with open(file_path, 'w') as f:
        f.writelines(new_lines)

    print(f"✅ Converted class Config → model_config in {file_path}")

if __name__ == '__main__':
    fix_config_classes('mcp_server/tools/params.py')

