from app import create_app, db
from app.models import Post, Comment
from collections import defaultdict

app = create_app()
with app.app_context():
    posts = Post.query.all()
    print(f"Total posts before: {len(posts)}")
    
    # Group by title and created_at (since the duplicates seem to match on these)
    # Using title as primary key for grouping
    title_map = defaultdict(list)
    for p in posts:
        # Use a tuple of (title, created_at) to avoid aggregating different posts with same title
        key = (p.title, p.created_at)
        title_map[key].append(p)
        
    deleted_count = 0
    for key, items in title_map.items():
        if len(items) > 1:
            # Sort items: preference to those WITH image_filename
            # If both have image or neither, prefer lower ID (older/original import)
            
            # Sort key: (has_image (True/False), -id) -> reversed -> (has_image, id)
            # We want to KEEP the one with image, or if equal, the one with lower ID.
            # actually better: simple loop
            
            keep = None
            
            # First pass: find best candidate to keep
            candidates_with_image = [p for p in items if p.image_filename]
            if candidates_with_image:
                 keep = min(candidates_with_image, key=lambda x: x.id) # Keep first one with image
            else:
                 keep = min(items, key=lambda x: x.id) # Keep first one (all no image)
            
            print(f"Keeping ID {keep.id} for '{key[0]}'")
            
            for item in items:
                if item.id != keep.id:
                    print(f"  Deleting duplicate ID {item.id}")
                    # Delete associated comments first just in case
                    Comment.query.filter_by(post_id=item.id).delete()
                    db.session.delete(item)
                    deleted_count += 1

    db.session.commit()
    print(f"Deleted {deleted_count} duplicate posts.")
    print(f"Total posts after: {Post.query.count()}")
