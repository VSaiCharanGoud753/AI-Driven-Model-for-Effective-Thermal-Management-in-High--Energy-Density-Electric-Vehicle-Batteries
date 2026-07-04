"""Add `user_id` column to `uploads` table if it doesn't exist (SQLite).

Run: python scripts/migrate_add_upload_userid.py
"""
import os
import sqlite3

project_root = os.path.dirname(os.path.dirname(__file__))
# Common locations for the SQLite DB created by the app
possible_paths = [
    os.path.join(project_root, 'smartbiz.db'),
    os.path.join(project_root, 'instance', 'smartbiz.db'),
    os.path.join(project_root, 'instance', 'database', 'smartbiz.db'),
    os.path.join(project_root, '..', 'smartbiz.db')
]

found = False
for db_path in possible_paths:
    if not os.path.exists(db_path):
        continue
    found = True
    print(f'Checking database: {db_path}')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info('uploads')")
        cols = [r[1] for r in cur.fetchall()]
        if 'user_id' in cols:
            print('  - user_id column already exists on uploads table.')
        else:
            print('  - Adding user_id column to uploads table...')
            cur.execute('ALTER TABLE uploads ADD COLUMN user_id INTEGER')
            conn.commit()
            print('  - Migration complete: user_id column added.')
    except Exception as e:
        print('  - Error checking/migrating DB:', e)
    finally:
        conn.close()

if not found:
    print('No database files found in expected locations:')
    for p in possible_paths:
        print(' -', p)
    print('Skipping migration.')
    raise SystemExit(1)
