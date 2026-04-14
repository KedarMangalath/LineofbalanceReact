"""Compatibility shim for crewai.tools.BaseTool when crewai is not installed."""

try:
    from crewai.tools import BaseTool
except (ImportError, ModuleNotFoundError):
    from pydantic import BaseModel

    class BaseTool(BaseModel):
        """Minimal stand-in for crewai BaseTool."""
        name: str = ""
        description: str = ""

        def _run(self, *args, **kwargs):
            raise NotImplementedError
