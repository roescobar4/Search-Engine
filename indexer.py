"""
Reverse index builder with TF-IDF calculation for document search.
"""
import math  # For logarithmic and square root calculations in TF-IDF scoring
from tokenizer import tokenize_html, HTMLTextExtractor  # Extract words and URLs from HTML content
from bfs_crawler import bfs_crawl  # Crawl through HTML files in ZIP archive
# Build reverse index and document map from ZIP file with TF-IDF scores
def build_reverse_index(zip_path):
    temp_index = {}
    doc_max_freqs = {}
    document_vector_lengths = {}
    files_crawled = 0
    total_words_indexed = 0
    parser = HTMLTextExtractor()
    # Iterate through all crawled HTML files from the ZIP archive #Removed multiple nested loops ex. for(for(for)). now it is for(for()for())
    for file, text in bfs_crawl(zip_path, 'rhf/index.html'):
        files_crawled += 1
        words_with_positions, urls = tokenize_html(text, parser)
        word_data = {}
        for word, position in words_with_positions:
            if word not in word_data:
                word_data[word] = {'count': 0, 'positions': []}
            word_data[word]['count'] += 1
            word_data[word]['positions'].append(position)
        total_words_indexed += len(word_data)
        url_counts = {}
        for url in urls:
            url_counts[url] = url_counts.get(url, 0) + 1
        all_counts = [data['count'] for data in word_data.values()]
        all_counts.extend(url_counts.values())
        max_freq = max(all_counts) if all_counts else 0
        doc_max_freqs[file] = max_freq
        for word, data in word_data.items():
            if word not in temp_index:
                temp_index[word] = {}
            temp_index[word][file] = data
        for url, count in url_counts.items():
            if url not in temp_index:
                temp_index[url] = {}
            temp_index[url][file] = {'count': count, 'positions': []}
        if files_crawled % 100 == 0:
            print(f"Progress: {files_crawled} files crawled, {total_words_indexed} unique words indexed...")
    reverse_index = {}
    total_docs = len(doc_max_freqs)
    # Calculate TF-IDF scores for each token across all documents
    for token, doc_data in temp_index.items():
        sorted_docs = sorted(doc_data.items())
        doc_objects = []
        df = len(doc_data)
        for doc_path, data in sorted_docs:
            max_freq = doc_max_freqs[doc_path]
            term_freq = data['count']
            positions = data['positions']
            tf = term_freq / max_freq if max_freq > 0 else 0
            idf = math.log2((total_docs) / (df + 1)) + 1
            tf_idf = tf * idf
            if doc_path not in document_vector_lengths:
                document_vector_lengths[doc_path] = 0
            document_vector_lengths[doc_path] += tf_idf ** 2
            doc_objects.append({
                'doc_id': doc_path,
                'term_freq': term_freq,
                'tf_idf': tf_idf,
                'positions': positions
            })
        reverse_index[token] = {
            'df': df,
            'docs': doc_objects,
        }
    document_map = {
        doc_id: {'vector_length': math.sqrt(vector_length_squared)}
        for doc_id, vector_length_squared in document_vector_lengths.items()
    }
    print(f"\nIndexing complete!")
    print(f"Total files crawled: {files_crawled}")
    print(f"Total unique words indexed: {total_words_indexed}")
    print(f"Total unique tokens in index: {len(reverse_index)}")
    print(f"Total documents in map: {len(document_map)}")
    return reverse_index, document_map

