from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, Product, Customer, Sale, Expense

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Renders main dashboard with real-time KPI metrics."""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)
    start_of_month = datetime(now.year, now.month, 1)
    start_of_year = datetime(now.year, 1, 1)
    start_of_today = datetime(now.year, now.month, now.day)
    
    # Prefer to show only data related to the current user's most recent upload.
    try:
        from models import Upload
        latest_upload = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.uploaded_at.desc()).first()
    except Exception:
        latest_upload = None

    if latest_upload:
        cutoff = latest_upload.uploaded_at
        all_sales = Sale.query.filter(Sale.status == 'Completed', Sale.date >= cutoff).all()
        all_products = Product.query.filter(Product.created_at >= cutoff).all()
        all_customers = Customer.query.filter(Customer.created_at >= cutoff).all()
        all_expenses = Expense.query.filter(Expense.date >= cutoff).all()
    else:
        # If user has no uploads, show zeroed KPIs (no global seeded/demo data)
        all_sales = []
        all_products = []
        all_customers = []
        all_expenses = []
    
    # 1. Total Revenue
    total_revenue = sum(s.total_amount for s in all_sales)
    
    # 2. Net Profit
    total_profit = sum(s.profit for s in all_sales)
    
    # 3. Total Expenses
    total_expenses = sum(e.amount for e in all_expenses)
    
    # 4. Total Orders
    total_orders = len(all_sales)
    
    # 5. Total Customers
    total_customers = len(all_customers)
    
    # 6. Inventory Valuation
    inventory_value = sum(p.stock_value for p in all_products)
    
    # 7. Products Count
    products_count = len(all_products)
    
    # 8. Average Order Value (AOV)
    aov = (total_revenue / total_orders) if total_orders > 0 else 0.0
    
    # 9. Growth Percentage (Last 30 days vs prev 30 days)
    recent_sales = [s.total_amount for s in all_sales if s.date >= thirty_days_ago]
    prev_sales = [s.total_amount for s in all_sales if sixty_days_ago <= s.date < thirty_days_ago]
    sum_recent = sum(recent_sales)
    sum_prev = sum(prev_sales)
    growth_pct = round(((sum_recent - sum_prev) / sum_prev * 100), 1) if sum_prev > 0 else (0.0 if total_orders == 0 else 100.0)
    
    # 10. Today's Revenue
    today_revenue = sum(s.total_amount for s in all_sales if s.date >= start_of_today)
    
    # 11. Monthly Revenue
    monthly_revenue = sum(s.total_amount for s in all_sales if s.date >= start_of_month)
    
    # 12. Annual Revenue
    annual_revenue = sum(s.total_amount for s in all_sales if s.date >= start_of_year)
    
    kpi_data = {
        'total_revenue': total_revenue,
        'net_profit': total_profit,
        'total_expenses': total_expenses,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'inventory_value': inventory_value,
        'products_count': products_count,
        'aov': aov,
        'growth_pct': growth_pct,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'annual_revenue': annual_revenue
    }
    
    return render_template('dashboard.html', kpi=kpi_data)

@dashboard_bp.route('/api/charts/data')
@login_required
def chart_data():
    """Returns structured JSON data for all 11 Chart.js interactive visualizations."""
    date_filter = request.args.get('filter', 'all').lower()
    now = datetime.utcnow()
    
    # Determine date range filtering
    if date_filter == 'today':
        start_date = datetime(now.year, now.month, now.day)
    elif date_filter == 'yesterday':
        start_date = datetime(now.year, now.month, now.day) - timedelta(days=1)
    elif date_filter == 'last_7_days':
        start_date = now - timedelta(days=7)
    elif date_filter == 'last_month':
        start_date = now - timedelta(days=30)
    elif date_filter == 'last_year':
        start_date = now - timedelta(days=365)
    else:
        start_date = datetime(2020, 1, 1) # All time
        
    try:
        from models import Upload
        latest_upload = Upload.query.filter_by(user_id=current_user.id).order_by(Upload.uploaded_at.desc()).first()
    except Exception:
        latest_upload = None

    if latest_upload:
        cutoff = max(start_date, latest_upload.uploaded_at)
        filtered_sales = Sale.query.filter(Sale.date >= cutoff, Sale.status == 'Completed').all()
        all_expenses = Expense.query.filter(Expense.date >= cutoff).all()
        all_products = Product.query.filter(Product.created_at >= cutoff).all()
        all_customers = Customer.query.filter(Customer.created_at >= cutoff).all()
    else:
        # If no uploads, return empty sets so charts don't show seeded data
        filtered_sales = []
        all_expenses = []
        all_products = []
        all_customers = []
    
    # 1. Monthly Revenue & Profit Trend (Last 12 Months)
    months_labels = []
    rev_by_month = []
    prof_by_month = []
    exp_by_month = []
    margin_by_month = []
    
    for i in range(11, -1, -1):
        target_month = (now - timedelta(days=i*30)).strftime('%b %Y')
        if target_month not in months_labels:
            months_labels.append(target_month)
            
    # Aggregate monthly
    month_map_rev = {m: 0.0 for m in months_labels}
    month_map_prof = {m: 0.0 for m in months_labels}
    month_map_exp = {m: 0.0 for m in months_labels}
    
    for s in Sale.query.filter_by(status='Completed').all():
        m_str = s.date.strftime('%b %Y')
        if m_str in month_map_rev:
            month_map_rev[m_str] += s.total_amount
            month_map_prof[m_str] += s.profit
            
    for e in Expense.query.all():
        m_str = e.date.strftime('%b %Y')
        if m_str in month_map_exp:
            month_map_exp[m_str] += e.amount
            
    for m in months_labels:
        rev_by_month.append(round(month_map_rev[m], 2))
        prof_by_month.append(round(month_map_prof[m], 2))
        exp_by_month.append(round(month_map_exp[m], 2))
        rev = month_map_rev[m]
        prof = month_map_prof[m]
        margin_by_month.append(round((prof / rev * 100), 1) if rev > 0 else 0.0)

    # 2. Category Sales Distribution
    cat_map = {}
    for s in filtered_sales:
        cat = s.product.category if s.product else 'General'
        cat_map[cat] = cat_map.get(cat, 0.0) + s.total_amount
    category_labels = list(cat_map.keys()) or ['No Category Data Yet']
    category_data = [round(v, 2) for v in cat_map.values()] or [0]

    # 3. Top Products Leaderboard
    prod_map = {}
    for s in filtered_sales:
        pname = s.product.name if s.product else 'Custom SKU'
        prod_map[pname] = prod_map.get(pname, 0.0) + s.total_amount
    sorted_prods = sorted(prod_map.items(), key=lambda x: x[1], reverse=True)[:5]
    top_prod_labels = [p[0] for p in sorted_prods] or ['No Products Loaded Yet']
    top_prod_data = [round(p[1], 2) for p in sorted_prods] or [0]

    # 4. Inventory Status Breakdown
    active_stock = sum(1 for p in all_products if p.status == 'Active')
    low_stock = sum(1 for p in all_products if p.status == 'Low Stock')
    out_stock = sum(1 for p in all_products if p.status == 'Out of Stock')

    # 5. Customer Growth & Segmentation
    seg_map = {'VIP': 0, 'Regular': 0, 'New': 0, 'At-Risk': 0}
    for c in all_customers:
        seg_map[c.segment] = seg_map.get(c.segment, 0) + 1

    # 6. Region-wise Sales
    reg_map = {}
    for s in filtered_sales:
        reg_map[s.region] = reg_map.get(s.region, 0.0) + s.total_amount
    region_labels = list(reg_map.keys()) or ['No Region Data Yet']
    region_data = [round(v, 2) for v in reg_map.values()] or [0]

    # 7. Expense Analysis
    exp_cat_map = {}
    for e in all_expenses:
        exp_cat_map[e.category] = exp_cat_map.get(e.category, 0.0) + e.amount
    expense_labels = list(exp_cat_map.keys()) or ['No Expense Data Yet']
    expense_data = [round(v, 2) for v in exp_cat_map.values()] or [0]

    return jsonify({
        'status': 'success',
        'months': months_labels,
        'monthly_revenue': rev_by_month,
        'sales_trend': rev_by_month, # Area trend
        'profit_trend': prof_by_month,
        'category_sales': {
            'labels': category_labels,
            'data': category_data
        },
        'top_products': {
            'labels': top_prod_labels,
            'data': top_prod_data
        },
        'inventory_status': {
            'labels': ['Active', 'Low Stock', 'Out of Stock'],
            'data': [active_stock, low_stock, out_stock]
        },
        'customer_growth': {
            'labels': list(seg_map.keys()),
            'data': list(seg_map.values())
        },
        'region_sales': {
            'labels': region_labels,
            'data': region_data
        },
        'expense_analysis': {
            'labels': expense_labels,
            'data': expense_data
        },
        'revenue_vs_expenses': {
            'revenue': rev_by_month,
            'expenses': exp_by_month
        },
        'profit_margin': margin_by_month
    })
