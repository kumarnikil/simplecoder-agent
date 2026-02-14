# SimpleCoder - AI Coding Agent

A ReAct-style CLI coding agent built for Dartmouth CS 189 (AI Agents). SimpleCoder helps you write code, navigate codebases, and complete software engineering tasks using planning, permissions, RAG, and web search.

## Features

- 🤖 **ReAct Loop**: Reasoning and Acting cycle for iterative task completion
- 🔧 **7 Tools**: File operations (list, read, write, edit, search) + web search + codebase search
- 🔒 **Permission System**: Ask before file modifications, session-level memory
- 📋 **Task Planning**: Break complex tasks into subtasks automatically
- 🔍 **RAG for Code**: Semantic search using AST-based chunking and embeddings
- 💬 **Context Management**: Stay within token limits with smart message compaction
- 🌐 **Web Search**: Get current information via Tavily API

## Installation
```bash
# Clone the repository
git clone https://github.com/kumarnikil/simplecoder-agent.git
cd simplecoder-agent

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .
```

## Setup

### Required API Keys
```bash
# Gemini (required)
export GEMINI_API_KEY="your-gemini-key-here"

# Tavily (optional, for web search)
export TAVILY_API_KEY="your-tavily-key-here"
```

## Usage

### Basic Usage
```bash
# Simple file creation
simplecoder "create hello.py that prints Hello World"

# With verbose output
simplecoder --verbose "create a calculator with add and subtract functions"
```

### Planning Mode
```bash
# Break complex tasks into subtasks
simplecoder --use-planning "create a Flask web server with home and about routes"
```

### RAG Mode
```bash
# Search codebase semantically
simplecoder --use-rag "find all permission-related functions"
```

### Interactive Mode
```bash
# Start a conversation
simplecoder --interactive
```

### Combined Features
```bash
# Planning + web search for current best practices
simplecoder --use-planning "search for Flask routing best practices, then create a demo app using those patterns"
```
---

## Implementation Approach

### agent.py - Main Agent Logic

Implements a ReAct (Reasoning + Acting) loop where the agent iteratively reasons about what to do next, executes tools, observes results, and decides on next steps. Uses LiteLLM for unified LLM API access across providers. The agent maintains conversation history and calls tools through a standardized JSON schema interface. Error handling includes retry logic for rate limits and clear user feedback. The loop continues until the agent provides a final answer or reaches max iterations.

### tools.py - Tool Functions and Schemas

Provides 7 tools for file operations and information retrieval: list_files, read_file, write_file, edit_file, search_files (filesystem operations), search_web (Tavily API), and search_codebase (RAG). Each tool has three components: (1) implementation function with error handling, (2) JSON schema defining parameters for the LLM, and (3) permission checks for write operations. The execute_tool dispatcher validates tool names and routes LLM requests to appropriate functions with type-safe argument passing.

### permissions.py - Permission Management

Implements a safety layer that asks users before file modifications. Supports two permission levels: operation-level (ask each time) and session-level (remember choice for current session). The request_permission method checks session memory first, then prompts if needed. This prevents unwanted file changes while enabling efficient workflows through session persistence. Auto-approve mode is available for non-interactive use cases.

### planner.py - Task Planning and Decomposition

Uses the LLM to break complex tasks into 3-7 actionable subtasks before execution. The create_plan method sends a structured prompt requesting JSON output of subtasks. Key improvement: the prompt explicitly instructs combining related actions (e.g., "create file.py with content X" not "create file.py" then "add content"), preventing unnecessary create-then-edit patterns. Tracks completion status and executes subtasks sequentially through the main ReAct loop.

### rag.py - Semantic Code Search

Enables fast semantic search over large codebases using three components: (1) AST-based chunking that parses Python files by functions and classes rather than arbitrary text chunks, (2) sentence-transformer embeddings that create vector representations of code, and (3) ChromaDB for similarity search. This allows finding code by purpose ("authentication logic") rather than just filename matching, making it far more useful than grep-style text search for understanding unfamiliar codebases.

### context.py - Context Management

Monitors conversation token usage and compacts history when approaching LLM context limits (128k tokens for Gemini). Uses a simple strategy: keep system prompt and last N messages (for continuity), discard middle messages when over 80% threshold. Token estimation uses ~4 characters per token heuristic. This prevents API errors from exceeding context windows and reduces costs by keeping conversations within reasonable bounds during long iterative sessions.

---

## Demo Project

[\[Demo\]](https://youtu.be/pcr_TaaWNek)

## Requirements

- Python 3.10+
- Gemini API key (free tier works)
- Tavily API key (optional, for web search)

## Dependencies

See `pyproject.toml` for full list:
- litellm (LLM API)
- rich (CLI formatting)
- click (CLI framework)
- tavily-python (web search)
- chromadb (vector storage)
- sentence-transformers (embeddings)

## Assignment Context

Built for Dartmouth College CS 189: AI Agents (Winter 2026)
Problem Set 1, Part III

**Author**: Nikil SENTHL KUMAR
**Date**: February 2026