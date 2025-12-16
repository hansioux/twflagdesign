import os
import glob
from bs4 import BeautifulSoup
from app import create_app
from app.models import Post
from datetime import datetime

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
    created_at = None
    if date_span:
        try:
            dt_str = date_span.get_text().strip()
            if '+' in dt_str:
                dt_str = dt_str.split('+')[0]
            created_at = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
        except:
            pass

    return title, created_at, content

GPLUS_DIR = 'gplus/Google+ Communities/自己的國旗自己畫/Posts'

app = create_app()
with app.app_context():
    files = glob.glob(os.path.join(GPLUS_DIR, '*.html'))
    print(f"Scanning {len(files)} files...")
    
    missing_count = 0
    for fpath in files:
        title, created_at, content = parse_html_file(fpath)
        
        if True: # Check ALL files
            # Check if exists in DB (Title match)
            # Checking Title is safer than Date because of potential timezone/format issues
            exists = Post.query.filter_by(title=title).first()
            if not exists:
                # Also check Design table! 
                # Migration split them into Post and Design.
                # Only report if missing from BOTH.
                from app.models import Design
                exists_design = Design.query.filter_by(title=title).first()
                
                if not exists_design:
                    # Double check keywords to highlight likely candidates
                    text = (title + " " + content).lower()
                    keywords = ['殖民', 'colonial', 'dutch', 'japanese', 'usmg']
                    is_colonial_candidate = any(k in text for k in keywords)
                    
                    prefix = "[COLONIAL?] " if is_colonial_candidate else ""
                    
                    print(f"MISSING: {prefix}{title}")
                    # print(f"  File: {os.path.basename(fpath)}")
                    missing_count += 1
                
    print(f"Total missing colonial posts: {missing_count}")
