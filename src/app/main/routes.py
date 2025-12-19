import os
import uuid
import re
from collections import Counter
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.main import bp
from app.models import Design, Comment, Rating, Post, User
from app.models import Design, Comment, Rating, Post, User
from flask import abort
from flask import abort
from sqlalchemy import or_, func

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
    q = request.args.get('q')
    sort_by = request.args.get('sort', 'newest')
    rating_filter = request.args.get('rating')
    
    query = Design.query.filter_by(approved=True)
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(or_(
            Design.title.ilike(search_term),
            Design.description.ilike(search_term),
            Design.hashtags.ilike(search_term)
        ))
        
    # Join if we need to sort by rating OR filter by rating
    if sort_by == 'top' or rating_filter:
        query = query.outerjoin(Design.ratings).group_by(Design.id)
        
    if rating_filter:
        if rating_filter == 'unrated':
            query = query.having(func.count(Rating.id) == 0)
        else:
            try:
                r_val = int(rating_filter)
                query = query.having(func.round(func.avg(Rating.value)) == r_val)
            except ValueError:
                pass

    if sort_by == 'top':
        query = query.order_by(func.avg(Rating.value).desc())
    else:
        # Default newest
        query = query.order_by(Design.created_at.desc())
        
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    designs = pagination.items

    if request.args.get('ajax'):
        return render_template('partials_design_list.html', designs=designs)
    
    # Calculate top hashtags from all approved designs (cache this in production!)
    all_designs = Design.query.filter_by(approved=True).all()
    tag_counts = Counter()
    for d in all_designs:
        if d.hashtags:
            tags = d.hashtags.lower().split()
            tag_counts.update(tags)
            
    top_tags = tag_counts.most_common(5)
    
    return render_template('index.html', designs=designs, search_query=q, top_tags=top_tags, sort_by=sort_by, rating_filter=rating_filter, pagination=pagination)

@bp.route('/hashtags')
def hashtags():
    # Calculate all hashtags from all approved designs
    all_designs = Design.query.filter_by(approved=True).all()
    tag_counts = Counter()
    for d in all_designs:
        if d.hashtags:
            # Split and clean tags
            tags = d.hashtags.lower().split()
            tag_counts.update(tags)
            
    # Sort by count desc, then alphabetical
    # most_common() returns list of (elem, count) sorted by count.
    # We might want secondary sort by name if counts are equal, but most_common is stable.
    all_tags = tag_counts.most_common()
    
    return render_template('hashtags.html', all_tags=all_tags)

