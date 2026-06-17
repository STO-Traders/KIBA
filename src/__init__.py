"""KIBA — an agentic AI coding platform for the terminal."""

__version__ = "1.2.3"
__author__ = "STO Algo LLC"

from .config import load_config, get_provider_config

try:  # pragma: no cover
    from .providers.base import BaseProvider
except Exception:  # pragma: no cover
    BaseProvider = None  # type: ignore[assignment]

__all__ = [
    "__version__",
    "__author__",
    "load_config",
    "get_provider_config",
    "BaseProvider",
]
