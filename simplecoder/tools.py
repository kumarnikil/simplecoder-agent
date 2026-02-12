"""
Tools for the SimpleCoder.

Details: Strict functions exposed to Agent to interact with internal files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from simplecoder.permissions import PermissionManager
from simplecoder.rag import CodeRAG

from tavily import TavilyClient

"""
GLOBAL Permissions Manager

"""
_permission_manager: Optional[PermissionManager] = None

def set_permission_manager(pm : PermissionManager) -> None:
    global _permission_manager
    _permission_manager = pm

"""
GLOBAL RAG Instance

"""

_rag_instance: Optional[CodeRAG] = None

def set_rag_instance(rag: CodeRAG) -> None:
    """Set the global RAG instance."""
    global _rag_instance
    _rag_instance = rag

"""
TOOL FUNCTION LOGIC

"""

def list_files(directory: str = ".") -> str:
    try:
        path = Path(directory).resolve()
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist!"

        if not path.is_dir():
            return f"Error: Directory '{directory}' is not directory!"

        # get all items, separate files and directories
        items = []
        for item in sorted(path.iterdir()):
            if item.is_dir():
                items.append(f"{item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"{item.name} ({size} bytes)")
        
        if not items:
            return f"Directory '{directory}' is empty"
        
        return f"Contents of '{directory}':\n" + "\n".join(items)

    except Exception as e:
        return f"Error listing directory: {str(e)}"


def read_file(filepath: str) -> str:
    try:
        path = Path(filepath).resolve()
        
        if not path.exists():
            return f"Error: File '{filepath}' does not exist"
        
        if not path.is_file():
            return f"Error: '{filepath}' is not a file"
        
        # Read file contents
        content = path.read_text()

        # Add line numbers to content
        lines = content.split("\n")
        numbered = [f"{i+1} | {line}" for i, line in enumerate(lines)]

        return f"Contents of '{filepath}':\n" +  "\n".join(numbered)         

    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(filepath: str, content: str) -> str:
    # check permission first (TODO: move logic to seperate function for code cleanliness)
    if _permission_manager:
        if not _permission_manager.request_permission(
            operation = "write_file",
            filepath = filepath
        ):
            return f"Permission denied: Cannot write to '{filepath}'"
    
    try:
        path = Path(filepath).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)  # create parent directories if they don't exist
        
        path.write_text(content)
        
        return f"Wrote {len(content)} characters to '{filepath}'"
    
    except Exception as e:
        return f"Error writing file: {str(e)}"


def search_files(pattern: str, directory: str) -> str:
    try:
        path = Path(directory).resolve()
        
        if not path.exists():
            return f"Error: Directory '{directory}' does not exist"

        matches = list(path.glob(pattern)) # list of files that matches pattern

        if not matches:
            return f"No files matching '{pattern}' found in '{directory}'"

        results = [str(m.relative_to(path)) for m in matches if m.is_file()]

        return f"Found {len(results)} file(s) matching pattern '{pattern}':\n" + "\n".join(f" -- {r}" for r in results)

    except Exception as e:
        return f"Error searching files: {str(e)}"


def edit_file(filepath: str, old_text: str, new_text: str) -> str:
    # check permission first (TODO: move logic to seperate function for code cleanliness)
    if _permission_manager:
        if not _permission_manager.request_permission(
            operation = "edit_file",
            filepath = filepath
        ):
            return f"Permission denied: Cannot edit '{filepath}'"
    
    try:
        path = Path(filepath).resolve()
        
        if not path.exists():
            return f"Error: File '{filepath}' does not exist"
        
        content = path.read_text()
        
        if old_text not in content:
            return f"Error: Could not find the text to replace in '{filepath}'"
        
        new_content = content.replace(old_text, new_text)
        path.write_text(new_content)
        
        return f"Successfully edited '{filepath}'"
    
    except Exception as e:
        return f"Error editing file: {str(e)}"


def search_codebase(query: str, max_results: int = 5) -> str:
    """
    Search the codebase semantically using RAG.
    Finds functions/classes by what they DO, not just filename.
    """
    if not _rag_instance:
        return "Error: RAG not initialized. Use --use-rag flag to enable codebase search."
    
    try:
        results = _rag_instance.search(query, top_k=max_results)
        
        if not results:
            return f"No code found matching: {query}"
        
        # Format results
        formatted = [f"Semantic search results for '{query}':\n"]
        for i, result in enumerate(results, 1):
            formatted.append(
                f"\n{i}. {result['type'].upper()}: {result['name']}\n"
                f"   File: {result['file']}:{result['line']}\n"
                f"   Code preview:\n{result['code'][:300]}...\n"
            )
        
        return "\n".join(formatted)
    
    except Exception as e:
        return f"Error searching codebase: {str(e)}"


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily for up-to-date information.
    
    """
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Error: TAVILY_API_KEY not set. Set it with: export TAVILY_API_KEY=<your-api-key>"
                
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=max_results)
        
        # result formatting
        if not response.get('results'):
            return f"No results found for: {query}"
    

        results = []
        for i, result in enumerate(response['results'][:max_results], 1):
            results.append(
                f"{i}. {result['title']}\n"
                f"   URL: {result['url']}\n"
                f"   {result['content'][:200]}..."
            )
        
        return f"Web search results for '{query}':\n\n" + "\n\n".join(results)
    
    except Exception as e:
        return f"Error searching web: {str(e)}"

