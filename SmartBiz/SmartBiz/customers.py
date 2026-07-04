from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db, Customer, Sale

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers')
@login_required
def index():
    """Displays customer directory with RFM segmentation and lifetime value rankings."""
    search_query = request.args.get('search', '').strip()
    segment_filter = request.args.get('segment', 'All')
    sort_by = request.args.get('sort', 'ltv_high')
    
    query = Customer.query
    
    if search_query:
        query = query.filter((Customer.name.ilike(f'%{search_query}%')) | (Customer.email.ilike(f'%{search_query}%')) | (Customer.company.ilike(f'%{search_query}%')))
        
    if segment_filter and segment_filter != 'All':
        query = query.filter_by(segment=segment_filter)
        
    customers = query.all()
    
    # Sorting
    if sort_by == 'ltv_high':
        customers.sort(key=lambda x: x.lifetime_value, reverse=True)
    elif sort_by == 'ltv_low':
        customers.sort(key=lambda x: x.lifetime_value)
    elif sort_by == 'freq_high':
        customers.sort(key=lambda x: x.purchase_frequency, reverse=True)
    elif sort_by == 'name':
        customers.sort(key=lambda x: x.name)
    else:
        customers.sort(key=lambda x: x.lifetime_value, reverse=True)
        
    # Calculate summary metrics
    total_customers = len(customers)
    vip_count = sum(1 for c in customers if c.segment == 'VIP')
    avg_ltv = (sum(c.lifetime_value for c in customers) / total_customers) if total_customers > 0 else 0.0
    repeat_rate = round((sum(1 for c in customers if c.purchase_frequency > 1) / total_customers * 100), 1) if total_customers > 0 else 0.0
    
    return render_template('customers.html',
                           customers=customers,
                           total_customers=total_customers,
                           vip_count=vip_count,
                           avg_ltv=avg_ltv,
                           repeat_rate=repeat_rate,
                           current_search=search_query,
                           current_segment=segment_filter,
                           current_sort=sort_by)

@customers_bp.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    """Adds a new customer account."""
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    company = request.form.get('company', '').strip()
    segment = request.form.get('segment', 'New').strip()
    
    if not name:
        flash('Customer Name is required.', 'error')
        return redirect(url_for('customers.index'))
        
    if email and Customer.query.filter_by(email=email).first():
        flash(f'Customer with email {email} already exists.', 'error')
        return redirect(url_for('customers.index'))
        
    new_cust = Customer(
        name=name,
        email=email,
        phone=phone,
        company=company,
        segment=segment
    )
    db.session.add(new_cust)
    db.session.commit()
    
    flash(f'Customer "{name}" added successfully!', 'success')
    return redirect(url_for('customers.index'))

@customers_bp.route('/customers/edit/<int:id>', methods=['POST'])
@login_required
def edit_customer(id):
    """Updates customer details and RFM segment."""
    cust = Customer.query.get_or_404(id)
    cust.name = request.form.get('name', cust.name).strip()
    cust.email = request.form.get('email', cust.email).strip().lower()
    cust.phone = request.form.get('phone', cust.phone).strip()
    cust.company = request.form.get('company', cust.company).strip()
    cust.segment = request.form.get('segment', cust.segment).strip()
    
    db.session.commit()
    flash(f'Customer "{cust.name}" updated successfully!', 'success')
    return redirect(url_for('customers.index'))

@customers_bp.route('/customers/delete/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    """Deletes a customer account."""
    cust = Customer.query.get_or_404(id)
    name = cust.name
    db.session.delete(cust)
    db.session.commit()
    flash(f'Customer "{name}" removed from directory.', 'info')
    return redirect(url_for('customers.index'))

@customers_bp.route('/customers/api/details/<int:id>')
@login_required
def get_customer_details(id):
    """Returns JSON details of a customer along with recent purchase orders for modal drill-down."""
    cust = Customer.query.get_or_404(id)
    recent_sales = Sale.query.filter_by(customer_id=id).order_by(Sale.date.desc()).limit(10).all()
    
    return jsonify({
        'status': 'success',
        'customer': cust.to_dict(),
        'orders': [s.to_dict() for s in recent_sales]
    })
