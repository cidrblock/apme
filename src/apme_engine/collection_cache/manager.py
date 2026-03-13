"""Populate and query the collection cache (Galaxy + GitHub)."""

import subprocess
from pathlib import Path

from apme_engine.collection_cache.config import (
    galaxy_cache_dir,
    get_cache_root,
    github_cache_dir,
)


def pull_galaxy_collection(
    spec: str,
    cache_root: Path | None = None,
    galaxy_server: str | None = None,
) -> Path:
    """Install a Galaxy collection into the cache via ansible-galaxy.

    Args:
        spec: Collection specifier, e.g. "namespace.collection" or "namespace.collection:1.2.3".
        cache_root: Cache root; uses get_cache_root() if None.
        galaxy_server: Optional Galaxy server URL.

    Returns:
        Path to the installed collection (cache_root/galaxy/ansible_collections/namespace/collection/).

    """
    root = cache_root or get_cache_root()
    target = galaxy_cache_dir(root)
    target.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ansible-galaxy",
        "collection",
        "install",
        spec,
        "-p",
        str(target),
        "--force",
    ]
    if galaxy_server:
        cmd.extend(["--server", galaxy_server])
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    # Resolve path: target is the -p dir, galaxy installs to target/ansible_collections/ns/coll/
    namespace, collection = _parse_collection_spec(spec)
    return target / "ansible_collections" / namespace / collection


def pull_galaxy_requirements(
    requirements_path: str | Path,
    cache_root: Path | None = None,
    galaxy_server: str | None = None,
) -> list[Path]:
    """Install collections from a requirements.yml into the cache.

    Args:
        requirements_path: Path to requirements.yml (collections list).
        cache_root: Cache root; uses get_cache_root() if None.
        galaxy_server: Optional Galaxy server URL.

    Returns:
        List of paths to installed collections (one per collection in the file).

    Raises:
        FileNotFoundError: If requirements_path does not exist.
        RuntimeError: If ansible-galaxy install fails.
    """
    root = cache_root or get_cache_root()
    target = galaxy_cache_dir(root)
    target.mkdir(parents=True, exist_ok=True)
    req_path = Path(requirements_path).resolve()
    if not req_path.is_file():
        raise FileNotFoundError(f"Requirements file not found: {requirements_path}")
    cmd = [
        "ansible-galaxy",
        "collection",
        "install",
        "-r",
        str(req_path),
        "-p",
        str(target),
        "--force",
    ]
    if galaxy_server:
        cmd.extend(["--server", galaxy_server])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ansible-galaxy install failed: {result.stderr or result.stdout}")
    # List installed: target/ansible_collections/namespace/collection/
    installed = []
    ac = target / "ansible_collections"
    if ac.is_dir():
        for ns in ac.iterdir():
            if ns.is_dir():
                for coll in ns.iterdir():
                    if coll.is_dir():
                        installed.append(coll)
    return installed


def _parse_collection_spec(spec: str) -> tuple[str, str]:
    """Return (namespace, collection) from 'namespace.collection' or 'namespace.collection:version'.

    Args:
        spec: Collection specifier string (e.g. namespace.collection or namespace.collection:version).

    Returns:
        Tuple of (namespace, collection).

    Raises:
        ValueError: If spec does not contain a dot (expected namespace.collection).
    """
    spec = spec.split(":")[0].strip()
    if "." not in spec:
        raise ValueError(f"Invalid collection spec (expected namespace.collection): {spec}")
    parts = spec.split(".")
    return parts[0], parts[1]


def pull_github_org(
    org: str,
    cache_root: Path | None = None,
    clone_depth: int | None = 1,
    token: str | None = None,
) -> list[Path]:
    """Clone GitHub org repos that look like Ansible collections into the cache.

    Uses the GitHub API to list org repos (requires network). Repos are considered
    collections if they contain galaxy.yml or meta/runtime.yml at the root.

    Args:
        org: GitHub organization name (e.g. "redhat-cop").
        cache_root: Cache root; uses get_cache_root() if None.
        clone_depth: Git clone depth (1 for shallow). None for full clone.
        token: Optional GitHub token for API (env GITHUB_TOKEN used if not set).

    Returns:
        List of paths to cloned repo roots (cache_root/github/org/repo_name/).

    """
    root = cache_root or get_cache_root()
    base = github_cache_dir(root) / org
    base.mkdir(parents=True, exist_ok=True)
    token = token or __import__("os").environ.get("GITHUB_TOKEN", "")
    repos = _list_org_repos(org, token)
    cloned = []
    for repo_name in repos:
        dest = base / repo_name
        if dest.is_dir():
            # Already cloned; could pull --rebase or skip
            if (dest / "galaxy.yml").is_file() or (dest / "meta" / "runtime.yml").is_file():
                cloned.append(dest)
            continue
        url = f"https://github.com/{org}/{repo_name}.git"
        cmd = ["git", "clone", url, str(dest)]
        if clone_depth is not None:
            cmd.extend(["--depth", str(clone_depth)])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            continue
        if (dest / "galaxy.yml").is_file() or (dest / "meta" / "runtime.yml").is_file():
            cloned.append(dest)
    return cloned


