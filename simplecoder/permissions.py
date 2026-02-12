"""
Permission management for file operations.

Asks user before doing potentially dangerous things like writing/editing files.
Supports session-level permissions (remember choice for the session).
"""

from typing import Dict, Set, Optional
from rich.prompt import Confirm
from rich.console import Console

console = Console()


class PermissionManager:
    """
    Manages user permissions for agent operations.
    """
    
    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.session_permissions: Dict[str, bool] = {}
        
        if auto_approve:
            console.print("[yellow] Auto-approve enabled - agent will not ask for permission [/yellow]")
    
    def request_permission(self, operation: str, filepath: Optional[str] = None) -> bool:
        """
        Request permission for an operation.

        Params:
            operation: type of operation (write_file, edit_file, etc.)
            filepath: path being operated on

        Returns:
            True if permission granted

        """

        # auto-approve if enabled
        if self.auto_approve:
            return True

        if operation in self.session_permissions:
            return self.session_permissions[operation]

        # build permission request to send back to the user
        message = f"Allow agent to [cyan]{operation}[/cyan]"
        if filepath:
            message += f" on [yellow]{filepath}[/yellow]"
        message += "?"
        
        console.print()
        approved = Confirm.ask(message, default=False)

        if approved:
            # ask if user wants session remembered
            remember = Confirm.ask(
                "Always allow this action for the session?",
                default=False
            )
            if remember:
                self.session_permissions[operation] = True
                console.print(f"[green]✓[/green] Will auto-approve [cyan]{operation}[/cyan] for this session")
        
        return approved
    
    def reset_session_permissions(self) -> None:
        self.session_permissions.clear()
        console.print(f"[yellow] Session Permissions cleared [/yellow]")