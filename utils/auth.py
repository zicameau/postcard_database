# utils/auth.py
from functools import wraps
from flask import redirect, url_for, flash, session, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from utils.user_db import UserDB
from utils.supabase_auth import SupabaseAuth, supabase

# User class for Flask-Login
class User(UserMixin):

    def __init__(self, user_data):
        # Check if user_data is already a Supabase User object
        if hasattr(user_data, 'id'):
            self.id = user_data.id
            self.email = user_data.email
            
            # Get metadata from Supabase user object
            metadata = getattr(user_data, 'user_metadata', {}) or {}
            self.username = metadata.get('username', self.email)
            self.role = metadata.get('role', 'user')
        else:
            # Handle dictionary data (from your database)
            self.id = user_data['id']
            self.email = user_data['email']
            self.username = user_data.get('username', self.email)
            
            # Get role from either top-level or nested metadata
            if 'role' in user_data:
                self.role = user_data['role']
            elif 'user_metadata' in user_data and 'role' in user_data['user_metadata']:
                self.role = user_data['user_metadata']['role']
            else:
                self.role = 'user'
    
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
        try:
            # Try to get user from Supabase Auth using the session
            if 'supabase_access_token' in session:
                supabase.auth.set_session(session['supabase_access_token'], session['supabase_refresh_token'])
                
                # Get current authenticated user from Supabase
                auth_response = SupabaseAuth.get_user()
                
                if auth_response and hasattr(auth_response, 'user') and auth_response.user:
                    # Check if the authenticated user matches the user_id
                    if str(auth_response.user.id) == str(user_id):
                        return User(auth_response.user)
        except Exception as e:
            print(f"Supabase Auth error in load_user: {str(e)}")
        
        # Fallback to database
        try:
            db_user = UserDB.get_user_by_id(user_id)
            if db_user:
                return User(db_user)
        except Exception as e:
            print(f"Database error in load_user: {str(e)}")
        
        return None

def requires_admin(func):
    """Decorator for routes that require admin access"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated_function