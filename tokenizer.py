"""
HTML parsing and tokenization for extracting text and URLs from HTML documents.
"""
import re  # Regular expressions for word pattern matching and text cleaning
from html.parser import HTMLParser  # Parse HTML structure and extract content
from html import unescape  # Convert HTML entities to normal characters
class HTMLTextExtractor(HTMLParser):
    # Initialize HTML parser with text and URL extraction
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.urls = []
        self.skip_tags = {'script', 'style', 'noscript'}
        self.current_skip = None
        self.position = 0
    # Handle start tags - extract URLs from anchors and skip script/style tags
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            # Extract href attribute value from anchor tag
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    self.urls.append(attr_value)
        if tag in self.skip_tags:
            self.current_skip = tag
    # Handle end tags - stop skipping when script/style tags close
    def handle_endtag(self, tag):
        if tag == self.current_skip:
            self.current_skip = None
    # Handle text data - extract if not in skip tags
    def handle_data(self, data):
        if self.current_skip is None:
            clean_data = unescape(data)
            self.text_parts.append((clean_data, self.position))
            self.position += len(clean_data)
    # Return extracted text
    def get_text(self):
        return ''.join(text for text, _ in self.text_parts)
    # Return extracted URLs
    def get_urls(self):
        return self.urls
    # Reset parser state for reuse
    def reset_state(self):
        self.text_parts = []
        self.urls = []
        self.position = 0
        self.current_skip = None
# Tokenize HTML content using html.parser for robust parsing
def tokenize_html(html_content, parser=None):
    if parser is None:
        parser = HTMLTextExtractor()
    else:
        parser.reset_state()
    parser.feed(html_content)
    text = parser.get_text()
    urls = parser.get_urls()
    text = re.sub(r'data:[^;]+;base64,[A-Za-z0-9+/=]+', '', text)
    text = re.sub(r'https?://[^\s]+', '', text)
    word_matches = re.finditer(r'\b[a-zA-Z]+(?:[-\'][a-zA-Z]+)*\b', text.lower())
    words_with_positions = [(match.group(), match.start()) for match in word_matches]
    return words_with_positions, urls
