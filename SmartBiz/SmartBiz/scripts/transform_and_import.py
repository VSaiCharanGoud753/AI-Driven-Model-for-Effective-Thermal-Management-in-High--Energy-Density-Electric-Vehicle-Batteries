"""Transform a Superstore-style CSV into the SmartBiz import schema and import it.
Usage: python scripts/transform_and_import.py <source_filename>
"""
import os
import sys
import csv
from decimal import Decimal

project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import create_app
from models import db, Upload, User, Notification
from utils import process_file_upload

app = create_app()

def transform_and_import(src_filename):
    src_path = os.path.join(project_root, 'uploads', src_filename)
    if not os.path.exists(src_path):
        print('Source file not found:', src_path)
        return

    dest_filename = f"trans_{src_filename}"
    dest_path = os.path.join(project_root, 'uploads', dest_filename)

    # Read source and write transformed CSV
    with open(src_path, 'r', encoding='utf-8', errors='replace') as sf, open(dest_path, 'w', newline='', encoding='utf-8') as df:
        reader = csv.DictReader(sf)
        fieldnames = ['INVOICE','DATE','PRODUCT','CUSTOMER','QUANTITY','UNIT PRICE','TOTAL','REGION']
        writer = csv.DictWriter(df, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            try:
                total = Decimal(row.get('Sales') or row.get('TOTAL') or '0')
            except Exception:
                total = Decimal('0')
            try:
                qty = int(float(row.get('Quantity') or row.get('QTY') or 0))
            except Exception:
                qty = 0
            unit_price = (total / qty) if qty > 0 else total
            out = {
                'INVOICE': row.get('Order ID') or row.get('OrderID') or '',
                'DATE': row.get('Order Date') or row.get('Date') or '',
                'PRODUCT': row.get('Product Name') or row.get('Product') or '',
                'CUSTOMER': row.get('Customer Name') or row.get('Customer') or '',
                'QUANTITY': qty,
                'UNIT PRICE': f"{unit_price}",
                'TOTAL': f"{total}",
                'REGION': row.get('Region') or row.get('region') or ''
            }
            writer.writerow(out)

    # Import using process_file_upload
    with app.app_context():
        admin = User.query.filter_by(email='admin@smartbiz.ai').first()
        if not admin:
            print('Admin user missing; cannot associate upload.')
            return

        print('Calling process_file_upload for', dest_filename)
        success, message, records_imported, total_rev, ai_preds, preview = process_file_upload(dest_path, 'csv', db.session, 'sales')
        print('Result:', success, records_imported, total_rev)

        # Create Upload record
        upload = Upload(
            filename=dest_filename,
            original_name=src_filename,
            file_type='csv',
            records_imported=records_imported,
            status='Success' if success else 'Failed',
            user_id=admin.id
        )
        db.session.add(upload)
        db.session.commit()

        notif = Notification(
            user_id=admin.id,
            title='Transformed Import Complete',
            message=f"Imported '{src_filename}' as '{dest_filename}' ({records_imported} records).",
            type='success' if success else 'warning',
            link='/data-studio'
        )
        db.session.add(notif)
        db.session.commit()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/transform_and_import.py <source_filename>')
        raise SystemExit(1)
    transform_and_import(sys.argv[1])
