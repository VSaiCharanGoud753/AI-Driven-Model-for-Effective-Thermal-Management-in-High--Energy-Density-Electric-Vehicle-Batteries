import os
import csv
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required
from models import db, Sale, Product, Customer

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/sales')
@login_required
def index():
    """Displays sales log, invoices, top products leaderboard, and revenue growth."""
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'All')
    region_filter = request.args.get('region', 'All')
    
    query = Sale.query
    
    if search_query:
        query = query.filter((Sale.invoice_no.ilike(f'%{search_query}%')) | (Sale.region.ilike(f'%{search_query}%')))
        
    if status_filter and status_filter != 'All':
        query = query.filter_by(status=status_filter)
        
    if region_filter and region_filter != 'All':
        query = query.filter_by(region=region_filter)
        
    sales_list = query.order_by(Sale.date.desc()).all()
    
    # Calculate summary metrics
    total_sales_val = sum(s.total_amount for s in sales_list if s.status == 'Completed')
    total_profit_val = sum(s.profit for s in sales_list if s.status == 'Completed')
    total_transactions = len(sales_list)
    
    # Top Selling Product calculation
    prod_map = {}
    for s in sales_list:
        if s.status == 'Completed' and s.product:
            prod_map[s.product.name] = prod_map.get(s.product.name, 0.0) + s.total_amount
    top_product_name = max(prod_map.items(), key=lambda x: x[1])[0] if prod_map else "N/A"
    
    products = Product.query.filter_by(status='Active').all() or Product.query.all()
    customers = Customer.query.order_by(Customer.name).all()
    regions = sorted(list(set(s.region for s in Sale.query.all())))
    
    return render_template('sales.html',
                           sales=sales_list,
                           total_sales_val=total_sales_val,
                           total_profit_val=total_profit_val,
                           total_transactions=total_transactions,
                           top_product_name=top_product_name,
                           products=products,
                           customers=customers,
                           regions=regions,
                           current_search=search_query,
                           current_status=status_filter,
                           current_region=region_filter)

@sales_bp.route('/sales/add', methods=['POST'])
@login_required
def add_sale():
    """Creates a new sales invoice transaction."""
    customer_id = request.form.get('customer_id')
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    region = request.form.get('region', 'North America').strip()
    status = request.form.get('status', 'Completed').strip()
    
    prod = Product.query.get(product_id) if product_id else None
    if not prod:
        flash('Please select a valid product.', 'error')
        return redirect(url_for('sales.index'))
        
    if prod.stock < quantity and status == 'Completed':
        flash(f'Insufficient stock for "{prod.name}". Only {prod.stock} remaining.', 'error')
        return redirect(url_for('sales.index'))
        
    unit_price = prod.price
    total_amount = round(quantity * unit_price, 2)
    profit = round(quantity * (unit_price - prod.cost_price), 2)
    invoice_no = f"INV-{now_year()}-{int(datetime.utcnow().timestamp())}"
    
    new_sale = Sale(
        invoice_no=invoice_no,
        customer_id=customer_id if customer_id else None,
        product_id=prod.id,
        quantity=quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        profit=profit,
        region=region,
        status=status
    )
    db.session.add(new_sale)
    
    if status == 'Completed':
        prod.stock -= quantity
        if customer_id:
            cust = Customer.query.get(customer_id)
            if cust:
                cust.lifetime_value += total_amount
                cust.purchase_frequency += 1
                if cust.lifetime_value > 15000:
                    cust.segment = 'VIP'
                elif cust.lifetime_value > 5000:
                    cust.segment = 'Regular'
                    
    db.session.commit()
    flash(f'Invoice {invoice_no} created successfully!', 'success')
    return redirect(url_for('sales.index'))

@sales_bp.route('/sales/invoice/<int:id>')
@login_required
def get_invoice_json(id):
    """Returns JSON details of an invoice for the interactive invoice modal."""
    sale = Sale.query.get_or_404(id)
    data = sale.to_dict()
    data['customer_company'] = sale.customer.company if sale.customer else 'Individual'
    data['customer_email'] = sale.customer.email if sale.customer else 'N/A'
    data['customer_phone'] = sale.customer.phone if sale.customer else 'N/A'
    data['product_sku'] = sale.product.sku if sale.product else 'N/A'
    return jsonify({'status': 'success', 'invoice': data})

@sales_bp.route('/sales/export')
@login_required
def export_sales_csv():
    """Exports all sales transactions to a downloadable CSV spreadsheet."""
    sales_list = Sale.query.order_by(Sale.date.desc()).all()
    
    def generate():
        data = []
        header = ['Invoice No', 'Date', 'Customer Name', 'Company', 'Product Name', 'SKU', 'Quantity', 'Unit Price ($)', 'Total Amount ($)', 'Profit ($)', 'Region', 'Status']
        yield ','.join(header) + '\n'
        for s in sales_list:
            row = [
                s.invoice_no,
                s.date.strftime('%Y-%m-%d'),
                f'"{s.customer.name}"' if s.customer else '"Guest"',
                f'"{s.customer.company}"' if s.customer and s.customer.company else '"Individual"',
                f'"{s.product.name}"' if s.product else '"Custom Item"',
                s.product.sku if s.product else '"N/A"',
                str(s.quantity),
                f"{s.unit_price:.2f}",
                f"{s.total_amount:.2f}",
                f"{s.profit:.2f}",
                f'"{s.region}"',
                s.status
            ]
            yield ','.join(row) + '\n'
            
    return Response(generate(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=smartbiz_sales_export.csv'})

def now_year():
    return datetime.utcnow().year
