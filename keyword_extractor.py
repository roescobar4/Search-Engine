"""
Keyword Extractor - Extracts keywords from top result pages.
"""
def extract_keywords(top_doc_ids, reverse_index):
    """
    Extract all unique keywords from top result pages.
    
    Args:
        top_doc_ids: List of document IDs from top results
        reverse_index: The reverse index containing all terms for each document
    
    Returns:
        List of unique keywords across all top result pages
    """
    all_keywords = set()
    
    for doc_id in top_doc_ids:
        # Find all terms in reverse_index that appear in this document
        for term, term_data in reverse_index.items():
            for doc_info in term_data['docs']:
                if doc_info['doc_id'] == doc_id:
                    all_keywords.add(term)
                    break
    
    return list(all_keywords)

