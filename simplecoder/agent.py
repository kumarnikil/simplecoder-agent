# take user input, think about what to do (ReAct framework), call tools, make sense of tool reponses and generate intermediate answers, return final answer

"""
The main Agent that orchestrates everything.

This implements a ReAct (Reasoning + Acting) loop:
1. Think: Agent reasons about what to do next
2. Act: Agent calls a tool or gives final answer
3. Observe: Agent sees the result of the action
4. Repeat until task is complete

"""

import json
import os
from typing import List, Dict, Any
from rich.console import Console
from rich.panel import Panel

from litellm import completion

from simplecoder.tools import TOOLS, execute_tool, set_permission_manager
from simplecoder.permissions import PermissionManager
from simplecoder.planner import TaskPlanner
from simplecoder.context import ContextManager

console = Console()

class Agent:
    """
    A ReAct-style coding agent that can use tools to complete tasks.
    """

    SYSTEM_PROMPT = """
                    You are SimpleCoder, a helpful coding assistant that can help users with programming tasks.

                    You have access to tools that let you interact with the filesystem:
                    - list_files: See what files and directories exist
                    - read_file: Read the contents of a file
                    - write_file: Create or overwrite a file
                    - edit_file: Make targeted edits to existing files
                    - search_files: Find files matching a pattern
                    - search_web: Search the internet for current information
                    - search_codebase: SEMANTIC search - use this to find code by PURPOSE not filename (e.g., "find authentication code", "locate database functions")

                    
                    IMPORTANT TOOL USAGE:
                    - Use search_codebase when you need to find code by what it DOES
                    - Use search_files when you need to find files by NAME or pattern
                    - Use read_file when you know the exact file to read
                    
                    How to use these tools:
                    1. When you need to do something (like check what files exist, or create a file), use a tool
                    2. After using a tool, you'll see the result and can decide what to do next
                    3. You can use multiple tools in sequence to complete complex tasks
                    4. When you're done with the task, respond with your final answer (without calling any tools)

                    IMPORTANT:
                    - Always read files before editing them to understand their current content
                    - Use list_files to explore the directory structure first
                    - Break complex tasks into smaller steps
                    - Be thorough and check your work

                    When you're completely done with the task, produce a final clear and consise response summarizing what you did.
                    
                    """
    
    def __init__(
        self,
        model: str = "gemini/gemini-3-flash-preview",
        max_iterations: int = 10,
        verbose: bool = False,
        use_planning: bool = False,
        use_rag: bool = False,
        rag_embedder: str = "text-embedding-004",
        rag_index_pattern: str = "**/*.py"
    ):
        """
        Initialize the agent.
        
        Params:
            model: LLM model to use
            max_iterations: Max number of ReAct iterations
            verbose: Print detailed debug info?
            use_planning: Use task planning?
            use_rag: Use RAG for code search? 
            rag_embedder: Embedding model for RAG
            rag_index_pattern: File pattern to index for RAG

        """
        
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.use_planning = use_planning
        self.use_rag = use_rag
        self.context_manager = ContextManager(max_tokens=128000, keep_last_n=10, verbose=self.verbose)

        # conversation history between LLM
        self.messages: List[Dict[str, str]] = []
        
        # check for API key
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it with: export GEMINI_API_KEY='your-key-here'"
            )

        self.permission_manager = PermissionManager(auto_approve=False)
        set_permission_manager(self.permission_manager)

        if self.verbose:
            console.print("[yellow]Permission system initialized[/yellow]")
            console.print(f"[yellow]Agent initialized[/yellow]")
            console.print(f"Model: {model}")
            console.print(f"Max iterations: {max_iterations}")

        self.planner = TaskPlanner(model = self.model) if self.use_planning else None


    def run(self, task: str) -> str:
        """
        Run Agent based on ReAct (Reasoning + Act) framework.
        Optionally uses planning to break down complex tasks.
        
        Args:
            Task description directly from user

        Returns:
            Final response back to user
        """
        if self.verbose:
            console.print(f"\n[bold cyan]Starting task:[/bold cyan] {task}")
        
        # If planning enabled, break down task first
        if self.use_planning and self.planner:
            plan = self.planner.create_plan(task)
            
            # Execute each subtask
            for subtask in plan:

                # Run ReAct loop on this subtask
                self._execute_subtask(subtask['description'])
                
                # Mark as completed
                self.planner.mark_completed(subtask['id'])
            
            # All subtasks done
            return "✓ All subtasks completed! Task finished successfully."
        
        else:
            return self._execute_subtask(task)


    def _execute_subtask(self, task: str) -> str:
        """
        Execute a single task/subtask using ReAct loop.
        
        Args:
            task: Task or subtask description
            
        Returns:
            Result of execution
        """

        # shows what's being worked on
        if not self.verbose:
            task_preview = task[:60] + "..." if len(task) > 60 else task
            console.print(f"[cyan]⚙️  {task_preview}[/cyan]")


        # Initialize conversation with system prompt and task
        self.messages = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            },
            {
                "role": "user",
                "content": task
            }
        ]
        
        # ReAct loop: iterate until max iterations or final answer
        for iteration in range(self.max_iterations):
            if self.verbose:
                console.print(f"\n[yellow]--- Iteration {iteration + 1}/{self.max_iterations} ---[/yellow]")

            # Check context to compact message if needed
            if self.context_manager.should_compact(self.messages):
                self.messages = self.context_manager.compact_messages(self.messages)
            
            response = self._call_llm()
            
            # Check if the agent wants to use a tool
            if response.get("tool_calls"):
                tool_call = response["tool_calls"][0] 
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                
                if self.verbose:
                    console.print(f"[blue]Tool:[/blue] {tool_name}")
                    console.print(f"[blue]Args:[/blue] {tool_args}")
                
                # Execute the tool
                tool_result = execute_tool(tool_name, tool_args)
                
                if self.verbose:
                    console.print(f"[green]Result:[/green] {tool_result[:200]}...")
                
                # Add to conversation
                self.messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call]
                })
                self.messages.append({
                    "role": "tool",
                    "content": tool_result,
                    "tool_call_id": tool_call["id"]
                })
                
                continue
            
            # No tool call = final answer
            final_answer = response.get("content", "")
            
            if self.verbose:
                console.print(f"[green]Final answer:[/green] {final_answer}")
            
            return final_answer
        
        return "Reached maximum iterations for this subtask."

     
    """
        Internal Methods
    """

    def _get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT


    def _call_llm(self) -> Dict[str, Any]:
        """
        Call the LLM to get the next action.
        
        Returns:
            Dictionary containing the LLM response
        """


        try: 
            response = completion(
                model=self.model,
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto"
            )

            # Extract the message from the response
            message = response.choices[0].message
            
            # Convert to dictionary format
            result = {
                "content": message.content,
                "tool_calls": []
            }
            
            # Add tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            if self.verbose:
                console.print(f"[dim]LLM response: {result}[/dim]")
            
            return result
            
        except Exception as e:
            console.print(f"\n[red]❌ Error calling LLM:[/red] {str(e)}")
            console.print("[yellow]💡 Please try again in a few moments[/yellow]")

            if self.verbose:
                import traceback
                traceback.print_exc()   

            raise
