from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client
from config import Config
import uuid
from functools import wraps
import traceback

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

class UserDB:
    @staticmethod
    def get_user_by_id(user_id):
        """Fetch a user by ID"""
        try:
            result = supabase.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching user by ID: {str(e)}")
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def get_user_by_email(email):
        """Fetch a user by email"""
        try:
            result = supabase.table('users').select('*').eq('email', email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching user by email: {str(e)}")
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def get_user_by_username(username):
        """Fetch a user by username"""
        try:
            result = supabase.table('users').select('*').eq('username', username).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching user by username: {str(e)}")
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def create_user(username, email, password, role='user'):
        """Create a new user"""
        try:
            # Generate a unique ID
            user_id = str(uuid.uuid4())
            
            # Hash the password for security
            password_hash = generate_password_hash(password)
            
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
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def create_user_from_auth(user_data):
        """Create a user from Supabase Auth data"""
        try:
            # Check if user already exists in database
            existing_user = UserDB.get_user_by_id(user_data['id'])
            if existing_user:
                print(f"User already exists with ID: {user_data['id']}")
                return existing_user
            
            # Ensure all required fields are present
            insert_data = {
                'id': user_data['id'],
                'email': user_data['email'],
                'username': user_data['username'],
                'role': user_data['role'],
                'password_hash': user_data.get('password_hash', generate_password_hash(str(uuid.uuid4())))
            }
            
            # Make sure to use the correct service role key for Supabase
            admin_supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
            
            # Insert into database using upsert to handle potential conflicts
            result = admin_supabase.table('users').upsert(insert_data).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating user from auth: {str(e)}")
            print(traceback.format_exc())
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
        try:
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
        except Exception as e:
            print(f"Error getting users: {str(e)}")
            print(traceback.format_exc())
            return []
    
    @staticmethod
    def is_admin(user_id):
        """Check if a user is an admin"""
        user = UserDB.get_user_by_id(user_id)
        return user and user['role'] == 'admin'
    
    @staticmethod
    def update_user(user_id, user_data):
        """Update user information"""
        try:
            # If password is being updated, hash it
            if 'password' in user_data:
                user_data['password_hash'] = generate_password_hash(user_data.pop('password'))
            
            result = supabase.table('users').update(user_data).eq('id', user_id).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            print(traceback.format_exc())
            return None