from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"Promoted user {user.name} ({user.email}) to Admin.")
    else:
        print("No users found in the database.")
