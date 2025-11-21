"""
Result Manager - Stores top N search results for later use.
"""
class ResultManager:
    """
    Stores the top N highest ranking document IDs from the current search.
    """
    def __init__(self):
        """Initialize empty result storage."""
        self.top_results = []
    
    def save_top_results(self, results, query, top_n=None):
        """
        Save top N document IDs, replacing any previous results.
        
        Args:
            results: List of result dictionaries from enhanced_search
            query: The search query string (unused, kept for compatibility)
            top_n: Number of top results to save (None = save all)
        """
        if not results:
            self.top_results = []
            return
        
        # Sort by relevance score and extract doc_ids
        sorted_results = sorted(results, key=lambda r: r.get('similarity', r.get('tf_idf', 0)), reverse=True)
        
        # Take top N doc_ids
        if top_n is None:
            self.top_results = [r['doc_id'] for r in sorted_results]
        else:
            self.top_results = [r['doc_id'] for r in sorted_results[:top_n]]
    
    def get_top_results(self):
        """Get the stored top document IDs."""
        return self.top_results
