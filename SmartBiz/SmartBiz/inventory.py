from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Product, Notification

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory')
@login_required
def index():
    """Displays inventory directory with filtering, search, and stock valuation."""
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', 'All')
    status_filter = request.args.get('status', 'All')
    sort_by = request.args.get('sort', 'name')
    
    query = Product.query
    
    if search_query:
        query = query.filter((Product.name.ilike(f'%{search_query}%')) | (Product.sku.ilike(f'%{search_query}%')) | (Product.supplier.ilike(f'%{search_query}%')))
        
    if category_filter and category_filter != 'All':
        query = query.filter_by(category=category_filter)
        
    products = query.all()
    
    # Filter by status property in Python since status is computed
    if status_filter and status_filter != 'All':
        products = [p for p in products if p.status == status_filter]
        
    # Sorting
    if sort_by == 'price_high':
        products.sort(key=lambda x: x.price, reverse=True)
    elif sort_by == 'price_low':
        products.sort(key=lambda x: x.price)
    elif sort_by == 'stock_low':
        products.sort(key=lambda x: x.stock)
    elif sort_by == 'stock_high':
        products.sort(key=lambda x: x.stock, reverse=True)
    else:
        products.sort(key=lambda x: x.name)
        
    # Calculate summary metrics
    total_items = len(products)
    total_value = sum(p.stock_value for p in products)
    low_stock_count = sum(1 for p in products if p.status == 'Low Stock')
    out_of_stock_count = sum(1 for p in products if p.status == 'Out of Stock')
    
    categories = sorted(list(set(p.category for p in Product.query.all())))
    
    return render_template('inventory.html', 
                           products=products, 
                           categories=categories,
                           total_items=total_items,
                           total_value=total_value,
                           low_stock_count=low_stock_count,
                           out_of_stock_count=out_of_stock_count,
                           current_search=search_query,
                           current_category=category_filter,
                           current_status=status_filter,
                           current_sort=sort_by)

@inventory_bp.route('/inventory/add', methods=['POST'])
@login_required
def add_product():
    """Adds a new SKU to inventory."""
    name = request.form.get('name', '').strip()
    sku = request.form.get('sku', '').strip().upper()
    category = request.form.get('category', 'General').strip()
    price = float(request.form.get('price', 0.0))
    cost_price = float(request.form.get('cost_price', 0.0))
    stock = int(request.form.get('stock', 0))
    min_stock = int(request.form.get('min_stock_level', 10))
    supplier = request.form.get('supplier', '').strip()
    
    if not name or not sku:
        flash('Product Name and SKU are required.', 'error')
        return redirect(url_for('inventory.index'))
        
    if Product.query.filter_by(sku=sku).first():
        flash(f'SKU {sku} already exists in inventory.', 'error')
        return redirect(url_for('inventory.index'))
        
    new_prod = Product(
        name=name,
        sku=sku,
        category=category,
        price=price,
        cost_price=cost_price,
        stock=stock,
        min_stock_level=min_stock,
        supplier=supplier
    )
    db.session.add(new_prod)
    db.session.commit()
    
    if stock <= min_stock:
        notif = Notification(
            user_id=current_user.id,
            title="Low Stock Alert",
            message=f"New product {name} ({sku}) was added with stock at or below minimum threshold ({stock}).",
            type="warning",
            link="/inventory"
        )
        db.session.add(notif)
        db.session.commit()
        
    flash(f'Product "{name}" added successfully!', 'success')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/inventory/edit/<int:id>', methods=['POST'])
@login_required
def edit_product(id):
    """Updates an existing inventory SKU."""
    prod = Product.query.get_or_404(id)
    prod.name = request.form.get('name', prod.name).strip()
    prod.sku = request.form.get('sku', prod.sku).strip().upper()
    prod.category = request.form.get('category', prod.category).strip()
    prod.price = float(request.form.get('price', prod.price))
    prod.cost_price = float(request.form.get('cost_price', prod.cost_price))
    prod.stock = int(request.form.get('stock', prod.stock))
    prod.min_stock_level = int(request.form.get('min_stock_level', prod.min_stock_level))
    prod.supplier = request.form.get('supplier', prod.supplier).strip()
    
    db.session.commit()
    flash(f'Product "{prod.name}" updated successfully!', 'success')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/inventory/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    """Deletes an inventory SKU."""
    prod = Product.query.get_or_404(id)
    name = prod.name
    db.session.delete(prod)
    db.session.commit()
    flash(f'Product "{name}" removed from inventory.', 'info')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/inventory/api/product/<int:id>')
@login_required
def get_product_json(id):
    """Returns JSON details of a product for editing or preview modals."""
    prod = Product.query.get_or_404(id)
    return jsonify({'status': 'success', 'data': prod.to_dict()})
