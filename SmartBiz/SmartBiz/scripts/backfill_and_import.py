"""Backfill orphan uploads to admin and re-run imports for uploads with 0 records.

Run from the project root: python scripts/backfill_and_import.py
"""
import os
from werkzeug.security import generate_password_hash

project_root = os.path.dirname(os.path.dirname(__file__))
import sys
sys.path.insert(0, project_root)

from app import create_app
from models import db, Upload, User, Notification
from utils import process_file_upload

app = create_app()

def main():
    with app.app_context():
        admin_email = 'admin@smartbiz.ai'
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            print(f'Admin user {admin_email} not found — creating it.')
            admin = User(
                full_name='Admin',
                business_name='SmartBiz',
                email=admin_email,
                phone='000-000-0000',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print('Created admin user with password: admin123')

        uploads = Upload.query.filter((Upload.user_id == None) | (Upload.user_id == 0)).all()
        print(f'Found {len(uploads)} orphan uploads to assign to {admin_email}.')
        for u in uploads:
            u.user_id = admin.id
            db.session.add(u)
        db.session.commit()

        to_process = Upload.query.filter_by(records_imported=0).all()
        print(f'Found {len(to_process)} uploads with 0 imported records to process.')
        imported_total = 0
        for u in to_process:
            file_path = os.path.join(project_root, 'uploads', u.filename)
            if not os.path.exists(file_path):
                print(f'  - Skipping missing file: {file_path}')
                continue
            print(f'  - Processing: {u.filename}')
            try:
                success, message, records_imported, total_rev, ai_preds, preview = process_file_upload(file_path, u.file_type, db.session, 'auto')
            except Exception as e:
                success = False
                message = str(e)
                records_imported = 0
                total_rev = 0.0
                ai_preds = None
                preview = None

            u.records_imported = records_imported
            u.status = 'Success' if success else 'Failed'
            db.session.add(u)
            db.session.commit()
            imported_total += records_imported

            notif = Notification(
                user_id=admin.id,
                title='Backfill Import Completed' if success else 'Backfill Import Failed',
                message=f"File '{u.original_name}' processed: imported={records_imported}. {message}",
                type='success' if success else 'warning',
                link='/data-studio'
            )
            db.session.add(notif)
            db.session.commit()

        print(f'Done. Total records imported across backfill run: {imported_total}')

if __name__ == '__main__':
    main()
