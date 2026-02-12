"""
Task planning and decomposition.

Complex tasks benefit from being broken down into smaller subtasks.
For example: "Create a web server" could be broken into:
1. Create main.py file
2. Add route handlers
3. Add error handling
4. Create README
"""

from typing import List, Dict, Any
from litellm import completion
import json

from rich.console import Console

console = Console()

class TaskPlanner:
    
    def __init__(self, model: str = "gemini/gemini-3-flash-preview"):
        """
        Initialize the task planner.
        
        Params:
            model: LLM model to use for planning
        """

        self.model = model
        self.current_plan: List[Dict[str, Any]] = []

        console.print(f"[yellow][Planner] Initialized with model: {model}[/yellow]")



    def create_plan(self, task: str) -> List[Dict[str, Any]]:
        """
        Break down a task into subtasks.
        
        Args:
            task: High-level task description
            
        Returns:
            List of subtasks with metadata
        """

        console.print(f"[cyan]📋 Creating plan for:[/cyan] {task}")
        console.print("[dim]⏳ Asking LLM to break down task...[/dim]")
        
        prompt = f"""Break down this task into 3-7 clear, actionable subtasks.

                    Task: {task}

                    IMPORTANT: 
                    - Combine related actions into single steps (e.g., "Create file.py with content X" not "Create file.py" then "Add content")
                    - Each subtask should be independently executable
                    - Be specific about what content goes in each file

                    Return ONLY a JSON array of subtasks.
                    Example: ["Create app.py with Flask imports and routes", "Create test.py with print('test')"]

                    JSON array:
                """

        
        try:
            response = completion(
                model = self.model,
                messages = [{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content.strip()
            
            # parse JSON (remove markdown if present)
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            subtasks = json.loads(response_text)
            
            # Convert to structured format
            plan = []
            for i, subtask in enumerate(subtasks, 1):
                plan.append({
                    "id": i,
                    "description": subtask,
                    "status": "pending"
                })
            
            self.current_plan = plan
            
            # display plan
            console.print("\n[green]✓ Plan created:[/green]")
            for item in plan:
                console.print(f"  {item['id']}. {item['description']}")
            console.print()
            
            return plan
            
        except Exception as e:
            console.print(f"[red]Error creating plan:[/red] {str(e)}")
            # fallback: return single task
            return [{
                "id": 1,
                "description": task,
                "status": "pending"
            }]


    """
    Utility Methods

    """
    def get_next_subtask(self) -> Dict[str, Any] | None:
        for subtask in self.current_plan:
            if subtask["status"] == "pending":
                return subtask
        return None


    def mark_completed(self, subtask_id: int) -> None:
        """Mark a subtask as completed."""
        for subtask in self.current_plan:
            if subtask["id"] == subtask_id:
                subtask["status"] = "completed"
                console.print(f"[green]  ✓ Done[/green]")
                break


    def is_plan_complete(self) -> bool:
        """Check if all subtasks are completed."""
        return all(s["status"] == "completed" for s in self.current_plan)

