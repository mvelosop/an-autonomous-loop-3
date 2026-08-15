"""The empty-run half of the CLI's exit-code contract.

A malformed run is loud (loader.RunError, exit 2). A run directory that is
well-formed but has no session files is a different, quieter failure (exit
1) -- the two must not share an exception type or the exit codes collapse.
"""

from __future__ import annotations


class EmptyRunError(Exception):
    """Raised when a run directory is well-formed but has no session files."""
