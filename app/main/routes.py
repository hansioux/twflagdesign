import os
import uuid
import re
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.main import bp
from app.models import Design, Comment, Rating, Post, User
from flask import abort

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

@bp.app_template_filter('format_content')
def format_content(text):
    if not text:
        return ""
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Limit consecutive newlines to 2 (stripping 3rd+)
    # Matches 3 or more occurrences of (newline + optional whitespace)
    text = re.sub(r'(\s*\n){3,}', '\n\n', text)
    return text

@bp.route('/')
def index():
    designs = Design.query.filter_by(approved=True).order_by(Design.created_at.desc()).all()
    return render_template('index.html', designs=designs)

@bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No image part', 'error')
            return redirect(request.url)
        
        file = request.files['image']
        title = request.form.get('title')
        desc = request.form.get('description')
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            # Create unique filename to prevent overwrites
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            save_path = os.path.join(current_app.root_path, 'static/uploads', unique_filename)
            file.save(save_path)
            
            public_id = str(uuid.uuid4())
            design = Design(
                title=title, 
                description=desc, 
                image_filename=unique_filename,
                public_id=public_id,
                author=current_user,
                approved=True # Auto-approve for MVP
            )
            db.session.add(design)
            db.session.commit()
            flash('Your design has been submitted successfully!', 'success')
            return redirect(url_for('main.index'))
    
    return render_template('submit.html')

@bp.route('/design/<public_id>', methods=['GET', 'POST'])
def design_detail(public_id):
    design = Design.query.filter_by(public_id=public_id).first_or_404()
    
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('You must be logged in to participate.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Handle Comment
        if 'comment_content' in request.form:
            content = request.form.get('comment_content')
            if content:
                comment = Comment(content=content, author=current_user, design=design)
                db.session.add(comment)
                db.session.commit()
                flash('Comment added.', 'success')
        
        # Handle Rating
        elif 'rating_value' in request.form:
            try:
                val = int(request.form.get('rating_value'))
                if 1 <= val <= 10:
                    # Check if already rated
                    existing = Rating.query.filter_by(user_id=current_user.id, design_id=design.id).first()
                    if existing:
                        existing.value = val
                    else:
                        rating = Rating(value=val, author=current_user, design=design)
                        db.session.add(rating)
                    db.session.commit()
                    db.session.commit()
                    # flash(f'You rated this design {val}/10.', 'success')
            except ValueError:
                pass
                
        return redirect(url_for('main.design_detail', public_id=design.public_id))
    
    user_rating = None
    if current_user.is_authenticated:
        rating_obj = Rating.query.filter_by(user_id=current_user.id, design_id=design.id).first()
        if rating_obj:
            user_rating = rating_obj.value

    # Calculate average rating
    ratings = design.ratings
    if ratings:
        avg_rating = round(sum(r.value for r in ratings) / len(ratings), 1)
    else:
        avg_rating = 0

    return render_template('design_detail.html', design=design, user_rating=user_rating, avg_rating=avg_rating)
@bp.route('/discuss', methods=['GET', 'POST'])
def discuss():
    # Admin defined subjects
    subjects = ['General', 'Design Feedback', 'Voting Process', 'Symbolism']
    
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        title = request.form.get('title')
        content = request.form.get('content')
        subject = request.form.get('subject')
        # Admin check logic
        post_type = 'discussion'
        if current_user.is_admin and request.form.get('is_announcement') == 'yes':
            post_type = 'announcement'
        
        post = Post(title=title, content=content, subject=subject, post_type=post_type, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('main.discuss'))
        
    # Filtering
    filter_type = request.args.get('filter')
    filter_subject = request.args.get('subject')
    
    query = Post.query
    if filter_type:
        if filter_type == 'announcement':
            query = query.filter_by(post_type='announcement')
    if filter_subject:
        query = query.filter_by(subject=filter_subject)
        
    posts = query.order_by(Post.created_at.desc()).all()
    
    return render_template('discuss.html', posts=posts, subjects=subjects)

@bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
        
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@bp.route('/admin/toggle_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin_status(user_id):
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
        
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'warning')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = "Admin" if user.is_admin else "User"
        flash(f'{user.name} is now an {status}.', 'success')
        
    return redirect(url_for('main.admin_users'))


# --- Edit Routes ---

@bp.route('/design/<public_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_design(public_id):
    design = Design.query.filter_by(public_id=public_id).first_or_404()
    
    # Auth check
    if design.author != current_user and not current_user.is_admin:
        abort(403)
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        design.title = title
        design.description = description
        db.session.commit()
        
        flash('Design updated successfully.', 'success')
        return redirect(url_for('main.design_detail', public_id=design.public_id))
        
    return render_template('edit_design.html', design=design)

@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if post.author != current_user and not current_user.is_admin:
        abort(403)
        
    # Subjects list for dropdown
    subjects = ['General', 'Design Feedback', 'Voting Process', 'Symbolism']

    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.subject = request.form.get('subject')
        
        # Only admin can toggle type, but we keep existing type logic stable if not provided
        if current_user.is_admin:
             if request.form.get('is_announcement') == 'yes':
                 post.post_type = 'announcement'
             else:
                 post.post_type = 'discussion'
                 
        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('main.discuss'))
        
    return render_template('edit_post.html', post=post, subjects=subjects)

@bp.route('/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.author != current_user and not current_user.is_admin:
        abort(403)
        
    if request.method == 'POST':
        comment.content = request.form.get('content')
        db.session.commit()
        flash('Comment updated.', 'success')
        
        # Redirect back to context
        if comment.design_id:
            return redirect(url_for('main.design_detail', public_id=comment.design.public_id))
        elif comment.post_id:
            return redirect(url_for('main.discuss')) # Ideally anchor to post, but MVP
        return redirect(url_for('main.index'))
        
    return render_template('edit_comment.html', comment=comment)
