"""
RAG (Retrieval-Augmented Generation) for semantic code search.

Uses AST to chunk code by functions/classes, creates embeddings,
and enables fast semantic search over large codebases.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from rich.console import Console

console = Console()


class CodeRAG:
    """
    Handles semantic search over a codebase using embeddings.
    
    """
    
    def __init__(
        self,
        embedder: str = "all-MiniLM-L6-v2",
        index_pattern: str = "**/*.py"
    ):
        """
        Initialize the RAG system.
        
        Args:
            embedder: Sentence transformer model name
            index_pattern: Glob pattern for files to index
        """
        self.index_pattern = index_pattern
        self.chunks: List[Dict[str, Any]] = []
        
        # Initialize ChromaDB with embeddings
        self.client = chromadb.Client()
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedder
        )
        
        # Create or get collection
        try:
            self.collection = self.client.create_collection(
                name="code_chunks",
                embedding_function=self.embedding_function
            )
        except:
            # Collection already exists
            self.collection = self.client.get_collection(
                name="code_chunks",
                embedding_function=self.embedding_function
            )
        
        console.print(f"[green]✓ RAG initialized with embedder: {embedder}[/green]")
    
    def _chunk_python_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Chunk a Python file by functions and classes using AST.
        
        Params:
            filepath: Path to Python file
            
        Returns:
            List of code chunks with metadata

        """

        chunks = []
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    chunk = {
                        "type": "function",
                        "name": node.name,
                        "code": ast.get_source_segment(content, node),
                        "file": filepath,
                        "line": node.lineno
                    }
                    chunks.append(chunk)

                # extract classes
                elif isinstance(node, ast.ClassDef):
                    chunk = {
                        "type": "class",
                        "name": node.name,
                        "code": ast.get_source_segment(content, node),
                        "file": filepath,
                        "line": node.lineno
                    }
                    chunks.append(chunk)
        
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse {filepath}: {e}[/yellow]")
        
        return chunks
    
    def index_codebase(self, root_dir: str = ".") -> None:
        """
        Index all code files in the codebase.
        
        Params:
            root_dir: Root directory to start indexing from
        """
        console.print(f"[cyan]📚 Indexing codebase at: {root_dir}[/cyan]")
        
        path = Path(root_dir).resolve()
        all_chunks = []
        
        # Find all Python files
        python_files = list(path.glob(self.index_pattern))
        
        console.print(f"[dim]Found {len(python_files)} Python files[/dim]")
        
        # Chunk each file
        for py_file in python_files:
            # Skip venv, .git, etc.
            if any(skip in str(py_file) for skip in ['venv', '.venv', 'site-packages', '.git']):
                continue
            
            chunks = self._chunk_python_file(str(py_file))
            all_chunks.extend(chunks)
        
        if not all_chunks:
            console.print("[yellow] No code chunks found to index [/yellow]")
            return
        
        # Add to vector database
        documents = [chunk["code"] for chunk in all_chunks]
        metadatas = [
            {
                "file": chunk["file"],
                "type": chunk["type"],
                "name": chunk["name"],
                "line": str(chunk["line"])
            }
            for chunk in all_chunks
        ]
        ids = [f"chunk_{i}" for i in range(len(all_chunks))]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        self.chunks = all_chunks
        console.print(f"[green]✓ Indexed {len(all_chunks)} code chunks[/green]")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant code chunks.
        
        Params:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant code chunks with metadata
        """
        if not self.chunks:
            console.print("[yellow] No chunks indexed. Call index_codebase() first. [/yellow]")
            return []
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                "code": results['documents'][0][i],
                "file": results['metadatas'][0][i]['file'],
                "type": results['metadatas'][0][i]['type'],
                "name": results['metadatas'][0][i]['name'],
                "line": int(results['metadatas'][0][i]['line'])
            })
    
        console.print(f"[green]✓ Found {len(formatted_results)} relevant chunks[/green]")
        return formatted_results