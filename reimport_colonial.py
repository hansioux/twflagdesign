import os
import glob
from bs4 import BeautifulSoup
from app import create_app, db
from app.models import Post, User
from datetime import datetime
import shutil

# Copied helper from migrate_gplus.py
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

    date_span = soup.find('span', itemprop='dateCreated')
    created_at = datetime.utcnow()
    if date_span:
        try:
            dt_str = date_span.get_text().strip()
            if '+' in dt_str:
                dt_str = dt_str.split('+')[0]
            created_at = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        except:
            pass

    return title, created_at, content, soup

GPLUS_DIR = 'gplus/Google+ Communities/自己的國旗自己畫/Posts'

app = create_app()
with app.app_context():
    # Find admin user to assign posts to (or create a bot user)
    # Migration used 'Google User'.
    # We'll try to find a user or use the first admin.
    author = User.query.filter_by(name='Google User').first()
    if not author:
        author = User.query.first()
        
    print(f"Assigning to author: {author.name}")

    files = glob.glob(os.path.join(GPLUS_DIR, '*.html'))
    keywords = ['荷蘭', 'Dutch', '殖民', 'Colonial', '日本', 'Japanese', '美國', 'USMG', '西班牙', 'Spain', 'Spanish', '明', 'Ming', '清', 'Qing', 
                '蔣中正', 'Chiang', '國民黨', 'KMT', 'ROC', '中華民國']
    
    reimported_count = 0
    
    for fpath in files:
        filename = os.path.basename(fpath)
        # Check if filename contains keywords (loose check first)
        hit = False
        for k in keywords:
            if k in filename:
                hit = True
                break
        
        if not hit:
            # Check content? No, user said "Colonial Flags category", likely triggered by title/filename keywords in migration
            # Read file to check content keywords if filename fails?
            # Let's start with filename + title match
            pass

        title, created_at, content, soup = parse_html_file(fpath)
        
        # Check content match for keywords if filename didn't match
        if not hit:
            text = (title + " " + content).lower()
            for k in keywords:
                if k.lower() in text:
                    hit = True
                    break
        
        if hit:
            # Check if exists
            post = Post.query.filter_by(title=title).first()
            
            # Logic to extract image
            image_filename = None
            img_tag = soup.find('img', class_='u-photo')
            if not img_tag:
                 img_tag = soup.find('img', class_='media')
                 
            if img_tag and img_tag.get('src'):
                src = img_tag['src']
                potential_img_name = os.path.basename(src)
                src_path = os.path.join(GPLUS_DIR, potential_img_name)
                if os.path.exists(src_path):
                    target_dir = os.path.join(app.root_path, 'static', 'uploads')
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    
                    clean_img_name = potential_img_name.split('?')[0]
                    import uuid
                    ext = os.path.splitext(clean_img_name)[1]
                    if not ext: ext = '.jpg'
                    new_img_name = str(uuid.uuid4()) + ext
                    shutil.copy(src_path, os.path.join(target_dir, new_img_name))
                    image_filename = new_img_name
                    print(f"  Attached image: {image_filename}")

            if post:
                if image_filename and not post.image_filename:
                    print(f"UPDATING IMAGE for: {title}")
                    post.image_filename = image_filename
                    reimported_count += 1
            else:
                from app.models import Design
                exists_design = Design.query.filter_by(title=title).first()
                if not exists_design:
                    print(f"RE-IMPORTING: {title}")
                    print(f"  File: {filename}")

                    # Determine Category
                    category = "Colonial Flags" 
                    
                    post = Post(
                        title=title,
                        content=content,
                        created_at=created_at,
                        author=author,
                        subject=category,
                        post_type='discussion', 
                        image_filename=image_filename
                    )
                    db.session.add(post)
                    reimported_count += 1
    
    if reimported_count > 0:
        db.session.commit()
        print(f"Successfully re-imported {reimported_count} posts.")
    else:
        print("No missing colonial posts found to re-import.")
