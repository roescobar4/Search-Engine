"""
Correlation Calculator - Finds keywords most correlated with query terms.
"""
def calculate_correlations(query, keywords, reverse_index):
    """
    Calculate correlation scores between query terms and keywords.
    Correlation is measured by summing TF-IDF values of both terms
    in documents where they co-occur.
    
    Args:
        query: Query string (will be tokenized)
        keywords: List of keywords from top results
        reverse_index: The reverse index containing all terms
    
    Returns:
        Dictionary mapping keyword to correlation score
    """
    # Tokenize query (simple split, lowercase)
    query_terms = [term.strip().lower() for term in query.split()]
    
    correlations = {}
    
    for keyword in keywords:
        total_score = 0
        
        # For each query term, find documents with both query_term and keyword
        for query_term in query_terms:
            # Skip if query term or keyword not in index
            if query_term not in reverse_index or keyword not in reverse_index:
                continue
            
            # Get document sets for both terms
            query_docs = {doc['doc_id']: doc for doc in reverse_index[query_term]['docs']}
            keyword_docs = {doc['doc_id']: doc for doc in reverse_index[keyword]['docs']}
            
            # Find documents containing both terms
            common_docs = set(query_docs.keys()) & set(keyword_docs.keys())
            
            # Sum TF-IDF values for both terms in common documents
            for doc_id in common_docs:
                query_tfidf = query_docs[doc_id]['tf_idf']
                keyword_tfidf = keyword_docs[doc_id]['tf_idf']
                total_score += query_tfidf + keyword_tfidf
        
        correlations[keyword] = total_score
    
    return correlations

