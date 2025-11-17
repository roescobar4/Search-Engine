"""
Search functions for document retrieval including phrase, boolean, and vector space search.
"""
import math  # Calculate square root for vector normalization in cosine similarity
# Get set of document IDs containing a term
def get_doc_ids(reverse_index, term):
    if term in reverse_index:
        return set(doc['doc_id'] for doc in reverse_index[term]['docs'])
    return set()
# Get document data for a specific term and doc_id
def get_doc_data(reverse_index, term, doc_id):
    if term in reverse_index:
        for doc in reverse_index[term]['docs']:
            if doc['doc_id'] == doc_id:
                return doc
    return None
# Aggregate TF-IDF scores and positions for multiple terms in a document
def aggregate_terms(reverse_index, terms, doc_id):
    combined_tf_idf = 0
    combined_freq = 0
    all_positions = []
    matched_terms = []
    # Collect and aggregate TF-IDF scores and positions for each term
    for term in terms:
        doc = get_doc_data(reverse_index, term, doc_id)
        if doc:
            combined_tf_idf += doc['tf_idf']
            combined_freq += doc['term_freq']
            all_positions.extend(doc['positions'])
            matched_terms.append(term)
    return combined_tf_idf, combined_freq, sorted(all_positions), matched_terms
# Check if words are close together for phrases
def check_proximity(word_positions, proximity):
    words = list(word_positions.keys())
    if len(words) < 2:
        return True
    # Check each position of the first word to find phrase matches
    for pos1 in word_positions[words[0]]:
        found_sequence = True
        current_pos = pos1
        # Loop through remaining words to check if they appear in sequence
        for i in range(1, len(words)):
            word = words[i]
            found_next = False
            # Loop through positions of current word to find one within proximity
            for pos in word_positions[word]:
                if pos > current_pos and pos <= current_pos + proximity:
                    current_pos = pos
                    found_next = True
                    break
            if not found_next:
                found_sequence = False
                break
        if found_sequence:
            return True
    return False
# Phrase search function with proximity tolerance
def phrase_search(reverse_index, words, proximity):
    missing_words = [word for word in words if word not in reverse_index]
    if missing_words:
        return [], f"No documents found. Words not in index: {', '.join(missing_words)}"
    doc_sets = [get_doc_ids(reverse_index, word) for word in words]
    common_docs = doc_sets[0].intersection(*doc_sets[1:]) if len(doc_sets) > 1 else doc_sets[0]
    if not common_docs:
        return [], f"No documents found containing all words: {', '.join(words)}"
    results = []
    phrase = ' '.join(words)
    # Check each document for phrase proximity matches
    for doc_id in sorted(common_docs):
        word_positions = {word: get_doc_data(reverse_index, word, doc_id)['positions'] for word in words}
        if check_proximity(word_positions, proximity):
            tf_idf, freq, positions, _ = aggregate_terms(reverse_index, words, doc_id)
            results.append({
                'doc_id': doc_id,
                'term_freq': freq,
                'tf_idf': tf_idf,
                'positions': positions,
                'matched_term': f'"{phrase}" (within {proximity} chars)'
            })
    if not results:
        return [], f"No documents found with phrase '{phrase}' within {proximity} characters"
    return results, f"Found {len(results)} document(s) containing phrase '{phrase}' (within {proximity} characters)"
