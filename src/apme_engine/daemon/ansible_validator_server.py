"""Ansible validator daemon: thin gRPC adapter over AnsibleValidator."""

import json
import os
import subprocess
import sys
import tempfile
from concurrent import futures
from pathlib import Path

import grpc
from apme.v1 import validate_pb2, validate_pb2_grpc, common_pb2

from apme_engine.collection_cache.config import get_cache_root
from apme_engine.collection_cache.venv_builder import build_venv, get_venv_python
from apme_engine.daemon.violation_convert import violation_dict_to_proto
from apme_engine.validators.ansible import AnsibleValidator
from apme_engine.validators.ansible._venv import (
    DEFAULT_VERSION,
    resolve_venv_root,
    setup_collections_env,
)
from apme_engine.validators.base import ScanContext


def _cache_root() -> Path:
    root = os.environ.get("APME_CACHE_ROOT", "").strip()
    if root:
        return Path(root).resolve()
    return get_cache_root()


def _write_chunked_fs(files: list) -> Path:
    """Write request.files into a temp directory; return path to that directory."""
    tmp = Path(tempfile.mkdtemp(prefix="apme_ansible_val_"))
    for f in files:
        path = tmp / f.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f.content)
    return tmp


class AnsibleValidatorServicer(validate_pb2_grpc.ValidatorServicer):
    """gRPC adapter: receives ValidateRequest, delegates to AnsibleValidator."""

    def Validate(self, request, context):
        violations: list[dict] = []
        temp_dir = None
        try:
            if not request.files:
                return validate_pb2.ValidateResponse(violations=[])

            temp_dir = _write_chunked_fs(list(request.files))

            raw_version = (request.ansible_core_version or "").strip() or DEFAULT_VERSION
            collection_specs = [s.strip() for s in (request.collection_specs or []) if s.strip()]

            # Resolve venv
            venv_root = resolve_venv_root(raw_version)
            if venv_root is None:
                try:
                    cache = _cache_root()
                    fallback_venvs = Path(tempfile.mkdtemp(prefix="apme_venvs_"))
                    venv_root = build_venv(
                        ansible_core_version=raw_version,
                        collection_specs=collection_specs,
                        cache_root=cache,
                        venvs_root=fallback_venvs,
                    )
                except (FileNotFoundError, subprocess.CalledProcessError) as e:
                    violations.append({
                        "rule_id": "L057",
                        "level": "error",
                        "message": f"No pre-built venv for {raw_version} and on-demand build failed: {e}",
                        "file": "",
                        "line": 1,
                        "path": "",
                    })
                    return validate_pb2.ValidateResponse(
                        violations=[violation_dict_to_proto(v) for v in violations]
                    )

            # Collection env
            env_extra = None
            if collection_specs:
                try:
                    env_extra = setup_collections_env(collection_specs, _cache_root())
                except Exception:
                    pass

            # Parse hierarchy payload
            hierarchy_payload = {}
            if request.hierarchy_payload:
                try:
                    hierarchy_payload = json.loads(request.hierarchy_payload)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    sys.stderr.write("Ansible validator: failed to parse hierarchy_payload\n")

            # Build context and run validator
            scan_context = ScanContext(
                hierarchy_payload=hierarchy_payload,
                root_dir=str(temp_dir),
            )
            validator = AnsibleValidator(venv_root=venv_root, env_extra=env_extra)
            violations = validator.run(scan_context)

            return validate_pb2.ValidateResponse(
                violations=[violation_dict_to_proto(v) for v in violations]
            )
        except Exception as e:
            import traceback
            sys.stderr.write(f"Ansible validator error: {e}\n")
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            violations.append({
                "rule_id": "L057",
                "level": "error",
                "message": str(e),
                "file": "",
                "line": 1,
                "path": "",
            })
            return validate_pb2.ValidateResponse(
                violations=[violation_dict_to_proto(v) for v in violations]
            )
        finally:
            if temp_dir is not None and temp_dir.is_dir():
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except OSError:
                    pass

    def Health(self, request, context):
        return common_pb2.HealthResponse(status="ok")


def serve(listen: str = "0.0.0.0:50053"):
    """Create and return a gRPC server with Ansible servicer (caller must start it)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    validate_pb2_grpc.add_ValidatorServicer_to_server(AnsibleValidatorServicer(), server)
    if ":" in listen:
        _, _, port = listen.rpartition(":")
        server.add_insecure_port(f"[::]:{port}")
    else:
        server.add_insecure_port(listen)
    return server
