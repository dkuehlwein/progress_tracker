#!/usr/bin/env python3
import re
import sys
from datetime import datetime

if len(sys.argv) != 3:
    print("Usage: sort_backup.py <input_file> <output_file>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Read the backup file
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the journal_entries COPY block
pattern = r'(COPY public\.journal_entries.*?FROM stdin;\n)(.*?)(\n\\\.\n)'
match = re.search(pattern, content, re.DOTALL)

if match:
    header = match.group(1)
    data = match.group(2)
    footer = match.group(3)

    # Split into lines and sort by date (3rd column, assuming tab-separated)
    lines = [line for line in data.split('\n') if line.strip()]
    lines.sort(key=lambda x: x.split('\t')[2] if len(x.split('\t')) > 2 else '')

    # Reconstruct sorted data
    sorted_data = '\n'.join(lines)
    sorted_block = header + sorted_data + footer

    # Replace in content
    new_content = content[:match.start()] + sorted_block + content[match.end():]

    # Write to output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Created sorted backup: {output_file}")
else:
    print("Could not find journal_entries COPY block")
    sys.exit(1)
