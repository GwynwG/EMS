"""Namespace bridge that lets desktop overrides coexist with the web src package."""
from __future__ import annotations

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
