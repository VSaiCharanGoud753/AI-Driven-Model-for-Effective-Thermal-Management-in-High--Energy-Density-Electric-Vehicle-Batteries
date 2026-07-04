"""Preview CSV headers and first rows for an upload file.
Usage: python scripts/preview_upload.py <filename>
"""
import sys
import os
import csv

project_root = os.path.dirname(os.path.dirname(__file__))
if len(sys.argv) < 2:
    print('Usage: python scripts/preview_upload.py <filename>')
    raise SystemExit(1)

filename = sys.argv[1]
path = os.path.join(project_root, 'uploads', filename)
if not os.path.exists(path):
    print('File not found:', path)
    raise SystemExit(1)

with open(path, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.reader(f)
    try:
        header = next(reader)
    except StopIteration:
        print('Empty file')
        raise SystemExit(1)
    print('Header columns:')
    for i, h in enumerate(header):
        print(f'{i+1}. {h}')
    print('\nFirst 3 rows:')
    for i, row in enumerate(reader):
        print(row)
        if i >= 2:
            break
