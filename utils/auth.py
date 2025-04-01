# utils/auth.py
from functools import wraps
from flask import redirect, url_for, flash, session, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from utils.user_db import UserDB
from utils.supabase_auth import SupabaseAuth

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.username = user_data.get('username') or user_data.get('user_metadata', {}).get('username', self.email)
        self.role = user_data.get('role') or user_data.get('user_metadata', {}).get('role', 'user')
    
    @property
    def is_admin(self):
        return self.role == 'admin'

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "error"
    
    @login_manager.user_loader
    def load_user(user_id):
        # Try to get user from Supabase Auth
        auth_user = SupabaseAuth.get_user(user_id)
        if auth_user and auth_user.user:
            return User(auth_user.user)
        
        # If not found, try fallback to database
        db_user = UserDB.get_user_by_id(user_id)
        if db_user:
            return User(db_user)
        
        return None
    
    return login_manager

def requires_admin(func):
    """Decorator for routes that require admin access"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function