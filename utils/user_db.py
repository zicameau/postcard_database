from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client
from config import Config
import uuid
from functools import wraps

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

class UserDB:
    @staticmethod
    def get_user_by_id(user_id):
        """Fetch a user by ID"""
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def get_user_by_email(email):
        """Fetch a user by email"""
        result = supabase.table('users').select('*').eq('email', email).execute()
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def get_user_by_username(username):
        """Fetch a user by username"""
        result = supabase.table('users').select('*').eq('username', username).execute()
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def create_user(username, email, password, role='user'):
        """Create a new user"""
        # Hash the password for security
        password_hash = generate_password_hash(password)
        
        # Generate UUID
        user_id = str(uuid.uuid4())
        
        # Create user data
        user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role
        }
        
        # Insert into database
        result = supabase.table('users').insert(user_data).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate a user by email and password"""
        user = UserDB.get_user_by_email(email)
        
        if user and check_password_hash(user['password_hash'], password):
            return user
        
        return None
    
    @staticmethod
    def get_all_users(limit=100, offset=0):
        """Get all users (for admin use)"""
        query = supabase.table('users').select('id, username, email, role, created_at')
        
        # Apply ordering
        query = query.order('created_at', desc=True)
        
        # Apply limit
        query = query.limit(limit)
        
        # Handle pagination
        if offset > 0:
            start = offset
            end = offset + limit - 1
            query = query.range(start, end)
        
        result = query.execute()
        
        return result.data
    
    @staticmethod
    def is_admin(user_id):
        """Check if a user is an admin"""
        user = UserDB.get_user_by_id(user_id)
        return user and user['role'] == 'admin'
    
    @staticmethod
    def update_user(user_id, user_data):
        """Update user information"""
        # If password is being updated, hash it
        if 'password' in user_data:
            user_data['password_hash'] = generate_password_hash(user_data.pop('password'))
        
        result = supabase.table('users').update(user_data).eq('id', user_id).execute()
        
        if result.data:
            return result.data[0]
        return None