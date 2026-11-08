"""Planted defects for QA demos (BUGGY_MODE=true only). See docs/qa/bug-reports.

Each defect is a small branch next to the correct code, marked with its bug ID.
Never enabled unless the BUGGY_MODE environment variable is set to true.
"""

from app.config import get_settings


def enabled(bug_id: str) -> bool:
    """True when planted defects are switched on. bug_id names the defect (BUG-01 …)."""
    return get_settings().buggy_mode
