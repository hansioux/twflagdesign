from app import create_app, db
from app.models import Post
from collections import defaultdict

app = create_app()
with app.app_context():
    posts = Post.query.all()
    print(f"Total posts: {len(posts)}")
    
    # Group by title
    title_map = defaultdict(list)
    for p in posts:
        title_map[p.title].append(p)
        
    duplicates = 0
    for title, items in title_map.items():
        if len(items) > 1:
            duplicates += 1
            print(f"Duplicate found: '{title}' - Count: {len(items)}")
            for item in items:
                print(f"  - ID: {item.id}, Created: {item.created_at}, Image: {item.image_filename}")

    print(f"Total duplicate groups: {duplicates}")
