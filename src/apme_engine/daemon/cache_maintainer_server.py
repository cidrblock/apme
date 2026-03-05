"""Cache maintainer daemon: gRPC server that populates the collection cache (Galaxy + GitHub)."""

import os
from pathlib import Path

import grpc
from apme.v1 import cache_pb2, cache_pb2_grpc, common_pb2
from concurrent import futures

from apme_engine.collection_cache.config import get_cache_root
from apme_engine.collection_cache.manager import (
    pull_galaxy_collection,
    pull_galaxy_requirements,
    pull_github_org,
    pull_github_repos,
)


def _cache_root() -> Path:
    """Cache root: APME_CACHE_ROOT (container mount) or get_cache_root()."""
    root = os.environ.get("APME_CACHE_ROOT", "").strip()
    if root:
        return Path(root).resolve()
    return get_cache_root()


class CacheMaintainerServicer(cache_pb2_grpc.CacheMaintainerServicer):
    """Implements CacheMaintainer RPCs using collection_cache manager."""

    def PullGalaxy(self, request, context):
        try:
            path = pull_galaxy_collection(
                spec=request.spec or "",
                cache_root=_cache_root(),
                galaxy_server=request.galaxy_server or None,
            )
            return cache_pb2.PullGalaxyResponse(success=True, path=str(path))
        except Exception as e:
            return cache_pb2.PullGalaxyResponse(success=False, error_message=str(e))

    def PullRequirements(self, request, context):
        try:
            req_path = (request.requirements_path or "").strip()
            if not req_path:
                return cache_pb2.PullRequirementsResponse(
                    success=False, error_message="requirements_path is required"
                )
            paths = pull_galaxy_requirements(
                requirements_path=req_path,
                cache_root=_cache_root(),
                galaxy_server=request.galaxy_server or None,
            )
            return cache_pb2.PullRequirementsResponse(
                success=True, paths=[str(p) for p in paths]
            )
        except Exception as e:
            return cache_pb2.PullRequirementsResponse(
                success=False, error_message=str(e)
            )

    def CloneOrg(self, request, context):
        try:
            org = (request.org or "").strip()
            if not org:
                return cache_pb2.CloneOrgResponse(
                    success=False, error_message="org is required"
                )
            depth = request.depth if request.depth > 0 else 1
            token = (request.token or "").strip() or None
            cache = _cache_root()
            if request.repos:
                repo_list = [r for r in request.repos if (r or "").strip()]
                paths = pull_github_repos(
                    org=org,
                    repo_names=repo_list,
                    cache_root=cache,
                    clone_depth=depth,
                )
            else:
                if token:
                    os.environ["GITHUB_TOKEN"] = token
                try:
                    paths = pull_github_org(
                        org=org,
                        cache_root=cache,
                        clone_depth=depth,
                        token=token,
                    )
                finally:
                    if token and "GITHUB_TOKEN" in os.environ:
                        del os.environ["GITHUB_TOKEN"]
            return cache_pb2.CloneOrgResponse(
                success=True, paths=[str(p) for p in paths]
            )
        except Exception as e:
            return cache_pb2.CloneOrgResponse(success=False, error_message=str(e))

    def Health(self, request, context):
        return common_pb2.HealthResponse(status="ok")


def serve(listen: str = "0.0.0.0:50052"):
    """Create and return a gRPC server with CacheMaintainer servicer (caller must start it)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    cache_pb2_grpc.add_CacheMaintainerServicer_to_server(
        CacheMaintainerServicer(), server
    )
    if ":" in listen:
        _, _, port = listen.rpartition(":")
        server.add_insecure_port(f"[::]:{port}")
    else:
        server.add_insecure_port(listen)
    return server