def pull_github_repos(
    org: str,
    repo_names: list[str],
    cache_root: Path | None = None,
    clone_depth: int | None = 1,
) -> list[Path]:
    """Clone specific GitHub org repos into the cache (no API needed).

    Args:
        org: GitHub organization name (e.g. "redhat-cop").
        repo_names: List of repository names to clone.
        cache_root: Cache root; uses get_cache_root() if None.
        clone_depth: Git clone depth (1 for shallow). None for full clone.

    Returns:
        List of paths to cloned repo roots.

    """
    root = cache_root or get_cache_root()
    base = github_cache_dir(root) / org
    base.mkdir(parents=True, exist_ok=True)
    cloned = []
    for repo_name in repo_names:
        dest = base / repo_name
        if dest.is_dir():
            cloned.append(dest)
            continue
        url = f"https://github.com/{org}/{repo_name}.git"
        cmd = ["git", "clone", url, str(dest)]
        if clone_depth is not None:
            cmd.extend(["--depth", str(clone_depth)])
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            cloned.append(dest)
    return cloned


def _list_org_repos(org: str, token: str) -> list[str]:
    """List public repo names for a GitHub org via API. Returns empty list on error.

    Args:
        org: GitHub organization name.
        token: Optional GitHub token for API authentication.

    Returns:
        List of non-archived public repo names, or empty list on error.
    """
    try:
        import json
        import urllib.request

        url = f"https://api.github.com/orgs/{org}/repos?per_page=100"
        req = urllib.request.Request(url)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return [r["name"] for r in data if not r.get("archived", False)]
    except Exception:
        return []


def collection_path_in_cache(
    namespace: str,
    collection: str,
    cache_root: Path | None = None,
    source: str = "galaxy",
) -> Path | None:
    """Return the path to a collection in the cache if present.

    Args:
        namespace: Collection namespace.
        collection: Collection name.
        cache_root: Cache root; uses get_cache_root() if None.
        source: "galaxy" or "github". For github, we scan github/org/repo for
                repos whose galaxy.yml or meta/runtime.yml declares this namespace.collection.

    Returns:
        Path to the collection root, or None if not found.

    """
    root = cache_root or get_cache_root()
    if source == "galaxy":
        path = galaxy_cache_dir(root) / "ansible_collections" / namespace / collection
        return path if path.is_dir() else None
    if source == "github":
        github_dir = github_cache_dir(root)
        for org_dir in github_dir.iterdir():
            if not org_dir.is_dir():
                continue
            for repo_dir in org_dir.iterdir():
                if not repo_dir.is_dir():
                    continue
                # Check if this repo is namespace.collection (galaxy.yml or meta/runtime.yml)
                galaxy_yml = repo_dir / "galaxy.yml"
                if galaxy_yml.is_file():
                    try:
                        import yaml

                        with open(galaxy_yml) as f:
                            meta = yaml.safe_load(f)
                        if meta:
                            n = meta.get("namespace") or meta.get("name", "").split(".")[0]
                            c = (
                                meta.get("name", "").split(".")[-1]
                                if "." in meta.get("name", "")
                                else meta.get("name", "")
                            )
                            if n == namespace and c == collection:
                                return repo_dir
                    except Exception:
                        pass
                runtime = repo_dir / "meta" / "runtime.yml"
                if runtime.is_file():
                    try:
                        import yaml

                        with open(runtime) as f:
                            meta = yaml.safe_load(f)
                        if meta:
                            full = (meta.get("galaxy_info") or {}).get("collection_name") or ""
                            if full == f"{namespace}.{collection}":
                                return repo_dir
                    except Exception:
                        pass
    return None
