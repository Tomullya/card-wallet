"""Planted defects for QA demos (BUGGY_MODE=true only). See docs/qa/bug-reports BUG-17…19.

Never enabled unless the BUGGY_MODE environment variable is set to true.
"""

import os


def enabled(bug_id: str) -> bool:
    """True when planted defects are switched on. bug_id names the defect (BUG-17 …)."""
    return os.getenv("BUGGY_MODE", "").lower() == "true"