"""
TOOL SCHEMAS

"""

TOOLS = [
    {
        "name": "list_files",
        "description": "List all files and directories in a given directory. Use this to explore the codebase structure.",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "The directory path to list (default: current directory)"
                }
            },
            "required": []
        }
    },
    {
        "name": "read_file",
        "description": "Read the complete contents of a file. Use this to understand existing code or check what's in a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the file to read"
                }
            },
            "required": ["filepath"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file. This will create a new file or completely overwrite an existing file. Use this for creating new files.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file"
                }
            },
            "required": ["filepath", "content"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files matching a pattern. Use glob patterns like '*.py' for Python files or '**/*.txt' for all text files recursively.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match files (e.g., '*.py', '**/*.txt')"
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)"
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "edit_file",
        "description": "Edit an existing file by replacing specific text. Use this to make targeted changes to existing files.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "The path to the file to edit"
                },
                "old_text": {
                    "type": "string",
                    "description": "The exact text to find and replace"
                },
                "new_text": {
                    "type": "string",
                    "description": "The text to replace with"
                }
            },
            "required": ["filepath", "old_text", "new_text"]
        }
    },
    {
        "name": "search_codebase",
        "description": "Semantically search the codebase for functions, classes, or code by PURPOSE. Use this to find code by what it DOES (e.g., 'authentication logic', 'database queries'), not by filename.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What you're looking for (e.g., 'permission checking functions', 'file writing code')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for current information, documentation, tutorials, or best practices. Use this when you need up-to-date information not in your training data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g., 'Python async best practices 2025')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5)"
                }
            },
            "required": ["query"]
        }
    }
]


"""
TOOL EXECUTOR - maps tools to respective function logic

"""

TOOL_FUNCTIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "search_files": search_files,
    "edit_file": edit_file,
    "search_codebase": search_codebase,
    "search_web": search_web
}

def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    if tool_name not in TOOL_FUNCTIONS:
        return f"Error: Unknown tool '{tool_name}'"
    
    try:
        func = TOOL_FUNCTIONS[tool_name]
        result = func(**tool_args)
        return result
    except TypeError as e:
        return f"Error: Invalid arguments for tool '{tool_name}': {str(e)}"
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"


# compilation testing 
# if __name__ == "__main__":
#     print(execute_tool("list_files", {"dir": "."}))
#     print("\n")
#     print(execute_tool("write_file", {"filepath": "test.txt", "text": "Hello!"}))
#     print(execute_tool("read_file", {"filepath": "test.txt"}))
