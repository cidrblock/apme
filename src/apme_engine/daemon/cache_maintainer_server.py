"""Cache maintainer daemon: gRPC server that populates the collection cache (Galaxy + GitHub)."""

import os
from concurrent import futures
from pathlib import Path

import grpc

from apme.v1 import cache_pb2_grpc, common_pb2
from apme.v1.cache_pb2 import (
    CloneOrgRequest,
    CloneOrgResponse,
    PullGalaxyRequest,
    PullGalaxyResponse,
    PullRequirementsRequest,
    PullRequirementsResponse,
)
from apme.v1.common_pb2 import HealthResponse
from apme_engine.collection_cache.config import get_cache_root
from apme_engine.collection_cache.manager import (
    pull_galaxy_collection,
    pull_galaxy_requirements,
    pull_github_org,
    pull_github_repos,
)


def _cache_root() -> Path:
    """Cache root: APME_CACHE_ROOT (container mount) or get_cache_root().

    Returns:
        Resolved Path to the collection cache root.
    """
    root = os.environ.get("APME_CACHE_ROOT", "").strip()
    if root:
        return Path(root).resolve()
    return get_cache_root()


class CacheMaintainerServicer(cache_pb2_grpc.CacheMaintainerServicer):
    """Implements CacheMaintainer RPCs using collection_cache manager."""

    def PullGalaxy(self, request: PullGalaxyRequest, context: grpc.ServicerContext) -> PullGalaxyResponse:
        """Handle PullGalaxy RPC: pull a single collection from Galaxy.

        Args:
            request: PullGalaxyRequest with spec and optional galaxy_server.
            context: gRPC servicer context.

        Returns:
            PullGalaxyResponse with success flag and path or error_message.
        """
        try:
            path = pull_galaxy_collection(
                spec=request.spec or "",
                cache_root=_cache_root(),
                galaxy_server=request.galaxy_server or None,
            )
            return PullGalaxyResponse(success=True, path=str(path))
        except Exception as e:
            return PullGalaxyResponse(success=False, error_message=str(e))

    def PullRequirements(
        self, request: PullRequirementsRequest, context: grpc.ServicerContext
    ) -> PullRequirementsResponse:
        """Handle PullRequirements RPC: pull collections from a requirements file.

        Args:
            request: PullRequirementsRequest with requirements_path.
            context: gRPC servicer context.

        Returns:
            PullRequirementsResponse with success flag and paths or error_message.
        """
        try:
            req_path = (request.requirements_path or "").strip()
            if not req_path:
                return PullRequirementsResponse(success=False, error_message="requirements_path is required")
            paths = pull_galaxy_requirements(
                requirements_path=req_path,
                cache_root=_cache_root(),
                galaxy_server=request.galaxy_server or None,
            )
            return PullRequirementsResponse(success=True, paths=[str(p) for p in paths])
        except Exception as e:
            return PullRequirementsResponse(success=False, error_message=str(e))

    def CloneOrg(self, request: CloneOrgRequest, context: grpc.ServicerContext) -> CloneOrgResponse:
        """Handle CloneOrg RPC: clone GitHub org or specified repos.

        Args:
            request: CloneOrgRequest with org, optional repos, depth, token.
            context: gRPC servicer context.

        Returns:
            CloneOrgResponse with success flag and paths or error_message.
        """
        try:
            org = (request.org or "").strip()
            if not org:
                return CloneOrgResponse(success=False, error_message="org is required")
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
            return CloneOrgResponse(success=True, paths=[str(p) for p in paths])
        except Exception as e:
            return CloneOrgResponse(success=False, error_message=str(e))

    def Health(self, request: common_pb2.HealthRequest, context: grpc.ServicerContext) -> HealthResponse:
        """Handle Health RPC.

        Args:
            request: Health request (unused).
            context: gRPC servicer context.

        Returns:
            HealthResponse with status "ok".
        """
        return HealthResponse(status="ok")


def serve(listen: str = "0.0.0.0:50052") -> grpc.Server:
    """Create and return a gRPC server with CacheMaintainer servicer (caller must start it).

    Args:
        listen: Host:port to bind (e.g. 0.0.0.0:50052).

    Returns:
        Unstarted gRPC server (caller must call start() and wait_for_termination()).
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    cache_pb2_grpc.add_CacheMaintainerServicer_to_server(CacheMaintainerServicer(), server)  # type: ignore[no-untyped-call]
    if ":" in listen:
        _, _, port = listen.rpartition(":")
        server.add_insecure_port(f"[::]:{port}")
    else:
        server.add_insecure_port(listen)
    return server
