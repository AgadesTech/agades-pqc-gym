import os

# CLI output is rendered with Rich. Without a terminal, Rich wraps at 80
# columns, which splits the messages that CLI tests match on. Pin a wide
# console so results do not depend on where the suite runs.
os.environ.setdefault("COLUMNS", "200")
