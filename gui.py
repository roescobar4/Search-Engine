"""
GUI application for document search engine using tkinter.
"""
import tkinter as tk  # Main GUI framework for creating the application window
from tkinter import ttk, scrolledtext  # Themed widgets and scrollable text area
import time  # Measure indexing elapsed time
import zipfile  # Read HTML files from ZIP archive for snippet extraction
import webbrowser  # Open HTML files in default browser
import tempfile  # Create temporary files for viewing documents
import os  # File path operations
from indexer import build_reverse_index  # Build the reverse index from ZIP file
from searcher import enhanced_search  # Perform search queries on the index
from tokenizer import tokenize_html, HTMLTextExtractor  # Extract text content from HTML documents
from result_manager import ResultManager  # Manage saved search results
from keyword_extractor import extract_keywords  # Extract keywords from top results
from correlation import calculate_correlations  # Calculate keyword correlations
class SearchGUI:
    # Initialize the search GUI with root window and ZIP file
    def __init__(self, root, zip_file="rhf.zip"):
        self.root = root
        self.root.title("Document Search Engine")
        self.root.geometry("600x500")
        self.zip_file = zip_file
        self.reverse_index = None
        self.document_map = None
        self.zip_handle = None
        self.snippet_parser = None
        self.result_manager = ResultManager()  # Initialize result manager
        self.load_data()
        self.setup_gui()
        self.zip_handle = zipfile.ZipFile(self.zip_file, 'r')
        self.snippet_parser = HTMLTextExtractor()
    # Close ZIP file when GUI is destroyed
    def __del__(self):
        if hasattr(self, 'zip_handle') and self.zip_handle:
            self.zip_handle.close()
    # Load the reverse index and document map
    def load_data(self):
        print(f"Loading index from {self.zip_file}...")
        print()
        start_time = time.time()
        self.reverse_index, self.document_map = build_reverse_index(self.zip_file)
        elapsed_time = time.time() - start_time
        print()
        print(f"✓ Total indexing time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    # Set up the GUI components
    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        ttk.Label(main_frame, text="Search Term:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=50)
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5), padx=(5, 0))
        self.search_entry.bind('<Return>', self.search_documents)
        self.search_button = ttk.Button(main_frame, text="Search", command=self.search_documents)
        self.search_button.grid(row=0, column=2, pady=(0, 5), padx=(5, 0))
        ttk.Label(main_frame, text="Search Results:").grid(row=1, column=0, sticky=tk.W, pady=(10, 5))
        
        # Create notebook (tab widget) for results
        self.results_notebook = ttk.Notebook(main_frame)
        self.results_notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Original results tab
        original_frame = ttk.Frame(self.results_notebook)
        self.results_text = scrolledtext.ScrolledText(original_frame, width=70, height=20, wrap=tk.WORD)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_notebook.add(original_frame, text="Original Results")
        
        # Reformulated results tab
        reformulated_frame = ttk.Frame(self.results_notebook)
        self.reformulated_text = scrolledtext.ScrolledText(reformulated_frame, width=70, height=20, wrap=tk.WORD)
        self.reformulated_text.pack(fill=tk.BOTH, expand=True)
        # Configure colored text tag for reformulated results
        self.reformulated_text.tag_config("reformulated", foreground="blue")
        self.results_notebook.add(reformulated_frame, text="Reformulated Results")

        # Configure clickable link tags for both text widgets
        self.results_text.tag_config("link", foreground="blue", underline=True)
        self.results_text.tag_bind("link", "<Button-1>", self.open_document)
        self.results_text.tag_bind("link", "<Enter>", lambda e: self.results_text.config(cursor="hand2"))
        self.results_text.tag_bind("link", "<Leave>", lambda e: self.results_text.config(cursor=""))

        self.reformulated_text.tag_config("link", foreground="blue", underline=True)
        self.reformulated_text.tag_bind("link", "<Button-1>", self.open_document_reformulated)
        self.reformulated_text.tag_bind("link", "<Enter>", lambda e: self.reformulated_text.config(cursor="hand2"))
        self.reformulated_text.tag_bind("link", "<Leave>", lambda e: self.reformulated_text.config(cursor=""))

        # Initialize document mapping for click handlers
        self.doc_links = {}  # Maps line numbers to doc_ids for original results
        self.reformulated_doc_links = {}  # Maps line numbers to doc_ids for reformulated results
        self.clear_button = ttk.Button(main_frame, text="Clear Results", command=self.clear_results)
        self.clear_button.grid(row=3, column=0, pady=(0, 10))
        self.stats_button = ttk.Button(main_frame, text="Show Stats", command=self.show_stats)
        self.stats_button.grid(row=3, column=1, pady=(0, 10), sticky=tk.W, padx=(5, 0))
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to search")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.grid(row=3, column=2, sticky=tk.W, pady=(0, 10))

    # Open document when clicked in original results
    def open_document(self, event):
        """Open the clicked document in the default browser."""
        try:
            # Get the clicked position
            index = self.results_text.index("@%s,%s" % (event.x, event.y))
            line_num = int(index.split('.')[0])

            # Find the doc_id for this line
            if line_num in self.doc_links:
                doc_id = self.doc_links[line_num]
                self._open_document_file(doc_id)
            else:
                self.status_var.set("Could not find document for this link")
        except Exception as e:
            self.status_var.set(f"Error opening document: {str(e)}")

    # Open document when clicked in reformulated results
    def open_document_reformulated(self, event):
        """Open the clicked document in the reformulated results tab."""
        try:
            # Get the clicked position
            index = self.reformulated_text.index("@%s,%s" % (event.x, event.y))
            line_num = int(index.split('.')[0])

            # Find the doc_id for this line
            if line_num in self.reformulated_doc_links:
                doc_id = self.reformulated_doc_links[line_num]
                self._open_document_file(doc_id)
            else:
                self.status_var.set("Could not find document for this link")
        except Exception as e:
            self.status_var.set(f"Error opening document: {str(e)}")

    # Helper method to extract and open a document from the ZIP file
    def _open_document_file(self, doc_id):
        """Extract document from ZIP and open in browser."""
        try:
            # Extract HTML content from ZIP
            with self.zip_handle.open(doc_id) as file:
                html_content = file.read()

            # Create a temporary file to store the extracted HTML
            temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.html', delete=False)
            temp_file.write(html_content)
            temp_file.close()

            # Open in default browser
            webbrowser.open('file://' + os.path.abspath(temp_file.name))
            self.status_var.set(f"Opened: {doc_id.split('/')[-1]}")
        except Exception as e:
            self.status_var.set(f"Error opening document: {str(e)}")

    # Search for documents containing the search term
    def search_documents(self, event=None):
        search_term = self.search_var.get().strip()
        if not search_term:
            self.status_var.set("Please enter a search term")
            return
        self.status_var.set("Searching...")
        self.root.update()
        self.results_text.delete(1.0, tk.END)
        # Clear document link mapping
        self.doc_links = {}
        # This is where searching happens
        # Need to get a list of top A pages from S
        results, message = enhanced_search(self.reverse_index, search_term, self.document_map)
        if results is None:
            self.results_text.insert(tk.END, f"Error: {message}\n")
            self.status_var.set("Search error")
            return
        if not results:
            self.results_text.insert(tk.END, f"{message}\n")
            self.status_var.set(message)
            return
        self.results_text.insert(tk.END, f"{message}:\n\n")
        # Display each search result with its ranking and details
        for i, doc in enumerate(results, 1):
            filename = doc['doc_id'].split('/')[-1]
            # Insert result number
            self.results_text.insert(tk.END, f"{i}. ")
            # Get current line number and insert filename as clickable link
            current_line = int(self.results_text.index(tk.INSERT).split('.')[0])
            start_pos = self.results_text.index(tk.INSERT)
            self.results_text.insert(tk.END, f"{filename}")
            end_pos = self.results_text.index(tk.INSERT)
            # Apply link tag to filename
            self.results_text.tag_add("link", start_pos, end_pos)
            # Store mapping from line number to doc_id
            self.doc_links[current_line] = doc['doc_id']
            self.results_text.insert(tk.END, "\n")
            if 'similarity' in doc:
                self.results_text.insert(tk.END, f"   - Similarity score: {doc['similarity']:.4f}\n")
                self.results_text.insert(tk.END, f"   - Matched terms: {', '.join(doc['matched_terms'])}\n")
                if doc['matched_terms']:
                    first_term = doc['matched_terms'][0]
                    if first_term in self.reverse_index:
                        for doc_data in self.reverse_index[first_term]['docs']:
                            if doc_data['doc_id'] == doc['doc_id'] and doc_data['positions']:
                                snippet = self.get_text_snippet(doc['doc_id'], doc_data['positions'][0])
                                self.results_text.insert(tk.END, f"   - Snippet: \"{snippet}\"\n")
                                break
            else:
                self.results_text.insert(tk.END, f"   - Appears {doc['term_freq']} times\n")
                self.results_text.insert(tk.END, f"   - TF-IDF score: {doc['tf_idf']:.4f}\n")
                self.results_text.insert(tk.END, f"   - Matched term: {doc['matched_term']}\n")
                if doc['positions']:
                    positions_str = ', '.join(map(str, doc['positions'][:5]))
                    if len(doc['positions']) > 5:
                        positions_str += f", ... (+{len(doc['positions']) - 5} more)"
                    self.results_text.insert(tk.END, f"   - Positions: [{positions_str}]\n")
                    snippet = self.get_text_snippet(doc['doc_id'], doc['positions'][0])
                    self.results_text.insert(tk.END, f"   - Snippet: \"{snippet}\"\n")
            self.results_text.insert(tk.END, "\n")
        # Save results for later use
        self.save_top_results(results, search_term)
        
        # Reformulate query and run new search
        reformulated_query = self.reformulate_query(search_term)
        if reformulated_query and reformulated_query != search_term:
            # Clear reformulated results tab and document links
            self.reformulated_text.delete(1.0, tk.END)
            self.reformulated_doc_links = {}

            # Display reformulated query info in reformulated tab
            self.reformulated_text.insert(tk.END, f"REFORMULATED QUERY: {reformulated_query}\n", "reformulated")
            self.reformulated_text.insert(tk.END, "="*70 + "\n\n", "reformulated")

            # Run search with reformulated query
            self.status_var.set("Searching with reformulated query...")
            self.root.update()

            reformulated_results, reformulated_message = enhanced_search(
                self.reverse_index, reformulated_query, self.document_map
            )

            if reformulated_results:
                self.reformulated_text.insert(tk.END, f"{reformulated_message}:\n\n", "reformulated")
                # Display reformulated results with colored text
                for i, doc in enumerate(reformulated_results, 1):
                    filename = doc['doc_id'].split('/')[-1]
                    # Insert result number
                    self.reformulated_text.insert(tk.END, f"{i}. ", "reformulated")
                    # Get current line number and insert filename as clickable link
                    current_line = int(self.reformulated_text.index(tk.INSERT).split('.')[0])
                    start_pos = self.reformulated_text.index(tk.INSERT)
                    self.reformulated_text.insert(tk.END, f"{filename}", "reformulated")
                    end_pos = self.reformulated_text.index(tk.INSERT)
                    # Apply link tag to filename (in addition to reformulated tag)
                    self.reformulated_text.tag_add("link", start_pos, end_pos)
                    # Store mapping from line number to doc_id
                    self.reformulated_doc_links[current_line] = doc['doc_id']
                    self.reformulated_text.insert(tk.END, "\n", "reformulated")
                    if 'similarity' in doc:
                        self.reformulated_text.insert(tk.END, f"   - Similarity score: {doc['similarity']:.4f}\n", "reformulated")
                        self.reformulated_text.insert(tk.END, f"   - Matched terms: {', '.join(doc['matched_terms'])}\n", "reformulated")
                        if doc['matched_terms']:
                            first_term = doc['matched_terms'][0]
                            if first_term in self.reverse_index:
                                for doc_data in self.reverse_index[first_term]['docs']:
                                    if doc_data['doc_id'] == doc['doc_id'] and doc_data['positions']:
                                        snippet = self.get_text_snippet(doc['doc_id'], doc_data['positions'][0])
                                        self.reformulated_text.insert(tk.END, f"   - Snippet: \"{snippet}\"\n", "reformulated")
                                        break
                    else:
                        self.reformulated_text.insert(tk.END, f"   - Appears {doc['term_freq']} times\n", "reformulated")
                        self.reformulated_text.insert(tk.END, f"   - TF-IDF score: {doc['tf_idf']:.4f}\n", "reformulated")
                        self.reformulated_text.insert(tk.END, f"   - Matched term: {doc['matched_term']}\n", "reformulated")
                        if doc['positions']:
                            positions_str = ', '.join(map(str, doc['positions'][:5]))
                            if len(doc['positions']) > 5:
                                positions_str += f", ... (+{len(doc['positions']) - 5} more)"
                            self.reformulated_text.insert(tk.END, f"   - Positions: [{positions_str}]\n", "reformulated")
                            snippet = self.get_text_snippet(doc['doc_id'], doc['positions'][0])
                            self.reformulated_text.insert(tk.END, f"   - Snippet: \"{snippet}\"\n", "reformulated")
                    self.reformulated_text.insert(tk.END, "\n", "reformulated")
                # Switch to reformulated tab to show results
                self.results_notebook.select(1)
                self.status_var.set(f"{message} | Reformulated: {reformulated_message}")
            else:
                self.reformulated_text.insert(tk.END, f"{reformulated_message}\n", "reformulated")
                self.status_var.set(f"{message} | Reformulated query: {reformulated_query}")
        else:
            self.status_var.set(message)
    
    # Save top N results to result manager
    def save_top_results(self, results, query, top_n=5):
        """Save top N results from a search for later use in algorithms."""
        self.result_manager.save_top_results(results, query, top_n)
    
    # Reformulate query using keyword correlation
    def reformulate_query(self, original_query, top_n_keywords=3):
        """
        Reformulate query by finding most correlated keywords from top results.
        
        Args:
            original_query: The original search query
            top_n_keywords: Number of top correlated keywords to add
        
        Returns:
            Reformulated query string, or None if no keywords found
        """
        top_doc_ids = self.result_manager.get_top_results()
        if not top_doc_ids:
            return None
        
        # Extract keywords from top results
        keywords = extract_keywords(top_doc_ids, self.reverse_index)
        if not keywords:
            return None
        
        # Calculate correlations
        correlations = calculate_correlations(original_query, keywords, self.reverse_index)
        if not correlations:
            return None
        
        # Get top N most correlated keywords
        sorted_keywords = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [kw for kw, score in sorted_keywords[:top_n_keywords]]

        # Create set of original query terms to prevent duplicates
        query_terms_set = set(term.strip().lower() for term in original_query.split())

        # Filter out keywords that are already in the original query
        unique_keywords = [kw for kw in top_keywords if kw.lower() not in query_terms_set]

        # Build reformulated query: original query + unique correlated keywords
        if unique_keywords:
            reformulated = original_query + " " + " ".join(unique_keywords)
      
        return reformulated
    


    # Clear the results text area
    def clear_results(self):
        self.results_text.delete(1.0, tk.END)
        self.reformulated_text.delete(1.0, tk.END)
        self.doc_links = {}
        self.reformulated_doc_links = {}
        self.status_var.set("Results cleared")
    # Extract text snippet around a word position from one period to the next
    def get_text_snippet(self, doc_id, position):
        try:
            with self.zip_handle.open(doc_id) as file:
                html_content = file.read().decode('utf-8', errors='ignore')
            words_with_positions, _ = tokenize_html(html_content, self.snippet_parser)
            if not words_with_positions:
                return "No text available"
            text_positions = {}
            for word, pos in words_with_positions:
                if pos not in text_positions:
                    text_positions[pos] = word
            sorted_positions = sorted(text_positions.keys())
            full_text = ' '.join(text_positions[pos] for pos in sorted_positions)
            char_position = 0
            for pos in sorted_positions:
                if pos >= position:
                    break
                char_position += len(text_positions[pos]) + 1
            start = 0
            # Find previous period
            for i in range(char_position - 1, -1, -1):
                if full_text[i] == '.':
                    start = i + 1
                    break
            end = len(full_text)
            # Find next period
            for i in range(char_position, len(full_text)):
                if full_text[i] == '.':
                    end = i + 1
                    break
            snippet = full_text[start:end].strip()
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            return snippet if snippet else "No snippet available"
        except Exception as e:
            return f"Error extracting snippet: {str(e)}"
    # Display comprehensive statistics about the index
    def show_stats(self):
        # Switch to original results tab
        self.results_notebook.select(0)
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Displaying index statistics...")
        self.root.update()
        self.results_text.insert(tk.END, "INDEX STATISTICS\n")
        self.results_text.insert(tk.END, "=" * 90 + "\n\n")
        total_tokens = len(self.reverse_index)
        total_docs = len(self.document_map)
        self.results_text.insert(tk.END, f"Total Unique Tokens: {total_tokens:,}\n")
        self.results_text.insert(tk.END, f"Total Documents: {total_docs:,}\n\n")
        token_stats = []
        # Calculate comprehensive statistics for each token
        for token, data in self.reverse_index.items():
            df = data['df']
            total_freq = sum(doc['term_freq'] for doc in data['docs'])
            avg_tfidf = sum(doc['tf_idf'] for doc in data['docs']) / len(data['docs'])
            max_tfidf = max(doc['tf_idf'] for doc in data['docs'])
            token_stats.append({
                'token': token,
                'doc_freq': df,
                'total_freq': total_freq,
                'avg_tfidf': avg_tfidf,
                'max_tfidf': max_tfidf
            })
        token_stats.sort(key=lambda x: x['doc_freq'], reverse=True)
        self.results_text.insert(tk.END, "TOP 30 TOKENS BY DOCUMENT FREQUENCY\n")
        self.results_text.insert(tk.END, "=" * 90 + "\n")
        header = f"{'Rank':<6}{'Token':<20}{'Doc Freq':<12}{'Total Freq':<14}{'Avg TF-IDF':<14}{'Max TF-IDF':<14}\n"
        self.results_text.insert(tk.END, header)
        self.results_text.insert(tk.END, "-" * 90 + "\n")
        # Display top 30 tokens in tabular format
        for i, stats in enumerate(token_stats[:30], 1):
            token_display = stats['token'][:18] + '..' if len(stats['token']) > 18 else stats['token']
            row = f"{i:<6}{token_display:<20}{stats['doc_freq']:<12}{stats['total_freq']:<14}{stats['avg_tfidf']:<14.4f}{stats['max_tfidf']:<14.4f}\n"
            self.results_text.insert(tk.END, row)
        self.results_text.insert(tk.END, "\n")
        self.results_text.insert(tk.END, "DOCUMENT STATISTICS\n")
        self.results_text.insert(tk.END, "=" * 90 + "\n")
        doc_token_counts = {}
        # Count unique tokens per document
        for token, data in self.reverse_index.items():
            for doc_info in data['docs']:
                doc_id = doc_info['doc_id']
                if doc_id not in doc_token_counts:
                    doc_token_counts[doc_id] = 0
                doc_token_counts[doc_id] += 1
        if doc_token_counts:
            avg_tokens = sum(doc_token_counts.values()) / len(doc_token_counts)
            max_doc = max(doc_token_counts.items(), key=lambda x: x[1])
            min_doc = min(doc_token_counts.items(), key=lambda x: x[1])
            self.results_text.insert(tk.END, f"Average Unique Tokens per Document: {avg_tokens:.2f}\n")
            self.results_text.insert(tk.END, f"Document with Most Tokens: {max_doc[0].split('/')[-1]} ({max_doc[1]:,} tokens)\n")
            self.results_text.insert(tk.END, f"Document with Fewest Tokens: {min_doc[0].split('/')[-1]} ({min_doc[1]:,} tokens)\n\n")
        vector_lengths = [doc['vector_length'] for doc in self.document_map.values()]
        if vector_lengths:
            avg_vector_length = sum(vector_lengths) / len(vector_lengths)
            max_vector_length = max(vector_lengths)
            min_vector_length = min(vector_lengths)
            self.results_text.insert(tk.END, f"Average Document Vector Length: {avg_vector_length:.4f}\n")
            self.results_text.insert(tk.END, f"Maximum Document Vector Length: {max_vector_length:.4f}\n")
            self.results_text.insert(tk.END, f"Minimum Document Vector Length: {min_vector_length:.4f}\n")
        self.status_var.set("Statistics displayed")
