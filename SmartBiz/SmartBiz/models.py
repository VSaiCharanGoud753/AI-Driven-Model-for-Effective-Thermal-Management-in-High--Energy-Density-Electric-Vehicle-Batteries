from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    business_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Settings
    dark_mode = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(20), default='en')
    currency = db.Column(db.String(10), default='USD ($)')
    
    # Relationships
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")
    ai_logs = db.relationship('AILog', backref='user', lazy=True, cascade="all, delete-orphan")
    uploads = db.relationship('Upload', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, nullable=False, default=10)
    supplier = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='product', lazy=True)

    @property
    def status(self):
        if self.stock <= 0:
            return 'Out of Stock'
        elif self.stock <= self.min_stock_level:
            return 'Low Stock'
        return 'Active'

    @property
    def stock_value(self):
        return self.stock * self.cost_price

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'category': self.category,
            'price': self.price,
            'cost_price': self.cost_price,
            'stock': self.stock,
            'min_stock_level': self.min_stock_level,
            'supplier': self.supplier,
            'status': self.status,
            'stock_value': self.stock_value
        }

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    segment = db.Column(db.String(50), default='New') # VIP, Regular, New, At-Risk
    lifetime_value = db.Column(db.Float, default=0.0)
    purchase_frequency = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email or 'N/A',
            'phone': self.phone or 'N/A',
            'company': self.company or 'Individual',
            'segment': self.segment,
            'lifetime_value': self.lifetime_value,
            'purchase_frequency': self.purchase_frequency,
            'created_at': self.created_at.strftime('%Y-%m-%d')
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    region = db.Column(db.String(50), default='North America')
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(50), default='Completed') # Completed, Pending, Cancelled

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_no': self.invoice_no,
            'customer_name': self.customer.name if self.customer else 'Guest',
            'product_name': self.product.name if self.product else 'Custom Item',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_amount': self.total_amount,
            'profit': self.profit,
            'region': self.region,
            'date': self.date.strftime('%Y-%m-%d'),
            'status': self.status
        }

class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False) # Rent, Salaries, Marketing, Utilities, Software, Logistics
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    description = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': self.amount,
            'date': self.date.strftime('%Y-%m-%d'),
            'description': self.description or 'N/A'
        }

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), default='PDF') # PDF, CSV
    generated_by = db.Column(db.String(100), default='System')
    date = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=True)

class Upload(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False) # csv, xlsx
    records_imported = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='Success')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    type = db.Column(db.String(50), default='info') # alert, info, success, warning
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'link': self.link or '#'
        }

class AILog(db.Model):
    __tablename__ = 'ai_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query_type = db.Column(db.String(100), default='General Analysis')
    prompt_summary = db.Column(db.String(500), nullable=True)
    response_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
