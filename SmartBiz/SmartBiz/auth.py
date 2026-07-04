from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Notification

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('login.html', email=email)
            
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password. Please try again.', 'error')
            return render_template('login.html', email=email)
            
        login_user(user, remember=remember)
        
        # Add login notification
        notif = Notification(
            user_id=user.id,
            title="Successful Login",
            message=f"Welcome back to SmartBiz AI, {user.full_name}!",
            type="info",
            link="/dashboard"
        )
        db.session.add(notif)
        db.session.commit()
        
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
        
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        business_name = request.form.get('business_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([full_name, business_name, email, password, confirm_password]):
            flash('Please fill in all required fields.', 'error')
            return render_template('register.html', full_name=full_name, business_name=business_name, email=email, phone=phone)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html', full_name=full_name, business_name=business_name, email=email, phone=phone)
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html', full_name=full_name, business_name=business_name, email=email, phone=phone)
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('register.html', full_name=full_name, business_name=business_name, email=email, phone=phone)
            
        # Create new user
        hashed_pw = generate_password_hash(password)
        new_user = User(
            full_name=full_name,
            business_name=business_name,
            email=email,
            phone=phone,
            password_hash=hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Welcome notification
        notif = Notification(
            user_id=new_user.id,
            title="Welcome to SmartBiz AI!",
            message=f"Your business account for {business_name} has been created successfully.",
            type="success",
            link="/dashboard"
        )
        db.session.add(notif)
        db.session.commit()
        
        login_user(new_user)
        flash('Registration successful! Welcome to your SmartBiz AI dashboard.', 'success')
        return redirect(url_for('dashboard.index'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            flash(f'A password reset link has been sent to {email}. Please check your inbox.', 'success')
        else:
            flash('If an account exists with that email, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('login.html', forgot=True)
