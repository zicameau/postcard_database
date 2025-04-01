from datetime import datetime
from flask import Markup

def register_filters(app):
    """Register custom template filters with the Flask app"""
    
    @app.template_filter('datetime')
    def format_datetime(value, format='%B %d, %Y'):
        """Format a datetime object to a string"""
        if not value:
            return ''
        
        # If it's a string, try to parse it
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return value
        
        # Format the datetime
        try:
            return value.strftime(format)
        except (AttributeError, ValueError):
            return value
    
    @app.template_filter('nl2br')
    def nl2br(value):
        """Convert newlines to <br> tags"""
        if not value:
            return ''
        
        return Markup(str(value).replace('\n', '<br>'))
    
    @app.template_filter('truncate_words')
    def truncate_words(value, length=30):
        """Truncate a string to a certain number of words"""
        if not value:
            return ''
        
        words = str(value).split()
        
        if len(words) <= length:
            return value
        
        return ' '.join(words[:length]) + '...'
    
    @app.context_processor
    def inject_now():
        """Inject the current datetime into templates"""
        return {'now': datetime.now()}