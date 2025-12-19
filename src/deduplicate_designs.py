from app import create_app, db
from app.models import Design
from collections import defaultdict
import os

app = create_app()
with app.app_context():
    all_designs = Design.query.all()
    print(f"Total designs before cleanup: {len(all_designs)}")
    
    # Group by unique content signature
    # Using title, description, and created_at (string format) as key
    groups = defaultdict(list)
    for d in all_designs:
        key = (d.title, d.description, str(d.created_at))
        groups[key].append(d)
        
    duplicates_found = 0
    deleted_count = 0
    
    for key, designs in groups.items():
        if len(designs) > 1:
            duplicates_found += 1
            # Sort by ID to keep the oldest import (or just consistent determinism)
            # Actually, lower ID usually means older DB record, but for import they might be close.
            # Let's keep the one with the lowest ID.
            designs.sort(key=lambda x: x.id)
            
            keep = designs[0]
            remove_list = designs[1:]
            
            print(f"Found duplicate group: '{keep.title[:30]}...' (Count: {len(designs)})")
            print(f"  Keeping ID: {keep.id}")
            
            for remove in remove_list:
                print(f"  Deleting ID: {remove.id}")
                
                # Delete image file
                if remove.image_filename:
                    # Check if the image filename is different from the kept one
                    # If they share the SAME filename string, we must NOT delete it if we keep the other.
                    # But the inspection showed different filenames (hashes).
                    if remove.image_filename != keep.image_filename:
                        path = os.path.join(app.root_path, 'static/uploads', remove.image_filename)
                        if os.path.exists(path):
                            try:
                                os.remove(path)
                                print(f"    Deleted image: {remove.image_filename}")
                            except Exception as e:
                                print(f"    Error deleting image: {e}")
                    else:
                        print(f"    Skipping image deletion (shared filename): {remove.image_filename}")
                
                # Reassign comments or ratings?
                # If these are straight duplicates, likely they don't have user interaction yet (or split interaction).
                # ideally we merge, but deletion is requested.
                # Assuming no interaction on duplicates for now or willing to lose it on the deleted one.
                # But to be safe, let's move comments/ratings to the kept one?
                # User didn't ask for merge, just remove.
                # But merging is safer for data integrity if users commented on the "wrong" duplicate.
                
                # Move comments/ratings
                for c in remove.comments:
                    c.design_id = keep.id
                for r in remove.ratings:
                    r.design_id = keep.id
                
                db.session.delete(remove)
                deleted_count += 1
                
    db.session.commit()
    print(f"Cleanup complete.")
    print(f"Duplicate groups processed: {duplicates_found}")
    print(f"Records deleted: {deleted_count}")
    print(f"Remaining designs: {Design.query.count()}")
