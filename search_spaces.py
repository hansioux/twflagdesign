from app import create_app, db
from app.models import Post

app = create_app()
with app.app_context():
    # Search for 4 spaces
    posts = Post.query.filter(Post.content.like('%    %')).all()
    print(f"Found {len(posts)} posts with 4+ spaces.")
    for p in posts:
        print(f"ID: {p.id}")
        start = p.content.find('    ')
        print(f"Context: {repr(p.content[max(0, start-10):start+20])}")
        
    # Check for ideographic space
    posts_wide = Post.query.filter(Post.content.like('%\u3000%')).all()
    print(f"Found {len(posts_wide)} posts with ideographic spaces.")
    for p in posts_wide:
         print(f"ID: {p.id} (Ideographic)")
         print(f"Context: {repr(p.content[:20])}")
