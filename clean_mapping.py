import json
import re
from pathlib import Path

BASE_OUTPUT_DIR = Path("runoob_content")
mapping_file = BASE_OUTPUT_DIR / "url_mapping.json"

if mapping_file.exists():
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    cleaned_mapping = {}
    
    for url, filename in mapping.items():
        clean_url = url
        
        if '<a href="' in url:
            match = re.search(r'href="([^"]+)"', url)
            if match:
                clean_url = match.group(1)
        
        if clean_url.startswith('http'):
            cleaned_mapping[clean_url] = filename
    
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"Cleaned URL mapping: {len(mapping)} -> {len(cleaned_mapping)} entries")
    print(f"Saved to: {mapping_file}")
    
    print("\nSample cleaned mappings:")
    for i, (url, filename) in enumerate(list(cleaned_mapping.items())[:10]):
        print(f"  {filename}: {url}")
else:
    print(f"Mapping file not found: {mapping_file}")
