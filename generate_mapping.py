import json
import os
import re
from pathlib import Path

BASE_OUTPUT_DIR = Path("runoob_content")

mapping = {}

if BASE_OUTPUT_DIR.exists():
    for html_file in BASE_OUTPUT_DIR.rglob("*.html"):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '原文链接:' in content:
                start = content.find('原文链接:') + 5
                end = content.find('</a>', start)
                if start > 4 and end > start:
                    url_with_tag = content[start:end].strip()
                    
                    url = url_with_tag
                    if 'href="' in url_with_tag:
                        match = re.search(r'href="([^"]+)"', url_with_tag)
                        if match:
                            url = match.group(1)
                    
                    if url.startswith('http'):
                        mapping[url] = html_file.name
        except Exception as e:
            print(f"Error processing {html_file}: {e}")

existing_mapping_file = BASE_OUTPUT_DIR / "url_mapping.json"
if existing_mapping_file.exists():
    try:
        with open(existing_mapping_file, 'r', encoding='utf-8') as f:
            existing_mapping = json.load(f)
        
        for url, filename in existing_mapping.items():
            clean_url = url
            if '<a href="' in url:
                match = re.search(r'href="([^"]+)"', url)
                if match:
                    clean_url = match.group(1)
            
            if clean_url.startswith('http') and clean_url not in mapping:
                mapping[clean_url] = filename
    except:
        pass

mapping_file = BASE_OUTPUT_DIR / "url_mapping.json"
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Generated URL mapping with {len(mapping)} entries")
print(f"Saved to: {mapping_file}")

print("\nSample mappings:")
for i, (url, filename) in enumerate(list(mapping.items())[:10]):
    print(f"  {filename}: {url}")
