#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import hashlib
import logging
from urllib.parse import urljoin, urlparse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    print("Warning: pdfkit not installed. PDF conversion will be disabled.")
    print("Install with: pip install pdfkit")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RunoobCrawler:
    BASE_URL = "https://www.runoob.com"
    BASE_OUTPUT_DIR = Path("runoob_content")
    BASE_PDF_DIR = Path("runoob_pdf")
    CONFIG_FILE = Path("config.json")

    CATEGORY_URLS = [
        "https://www.runoob.com/pytorch/pytorch-tutorial.html",
    ]

    def __init__(self, delay=1.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.BASE_OUTPUT_DIR.mkdir(exist_ok=True)
        self.BASE_PDF_DIR.mkdir(exist_ok=True)
        self.driver = None
        self.current_output_dir = None
        self.current_pdf_dir = None
        self._load_config()

    def _load_config(self):
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if 'category_urls' in config and config['category_urls']:
                    self.CATEGORY_URLS = config['category_urls']
                    logger.info(f"Loaded {len(self.CATEGORY_URLS)} URLs from config.json")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")

    def _save_default_config(self):
        default_config = {
            "category_urls": [
                "https://www.runoob.com/pytorch/pytorch-tutorial.html",
            ],
            "delay": 1.5,
            "auto_discover": False
        }
        try:
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info(f"Created default config file: {self.CONFIG_FILE}")
        except Exception as e:
            logger.error(f"Failed to create config: {e}")

    def discover_tutorial_categories(self):
        logger.info("Discovering available tutorial categories on Runoob...")
        
        index_url = f"{self.BASE_URL}//tutorial/category/cat-python.html"
        if "python" not in self.BASE_URL:
            index_url = self.BASE_URL
        
        html = self.fetch_page(index_url)
        if not html:
            logger.warning("Failed to fetch homepage, trying alternative method")
            html = self.fetch_page(self.BASE_URL)
        
        if not html:
            logger.error("Cannot access Runoob website")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        categories = []
        
        tutorial_links = set()
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/tutorial/' in href and 'tutorial.html' in href:
                if href.startswith('/'):
                    full_url = urljoin(self.BASE_URL, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                if full_url not in tutorial_links and 'runoob.com' in full_url:
                    tutorial_links.add(full_url)
        
        categories = sorted(list(tutorial_links))
        logger.info(f"Discovered {len(categories)} tutorial categories")
        
        for i, cat in enumerate(categories[:10], 1):
            logger.info(f"  {i}. {cat}")
        
        if len(categories) > 10:
            logger.info(f"  ... and {len(categories) - 10} more")
        
        return categories

    def get_crawled_files(self):
        crawled_files = set()
        
        if self.BASE_OUTPUT_DIR.exists():
            for html_file in self.BASE_OUTPUT_DIR.rglob("*.html"):
                crawled_files.add(html_file.stem)
        
        if self.BASE_PDF_DIR.exists():
            for pdf_file in self.BASE_PDF_DIR.rglob("*.pdf"):
                crawled_files.add(pdf_file.stem)
        
        logger.info(f"Found {len(crawled_files)} previously crawled files")
        return crawled_files

    def get_url_mapping(self):
        mapping_file = self.BASE_OUTPUT_DIR / "url_mapping.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_url_mapping(self, url, filename):
        mapping_file = self.BASE_OUTPUT_DIR / "url_mapping.json"
        mapping = self.get_url_mapping()
        mapping[url] = filename
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

    def is_already_crawled(self, url):
        mapping = self.get_url_mapping()
        
        if url in mapping:
            logger.info(f"Skipping (exact URL match): {url} -> {mapping[url]}")
            return True
        
        for mapped_url, filename in mapping.items():
            clean_mapped_url = mapped_url
            if '<a href="' in mapped_url:
                import re
                match = re.search(r'href="([^"]+)"', mapped_url)
                if match:
                    clean_mapped_url = match.group(1)
            
            if clean_mapped_url == url:
                logger.info(f"Skipping (cleaned URL match): {url} -> {filename}")
                return True
        
        if not hasattr(self, '_crawled_cache'):
            self._crawled_cache = self.get_crawled_files()
        
        url_filename = url.split('/')[-1].replace('.html', '')
        url_base = url_filename.lower().replace('pytorch-', '')
        
        for cached in self._crawled_cache:
            cached_lower = cached.lower()
            cached_base = cached_lower.replace('pytorch-', '').replace('pytorch', '')
            
            if cached_base in url_base or url_base in cached_base:
                logger.info(f"Skipping (substring match): {url_filename} matches '{cached}'")
                return True
            
            cached_words = set(cached_base.replace('-', ' ').replace('_', ' ').split())
            url_words = set(url_base.replace('-', ' ').replace('_', ' ').split())
            common_words = cached_words & url_words
            
            if common_words and len(common_words) >= 2:
                logger.info(f"Skipping (keyword match): {url_filename} matches '{cached}'")
                return True
        
        return False

    def set_category_dirs(self, category_name):
        safe_name = re.sub(r'[^\w\s-]', '', category_name)
        safe_name = re.sub(r'[-\s]+', '-', safe_name).strip('-')
        self.current_output_dir = self.BASE_OUTPUT_DIR / safe_name
        self.current_pdf_dir = self.BASE_PDF_DIR / safe_name
        self.current_output_dir.mkdir(exist_ok=True)
        self.current_pdf_dir.mkdir(exist_ok=True)
        logger.info(f"Category directories设置为：{self.current_output_dir} 和 {self.current_pdf_dir}")

    def init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Chrome driver: {e}, will use requests instead")
            self.driver = None

    def close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def fetch_page(self, url, use_selenium=False):
        time.sleep(self.delay)
        
        if use_selenium and self.driver:
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "content"))
                )
                return self.driver.page_source
            except Exception as e:
                logger.warning(f"Selenium failed for {url}: {e}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_tutorial_links(self, category_url):
        html = self.fetch_page(category_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        left_column = soup.find('div', class_='left-column')
        if left_column:
            for a in left_column.find_all('a', href=True):
                href = a['href']
                if href.endswith('.html') and not href.startswith('http'):
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in links and 'tutorial' in full_url or '.html' in full_url:
                        links.append(full_url)
        
        sidebar_box = soup.find('div', class_='sidebar-box')
        if sidebar_box:
            for a in sidebar_box.find_all('a', href=True):
                href = a['href']
                if href.endswith('.html') and not href.startswith('http'):
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in links:
                        links.append(full_url)
        
        if not links:
            article_body = soup.find('div', class_='article-body')
            if article_body:
                for a in article_body.find_all('a', href=True):
                    href = a['href']
                    if href.endswith('.html') and not href.startswith('http'):
                        full_url = urljoin(self.BASE_URL, href)
                        if full_url not in links:
                            links.append(full_url)
        
        return links

    def extract_tutorial_content(self, url):
        html = self.fetch_page(url, use_selenium=True)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text(strip=True).replace('| 菜鸟教程', '').strip()
        else:
            title = soup.find('h1')
            title_text = title.get_text(strip=True) if title else "Untitled"
        
        content_div = soup.find('div', class_='article-body')
        if not content_div:
            content_div = soup.find('div', class_='article')
        if not content_div:
            content_div = soup.find('div', id='content')
        if not content_div:
            content_div = soup.find('main')
        
        if not content_div:
            logger.warning(f"No content found for {url}")
            return None
        
        for unwanted in content_div.find_all(['script', 'style', 'nav', 'footer', 'iframe']):
            unwanted.decompose()
        
        return {
            'url': url,
            'title': title_text,
            'content': str(content_div)
        }

    def save_html(self, content_data, filename=None):
        if not content_data:
            return None
        
        if filename is None:
            safe_title = re.sub(r'[^\w\s-]', '', content_data['title'])
            safe_title = re.sub(r'[-\s]+', '-', safe_title).strip('-')
            filename = f"{safe_title}.html"
        
        if self.current_output_dir is None:
            filepath = self.BASE_OUTPUT_DIR / filename
        else:
            filepath = self.current_output_dir / filename
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content_data['title']}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2, h3, h4 {{
            color: #34495e;
            margin-top: 1.5em;
        }}
        pre {{
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            overflow-x: auto;
        }}
        code {{
            background-color: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
        }}
        pre code {{
            padding: 0;
            background: none;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        .original-url {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>{content_data['title']}</h1>
    {content_data['content']}
    <div class="original-url">
        原文链接: <a href="{content_data['url']}">{content_data['url']}</a>
    </div>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        self.save_url_mapping(content_data.get('url', ''), filepath.name)
        logger.info(f"Saved HTML: {filepath}")
        return filepath

    def convert_to_pdf(self, html_path, pdf_name=None):
        if not html_path or not html_path.exists():
            logger.warning(f"HTML file not found: {html_path}")
            return None
        
        if not PDFKIT_AVAILABLE:
            logger.warning("pdfkit not available, skipping PDF conversion")
            return None
        
        if pdf_name is None:
            pdf_name = html_path.stem + ".pdf"
        
        if self.current_pdf_dir is None:
            pdf_path = self.BASE_PDF_DIR / pdf_name
        else:
            pdf_path = self.current_pdf_dir / pdf_name
        
        try:
            options = {
                'page-size': 'A4',
                'encoding': 'utf-8',
                'margin-top': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '15mm',
                'margin-right': '15mm',
            }
            import platform, os
            if platform.system() == 'Windows':
                wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
                try:
                    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                    pdfkit.from_file(str(html_path), str(pdf_path), options=options, configuration=config)
                except Exception as config_error:
                    logger.warning(f'Failed to use specified wkhtmltopdf path: {config_error}')
                    logger.info('Trying to find wkhtmltopdf in PATH...')
                    import shutil
                    wkhtmltopdf_exe = shutil.which('wkhtmltopdf')
                    if wkhtmltopdf_exe:
                        logger.info(f'Found wkhtmltopdf at: {wkhtmltopdf_exe}')
                        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_exe)
                        pdfkit.from_file(str(html_path), str(pdf_path), options=options, configuration=config)
                    else:
                        logger.error('wkhtmltopdf not found in PATH. Please ensure it is installed and added to PATH.')
                        raise
            else:
                pdfkit.from_file(str(html_path), str(pdf_path), options=options)
            logger.info(f"Converted to PDF: {pdf_path}")
            return pdf_path
        except Exception as e:
            logger.error(f"Failed to convert {html_path} to PDF: {e}")
            return None

    def process_single_tutorial(self, url):
        content_data = self.extract_tutorial_content(url)
        if not content_data:
            return None
        
        html_path = self.save_html(content_data)
        if html_path:
            self.convert_to_pdf(html_path)
        
        return content_data

    def crawl_category(self, category_url, limit=None, skip_existing=True):
        logger.info(f"Crawling category: {category_url}")
        
        category_name = category_url.split('/')[-1].replace('-tutorial.html', '').replace('-intro.html', '').replace('-', ' ').title()
        self.set_category_dirs(category_name)
        
        links = self.get_tutorial_links(category_url)
        logger.info(f"Found {len(links)} tutorial links")
        
        if skip_existing:
            skipped_count = 0
            filtered_links = []
            for link in links:
                if self.is_already_crawled(link):
                    skipped_count += 1
                    logger.info(f"Skipping already crawled: {link}")
                else:
                    filtered_links.append(link)
            logger.info(f"Skipped {skipped_count} already crawled tutorials, {len(filtered_links)} remaining")
            links = filtered_links
        
        if limit:
            links = links[:limit]
        
        results = []
        for i, link in enumerate(tqdm(links, desc="Crawling tutorials")):
            logger.info(f"[{i+1}/{len(links)}] Processing: {link}")
            result = self.process_single_tutorial(link)
            if result:
                results.append(result)
        
        return results

    def crawl_all(self, limit_per_category=None, skip_existing=True):
        logger.info("Starting to crawl all categories...")
        
        self.init_driver()
        
        all_results = []
        
        for category_url in tqdm(self.CATEGORY_URLS, desc="Categories"):
            try:
                results = self.crawl_category(category_url, limit_per_category, skip_existing)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Error crawling {category_url}: {e}")
                continue
        
        self.close_driver()
        
        summary_file = self.BASE_OUTPUT_DIR / "crawl_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_tutorials': len(all_results),
                'categories': self.CATEGORY_URLS,
                'tutorials': [{'title': r['title'], 'url': r['url']} for r in all_results]
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Crawling completed! Total tutorials: {len(all_results)}")
        logger.info(f"HTML files saved to: {self.BASE_OUTPUT_DIR}")
        logger.info(f"PDF files saved to: {self.BASE_PDF_DIR}")
        
        return all_results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Crawl Runoob tutorials and convert to PDF')
    parser.add_argument('--limit', type=int, default=None, help='Limit tutorials per category')
    parser.add_argument('--delay', type=float, default=1.5, help='Delay between requests (seconds)')
    parser.add_argument('--category', type=str, default=None, help='Crawl specific category URL')
    parser.add_argument('--url', type=str, default=None, help='Crawl specific tutorial URL')
    parser.add_argument('--urls', type=str, default=None, help='Multiple URLs separated by commas')
    parser.add_argument('--discover', action='store_true', help='Discover all available tutorial categories')
    parser.add_argument('--config', type=str, default=None, help='Path to config file (default: config.json)')
    parser.add_argument('--init-config', action='store_true', help='Create a default config.json file')
    parser.add_argument('--no-skip', action='store_true', help='Do NOT skip already crawled tutorials (crawl everything)')
    parser.add_argument('--check-crawled', action='store_true', help='Show already crawled files and exit')
    
    args = parser.parse_args()
    
    if args.init_config:
        config_path = args.config or "config.json"
        default_config = {
            "category_urls": [
                "https://www.runoob.com/pytorch/pytorch-tutorial.html",
            ],
            "delay": 1.5,
            "auto_discover": False
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        print(f"Created config file: {config_path}")
        print("Edit this file to add your desired tutorial URLs, then run the crawler again.")
        return
    
    crawler = RunoobCrawler(delay=args.delay)
    
    if args.config:
        crawler.CONFIG_FILE = Path(args.config)
        crawler._load_config()
    
    if args.discover:
        categories = crawler.discover_tutorial_categories()
        print(f"\nFound {len(categories)} tutorial categories:")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat}")
        return
    
    if args.check_crawled:
        crawled = crawler.get_crawled_files()
        print(f"\nAlready crawled {len(crawled)} files:")
        for f in sorted(crawled):
            print(f"  - {f}")
        return
    
    skip_existing = not args.no_skip
    
    if args.url:
        crawler.process_single_tutorial(args.url)
    elif args.urls:
        urls = [u.strip() for u in args.urls.split(',') if u.strip()]
        for url in urls:
            if '/tutorial/' in url and 'tutorial.html' in url:
                crawler.crawl_category(url, args.limit, skip_existing)
            else:
                crawler.process_single_tutorial(url)
    elif args.category:
        crawler.crawl_category(args.category, args.limit, skip_existing)
    else:
        crawler.crawl_all(args.limit, skip_existing)


if __name__ == "__main__":
    main()
