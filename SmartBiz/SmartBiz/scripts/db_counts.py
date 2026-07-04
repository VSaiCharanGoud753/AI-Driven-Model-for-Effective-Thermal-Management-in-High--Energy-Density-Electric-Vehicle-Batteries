"""Print basic DB record counts to verify imports."""
import os
import sys
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import create_app
from models import db, Product, Customer, Sale, Expense, Upload, User

app = create_app()

with app.app_context():
    print('Users:', User.query.count())
    print('Products:', Product.query.count())
    print('Customers:', Customer.query.count())
    print('Sales:', Sale.query.count())
    print('Expenses:', Expense.query.count())
    print('Uploads:', Upload.query.count())
