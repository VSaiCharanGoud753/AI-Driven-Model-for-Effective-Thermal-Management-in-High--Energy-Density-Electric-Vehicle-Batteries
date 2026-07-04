import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Product, Customer, Sale, Expense, Report, Upload, Notification, User, AILog
from utils import process_file_upload, parse_universal_file, analyze_dataset_with_ai

main_bp = Blueprint('main', __name__)
import logging
logger = logging.getLogger('smartbiz')

@main_bp.route('/')
def index():
    """Renders the SaaS landing page with features, AI showcase, pricing, FAQ, and CTA."""
    # Provide live KPI preview when possible (helps show uploaded data on homepage)
    try:
        total_rev = sum(s.total_amount for s in Sale.query.all())
        total_prof = sum(s.profit for s in Sale.query.all())
        margin = round((total_prof / total_rev * 100), 1) if total_rev > 0 else 0.0
        records = len(Sale.query.all()) + len(Product.query.all()) + len(Expense.query.all())
        recent_uploads = Upload.query.order_by(Upload.uploaded_at.desc()).limit(3).all()
    except Exception:
        total_rev = None
        margin = None
        records = None
        recent_uploads = []

    return render_template('landing.html', total_revenue=total_rev, total_margin=margin, total_records=records, recent_uploads=recent_uploads)

@main_bp.route('/data-studio')
@login_required
def data_studio():
    """Renders the dedicated Business Data Studio & AI Ingestion Center page."""
    total_rev = sum(s.total_amount for s in Sale.query.all())
    records = len(Sale.query.all()) + len(Product.query.all()) + len(Expense.query.all())
    return render_template('data_studio.html', total_revenue=total_rev, total_records=records)

@main_bp.route('/api/data/reset', methods=['POST'])
@login_required
def reset_business_data():
    """Clears all demo data so dashboard KPIs and Chart.js graphs start at 0% / $0.00 before uploading business files."""
    try:
        Sale.query.delete()
        Product.query.delete()
        Customer.query.delete()
        Expense.query.delete()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'All demo records cleared! Dashboard is now at 0%. Ready for your custom file upload.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/api/upload/preview', methods=['POST'])
@login_required
def preview_upload_file():
    """Parses file (CSV, Excel, PDF, TXT, JSON) without importing, returns table preview & deep AI analysis."""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file selected.'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected.'}), 400
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[-1].lower()
    if file_ext not in ['csv', 'xls', 'xlsx', 'pdf', 'txt', 'json']:
        return jsonify({'status': 'error', 'message': f'Unsupported format .{file_ext}. Supported: CSV, Excel, PDF, TXT, JSON.'}), 400
    os.makedirs('uploads', exist_ok=True)
    file_path = os.path.join('uploads', f"prev_{int(datetime.utcnow().timestamp())}_{filename}")
    file.save(file_path)
    logger.debug("preview_upload_file saved temporary preview file: %s", file_path)
    
    success, df_or_text, is_tabular, preview_rows, columns, msg = parse_universal_file(file_path, file_ext)
    if not success:
        logger.warning("preview parse failed for %s: %s", file_path, msg)
        return jsonify({'status': 'error', 'message': msg}), 400
        
    # Run deep AI analysis
    records_count = len(df_or_text) if is_tabular else len(preview_rows)
    ai_preds = analyze_dataset_with_ai(file_ext, filename, 0.0, records_count, df_or_text, is_tabular)
    
    return jsonify({
        'status': 'success',
        'filename': filename,
        'file_type': file_ext,
        'is_tabular': is_tabular,
        'columns': columns,
        'preview_rows': preview_rows,
        'records_count': records_count,
        'ai_analysis': ai_preds
    })

@main_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handles drag-and-drop file upload (CSV, Excel, PDF, TXT, JSON) and imports into SQLite."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('ajax') == 'true'
    target_module = request.form.get('target_module', 'auto')
    
    if 'file' not in request.files:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'No file selected for upload.'}), 400
        flash('No file selected for upload.', 'error')
        return redirect(url_for('main.data_studio'))
        
    file = request.files['file']
    if file.filename == '':
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'No file selected.'}), 400
        flash('No file selected.', 'error')
        return redirect(url_for('main.data_studio'))
        
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[-1].lower()
    
    if file_ext not in ['csv', 'xls', 'xlsx', 'pdf', 'txt', 'json']:
        if is_ajax:
            return jsonify({'status': 'error', 'message': 'Invalid file format. Please upload CSV, Excel, PDF, TXT, or JSON.'}), 400
        flash('Invalid file format. Please upload CSV, Excel, PDF, TXT, or JSON.', 'error')
        return redirect(url_for('main.data_studio'))
        
    os.makedirs('uploads', exist_ok=True)
    file_path = os.path.join('uploads', f"{int(datetime.utcnow().timestamp())}_{filename}")
    file.save(file_path)
    logger.debug("upload_file saved file: %s (ext=%s) target_module=%s ajax=%s", file_path, file_ext, target_module, is_ajax)
    
    # Process using universal engine
    try:
        success, message, records_imported, total_rev, ai_preds, preview_data = process_file_upload(file_path, file_ext, db.session, target_module)
        logger.debug("process_file_upload result: success=%s imported=%s revenue=%s", success, records_imported, total_rev)
    except Exception as e:
        logger.exception("Unhandled exception during process_file_upload for %s", file_path)
        success, message, records_imported, total_rev, ai_preds, preview_data = False, f"Error processing upload: {str(e)}", 0, 0.0, None, None
    
    # Record upload
    upload_record = Upload(
        filename=os.path.basename(file_path),
        original_name=filename,
        file_type=file_ext,
        records_imported=records_imported,
        status='Success' if success else 'Failed'
    )
    # Associate upload with the current logged-in user when available
    try:
        upload_record.user_id = current_user.id
    except Exception:
        pass
    db.session.add(upload_record)
    
    if success:
        notif = Notification(
            user_id=current_user.id,
            title="Business Data Ingestion Complete",
            message=f"Uploaded '{filename}' ({file_ext.upper()}) and imported {records_imported} records into SmartBiz AI.",
            type="success",
            link="/data-studio"
        )
        db.session.add(notif)
        db.session.commit()
        if is_ajax:
            return jsonify({
                'status': 'success',
                'message': message,
                'records_imported': records_imported,
                'total_revenue': total_rev,
                'ai_predictions': ai_preds,
                'preview_data': preview_data
            })
        flash(message, 'success')
    else:
        db.session.commit()
        if is_ajax:
            return jsonify({'status': 'error', 'message': message}), 400
        flash(message, 'error')
        
    return redirect(url_for('main.data_studio'))

