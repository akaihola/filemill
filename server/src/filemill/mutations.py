"""Browser mutation policy. See ADR 0081 for the same-origin trust boundary."""

import secrets
from urllib.parse import urlsplit

from filemill.env import env


def _origin(value: str) -> tuple[str, str, int] | None:
    try:
        parts = urlsplit(value)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or parts.path
            or parts.query
            or parts.fragment
        ):
            return None
        return (
            parts.scheme,
            parts.hostname,
            parts.port
            if parts.port is not None
            else (443 if parts.scheme == "https" else 80),
        )
    except ValueError:
        return None


def authorized(request) -> bool:
    # Reject ambiguous duplicate headers instead of depending on proxy ordering.
    if any(
        len(request.headers.getlist(name)) != 1
        for name in ("origin", "host", "x-filemill-token")
    ):
        return False
    origin = _origin(request.headers["origin"])
    if origin is None or _origin(f"{origin[0]}://{request.headers['host']}") != origin:
        return False
    configured = {_origin(value) for value in env("ORIGINS").split()}
    local = (
        origin[1] in {"127.0.0.1", "localhost", "::1"}
        and origin[0] == request.url.scheme
    )
    if not local and origin not in configured:
        return False
    token = request.headers["x-filemill-token"]
    return token.isascii() and secrets.compare_digest(
        token, request.app.state.mutation_token
    )
