from supabase import create_client
from config import Config
import uuid

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

class PostcardDB:
    @staticmethod
    def get_all_postcards(limit=20, offset=0, filters=None):
        """Fetch all postcards with optional filtering and pagination"""
        query = supabase.table('postcards').select('*')
        
        if filters:
            for field, value in filters.items():
                if value:
                    query = query.eq(field, value)
        
        # Apply ordering
        query = query.order('created_at', desc=True)
        
        # Apply limit
        query = query.limit(limit)
        
        # Handle pagination differently since .offset() isn't available
        # We'll use range instead, which is supported by Supabase
        if offset > 0:
            # Calculate the range based on offset and limit
            # Supabase uses inclusive start, exclusive end
            start = offset
            end = offset + limit - 1
            query = query.range(start, end)
        
        result = query.execute()
        
        return result.data
    
    @staticmethod
    def get_postcard(postcard_id):
        """Fetch a single postcard by ID"""
        result = supabase.table('postcards').select('*').eq('id', postcard_id).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def create_postcard(postcard_data):
        """Create a new postcard"""
        # Generate UUID for the postcard
        if 'id' not in postcard_data:
            postcard_data['id'] = str(uuid.uuid4())
            
        result = supabase.table('postcards').insert(postcard_data).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def update_postcard(postcard_id, postcard_data):
        """Update an existing postcard"""
        result = supabase.table('postcards').update(postcard_data).eq('id', postcard_id).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def delete_postcard(postcard_id):
        """Delete a postcard"""
        result = supabase.table('postcards').delete().eq('id', postcard_id).execute()
        return result.data
    
    @staticmethod
    def get_postcard_types():
        """Get all postcard types"""
        # For enums in Supabase, we need to query them differently
        # This is a simplified version - you might need to adjust based on your Supabase setup
        types = ['RPPC', 'Divided Back', 'Undivided Back', 'Linen', 'Chrome', 'Continental']
        return types
    
    @staticmethod
    def get_postcard_eras():
        """Get all postcard eras"""
        eras = [
            '1860s', '1870s', '1880s', '1890s', '1900s', '1910s', '1920s', 
            '1930s', '1940s', '1950s', '1960s', '1970s', '1980s', '1990s', 
            '2000s', '2010s', '2020s'
        ]
        return eras

    @staticmethod
    def get_user_postcards(user_id, limit=20, offset=0):
        """Fetch all postcards for a specific user"""
        query = supabase.table('postcards').select('*').eq('user_id', user_id)
        
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

class TagDB:
    @staticmethod
    def get_all_tags():
        """Fetch all tags"""
        result = supabase.table('tags').select('*').execute()
        return result.data
    
    @staticmethod
    def create_tag(name):
        """Create a new tag"""
        tag_id = str(uuid.uuid4())
        result = supabase.table('tags').insert({'id': tag_id, 'name': name}).execute()
        
        if result.data:
            return result.data[0]
        return None
    
    @staticmethod
    def link_tag_to_postcard(postcard_id, tag_id):
        """Link a tag to a postcard"""
        result = supabase.table('postcard_tags').insert({
            'postcard_id': postcard_id, 
            'tag_id': tag_id
        }).execute()
        
        return result.data
    
    @staticmethod
    def get_postcard_tags(postcard_id):
        """Get all tags for a postcard"""
        result = supabase.table('postcard_tags')\
            .select('tags(*)')\
            .eq('postcard_id', postcard_id)\
            .execute()
        
        # Extract tag data from the result
        tags = []
        for item in result.data:
            if 'tags' in item and item['tags']:
                tags.append(item['tags'])
        
        return tags