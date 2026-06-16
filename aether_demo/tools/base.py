from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel

class BaseSchema(BaseModel):
    """Base class for all tool schemas."""
    pass

def ask_confirmation(action_description: str) -> bool:
    """Prompts the user to confirm a destructive or write action."""
    print(f"Confirm: {action_description}")
    answer = input("Proceed? (yes/no): ").strip().lower()
    return answer in ("yes", "y")

class BaseTool(ABC):
    name: str
    description: str
    example_queries: list[str]
    schema_class: type[BaseSchema]
    safety_level: Literal["auto", "confirm"]

    @abstractmethod
    def extract(self, query: str) -> dict:
        """Extracts parameters from a query. Raises ValueError if ambiguous/incomplete."""
        pass

    @abstractmethod
    def execute(self, params: BaseSchema) -> str:
        """Executes the tool with the validated parameters and returns a human-readable result."""
        pass

    def get_action_description(self, params: BaseSchema) -> str:
        """Returns a human-readable description of the action to be confirmed."""
        return f"{self.name} with params {params.dict()}"

    def run(self, query: str) -> str:
        """Orchestrates the entire tool execution flow."""
        try:
            params_dict = self.extract(query)
        except ValueError as e:
            return f"Error: {e}"

        try:
            # Support Pydantic model validation
            params = self.schema_class(**params_dict)
        except Exception as e:
            return f"Validation error: {e}"

        if self.safety_level == "confirm":
            action_desc = self.get_action_description(params)
            # Make sure to print 'Are you sure? (yes/no)' as specified under Safety section:
            # "Confirm prompt: print 'Are you sure? (yes/no)' before executing"
            # And under CONFIRMATION PROMPT:
            # "def ask_confirmation(action_description: str) -> bool:
            #      print(f"Confirm: {action_description}")
            #      answer = input("Proceed? (yes/no): ").strip().lower()
            #      return answer in ("yes", "y")"
            # Let's combine both or match the CONFIRMATION PROMPT signature:
            if not ask_confirmation(action_desc):
                return "Action cancelled by user."

        try:
            return self.execute(params)
        except Exception as e:
            return f"Error executing {self.name}: {e}"
