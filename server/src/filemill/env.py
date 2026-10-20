"""Environment variables, with the pre-rebrand names still honoured.

This edition was called *pykofinder* before it became Filemill's server build.
A rename that silently stopped reading a running service's environment would be
a poor trade for a nicer prefix, so ``FILEMILL_ROOT`` wins and
``PYKOFINDER_ROOT`` still works. The fallback can go once nothing sets the old
names.

Its own module so that ``cli.py``, ``app.py`` and ``mutations.py`` share one
lookup. ``cli.py`` needs it at import time, because a Typer option default is
evaluated then.
"""

from __future__ import annotations

import os

LEGACY_PREFIX = "PYKOFINDER"


def env(name: str, default: str = "") -> str:
    """Return ``FILEMILL_<name>``, else ``PYKOFINDER_<name>``, else *default*."""
    return os.environ.get(f"FILEMILL_{name}") or os.environ.get(
        f"{LEGACY_PREFIX}_{name}", default
    )


def env_flag(name: str) -> bool:
    """True unless ``env(name)`` is empty, ``0``, ``false``, ``no`` or ``off``.

    Anything else turns the flag on, so a misspelt value fails closed.
    """
    return env(name).strip().lower() not in {"", "0", "false", "no", "off"}
