import os
from flask import Flask, render_template
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import flask_login

# Make `login_required` a no-op so the app can run without requiring auth.
# This overrides the decorator in `flask_login` before other modules import it,
# ensuring routes decorated with `@login_required` remain callable.
flask_login.login_required = lambda f: f

from models import db, User
from utils import seed_sample_data
from auth import auth_bp
from dashboard import dashboard_bp
from inventory import inventory_bp
from customers import customers_bp
from sales import sales_bp
from reports import reports_bp
from ai import ai_bp
from routes import main_bp

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-smartbiz-enterprise-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///smartbiz.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB max upload size
    
    # Initialize Database
    db.init_app(app)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access your SmartBiz AI Enterprise dashboard.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Custom Jinja2 Template Filters
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            return f"${float(val):,.2f}"
        except:
            return "$0.00"
            
    @app.template_filter('percentage')
    def percentage_filter(val):
        try:
            return f"{float(val):+.1f}%"
        except:
            return "0.0%"
            
    @app.template_filter('date_format')
    def date_format_filter(val):
        try:
            if hasattr(val, 'strftime'):
                return val.strftime('%b %d, %Y')
            return str(val)[:10]
        except:
            return str(val)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(main_bp)
    
    # Error Handlers for Premium UX
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('dashboard.html', error_mode=404, message="The requested analytics view or module could not be found."), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('dashboard.html', error_mode=500, message="An internal server error occurred while processing data."), 500

    # Initialize DB & Seed Sample Data
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs('database', exist_ok=True)
        os.makedirs(os.path.join(app.instance_path, 'database'), exist_ok=True)
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        db.create_all()
        # Seed sample data only when explicitly requested via environment variable.
        # This prevents placeholder/sample records from appearing and ensures
        # the app shows only user-imported data by default.
        if os.environ.get('SEED_SAMPLE_DATA', 'false').lower() == 'true':
            seed_sample_data()
        
    return app

app = create_app()

if __name__ == '__main__':
    print("=========================================================================")
    print("   SMARTBIZ AI - ENTERPRISE BUSINESS ANALYTICS DASHBOARD FOR SMES")
    print("   Running locally on: http://127.0.0.1:5000")
    print("   Default Admin Login: admin@smartbiz.ai / password: admin123")
    print("=========================================================================")
    app.run(debug=True, host='0.0.0.0', port=5000)
