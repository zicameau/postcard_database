import os
import uuid
from PIL import Image
from flask import current_app
from supabase import create_client
from config import Config

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_image(file, bucket_name='postcard-images'):
    """
    Save an image to Supabase Storage
    """
    if not file or not allowed_file(file.filename):
        return None
    
    try:
        # Generate a complete UUID (full 36 character format with hyphens)
        file_uuid = uuid.uuid4()
        filename = f"{str(file_uuid)}.{file.filename.rsplit('.', 1)[1].lower()}"
        current_app.logger.info(f"Generated filename: {filename}")
        
        # Validate UUID is complete (should be 36 chars plus extension)
        if len(str(file_uuid)) != 36:
            current_app.logger.error(f"Generated UUID is incomplete: {file_uuid}")
            return None
        
        # Upload the file to Supabase Storage
        result = supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=file.read(),
            file_options={"content-type": file.content_type}
        )
        
        # Get the public URL
        file_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        current_app.logger.info(f"Generated image URL: {file_url}")
        
        # Verify URL contains full UUID
        if str(file_uuid) not in file_url:
            current_app.logger.error(f"UUID not found in generated URL: {file_url}")
            # Still return the URL even if verification fails, as it might be formatted differently
        
        return file_url
    except Exception as e:
        current_app.logger.error(f"Error saving image: {str(e)}")
        return None

def delete_image(image_url, bucket_name='postcard-images'):
    """
    Delete an image from Supabase Storage
    
    Args:
        image_url: The URL of the image to delete
        bucket_name: The Supabase storage bucket name
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract filename from URL
        filename = image_url.split('/')[-1]
        
        # Delete from Supabase Storage
        supabase.storage.from_(bucket_name).remove([filename])
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting image: {str(e)}")
        return False