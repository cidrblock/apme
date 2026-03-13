"""Configuration for the collection cache."""

import os
from pathlib import Path


def get_cache_root() -> Path:
    """Return the collection cache root directory (e.g. ~/.apme-data/collection-cache).

    Returns:
        Path to the collection cache root directory.
    """
    base = os.environ.get("APME_COLLECTION_CACHE", "").strip()
    if base:
        return Path(base).expanduser().resolve()
    return Path(os.path.expanduser("~/.apme-data/collection-cache")).resolve()


def galaxy_cache_dir(cache_root: Path) -> Path:
    """Path where Galaxy collections are installed (ansible_collections under this).

    Args:
        cache_root: Root directory for the collection cache.

    Returns:
        Path to the galaxy cache directory.
    """
    d = cache_root / "galaxy"
    d.mkdir(parents=True, exist_ok=True)
    return d


def github_cache_dir(cache_root: Path) -> Path:
    """Path where GitHub org clones live (e.g. redhat-cop/infra.aap_configuration).

    Args:
        cache_root: Root directory for the collection cache.

    Returns:
        Path to the GitHub cache directory.
    """
    d = cache_root / "github"
    d.mkdir(parents=True, exist_ok=True)
    return d
