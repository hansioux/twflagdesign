import os
import glob
import shutil
import uuid
from collections import defaultdict
from bs4 import BeautifulSoup
from datetime import datetime
from app import create_app, db
from app.models import User, Design, Post, Comment

# Constants
GPLUS_DIR = 'gplus/Google+ Communities/自己的國旗自己畫/Posts'
UPLOAD_DIR = 'app/static/uploads'
DEFAULT_PASSWORD = 'password'  # Not used for OAuth users but needed for model consistency if we successfully made local auth? We only have OAuth.
# Actually User model doesn't have password field in provided code (only Google ID).
# So we can just create users with google_id=None or a fake one.

# Keyword Mappings
# Mapped to (Model, 'Category/Subject/Tag')
# Order matters: specific first.
KEYWORD_RULES = [
    (['票選', 'Voting'], ('Post', 'Voting Process')),
    (['殖民', 'Colonial', 'Dutch', 'Japanese', 'USMG'], ('Post', 'Colonial Flags')),
    (['前輩', 'Ancestor', 'Senior'], ('Post', 'Past Designs')),
    (['國歌', 'Anthem'], ('Post', 'General')),
    (['時事', 'News'], ('Post', 'General')),
    (['工具', 'Tool'], ('Post', 'General')),
    
    (['3D', '視覺化'], ('Design', '#3DVisual')),
    (['向量', 'Vector', 'SVG'], ('Design', '#Vector')),
    (['搞笑', 'Funny', 'Kuso'], ('Design', '#Funny')),
    (['國徽', 'Emblem'], ('Design', '#Emblem')),
    (['平面', 'Graphic'], ('Design', '#GraphicDesign')),
]

def parse_html_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Content
    content_div = soup.find('div', class_='main-content')
    content = content_div.get_text('\n').strip() if content_div else ""
    
    # Title (Filename often contains it, or extract from content)
    # The HTML title tag is often generic.
    # The GPlus export uses the first few words as filename, or date.
    # We'll use the first line of content as title, or filename if content empty.
    filename_base = os.path.basename(fpath).replace('.html', '')
    # Remove date prefix from filename "YYYYMMDD - "
    if ' - ' in filename_base:
        title_candidate = filename_base.split(' - ', 1)[1]
    else:
        title_candidate = filename_base
        
    if not content:
        content = title_candidate
    
    title = title_candidate[:100] # Truncate to match DB limit

    # Author
    author_span = soup.find('span', itemprop='name')
    author_name = author_span.get_text().strip() if author_span else "Unknown"
    
    # Date
    date_span = soup.find('span', itemprop='dateCreated')
    created_at = datetime.utcnow()
    if date_span:
        try:
            # Format: 2014-06-08T06:53:14+0000
            dt_str = date_span.get_text().strip()
            # Python 3.12 might handle isoformat, but let's be safe with strptime/split
            # Remove +0000 key for simple UTC
            if '+' in dt_str:
                dt_str = dt_str.split('+')[0]
            created_at = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        except:
            pass

    # Image
    image_filename = None
    media_img = soup.find('img', class_='media')
    if media_img and media_img.get('src'):
        src = media_img['src']
        # The src is often a relative path in the local folder
        # Check if file exists
        potential_path = os.path.join(os.path.dirname(fpath), src)
        if os.path.exists(potential_path):
            image_filename = potential_path

    return {
        'title': title,
        'content': content,
        'author_name': author_name,
        'created_at': created_at,
        'image_path': image_filename
    }

def determine_type_and_category(parsed_data):
    text = (parsed_data['title'] + " " + parsed_data['content']).lower()
    
    for keywords, (model_type, category) in KEYWORD_RULES:
        for kw in keywords:
            if kw.lower() in text:
                return model_type, category
    
    # Default
    if parsed_data['image_path']:
        return 'Design', '#GPlusImport'
    else:
        return 'Post', 'General'

def migrate():
    app = create_app()
    with app.app_context():
        # Ensure upload dir
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        files = glob.glob(os.path.join(GPLUS_DIR, '*.html'))
        print(f"Processing {len(files)} posts...")
        
        for fpath in files:
            parsed = parse_html_file(fpath)
            model_type, category = determine_type_and_category(parsed)
            
            # Find or Create User
            user = User.query.filter_by(name=parsed['author_name']).first()
            if not user:
                # Create fake email
                email = f"{parsed['author_name'].replace(' ', '.').lower()}@gplus.archive.local"
                # Handle duplicates
                if User.query.filter_by(email=email).first():
                    email = f"{uuid.uuid4().hex[:8]}@gplus.archive.local"
                    
                user = User(
                    name=parsed['author_name'],
                    email=email,
                    google_id=f"gplus_{uuid.uuid4().hex}" # Fake google ID
                )
                db.session.add(user)
                db.session.commit()
            
            if model_type == 'Design' and parsed['image_path']:
                # Copy Image
                ext = os.path.splitext(parsed['image_path'])[1]
                new_filename = f"{uuid.uuid4().hex}{ext}"
                shutil.copy(parsed['image_path'], os.path.join(UPLOAD_DIR, new_filename))
                
                design = Design(
                    public_id=str(uuid.uuid4()),
                    title=parsed['title'],
                    description=parsed['content'],
                    image_filename=new_filename,
                    hashtags=category, # e.g. #3DVisual
                    created_at=parsed['created_at'],
                    approved=True,
                    author=user
                )
                db.session.add(design)
                print(f"[Design] Imported: {parsed['title'][:30]}")
                
            elif model_type == 'Post':
                # Map category to subject
                post = Post(
                    title=parsed['title'],
                    content=parsed['content'],
                    subject=category, # e.g. "Voting Process"
                    post_type='discussion', # Default
                    created_at=parsed['created_at'],
                    author=user
                )
                if parsed['image_path']:
                     # Copy Image
                    ext = os.path.splitext(parsed['image_path'])[1]
                    new_filename = f"{uuid.uuid4().hex}{ext}"
                    shutil.copy(parsed['image_path'], os.path.join(UPLOAD_DIR, new_filename))
                    post.image_filename = new_filename
                
                db.session.add(post)
                # Check if it was a duplicate import (avoid errors if we re-run)
                # For this script we are doing naive imports. 
                # Ideally we should check if post with same title/date already exists.
                # But user asked to "import images that were left out", implying re-run or update.
                # Since we didn't add uniqueness constraints on title, we might duplicate posts if we just re-run.
                # Let's check for existence first.
                exists = Post.query.filter_by(title=parsed['title'], created_at=parsed['created_at']).first()
                if not exists:
                     print(f"[Post]   Imported: {parsed['title'][:30]}")
                else:
                     # Update existing post if it doesn't have image but we found one
                     if not exists.image_filename and parsed['image_path']:
                          exists.image_filename = new_filename
                          print(f"[Post]   Updated image: {parsed['title'][:30]}")
                     db.session.expunge(post) # Don't add new one
            
            db.session.commit()

if __name__ == '__main__':
    migrate()
