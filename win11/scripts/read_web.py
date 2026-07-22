import sys
import re
import urllib.request
import urllib.error

def fetch_and_clean(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Remove scripts and styles
            html = re.sub(r'<script.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style.*?</style>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            
            # Unescape some common HTML entities
            text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            
            # Collapse whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Print up to 4000 characters
            print(text[:4000])
    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_and_clean(sys.argv[1])
    else:
        print("Usage: python read_web.py <url>")
