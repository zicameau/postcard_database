from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
from config import Config
from utils.db import PostcardDB, TagDB
from utils.image_handler import save_image, delete_image
from utils.template_filters import register_filters

app = Flask(__name__)
app.config.from_object(Config)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register custom template filters
register_filters(app)

@app.route('/')
def index():
    """Homepage with featured postcards"""
    # Get the latest postcards
    postcards = PostcardDB.get_all_postcards(limit=8)
    return render_template('index.html', postcards=postcards)

@app.route('/postcards')
def list_postcards():
    """List all postcards with optional filtering"""
    # Get filter parameters
    era = request.args.get('era')
    postcard_type = request.args.get('type')
    manufacturer = request.args.get('manufacturer')
    is_posted = request.args.get('is_posted', type=bool)
    is_written = request.args.get('is_written', type=bool)
    
    # Prepare filters
    filters = {}
    if era:
        filters['era'] = era
    if postcard_type:
        filters['type'] = postcard_type
    if manufacturer:
        filters['manufacturer'] = manufacturer
    if is_posted is not None:
        filters['is_posted'] = is_posted
    if is_written is not None:
        filters['is_written'] = is_written
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # Get postcards
    postcards = PostcardDB.get_all_postcards(limit=per_page, offset=offset, filters=filters)
    
    # Get filter options for dropdowns
    eras = PostcardDB.get_postcard_eras()
    types = PostcardDB.get_postcard_types()
    
    return render_template(
        'postcards/list.html', 
        postcards=postcards,
        eras=eras,
        types=types,
        current_filters=filters,
        page=page
    )

@app.route('/postcards/<uuid:postcard_id>')
def view_postcard(postcard_id):
    """View a single postcard"""
    postcard = PostcardDB.get_postcard(str(postcard_id))
    
    if not postcard:
        flash('Postcard not found', 'error')
        return redirect(url_for('list_postcards'))
    
    # Get tags for this postcard
    tags = TagDB.get_postcard_tags(str(postcard_id))
    
    return render_template('postcards/detail.html', postcard=postcard, tags=tags)

@app.route('/postcards/add', methods=['GET', 'POST'])
def add_postcard():
    """Add a new postcard"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        era = request.form.get('era')
        manufacturer = request.form.get('manufacturer')
        postcard_type = request.form.get('type')
        is_posted = 'is_posted' in request.form
        is_written = 'is_written' in request.form
        tags = request.form.get('tags', '').split(',')
        
        # Validate required fields
        if not title:
            flash('Title is required', 'error')
            return redirect(url_for('add_postcard'))
        
        # Handle image uploads
        front_image_url = None
        back_image_url = None
        
        if 'front_image' in request.files:
            front_image = request.files['front_image']
            if front_image.filename:
                front_image_url = save_image(front_image)
        
        if 'back_image' in request.files:
            back_image = request.files['back_image']
            if back_image.filename:
                back_image_url = save_image(back_image)
        
        # Create postcard data
        postcard_data = {
            'title': title,
            'description': description,
            'era': era,
            'manufacturer': manufacturer,
            'type': postcard_type,
            'is_posted': is_posted,
            'is_written': is_written,
            'front_image_url': front_image_url,
            'back_image_url': back_image_url
        }
        
        # Save to database
        postcard = PostcardDB.create_postcard(postcard_data)
        
        if postcard:
            # Handle tags
            for tag_name in tags:
                tag_name = tag_name.strip()
                if tag_name:
                    # Create tag if it doesn't exist
                    existing_tags = TagDB.get_all_tags()
                    tag = next((t for t in existing_tags if t['name'].lower() == tag_name.lower()), None)
                    
                    if not tag:
                        tag = TagDB.create_tag(tag_name)
                    
                    if tag:
                        TagDB.link_tag_to_postcard(postcard['id'], tag['id'])
            
            flash('Postcard added successfully', 'success')
            return redirect(url_for('view_postcard', postcard_id=postcard['id']))
        else:
            flash('Failed to add postcard', 'error')
    
    # GET request - show form
    eras = PostcardDB.get_postcard_eras()
    types = PostcardDB.get_postcard_types()
    
    return render_template('postcards/add.html', eras=eras, types=types)

@app.route('/postcards/<uuid:postcard_id>/edit', methods=['GET', 'POST'])
def edit_postcard(postcard_id):
    """Edit an existing postcard"""
    postcard = PostcardDB.get_postcard(str(postcard_id))
    
    if not postcard:
        flash('Postcard not found', 'error')
        return redirect(url_for('list_postcards'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        era = request.form.get('era')
        manufacturer = request.form.get('manufacturer')
        postcard_type = request.form.get('type')
        is_posted = 'is_posted' in request.form
        is_written = 'is_written' in request.form
        
        # Validate required fields
        if not title:
            flash('Title is required', 'error')
            return redirect(url_for('edit_postcard', postcard_id=postcard_id))
        
        # Handle image uploads
        front_image_url = postcard.get('front_image_url')
        back_image_url = postcard.get('back_image_url')
        
        if 'front_image' in request.files:
            front_image = request.files['front_image']
            if front_image.filename:
                # Delete old image if it exists
                if front_image_url:
                    delete_image(front_image_url)
                
                # Upload new image
                front_image_url = save_image(front_image)
        
        if 'back_image' in request.files:
            back_image = request.files['back_image']
            if back_image.filename:
                # Delete old image if it exists
                if back_image_url:
                    delete_image(back_image_url)
                
                # Upload new image
                back_image_url = save_image(back_image)
        
        # Update postcard data
        postcard_data = {
            'title': title,
            'description': description,
            'era': era,
            'manufacturer': manufacturer,
            'type': postcard_type,
            'is_posted': is_posted,
            'is_written': is_written,
            'front_image_url': front_image_url,
            'back_image_url': back_image_url
        }
        
        # Save to database
        updated_postcard = PostcardDB.update_postcard(str(postcard_id), postcard_data)
        
        if updated_postcard:
            flash('Postcard updated successfully', 'success')
            return redirect(url_for('view_postcard', postcard_id=postcard_id))
        else:
            flash('Failed to update postcard', 'error')
    
    # GET request - show form with current data
    eras = PostcardDB.get_postcard_eras()
    types = PostcardDB.get_postcard_types()
    tags = TagDB.get_postcard_tags(str(postcard_id))
    
    return render_template(
        'postcards/edit.html', 
        postcard=postcard, 
        eras=eras, 
        types=types,
        tags=tags
    )

@app.route('/postcards/<uuid:postcard_id>/delete', methods=['POST'])
def delete_postcard(postcard_id):
    """Delete a postcard"""
    postcard = PostcardDB.get_postcard(str(postcard_id))
    
    if not postcard:
        flash('Postcard not found', 'error')
        return redirect(url_for('list_postcards'))
    
    # Delete associated images
    if postcard.get('front_image_url'):
        delete_image(postcard['front_image_url'])
    
    if postcard.get('back_image_url'):
        delete_image(postcard['back_image_url'])
    
    # Delete from database
    PostcardDB.delete_postcard(str(postcard_id))
    
    flash('Postcard deleted successfully', 'success')
    return redirect(url_for('list_postcards'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    app.run(debug=True)