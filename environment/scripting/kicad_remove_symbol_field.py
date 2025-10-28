#!/usr/bin/env python3
"""
Remove all (property "<FIELDNAME>" ...) blocks from every *.kicad_sym file in the current folder. Originally used for migration to built-in DNP field.
Preserves original formatting and whitespace.
Created by ChatGPT-5. Tested with KiCad 9 symbol library format on Windows (and apparented Linux OK too).

Usage:
    python remove_property_field.py
"""

import re
from pathlib import Path
import shutil

# ==== CONFIGURATION ====
FIELD_NAME = "FitPart"   # ← change this to the property name to remove
RECURSIVE = False         # True → include subdirectories
BACKUP_SUFFIX = ".bak"    # backup extension
# ========================


# Regex pattern to match a full multi-line (property "FIELD_NAME" ...) block.
# Uses non-greedy matching to ensure it stops at the first closing parenthesis pair.
pattern = re.compile(
    rf'\(\s*property\s+"{re.escape(FIELD_NAME)}"\s+[^)]*?\n(?:.*?\n)*?\s*\)\s*',
    flags=re.IGNORECASE
)


def remove_field_blocks(text: str) -> str:
    """Remove all matching (property "<FIELD_NAME>" ...) blocks."""
    # Simpler, safe multi-line search by counting parentheses instead of regex (handles nesting)
    lines = text.splitlines(keepends=True)
    out_lines = []
    skip = False
    depth = 0
    for line in lines:
        if not skip:
            if re.search(rf'\(\s*property\s+"{re.escape(FIELD_NAME)}"', line):
                skip = True
                depth = line.count('(') - line.count(')')
                continue
            else:
                out_lines.append(line)
        else:
            depth += line.count('(') - line.count(')')
            if depth <= 0:
                skip = False
    return ''.join(out_lines)


def process_file(path: Path):
    print(f"Processing: {path}")
    backup_path = path.with_suffix(path.suffix + BACKUP_SUFFIX)
    shutil.copy2(path, backup_path)

    text = path.read_text(encoding="utf-8", errors="ignore")
    new_text = remove_field_blocks(text)

    if new_text != text:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        print(f" → Field '{FIELD_NAME}' removed where present (backup: {backup_path.name})")
    else:
        print(f" → No '{FIELD_NAME}' field found (no changes)")


def main():
    base = Path(".")
    files = base.rglob("*.kicad_sym") if RECURSIVE else base.glob("*.kicad_sym")
    for f in files:
        try:
            process_file(f)
        except Exception as e:
            print(f" !! Error processing {f}: {e}")


if __name__ == "__main__":
    main()
