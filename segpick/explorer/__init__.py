"""
Explorer layer.

Provides the stable public API used by dashboard, CLI, reports and future
LLM integrations to interrogate the reasoning graph.
"""

from .explorer import ReasoningExplorer

__all__ = ["ReasoningExplorer"]
