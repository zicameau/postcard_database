# utils/auth.py
from functools import wraps
from flask import redirect, url_for, flash, session, request, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from utils.user_db import UserDB
from utils.supabase_auth import SupabaseAuth, supabase
import traceback
import gotrue

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        # Handle different input types (Supabase Auth user or database user)
        if hasattr(user_data, 'id'):
            # Supabase Auth user
            self.id = user_data.id
            self.email = user_data.email
            
            # Get metadata from Supabase user object
            metadata = getattr(user_data, 'user_metadata', {}) or {}
            self.username = metadata.get('username', self.email)
            self.role = metadata.get('role', 'user')
        else:
            # Database user dictionary
            self.id = user_data['id']
            self.email = user_data['email']
            self.username = user_data.get('username', self.email)
            self.role = user_data.get('role', 'user')
    
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
        current_app.logger.info(f"Attempting to load user with ID: {user_id}")
        try:
            # First, try to get user from database
            db_user = UserDB.get_user_by_id(user_id)
            
            if db_user:
                current_app.logger.info(f"User found in database: {db_user['email']}")
                return User(db_user)
            
            # If not in database, try to fetch from Supabase Auth
            try:
                # Set session if available
                if 'supabase_access_token' in session:
                    try:
                        supabase.auth.set_session(
                            session['supabase_access_token'], 
                            session.get('supabase_refresh_token')
                        )
                        
                        # Attempt to get user from Supabase Auth
                        auth_response = SupabaseAuth.get_user()
                        
                        if auth_response and hasattr(auth_response, 'user') and auth_response.user:
                            current_app.logger.info(f"User found in Supabase Auth: {auth_response.user.email}")
                            
                            # Ensure user exists in database
                            existing_user = UserDB.get_user_by_email(auth_response.user.email)
                            if not existing_user:
                                # Create user in database if not exists
                                user_data = {
                                    'id': auth_response.user.id,
                                    'email': auth_response.user.email,
                                    'username': (auth_response.user.user_metadata.get('username') 
                                                 or auth_response.user.email.split('@')[0]),
                                    'role': auth_response.user.user_metadata.get('role', 'user')
                                }
                                existing_user = UserDB.create_user_from_auth(user_data)
                            
                            return User(existing_user)
                    except gotrue.errors.AuthApiError as auth_error:
                        # If we get "User from sub claim in JWT does not exist", clear the session
                        if "User from sub claim in JWT does not exist" in str(auth_error):
                            current_app.logger.warning("Invalid session detected, clearing session")
                            session.pop('supabase_access_token', None)
                            session.pop('supabase_refresh_token', None)
                        else:
                            current_app.logger.error(f"Supabase Auth error: {str(auth_error)}")
                            current_app.logger.error(traceback.format_exc())
                else:
                    current_app.logger.info("No Supabase session in Flask session")
            
            except Exception as auth_error:
                current_app.logger.error(f"Supabase Auth error: {str(auth_error)}")
                current_app.logger.error(traceback.format_exc())
        
        except Exception as e:
            current_app.logger.error(f"Error in load_user: {str(e)}")
            current_app.logger.error(traceback.format_exc())
        
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