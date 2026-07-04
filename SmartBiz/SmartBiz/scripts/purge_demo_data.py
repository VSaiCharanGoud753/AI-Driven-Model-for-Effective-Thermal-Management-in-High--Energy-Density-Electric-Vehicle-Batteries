"""One-shot script to delete known seeded demo records.

This targets records created by `utils.seed_sample_data()` by matching
seed SKUs, seed customer emails, and seed notification titles/messages.

Run from the project root with the app context: `python -m scripts.purge_demo_data`
"""
from app import app
from models import db, Product, Customer, Sale, Expense, Notification

SEED_SKUS = [
    'LAP-MBP16-001','LAP-DXPS-002','AUD-SNY-003','FUR-HMA-004','FUR-STD-005','PER-LGT-006',
    'PER-KEY-007','DIS-LGU-008','SOF-SFDC-009','CLO-AWS-010','NET-CSCO-011','NET-UBI-012',
    'FUR-EXL-013','FUR-BOO-014','SOF-ADOB-015','SOF-MSFT-016','AUD-SHU-017','LIG-ELG-018',
    'POW-ANK-019','LIG-DYS-020','SOF-NOT-021','SOF-FIG-022','SOF-DDG-023','FIN-STP-024',
    'TAB-APP-025','TAB-SAM-026','FUR-STC-027','DIS-BNQ-028','AUD-JAB-029','NET-ZOM-030'
]

SEED_CUSTOMER_EMAILS = [
    'admin@smartbiz.ai','s.connor@cyberdyne.com','elon@xtech.com','satya@cloudscale.net','sundar@alphainnovate.com',
    'amara@lagos-tech.ng','k.sato@tokyo-robotics.jp','elena@madrid-creative.es','m.vance@vance-global.co.uk',
    'chloe@sydney-design.au','d.kim@seoul-ai.kr','fiona@chicago-logistics.com','liam@dublin-security.ie',
    'zoe@avatar-media.com','hans@nakatomi-invest.de','arthur@dutch-van.com','j.pearson@pearson-specter.com',
    'harvey@specter-litigation.com','donna@the-firm.com','mike@legal-aid.org','rachel@zane-law.com',
    'louis@litt-financial.com','katrina@bennett-legal.com','alex@williams-group.com','samantha@wheeler-ops.com',
    'robert@zane-partners.com'
]

def purge():
    with app.app_context():
        print('Purging demo data...')
        # Delete sales linked to seed products or seed customers
        seed_products = Product.query.filter(Product.sku.in_(SEED_SKUS)).all()
        seed_product_ids = [p.id for p in seed_products]
        seed_customers = Customer.query.filter(Customer.email.in_(SEED_CUSTOMER_EMAILS)).all()
        seed_customer_ids = [c.id for c in seed_customers]

        # Delete Sales
        sales_q = Sale.query.filter((Sale.product_id.in_(seed_product_ids)) | (Sale.customer_id.in_(seed_customer_ids)))
        deleted_sales = sales_q.count()
        sales_q.delete(synchronize_session='fetch')

        # Delete Products
        prod_q = Product.query.filter(Product.sku.in_(SEED_SKUS))
        deleted_products = prod_q.count()
        prod_q.delete(synchronize_session='fetch')

        # Delete Customers
        cust_q = Customer.query.filter(Customer.email.in_(SEED_CUSTOMER_EMAILS))
        deleted_customers = cust_q.count()
        cust_q.delete(synchronize_session='fetch')

        # Delete Notifications with seed-like messages
        notif_q = Notification.query.filter(Notification.message.ilike('%Welcome to SmartBiz AI%') | Notification.message.ilike('%Gemini AI has generated%'))
        deleted_notifs = notif_q.count()
        notif_q.delete(synchronize_session='fetch')

        db.session.commit()
        print(f'Deleted sales: {deleted_sales}, products: {deleted_products}, customers: {deleted_customers}, notifications: {deleted_notifs}')

if __name__ == '__main__':
    purge()
