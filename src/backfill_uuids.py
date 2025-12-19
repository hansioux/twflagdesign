import uuid
from app import create_app, db
from app.models import Design

app = create_app()
with app.app_context():
    designs = Design.query.all()
    print(f"Found {len(designs)} designs to update.")
    count = 0
    for d in designs:
        if not d.public_id:
            d.public_id = str(uuid.uuid4())
            count += 1
    db.session.commit()
    print(f"Backfilled {count} designs with UUIDs.")
