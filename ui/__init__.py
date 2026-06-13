"""UI rendering modules for the Streamlit tabs.

Each tab has its own render_<tab> function for clean separation.
Reusable pieces live in components.py.
"""
from .dashboard import render_dashboard
from .trade import render_trade
from .history import render_history
from .ai_insights import render_ai_insights

__all__ = [
    "render_dashboard",
    "render_trade",
    "render_history",
    "render_ai_insights",
]
