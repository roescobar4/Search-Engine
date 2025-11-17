"""
Document Search Engine - Main Entry Point

This program builds a reverse index from HTML documents in a ZIP file
and provides a GUI for searching through them using various search methods:
- Single word search
- Phrase search ("quoted terms")
- Boolean operators (OR, AND, BUT)
- Vector space model (multi-word queries with cosine similarity)

Usage:
    python3 main.py [zip_file]

Arguments:
    zip_file: Optional path to ZIP file containing HTML documents.
              Defaults to "rhf.zip"
"""
import sys  # Access command line arguments
import time  # Measure total application startup time
import tkinter as tk  # Create the main application window
from gui import SearchGUI  # Main GUI class for the search interface
# Main entry point for the document search application
def main():
    zip_file = sys.argv[1] if len(sys.argv) > 1 else "rhf.zip"
    print("=" * 60)
    print("DOCUMENT SEARCH ENGINE")
    print("=" * 60)
    print(f"Data source: {zip_file}")
    print("=" * 60)
    print()
    root = tk.Tk()
    start_time = time.time()
    app = SearchGUI(root, zip_file=zip_file)
    elapsed_time = time.time() - start_time
    print()
    print("=" * 60)
    print(f"INDEXING COMPLETED IN {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    print("=" * 60)
    print()
    root.mainloop()
if __name__ == "__main__":
    main()
