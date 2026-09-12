"""Guards against `datetime.utcnow()` creeping back in — it's deprecated
since Python 3.12 and the repo standardizes on `core.timeutils.utc_now()`
instead (found via real dogfooding on Python 3.14, where it emits a
DeprecationWarning; see docs/autonomous-session-report.md)."""
import re
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src" / "research_os"


def test_no_source_file_calls_datetime_utcnow():
    offenders = []
    for path in SRC_DIR.rglob("*.py"):
        if path == SRC_DIR / "core" / "timeutils.py":
            continue  # only file allowed to mention it, in a docstring
        text = path.read_text(encoding="utf-8")
        if re.search(r"\.utcnow\(\)", text):
            offenders.append(str(path.relative_to(SRC_DIR)))
    assert not offenders, f"use research_os.core.timeutils.utc_now() instead: {offenders}"
