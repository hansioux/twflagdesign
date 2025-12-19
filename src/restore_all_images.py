import os
import glob
from bs4 import BeautifulSoup
from app import create_app, db
from app.models import Post, Design
from datetime import datetime
import shutil

# Copied helper
def parse_html_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    content_div = soup.find('div', class_='main-content')
    content = content_div.get_text('\n').strip() if content_div else ""
    
    filename_base = os.path.basename(fpath).replace('.html', '')
    if ' - ' in filename_base:
        title_candidate = filename_base.split(' - ', 1)[1]
    else:
        title_candidate = filename_base
        
    if not content:
        content = title_candidate
    
    title = title_candidate[:100]
    return title, soup

GPLUS_DIR = 'gplus/Google+ Communities/自己的國旗自己畫/Posts'

app = create_app()
with app.app_context():
    files = glob.glob(os.path.join(GPLUS_DIR, '*.html'))
    print(f"Scanning {len(files)} files for missing images...")
    
    updated_count = 0
    
    for fpath in files:
        title, soup = parse_html_file(fpath)
        
        # Check if exists in DB (Post or Design)
        post = Post.query.filter_by(title=title).first()
        design = Design.query.filter_by(title=title).first()
        
        target = post if post else design
        target_type = "Post" if post else ("Design" if design else None)
        
        if target:
            # Check if target already has image
            if not target.image_filename:
                # Target has no image, check if HTML supports one
                image_filename = None
                
                # Check u-photo first
                img_tag = soup.find('img', class_='u-photo')
                # Fallback to media class
                if not img_tag:
                     img_tag = soup.find('img', class_='media')
                     
                if img_tag and img_tag.get('src'):
                    src = img_tag['src']
                    potential_img_name = os.path.basename(src)
                    
                    # Ignore generic GPlus avatar/icon placeholders if any
                    # Usually real images are UUID-like or hashes. 
                    # Let's assume valid if exists in folder.
                    
                    src_path = os.path.join(GPLUS_DIR, potential_img_name)
                    if os.path.exists(src_path):
                        # Copy to static/uploads
                        target_dir = os.path.join(app.root_path, 'static', 'uploads')
                        if not os.path.exists(target_dir):
                            os.makedirs(target_dir)
                        
                        clean_img_name = potential_img_name.split('?')[0]
                        import uuid
                        ext = os.path.splitext(clean_img_name)[1]
                        if not ext: ext = '.jpg'
                        new_img_name = str(uuid.uuid4()) + ext
                        
                        shutil.copy(src_path, os.path.join(target_dir, new_img_name))
                        
                        target.image_filename = new_img_name
                        updated_count += 1
                        print(f"[{target_type}] Restored image for: {title[:30]}...")

    if updated_count > 0:
        db.session.commit()
        print(f"Successfully restored images for {updated_count} items.")
    else:
        print("No items found needing image restoration.")
