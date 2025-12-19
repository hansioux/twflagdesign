from app import create_app, db
from app.models import Design

app = create_app()
with app.app_context():
    # Show last 5 created designs by ID (which is auto-increment)
    designs = Design.query.order_by(Design.id.desc()).limit(5).all()
    print("--- Latest 5 Designs by ID ---")
    for d in designs:
        print(f"ID: {d.id} | Title: {d.title} | CreatedAt: {d.created_at} | Approved: {d.approved}")
        
    print("\nTotal Designs:", Design.query.count())
