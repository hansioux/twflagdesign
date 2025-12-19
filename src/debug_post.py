from app import create_app, db
from app.models import Post

app = create_app()
with app.app_context():
    # Search for the post
    posts = Post.query.filter(Post.title.like('%蔣中正%')).all()
    print(f"Found {len(posts)} posts matching '蔣中正'.")
    for p in posts:
        print(f"ID: {p.id} | Title: {p.title} | Image: {p.image_filename} | Type: {p.post_type}")
