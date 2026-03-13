"""Thread-local YAML loader/dumper with round-trip and retry support."""

from __future__ import annotations

import io
from contextvars import ContextVar
from typing import cast

from ruamel.yaml import YAML
from ruamel.yaml.emitter import EmitterError

from .models import YAMLValue

_yaml: ContextVar[YAML] = ContextVar("yaml")


def _set_yaml(force: bool = False) -> None:
    """Initialize or reset the thread-local YAML instance.

    Creates a round-trip YAML loader with preserve_quotes and allow_duplicate_keys.
    Used to work around ruamel.yaml multi-threading issues.

    Args:
        force: If True, replace existing instance even if one exists.
    """
    if not _yaml.get(None) or force:
        yaml = YAML(typ="rt", pure=True)
        yaml.default_flow_style = False
        yaml.preserve_quotes = True
        yaml.allow_duplicate_keys = True
        yaml.width = 1024
        _yaml.set(yaml)


def config(**kwargs: YAMLValue) -> None:
    """Configure the thread-local YAML instance with keyword arguments.

    Args:
        **kwargs: Attributes to set on the YAML instance (e.g. width, indent).
    """
    _set_yaml()
    yaml = _yaml.get()
    for key, value in kwargs.items():
        setattr(yaml, key, value)
    _yaml.set(yaml)


def indent(**kwargs: YAMLValue) -> None:
    """Configure indentation on the thread-local YAML instance.

    Args:
        **kwargs: Arguments passed to yaml.indent().
    """
    _set_yaml()
    yaml = _yaml.get()
    yaml.indent(**kwargs)
    _yaml.set(yaml)


def load(stream: object) -> YAMLValue | None:
    """Load YAML from a stream.

    Args:
        stream: Input stream (file-like or string).

    Returns:
        Parsed YAML value, or None for empty document.
    """
    _set_yaml()
    yaml = _yaml.get()
    result = yaml.load(stream)
    return cast(YAMLValue | None, result)


# `ruamel.yaml` has a bug around multi-threading, and its YAML() instance could be broken
# while concurrent dump() operation. So we try retrying if the specific error occurs.
# Bug details: https://sourceforge.net/p/ruamel-yaml/tickets/367/
def dump(data: YAMLValue) -> str:
    """Serialize data to YAML string with retry on EmitterError.

    Retries up to 2 times on EmitterError (ruamel.yaml multi-threading bug),
    forcing a fresh YAML instance on retry.

    Args:
        data: YAML-serializable data to dump.

    Returns:
        YAML string representation.

    Raises:
        EmitterError: If retries are exhausted (after 2 retries).
    """  # noqa: DOC503
    _set_yaml()
    retry = 2
    err = None
    result = None
    for i in range(retry):
        try:
            yaml = _yaml.get()
            output = io.StringIO()
            yaml.dump(data, output)
            result = output.getvalue()
        except EmitterError as exc:
            err = exc
        except Exception:
            raise
        if err:
            if i < retry - 1:
                _set_yaml(force=True)
                err = None
            else:
                raise err
        else:
            break
    return str(result) if result is not None else ""
