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

## Module Architecture

### agent.py - ReAct Loop Engine

Implements the core Reasoning-Acting-Observing cycle. The agent iteratively:
1. Reasons about what to do next (via LLM)
2. Acts by calling tools or providing answers
3. Observes tool results and decides next steps

Uses LiteLLM for unified LLM API access, supporting multiple providers. Includes error handling for rate limits and API failures.

### tools.py - Tool System

Provides 7 tools for file operations and information retrieval:
- **File ops**: list_files, read_file, write_file, edit_file, search_files
- **Search**: search_web (Tavily), search_codebase (RAG)

Each tool has: (1) implementation function, (2) JSON schema for LLM, (3) permission checks. The execute_tool dispatcher routes LLM requests to appropriate functions.

### permissions.py - Safety Layer

Implements permission system to prevent unwanted file modifications. Supports:
- Operation-level permissions (ask each time)
- Session-level permissions (remember for session)
- Auto-approve mode for non-interactive use

Designed to give users control while enabling efficient workflows.

### planner.py - Task Decomposition

Uses LLM to break complex tasks into 3-7 actionable subtasks. Tracks completion status and executes subtasks sequentially. 

Improved planning prompt ensures subtasks are independently executable and avoid unnecessary create-then-edit patterns. Combines related actions into single steps (e.g., "create file.py with content X" not "create file.py" then "add content").

### rag.py - Semantic Code Search

Enables fast semantic search over large codebases using:
1. **AST-based chunking**: Parses code by functions/classes (not arbitrary chunks)
2. **Embeddings**: Creates vector representations using sentence-transformers
3. **ChromaDB**: Vector database for similarity search

This allows finding relevant code by *purpose* rather than just filename matching.

### context.py - Token Management

Monitors conversation token usage and compacts history when approaching LLM limits (128k tokens). Strategy:
- Keep system prompt (instructions)
- Keep last N messages (continuity)
- Discard middle messages when over 80% threshold

Simple estimation: ~4 characters per token. Prevents API errors and reduces costs.

## Demo Project

[Include your demo description here after you build it]

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