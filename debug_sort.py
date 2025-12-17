from app import create_app, db
from app.models import Design, Rating, User
from sqlalchemy import func

app = create_app()
with app.app_context():
    # Helper to print results
    def print_query(desc=True):
        direction = "DESC" if desc else "ASC"
        print(f"--- Testing ORDER BY avg(value) {direction} ---")
        q = Design.query.outerjoin(Design.ratings)\
                    .group_by(Design.id)
        
        if desc:
            q = q.order_by(func.avg(Rating.value).desc())
        else:
            q = q.order_by(func.avg(Rating.value).asc())
            
        results = q.all()
        
        for d in results[:10]: # First 10
            # Calculate avg manually to verify
            ratings = [r.value for r in d.ratings]
            avg = sum(ratings)/len(ratings) if ratings else None
            print(f"ID: {d.id} | Title: {d.title[:20]} | Manual Avg: {avg} | Ratings: {ratings}")

    # Add test ratings
    try:
        u = User.query.first()
        if not u:
            u = User(name='Test', email='test@test.com')
            db.session.add(u)
            db.session.commit()
            
        d_low = Design.query.get(5)
        d_high = Design.query.get(6)
        
        if d_low and not d_low.ratings:
            r1 = Rating(value=1, user_id=u.id, design_id=d_low.id)
            db.session.add(r1)
        
        if d_high and not d_high.ratings:
            r2 = Rating(value=10, user_id=u.id, design_id=d_high.id)
            db.session.add(r2)
            
        db.session.commit()
    except Exception as e:
        print(f"Error adding ratings: {e}")

    print_query(desc=True)
