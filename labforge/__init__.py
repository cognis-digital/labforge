"""labforge — homelab & dev-AI hardware toolkit: catalog, model-fit, compatibility
matrix, budget procurement planner, and interop with the Cognis suite + industry tools.
Helps developers build and scale a local AI / dev lab on real hardware."""
from .hardware import TOOL_NAME, TOOL_VERSION, Component, KINDS, catalog, get, add
from . import fit, compat, detect, procure, interop

__all__ = ["TOOL_NAME", "TOOL_VERSION", "Component", "KINDS", "catalog", "get", "add",
           "fit", "compat", "detect", "procure", "interop"]
