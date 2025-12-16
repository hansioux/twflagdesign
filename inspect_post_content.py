from app import create_app, db
from app.models import Post

app = create_app()
with app.app_context():
    posts = Post.query.all()
    count = 0
    print("--- Scanning ALL Posts for Leading Whitespace ---")
    for p in posts:
        if p.content and p.content[0].isspace():
            count += 1
            print(f"ID: {p.id} | Leading WS: {repr(p.content[:20])}...")
            
    print(f"Total posts with leading whitespace: {count} / {len(posts)}")