@main_bp.route('/api/search')
@login_required
def global_search():
    """Global Search Bar API: queries Products, Customers, Sales Invoices, and Reports simultaneously."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'status': 'success', 'results': []})
        
    results = []
    
    # Search Products
    prods = Product.query.filter((Product.name.ilike(f'%{query}%')) | (Product.sku.ilike(f'%{query}%')) | (Product.category.ilike(f'%{query}%'))).limit(5).all()
    for p in prods:
        results.append({
            'type': 'Product',
            'title': p.name,
            'subtitle': f"SKU: {p.sku} | Price: ${p.price:,.2f} | Stock: {p.stock}",
            'url': f"/inventory?search={p.sku}",
            'icon': 'fa-box'
        })
        
    # Search Customers
    custs = Customer.query.filter((Customer.name.ilike(f'%{query}%')) | (Customer.company.ilike(f'%{query}%')) | (Customer.email.ilike(f'%{query}%'))).limit(5).all()
    for c in custs:
        results.append({
            'type': 'Customer',
            'title': c.name,
            'subtitle': f"Company: {c.company or 'Individual'} | Segment: {c.segment} | LTV: ${c.lifetime_value:,.2f}",
            'url': f"/customers?search={c.name}",
            'icon': 'fa-user-tie'
        })
        
    # Search Sales Invoices
    sales = Sale.query.filter(Sale.invoice_no.ilike(f'%{query}%')).limit(5).all()
    for s in sales:
        results.append({
            'type': 'Invoice',
            'title': s.invoice_no,
            'subtitle': f"Amount: ${s.total_amount:,.2f} | Customer: {s.customer.name if s.customer else 'Guest'} | Region: {s.region}",
            'url': f"/sales?search={s.invoice_no}",
            'icon': 'fa-file-invoice-dollar'
        })
        
    # Search Reports
    reps = Report.query.filter(Report.title.ilike(f'%{query}%')).limit(3).all()
    for r in reps:
        results.append({
            'type': 'Report',
            'title': r.title,
            'subtitle': f"Type: {r.type} | Date: {r.date.strftime('%Y-%m-%d')}",
            'url': "/reports",
            'icon': 'fa-chart-pie'
        })
        
    return jsonify({'status': 'success', 'results': results})

@main_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Returns unread notifications and unread badge count for top navbar bell."""
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(15).all()
    unread_count = sum(1 for n in notifs if not n.is_read)
    
    return jsonify({
        'status': 'success',
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifs]
    })

@main_bp.route('/api/notifications/read/<int:id>', methods=['POST'])
@login_required
def mark_notif_read(id):
    notif = Notification.query.get_or_404(id)
    if notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return jsonify({'status': 'success'})

@main_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifs_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'success'})

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Manages user profile, business name, password updates, theme toggle, and preferences."""
    if request.method == 'POST':
        action = request.form.get('action', 'profile')
        
        if action == 'profile':
            current_user.full_name = request.form.get('full_name', current_user.full_name).strip()
            current_user.business_name = request.form.get('business_name', current_user.business_name).strip()
            current_user.phone = request.form.get('phone', current_user.phone).strip()
            current_user.language = request.form.get('language', current_user.language)
            current_user.currency = request.form.get('currency', current_user.currency)
            db.session.commit()
            flash('Profile and business preferences updated successfully!', 'success')
            
        elif action == 'password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')
            
            if not check_password_hash(current_user.password_hash, current_pw):
                flash('Current password is incorrect.', 'error')
            elif len(new_pw) < 6 or new_pw != confirm_pw:
                flash('New password must be at least 6 characters and match confirmation.', 'error')
            else:
                current_user.password_hash = generate_password_hash(new_pw)
                db.session.commit()
                flash('Password changed successfully!', 'success')
                
        elif action == 'theme':
            dark_val = request.form.get('dark_mode') == 'true'
            current_user.dark_mode = dark_val
            db.session.commit()
            return jsonify({'status': 'success', 'dark_mode': current_user.dark_mode})
            
        return redirect(url_for('main.settings'))
        
    return render_template('settings.html', user=current_user)
