# utils/supabase_auth.py
from supabase import create_client
from config import Config

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

class SupabaseAuth:
    @staticmethod
    def register_user(email, password, username=None, metadata=None):
        """Register a new user with Supabase Auth"""
        user_metadata = metadata or {}
        if username:
            user_metadata['username'] = username
        
        try:
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            return response
        except Exception as e:
            print(f"Error registering user: {str(e)}")
            return None
    
    @staticmethod
    def login_user(email, password):
        """Log in a user with Supabase Auth"""
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return response
        except Exception as e:
            print(f"Error logging in user: {str(e)}")
            return None
    
    @staticmethod
    def logout_user():
        """Log out the current user"""
        try:
            response = supabase.auth.sign_out()
            return response
        except Exception as e:
            print(f"Error logging out user: {str(e)}")
            return None
    
    @staticmethod
    def get_user():
        """Get current user data from Supabase Auth"""
        try:
            # Get the current authenticated user from the session
            response = supabase.auth.get_user()
            return response
        except Exception as e:
            print(f"Error getting user details: {str(e)}")
            return None
    
    @staticmethod
    def update_user(user_id, user_data):
        """Update user data in Supabase Auth"""
        try:
            response = supabase.auth.admin.update_user_by_id(
                user_id,
                user_data
            )
            return response
        except Exception as e:
            print(f"Error updating user: {str(e)}")
            return None