# utils/supabase_auth.py
from supabase import create_client
from config import Config
from utils.user_db import UserDB
import traceback
import uuid
import gotrue

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

class SupabaseAuth:
    @staticmethod
    def register_user(email, password, username=None, metadata=None):
        """Register a new user with Supabase Auth"""
        try:
            # Prepare metadata for Supabase Auth
            user_metadata = metadata or {}
            
            # Generate a unique username if not provided
            if not username:
                # Use email prefix and truncate to 50 characters
                username = email.split('@')[0][:50]
                
                # Ensure username uniqueness
                base_username = username
                counter = 1
                while UserDB.get_user_by_username(username):
                    username = f"{base_username}_{counter}"
                    counter += 1
            
            # Prepare metadata
            user_metadata['username'] = username
            user_metadata['role'] = user_metadata.get('role', 'user')
            
            # Create user in Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": user_metadata
                }
            })
            
            # If auth registration is successful, create user in database
            if auth_response and auth_response.user:
                # Prepare user data for database
                user_data = {
                    'id': str(auth_response.user.id),
                    'email': email,
                    'username': username,
                    'role': user_metadata['role']
                }
                
                # Create user in database
                UserDB.create_user_from_auth(user_data)
            
            return auth_response
        
        except Exception as e:
            print(f"Error registering user: {str(e)}")
            print(traceback.format_exc())
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
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def logout_user():
        """Log out the current user"""
        try:
            response = supabase.auth.sign_out()
            return response
        except Exception as e:
            print(f"Error logging out user: {str(e)}")
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def get_user():
        """Get current user data from Supabase Auth"""
        try:
            # Get the current authenticated user from the session
            response = supabase.auth.get_user()
            return response
        except gotrue.errors.AuthApiError as e:
            # If the token is invalid or user doesn't exist, return None instead of raising
            if "User from sub claim in JWT does not exist" in str(e):
                print("Invalid session token detected")
                return None
            else:
                print(f"Error getting user details: {str(e)}")
                print(traceback.format_exc())
                return None
        except Exception as e:
            print(f"Error getting user details: {str(e)}")
            print(traceback.format_exc())
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
            print(traceback.format_exc())
            return None
    
    @staticmethod
    def delete_user(user_id):
        """Delete a user from Supabase Auth"""
        try:
            # Note: This requires admin privileges via the service role key
            admin_supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
            response = admin_supabase.auth.admin.delete_user(user_id)
            return response
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            print(traceback.format_exc())
            return None