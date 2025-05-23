from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
import os
from config import Config
from utils.db import PostcardDB, TagDB
from utils.user_db import UserDB
from utils.image_handler import save_image, delete_image, verify_storage_settings
from utils.template_filters import register_filters
from utils.auth import User, init_login_manager, requires_admin
from utils.supabase_auth import SupabaseAuth

app = Flask(__name__)
app.config.from_object(Config)

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = init_login_manager(app)

# Register custom template filters
register_filters(app)

# Verify storage settings on startup - don't use before_first_request
with app.app_context():
    verify_storage_settings()

# Routes for public access
@app.route('/')
def index():
    """Homepage with featured postcards"""
    # Get the latest postcards
    postcards = PostcardDB.get_all_postcards(limit=8)
    return render_template('index.html', postcards=postcards)

@app.route('/user/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    """User settings page"""
    if request.method == 'POST':
        # Handle user settings update
        # This is a stub - you'd implement actual settings updates here
        flash('Settings updated successfully', 'success')
        return redirect(url_for('user_settings'))
    
    # Use current_user directly instead of trying to fetch from Supabase again
    return render_template('auth/settings.html', user=current_user)

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

# Modify existing view_postcard route to handle different statuses
@app.route('/postcards/<uuid:postcard_id>')
def view_postcard(postcard_id):
    """View a single postcard"""
    postcard = PostcardDB.get_postcard(str(postcard_id))
    
    if not postcard:
        flash('Postcard not found', 'error')
        return redirect(url_for('list_postcards'))
    
    # Check postcard visibility
    is_owner = current_user.is_authenticated and postcard['user_id'] == current_user.id
    is_admin = current_user.is_authenticated and current_user.is_admin
    
    # Determine if postcard can be viewed
    if (postcard['status'] != 'approved' and 
        not is_owner and 
        not is_admin):
        flash('This postcard is not available for viewing', 'error')
        return redirect(url_for('list_postcards'))
    
    # Get tags for this postcard
    tags = TagDB.get_postcard_tags(str(postcard_id))
    
    # Pass additional context about user's permissions
    context = {
        'postcard': postcard, 
        'tags': tags,
        'can_submit': is_owner and postcard['status'] == 'draft',
        'can_review': is_admin and postcard['status'] == 'staged'
    }
    
    return render_template('postcards/detail.html', **context)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    # Clear any existing invalid sessions first
    if 'supabase_access_token' in session:
        session.pop('supabase_access_token', None)
        session.pop('supabase_refresh_token', None)
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return redirect(url_for('login'))
        
        # Use Supabase Auth to log in
        try:
            auth_response = SupabaseAuth.login_user(email, password)
            
            if auth_response and hasattr(auth_response, 'user') and auth_response.user:
                user = User(auth_response.user)
                login_user(user)
                
                # Store Supabase session in Flask session if it exists
                if hasattr(auth_response, 'session'):
                    session['supabase_access_token'] = auth_response.session.access_token
                    session['supabase_refresh_token'] = auth_response.session.refresh_token
                
                # Redirect to the page the user was trying to access
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            app.logger.error(f"Login error: {str(e)}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        # Check if username already exists
        existing_user = UserDB.get_user_by_username(username)
        if existing_user:
            flash('Username is already in use', 'error')
            return redirect(url_for('register'))
        
        # Check if email already exists
        existing_user = UserDB.get_user_by_email(email)
        if existing_user:
            flash('Email is already in use', 'error')
            return redirect(url_for('register'))
        
        try:
            # First create the user in Supabase Auth
            metadata = {
                'username': username,
                'role': 'user'  # Default role
            }
            
            auth_response = SupabaseAuth.register_user(email, password, username, metadata)
            
            if auth_response and hasattr(auth_response, 'user') and auth_response.user:
                # Now create the user in the database
                user_data = {
                    'id': auth_response.user.id,
                    'email': email,
                    'username': username,
                    'role': 'user',
                    'password_hash': generate_password_hash(password)
                }
                
                user_created = UserDB.create_user_from_auth(user_data)
                
                if user_created:
                    flash('Registration successful! Please check your email to verify your account.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('User created in authentication system, but database creation failed.', 'warning')
                    return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'error')
        except Exception as e:
            error_message = str(e)
            app.logger.error(f"Registration error: {error_message}")
            
            if 'already been registered' in error_message:
                flash('Email is already registered', 'error')
            elif 'SupabaseAuth' in error_message and 'delete_user' in error_message:
                flash('Registration error: Authentication system configuration issue', 'error')
            else:
                flash(f'Registration error: {error_message}', 'error')
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    # Clear Supabase session
    SupabaseAuth.logout_user()
    session.pop('supabase_access_token', None)
    session.pop('supabase_refresh_token', None)
    
    # Log out of Flask-Login
    logout_user()
    
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def user_profile():
    """User profile page"""
    # Get user postcards
    user_postcards = PostcardDB.get_user_postcards(current_user.id)
    
    return render_template('auth/profile.html', postcards=user_postcards)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Validation
        if not username or not email:
            flash('Username and email are required', 'error')
            return redirect(url_for('edit_profile'))
        
        # Check if email already exists and is not the current user's email
        existing_user = UserDB.get_user_by_email(email)
        if existing_user and existing_user['id'] != current_user.id:
            flash('Email already in use', 'error')
            return redirect(url_for('edit_profile'))
        
        # Check if username already exists and is not the current user's username
        existing_user = UserDB.get_user_by_username(username)
        if existing_user and existing_user['id'] != current_user.id:
            flash('Username already in use', 'error')
            return redirect(url_for('edit_profile'))
        
        # Update user
        user_data = {
            'username': username,
            'email': email
        }
        
        updated_user = UserDB.update_user(current_user.id, user_data)
        
        if updated_user:
            flash('Profile updated successfully', 'success')
            # Update current_user session
            refresh_user = User(updated_user)
            login_user(refresh_user)
            return redirect(url_for('user_profile'))
        else:
            flash('Failed to update profile', 'error')
    
    return render_template('auth/edit_profile.html')

@app.route('/profile/password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('change_password'))
        
        # Verify current password
        user = UserDB.get_user_by_id(current_user.id)
        if not check_password_hash(user['password_hash'], current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('change_password'))
        
        # Update password
        user_data = {
            'password': new_password  # It will be hashed in the update_user method
        }
        
        updated_user = UserDB.update_user(current_user.id, user_data)
        
        if updated_user:
            flash('Password changed successfully', 'success')
            return redirect(url_for('user_profile'))
        else:
            flash('Failed to change password', 'error')
    
    return render_template('auth/change_password.html')

# Admin routes
@app.route('/admin/users')
@login_required
@requires_admin
def admin_users():
    """Admin page to view all users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    users = UserDB.get_all_users(limit=per_page, offset=offset)
    
    return render_template('admin/users.html', users=users, page=page)

@app.route('/admin/users/<uuid:user_id>', methods=['GET', 'POST'])
@login_required
@requires_admin
def admin_edit_user(user_id):
    """Admin page to edit a user"""
    user = UserDB.get_user_by_id(str(user_id))
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        
        # Prepare update data
        user_data = {
            'username': username,
            'email': email,
            'role': role
        }
        
        # Update user
        updated_user = UserDB.update_user(str(user_id), user_data)
        
        if updated_user:
            flash('User updated successfully', 'success')
            return redirect(url_for('admin_users'))
        else:
            flash('Failed to update user', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin')
@login_required
@requires_admin
def admin_dashboard():
    """Admin dashboard with links to all admin functions"""
    # Get some basic stats for the dashboard
    stats = {
        'total_users': len(UserDB.get_all_users(limit=1000)),
        'total_postcards': len(PostcardDB.get_all_postcards(limit=1000)),
        'total_tags': len(TagDB.get_all_tags())
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/tags')
@login_required
@requires_admin
def admin_tags():
    """Admin page to view and manage all tags"""
    tags = TagDB.get_all_tags()
    return render_template('admin/tags.html', tags=tags)

@app.route('/postcards/add', methods=['GET', 'POST'])
@login_required
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
        
        # Determine action (draft or submit)
        action = request.form.get('action', 'draft')
        
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
            'back_image_url': back_image_url,
            'user_id': current_user.id,  # Add user ID to track ownership
            'status': 'draft' if action == 'draft' else 'staged'
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
            
            # Determine flash message based on action
            if action == 'draft':
                flash('Postcard saved as draft', 'success')
                return redirect(url_for('user_profile'))
            else:
                flash('Postcard submitted for review', 'success')
                return redirect(url_for('view_postcard', postcard_id=postcard['id']))
        else:
            flash('Failed to add postcard', 'error')
    
    # GET request - show form
    eras = PostcardDB.get_postcard_eras()
    types = PostcardDB.get_postcard_types()
    
    return render_template('postcards/add.html', eras=eras, types=types)

@app.route('/postcards/<uuid:postcard_id>/submit', methods=['POST'])
@login_required
def submit_postcard(postcard_id):
    """Submit a draft postcard for review"""
    postcard = PostcardDB.get_postcard(str(postcard_id))
    
    if not postcard:
        flash('Postcard not found', 'error')
        return redirect(url_for('list_postcards'))
    
    # Check if user owns this postcard or is admin
    if postcard['user_id'] != current_user.id and not current_user.is_admin:
        flash('You do not have permission to submit this postcard', 'error')
        return redirect(url_for('list_postcards'))
    
    # Check current status
    if postcard['status'] != 'draft':
        flash('Only draft postcards can be submitted for review', 'error')
        return redirect(url_for('view_postcard', postcard_id=postcard_id))
    
    # Stage the postcard
    staged_postcard = PostcardDB.stage_postcard(str(postcard_id))
    
    if staged_postcard:
        flash('Postcard submitted for review', 'success')
    else:
        flash('Failed to submit postcard', 'error')
    
    return redirect(url_for('view_postcard', postcard_id=postcard_id))

@app.route('/admin/postcards/staged')
@login_required
@requires_admin
def admin_staged_postcards():
    """View all staged postcards for admin review"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    # Fetch staged postcards
    staged_postcards = PostcardDB.get_staged_postcards(limit=per_page, offset=offset)
    
    return render_template('admin/staged_postcards.html', postcards=staged_postcards, page=page)

@app.route('/admin/postcards/<uuid:postcard_id>/review', methods=['POST'])
@login_required
@requires_admin
def review_postcard(postcard_id):
    """Admin review of a staged postcard"""
    # Get form data
    action = request.form.get('action')
    review_notes = request.form.get('review_notes', '').strip()
    
    # Validate input
    if action not in ['approve', 'reject']:
        flash('Invalid review action', 'error')
        return redirect(url_for('admin_staged_postcards'))
    
    # Prepare status based on action
    status = 'approved' if action == 'approve' else 'rejected'
    
    # Review the postcard
    reviewed_postcard = PostcardDB.review_postcard(
        str(postcard_id), 
        status, 
        review_notes if review_notes else None
    )
    
    if reviewed_postcard:
        # Success message
        if status == 'approved':
            flash('Postcard approved successfully', 'success')
        else:
            flash('Postcard rejected', 'warning')
    else:
        flash('Failed to process postcard review', 'error')
    
    return redirect(url_for('admin_staged_postcards'))

@app.route('/postcards/<uuid:postcard_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_postcard(postcard_id):
    """Edit an existing postcard"""
    postcard = PostcardDB.get_postcard(str(postcard_id))
    
    if not postcard:
        flash('Postcard not found', 'error')
        return redirect(url_for('list_postcards'))
    
    # Check if user owns this postcard or is admin
    if postcard['user_id'] != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this postcard', 'error')
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
@login_required
def delete_postcard(postcard_id):
    """Delete a postcard"""
    postcard = PostcardDB.get_postcard(str(postcard_id))
    
    if not postcard:
        flash('Postcard not found', 'error')
        return redirect(url_for('list_postcards'))
    
    # Check if user owns this postcard or is admin
    if postcard['user_id'] != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this postcard', 'error')
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