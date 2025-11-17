#BFS Crawler for HTML files in ZIP archives starting at index.html

import zipfile  # Read and extract files from ZIP archives
from html.parser import HTMLParser  # Parse HTML tags and extract attributes
import posixpath  # Handle POSIX-style paths within ZIP archives

# Resolves a link relative to the current file path within the ZIP structure
def normalize_path(current_path, link):
    link = link.split('#')[0].split('?')[0].strip()
    if not link:
        return None
    if link.startswith(('http://', 'https://', 'mailto:', 'ftp://', 'javascript:', 'tel:')):
        return None
    current_dir = posixpath.dirname(current_path)
    if link.startswith('/'):
        normalized = link.lstrip('/')
    else:
        if current_dir:
            combined = posixpath.join(current_dir, link)
        else:
            combined = link
        normalized = posixpath.normpath(combined)
    normalized = normalized.lstrip('./')
    if normalized.startswith('..'):
        return None
    return normalized
# HTML Parser that extracts all href attributes from anchor tags
class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    # Extract href attributes from <a> tags
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            # Extract href attribute from anchor tag attributes
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    self.links.append(attr_value)
# Extracts all links from HTML content and resolves them relative to current_file
def extract_links_from_html(html_content, current_file):
    parser = LinkExtractor()
    parser.feed(html_content)
    normalized_links = []
    # Normalize each extracted link relative to the current file path
    for link in parser.links:
        normalized = normalize_path(current_file, link)
        if normalized:
            normalized_links.append(normalized)
    return normalized_links
# Performs breadth-first search crawl of HTML files in a ZIP archive
def bfs_crawl(zip_path, start_file='rhf/index.html'):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        all_files = set(zf.namelist())
        if start_file not in all_files:
            potential_starts = [
                'index.html',
                'rhf/index.html',
            ]
            start_file = None
            # Try each potential start file path to find a valid entry point
            for potential in potential_starts:
                if potential in all_files:
                    start_file = potential
                    break
        queue = [start_file]
        visited = set([start_file])
        while queue:
            current_file = queue.pop(0)
            if not (current_file.endswith('.html') or current_file.endswith('.htm')):
                continue
            with zf.open(current_file) as file:
                html_content = file.read().decode('utf-8', errors='ignore')
            yield current_file, html_content
            links = extract_links_from_html(html_content, current_file)
            # Add unvisited HTML links to the BFS queue
            for link in links:
                if link in all_files and link not in visited:
                    if link.endswith('.html') or link.endswith('.htm'):
                        queue.append(link)
                        visited.add(link)

"""
Add Directed Graph in order to continue ------ Priority ----------

Add Hubs -- index pages that provide lots of links to relevant pages/ hubs point to lots of authorities
Add Authorities -- pages that have multiple hubs pointing towards it rather than a bunch of meaningless pages

    start with normal query -- HITS algorithm--
        -get the top r pages, r will be considered the root set (*200 pages good size)
        -expand the root set based on the pages they point to and the pages that point to them, point to them is hard.
    this will require multiple iterations
        - one to see who points to who
        - then give them all values
        -then iterate again, continue iterations until stabalization
    after stabalization those values will be the authoritiy scores and hubscores
        - use top n to determine the authority and hub pages
    ------------------NOTES----------------------------------------------------------
    url: authority_score, hub_score   
    host pages should be limited to 4-8
"""