@bp.route('/api/hashtags')
def api_hashtags():
    # Helper to clean tags
    def get_tags():
        all_designs = Design.query.filter_by(approved=True).all()
        unique_tags = set()
        for d in all_designs:
            if d.hashtags:
                tags = d.hashtags.lower().split()
                unique_tags.update(tags)
        return sorted(list(unique_tags))
        
    return jsonify(get_tags())

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
            
            file.save(save_path)
            
            public_id = str(uuid.uuid4())
            hashtags = request.form.get('hashtags')
            
            design = Design(
                title=title, 
                description=desc, 
                image_filename=unique_filename,
                hashtags=hashtags,
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
    subjects = ['General', 'Design Feedback', 'Voting Process', 'Symbolism', 'Past Designs', 'Colonial Flags']
    
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
        
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(current_app.root_path, 'static/uploads', unique_filename)
                file.save(save_path)
                image_filename = unique_filename
        
        post = Post(title=title, content=content, subject=subject, post_type=post_type, image_filename=image_filename, author=current_user)
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
        hashtags = request.form.get('hashtags')
        
        design.title = title
        design.description = description
        design.hashtags = hashtags
        
        # Image handling
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Delete old image if exists
                if design.image_filename:
                    old_path = os.path.join(current_app.root_path, 'static/uploads', design.image_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Save new
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(current_app.root_path, 'static/uploads', unique_filename)
                file.save(save_path)
                design.image_filename = unique_filename
        
        elif request.form.get('remove_image') == 'yes':
             if design.image_filename:
                old_path = os.path.join(current_app.root_path, 'static/uploads', design.image_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
                design.image_filename = None

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
    subjects = ['General', 'Design Feedback', 'Voting Process', 'Symbolism', 'Past Designs', 'Colonial Flags']

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
                 
        # Image handling
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Delete old image if exists
                if post.image_filename:
                    old_path = os.path.join(current_app.root_path, 'static/uploads', post.image_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Save new
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                save_path = os.path.join(current_app.root_path, 'static/uploads', unique_filename)
                file.save(save_path)
                post.image_filename = unique_filename
        
        elif request.form.get('remove_image') == 'yes':
             if post.image_filename:
                old_path = os.path.join(current_app.root_path, 'static/uploads', post.image_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
                post.image_filename = None

        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('main.discuss'))
        
    return render_template('edit_post.html', post=post, subjects=subjects)

@bp.route('/post/<int:post_id>/convert', methods=['POST'])
@login_required
def convert_post_to_design(post_id):
    print(f"DEBUG: Convert route hit for post_id={post_id}")
    if not current_user.is_admin:
        print("DEBUG: Access denied (not admin)")
        abort(403)
        
    post = Post.query.get_or_404(post_id)
    
    if not post.image_filename:
        flash('Cannot convert post to design: Post must have an image.', 'error')
        return redirect(url_for('main.edit_post', post_id=post.id))
        
    # Create Design
    design = Design(
        public_id=str(uuid.uuid4()),
        title=post.title,
        description=post.content,
        image_filename=post.image_filename,
        author=post.author,
        created_at=post.created_at,
        hashtags='#Converted',
        approved=True # Admin action implies approval
    )
    db.session.add(design)
    db.session.flush() # Get ID
    
    # Move comments
    for comment in post.comments:
        comment.post_id = None
        comment.design_id = design.id
        
    # Delete post (prevent image deletion since it's now used by Design)
    # We need to detach image from post before deleting, OR rely on the fact we just copied the filename string.
    # But delete_post logic might try to delete the file!
    # Let's check delete_post logic.
    # Actually we are not calling delete_post route, we are doing db.session.delete(post).
    # Does Post model have cascade delete that removes file?
    # No, file deletion is manual in delete_post route.
    # So db.session.delete(post) is safe for the file.
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post successfully converted to Design.', 'success')
    return redirect(url_for('main.design_detail', public_id=design.public_id))

@bp.route('/design/<public_id>/convert', methods=['POST'])
@login_required
def convert_design_to_post(public_id):
    print(f"DEBUG: Convert Design route hit for public_id={public_id}")
    if not current_user.is_admin:
        print("DEBUG: Access denied (not admin)")
        abort(403)
        
    design = Design.query.filter_by(public_id=public_id).first_or_404()
    
    # Create Post
    # Append hashtags to description if they exist, as posts don't have separate hashtags field
    content = design.description
    if design.hashtags:
        content += f"\n\n{design.hashtags}"
        
    post = Post(
        title=design.title,
        content=content,
        post_type='discussion',
        subject='General',
        image_filename=design.image_filename,
        author=design.author,
        created_at=design.created_at
    )
    db.session.add(post)
    db.session.flush() # Get ID
    
    # Move comments
    for comment in design.comments:
        comment.design_id = None
        comment.post_id = post.id
        
    # Delete Ratings (Posts don't support ratings)
    for rating in design.ratings:
        db.session.delete(rating)
        
    # Delete Design
    db.session.delete(design)
    db.session.commit()
    
    flash('Design successfully converted to Discussion Post.', 'success')
    return redirect(url_for('main.discuss'))

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

@bp.route('/design/<public_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_design(public_id):
    design = Design.query.filter_by(public_id=public_id).first_or_404()
    if design.author != current_user and not current_user.is_admin:
        abort(403)
        
    if request.method == 'GET':
        return render_template('confirm_delete.html', 
                             item_type="Design", 
                             item_title=design.title, 
                             cancel_url=url_for('main.design_detail', public_id=public_id))
        
    # Delete image file if exists
    if design.image_filename:
        image_path = os.path.join(current_app.root_path, 'static/uploads', design.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
            
    # Delete associated comments and ratings
    Comment.query.filter_by(design_id=design.id).delete()
    Rating.query.filter_by(design_id=design.id).delete()
    
    db.session.delete(design)
    db.session.commit()
    flash('Design deleted.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/post/<int:post_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        abort(403)
        
    if request.method == 'GET':
        return render_template('confirm_delete.html', 
                             item_type="Post", 
                             item_title=post.title, 
                             cancel_url=url_for('main.discuss'))
        
    if post.image_filename:
         image_path = os.path.join(current_app.root_path, 'static/uploads', post.image_filename)
         if os.path.exists(image_path):
             os.remove(image_path)
             
    Comment.query.filter_by(post_id=post.id).delete()
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('main.discuss'))

@bp.route('/comment/<int:comment_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user and not current_user.is_admin:
        abort(403)
        
    design_public_id = comment.design.public_id if comment.design else None
    cancel_url = url_for('main.design_detail', public_id=design_public_id) if design_public_id else url_for('main.discuss')
    
    if request.method == 'GET':
        return render_template('confirm_delete.html', 
                             item_type="Comment", 
                             item_title=None, 
                             cancel_url=cancel_url)
    
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'success')
    
    if design_public_id:
        return redirect(url_for('main.design_detail', public_id=design_public_id))
    return redirect(url_for('main.discuss'))
@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404