# Vector space model search using cosine similarity
def vector_space_search(reverse_index, document_map, query_terms):
    query_vector = {}
    total_docs = len(document_map)
    query_term_counts = {}
    # Count occurrences of each term in the query
    for term in query_terms:
        query_term_counts[term] = query_term_counts.get(term, 0) + 1
    # Calculate TF-IDF weights for each unique query term
    for term, count in query_term_counts.items():
        if term in reverse_index:
            df = reverse_index[term]['df']
            max_freq_in_query = max(query_term_counts.values())
            tf = count / max_freq_in_query
            idf = math.log2(total_docs / (df + 1)) + 1
            query_vector[term] = tf * idf
    if not query_vector:
        return [], "No query terms found in index"
    similarities = []
    query_vector_length = math.sqrt(sum(tfidf**2 for tfidf in query_vector.values()))
    # Calculate cosine similarity between query and each document
    for doc_id in document_map.keys():
        query_doc_dot_product = 0
        # Loop through query vector terms to compute dot product with document vector
        for term, query_tfidf in query_vector.items():
            doc = get_doc_data(reverse_index, term, doc_id)
            if doc:
                query_doc_dot_product += query_tfidf * doc['tf_idf']
        doc_vector_length = document_map[doc_id]['vector_length']
        if doc_vector_length > 0 and query_vector_length > 0:
            cosine_similarity = query_doc_dot_product / (doc_vector_length * query_vector_length)
            if cosine_similarity > 0:
                similarities.append({
                    'doc_id': doc_id,
                    'similarity': cosine_similarity,
                    'matched_terms': list(query_vector.keys())
                })
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    return similarities, f"Found {len(similarities)} document(s) using vector space model"
# Enhanced search function that handles OR, AND, BUT, phrase queries, and vector space model
def enhanced_search(reverse_index, query, document_map=None):
    query = query.strip().lower()
    if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
        phrase_query = query[1:-1].strip()
        words = phrase_query.split()
        if len(words) > 1:
            return phrase_search(reverse_index, words, proximity=100)
        else:
            query = phrase_query
    if " or " in query:
        terms = [term.strip() for term in query.split(" or ")]
        if len(terms) < 2:
            return None, "Invalid OR query format. Use: 'term1 or term2' or 'term1 or term2 or term3'"
        results = []
        found_docs = set()
        # Collect documents matching any of the OR terms
        for term in terms:
            for doc_id in get_doc_ids(reverse_index, term):
                if doc_id not in found_docs:
                    doc = get_doc_data(reverse_index, term, doc_id)
                    results.append({
                        'doc_id': doc_id,
                        'term_freq': doc['term_freq'],
                        'tf_idf': doc['tf_idf'],
                        'positions': doc['positions'],
                        'matched_term': term
                    })
                    found_docs.add(doc_id)
        terms_str = ' OR '.join([f"'{t}'" for t in terms])
        result_msg = f"Found {len(results)} document(s) containing {terms_str}"
        return results, result_msg
    elif " but " in query:
        terms = [term.strip() for term in query.split(" but ")]
        if len(terms) != 2:
            return None, "Invalid BUT query format. Use: 'term1 but term2'"
        term1, term2 = terms
        if term1 not in reverse_index:
            return [], f"No documents found. First term '{term1}' not in index"
        result_docs = get_doc_ids(reverse_index, term1) - get_doc_ids(reverse_index, term2)
        if not result_docs:
            return [], f"No documents found containing '{term1}' but not '{term2}'"
        results = []
        # Build result list from documents containing first term but not second
        for doc_id in sorted(result_docs):
            doc = get_doc_data(reverse_index, term1, doc_id)
            results.append({
                'doc_id': doc_id,
                'term_freq': doc['term_freq'],
                'tf_idf': doc['tf_idf'],
                'positions': doc['positions'],
                'matched_term': f"{term1} (but not {term2})"
            })
        return results, f"Found {len(results)} document(s) containing '{term1}' but not '{term2}'"
    elif " and " in query:
        terms = [term.strip() for term in query.split(" and ")]
        if len(terms) < 2:
            return None, "Invalid AND query format. Use: 'term1 and term2' or 'term1 and term2 and term3'"
        missing_terms = [term for term in terms if term not in reverse_index]
        if missing_terms:
            return [], f"No documents found. Terms not in index: {', '.join(missing_terms)}"
        doc_sets = [get_doc_ids(reverse_index, term) for term in terms]
        common_docs = doc_sets[0].intersection(*doc_sets[1:]) if len(doc_sets) > 1 else doc_sets[0]
        if not common_docs:
            return [], f"No documents found containing all terms: {', '.join(terms)}"
        results = []
        # Build results from documents containing all AND terms
        for doc_id in sorted(common_docs):
            tf_idf, freq, positions, matched = aggregate_terms(reverse_index, terms, doc_id)
            results.append({
                'doc_id': doc_id,
                'term_freq': freq,
                'tf_idf': tf_idf,
                'positions': positions,
                'matched_term': ', '.join(matched)
            })
        terms_str = " AND ".join([f"'{term}'" for term in terms])
        result_msg = f"Found {len(results)} document(s) containing {terms_str}"
        return results, result_msg
    else:
        words = query.split()
        if len(words) > 1:
            if document_map is not None:
                return vector_space_search(reverse_index, document_map, words)
            else:
                return phrase_search(reverse_index, words, proximity=100)
        else:
            if query in reverse_index:
                entry = reverse_index[query]
                results = []
                # Collect all documents containing the single query term
                for doc in entry['docs']:
                    results.append({
                        'doc_id': doc['doc_id'],
                        'term_freq': doc['term_freq'],
                        'tf_idf': doc['tf_idf'],
                        'positions': doc['positions'],
                        'matched_term': query
                    })
                return results, f"Found {len(results)} document(s) containing '{query}'"
            else:
                return [], f"No documents found containing '{query}'"
