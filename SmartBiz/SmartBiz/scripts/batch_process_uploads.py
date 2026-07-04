"""Batch process remaining uploads:
- For uploads with records_imported == 0: if file resembles Superstore (has 'Order ID'), transform then import; else call process_file_upload directly.
"""
import os
import sys
import csv

project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import create_app
from models import db, Upload, User
from utils import process_file_upload

app = create_app()

def looks_like_superstore(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader)
            return any('Order ID' in h or 'Order Date' in h for h in header)
    except Exception:
        return False

def transform_file(src_path, dest_path):
    import csv
    from decimal import Decimal
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

def main():
    with app.app_context():
        admin = User.query.filter_by(email='admin@smartbiz.ai').first()
        if not admin:
            print('Admin user not found; create one first.')
            return

        uploads = Upload.query.filter_by(records_imported=0).all()
        print('Pending uploads:', len(uploads))
        total_imported = 0
        for u in uploads:
            src = os.path.join(project_root, 'uploads', u.filename)
            if not os.path.exists(src):
                print('Missing file, skipping:', u.filename)
                continue
            print('Processing', u.filename)
            if looks_like_superstore(src):
                dest = os.path.join(project_root, 'uploads', f'trans_{u.filename}')
                transform_file(src, dest)
                success, msg, records_imported, total_rev, ai, preview = process_file_upload(dest, 'csv', db.session, 'sales')
            else:
                success, msg, records_imported, total_rev, ai, preview = process_file_upload(src, u.file_type, db.session, 'auto')

            u.records_imported = records_imported
            u.status = 'Success' if success else 'Failed'
            u.user_id = admin.id
            db.session.add(u)
            db.session.commit()
            print('  -> imported:', records_imported)
            total_imported += records_imported

        print('Batch complete. Total records imported:', total_imported)

if __name__ == '__main__':
    main()
