#!/usr/bin/env python3
"""Update version strings in project files.

Usage:
    python update_version.py <new_version>

This script updates:
1. src/__init__.py: __version__ = "x.y.z"
2. pyproject.toml: version = "x.y.z" (in [project] section only)
"""

import re
import sys
from pathlib import Path


def update_init_py(version: str) -> None:
    """Update __version__ in src/__init__.py."""
    init_path = Path("src/__init__.py")
    content = init_path.read_text()
    new_content = re.sub(
        r'^__version__ = ".*"$',
        f'__version__ = "{version}"',
        content,
        flags=re.MULTILINE,
    )
    init_path.write_text(new_content)
    print(f"Updated {init_path}: __version__ = \"{version}\"")


def update_pyproject_toml(version: str) -> None:
    """Update version in pyproject.toml [project] section only."""
    pyproject_path = Path("pyproject.toml")
    lines = pyproject_path.read_text().splitlines(keepends=True)
    
    in_project_section = False
    new_lines = []
    
    for line in lines:
        # Track section changes
        if line.strip().startswith("[project]"):
            in_project_section = True
        elif line.strip().startswith("[") and not line.strip().startswith("[project"):
            in_project_section = False
        
        # Only update version in [project] section
        if in_project_section and line.strip().startswith("version ="):
            line = f'version = "{version}"\n'
            print(f"Updated pyproject.toml: version = \"{version}\"")
        
        new_lines.append(line)
    
    pyproject_path.write_text("".join(new_lines))


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)
    
    version = sys.argv[1]
    
    update_init_py(version)
    update_pyproject_toml(version)
    
    print(f"Version updated to {version}")


if __name__ == "__main__":
    main()
