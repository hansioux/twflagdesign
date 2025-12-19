from app import create_app, db
from app.models import Design

app = create_app()
with app.app_context():
    id1 = '7ede8559-721c-4530-8872-ff8d3ff082c6'
    id2 = '3778446a-beea-44cb-8829-1b4f31ee5509'
    
    d1 = Design.query.filter_by(public_id=id1).first()
    d2 = Design.query.filter_by(public_id=id2).first()
    
    if d1 and d2:
        print(f"Design 1: {d1.id} | {d1.title} | {d1.image_filename} | {d1.created_at}")
        print(f"Design 2: {d2.id} | {d2.title} | {d2.image_filename} | {d2.created_at}")
        print(f"Description Match: {d1.description == d2.description}")
        print(f"Title Match: {d1.title == d2.title}")
    else:
        print("One or both designs not found.")
