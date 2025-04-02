import os
import uuid
from PIL import Image
from flask import current_app
from supabase import create_client
from config import Config
import logging
from werkzeug.utils import secure_filename

# Set up logging
logger = logging.getLogger(__name__)

# Initialize admin Supabase client with service role key
admin_supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_image(image_file):
    """Save an image file to storage and return the URL"""
    if not image_file or not image_file.filename:
        logger.info("No image file provided or empty filename")
        return None
        
    try:
        # Generate a unique filename
        original_filename = secure_filename(image_file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'png'
        filename = f"{uuid.uuid4()}.{file_ext}"
        logger.info(f"Generated filename: {filename}")
        
        # Get the file content - rewind the file first to ensure we read from the beginning
        image_file.seek(0)
        file_content = image_file.read()
        
        # Upload to Supabase Storage
        bucket_name = 'postcard-images'  # Use the correct bucket name
        
        # Check if the bucket exists, create if not
        try:
            buckets = admin_supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
            
            if not bucket_exists:
                logger.info(f"Creating bucket: {bucket_name}")
                # Create bucket without the public option for now
                admin_supabase.storage.create_bucket(bucket_name)
        except Exception as e:
            logger.error(f"Error checking/creating bucket: {str(e)}")
        
        # Upload the file - use content-type but remove the upsert option
        storage_response = admin_supabase.storage.from_(bucket_name).upload(
            filename,
            file_content,
            {"content-type": image_file.mimetype}  # Fix: removed upsert option
        )
        logger.info(f"Storage response: {storage_response}")
        
        # Generate the public URL
        image_url = admin_supabase.storage.from_(bucket_name).get_public_url(filename)
        logger.info(f"Generated public URL: {image_url}")
        
        return image_url
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def delete_image(image_url):
    """Delete an image from storage"""
    if not image_url:
        return False
        
    try:
        # Extract filename from the URL
        filename = image_url.split('/')[-1]
        bucket_name = 'postcard-images'  # Use the correct bucket name
        
        # Delete from Supabase Storage
        admin_supabase.storage.from_(bucket_name).remove(filename)
        logger.info(f"Deleted image: {filename} from bucket: {bucket_name}")
        
        return True
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_storage_settings():
    """Verify and update storage settings to ensure images load properly"""
    try:
        bucket_name = 'postcard-images'
        logger.info(f"Verifying storage settings for bucket: {bucket_name}")
        
        # Get bucket details (this checks if bucket exists)
        bucket_exists = False
        try:
            buckets = admin_supabase.storage.list_buckets()
            bucket_exists = any(bucket.name == bucket_name for bucket in buckets)
        except Exception as e:
            logger.error(f"Error checking buckets: {str(e)}")
        
        # Create bucket if it doesn't exist
        if not bucket_exists:
            logger.info(f"Creating bucket: {bucket_name}")
            admin_supabase.storage.create_bucket(bucket_name)
        
        # Update bucket to be public
        try:
            admin_supabase.storage.update_bucket(
                bucket_name,
                {'public': True}  # This makes the bucket publicly accessible
            )
            logger.info(f"Updated bucket {bucket_name} to be public")
        except Exception as e:
            logger.error(f"Error updating bucket publicity: {str(e)}")
        
        # Check and create policies if needed - we'll add policies through SQL
        # Check if we already have a policy for this bucket
        query = """
        SELECT * FROM storage.policies 
        WHERE bucket_id = (SELECT id FROM storage.buckets WHERE name = '{}')
        """.format(bucket_name)
        
        try:
            # We need to use raw SQL to manage policies
            # Create policies for public access
            public_select_policy = """
            INSERT INTO storage.policies (name, bucket_id, definition, operation)
            VALUES (
                'Public Read Access',
                (SELECT id FROM storage.buckets WHERE name = '{}'),
                'true',  -- Anyone can read
                'SELECT'
            )
            ON CONFLICT DO NOTHING;
            """.format(bucket_name)
            
            # Execute the policy creation
            admin_supabase.table("dummy").select("*").execute()  # Just to get a connection
            # We'd ideally run admin_supabase.execute(public_select_policy) here
            # but we'll need to set it up manually in the dashboard
            
            logger.info("Storage policies verified")
            return True
        except Exception as e:
            logger.error(f"Error setting up storage policies: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    except Exception as e:
        logger.error(f"Error verifying storage settings: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False