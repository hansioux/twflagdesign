import os
import glob
from bs4 import BeautifulSoup

base_path = 'gplus/Google+ Communities/自己的國旗自己畫/Posts'
files = glob.glob(os.path.join(base_path, '*.html'))

print(f"Found {len(files)} files.")

categories_found = set()
count = 0
for fpath in files:
    if count > 50: break
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            visibility = soup.find('div', class_='visibility')
            if visibility:
                text = visibility.get_text().strip()
                # Expected: "Shared to the community 自己的國旗自己畫 - Category" or " - Public"
                if '-' in text:
                    parts = text.split('-')
                    if len(parts) >= 2:
                        cat = parts[-1].strip()
                        categories_found.add(cat)
                        print(f"File: {os.path.basename(fpath)} -> Cat: {cat}")
    except Exception as e:
        print(f"Error {fpath}: {e}")
    count += 1

print("\nCategories Found:", categories_found)
