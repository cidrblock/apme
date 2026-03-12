"""Gitleaks validator daemon: async gRPC server that writes files to a temp dir,
runs gitleaks detect, and returns violations."""

import asyncio
import contextlib
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

import grpc
import grpc.aio

from apme.v1 import common_pb2, validate_pb2, validate_pb2_grpc
from apme_engine.daemon.violation_convert import violation_dict_to_proto
from apme_engine.validators.gitleaks.scanner import GITLEAKS_BIN, run_gitleaks

_MAX_CONCURRENT_RPCS = int(os.environ.get("APME_GITLEAKS_MAX_RPCS", "16"))

_SCANNABLE_EXTENSIONS = (
    ".yml",
    ".yaml",
    ".cfg",
    ".ini",
    ".conf",
    ".env",
    ".py",
    ".sh",
    ".json",
)


def _run_scan(files: list) -> tuple[list[dict], int]:
    """Blocking function: write files to temp dir, run gitleaks, return (violations, files_written)."""
    temp_dir = Path(tempfile.mkdtemp(prefix="apme_gitleaks_"))
    try:
        file_count = 0
        for f in files:
            if not f.path.endswith(_SCANNABLE_EXTENSIONS):
                continue
            out = temp_dir / f.path
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(f.content)
            file_count += 1

        return run_gitleaks(temp_dir), file_count
    finally:
        with contextlib.suppress(OSError):
            shutil.rmtree(temp_dir)


def _get_gitleaks_version() -> str:
    """Attempt to get gitleaks version string (best-effort)."""
    import subprocess as _sp

    try:
        r = _sp.run([GITLEAKS_BIN, "version"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


class GitleaksValidatorServicer(validate_pb2_grpc.ValidatorServicer):
    """Async gRPC adapter: runs gitleaks in executor thread."""

    async def Validate(self, request, context):
        req_id = request.request_id or ""
        t0 = time.monotonic()
        try:
            if not request.files:
                return validate_pb2.ValidateResponse(violations=[], request_id=req_id)

            sys.stderr.write(f"[req={req_id}] Gitleaks: scanning {len(request.files)} file(s)\n")
            sys.stderr.flush()

            violations, files_written = await asyncio.get_event_loop().run_in_executor(
                None,
                _run_scan,
                list(request.files),
            )

            total_ms = (time.monotonic() - t0) * 1000
            sys.stderr.write(f"[req={req_id}] Gitleaks: {len(violations)} finding(s) in {total_ms:.1f}ms\n")
            sys.stderr.flush()

            diag = common_pb2.ValidatorDiagnostics(
                validator_name="gitleaks",
                request_id=req_id,
                total_ms=total_ms,
                files_received=len(request.files),
                violations_found=len(violations),
                rule_timings=[
                    common_pb2.RuleTiming(
                        rule_id="gitleaks_subprocess",
                        elapsed_ms=total_ms,
                        violations=len(violations),
                    ),
                ],
                metadata={
                    "subprocess_ms": f"{total_ms:.1f}",
                    "files_written": str(files_written),
                },
            )

            return validate_pb2.ValidateResponse(
                violations=[violation_dict_to_proto(v) for v in violations],
                request_id=req_id,
                diagnostics=diag,
            )
        except Exception as e:
            import traceback

            sys.stderr.write(f"[req={req_id}] Gitleaks error: {e}\n")
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return validate_pb2.ValidateResponse(violations=[], request_id=req_id)

    async def Health(self, request, context):
        try:
            proc = await asyncio.create_subprocess_exec(
                GITLEAKS_BIN,
                "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0:
                version = stdout.decode().strip()
                return common_pb2.HealthResponse(status=f"ok (gitleaks {version})")
            return common_pb2.HealthResponse(status=f"gitleaks exited {proc.returncode}")
        except FileNotFoundError:
            return common_pb2.HealthResponse(status="gitleaks binary not found")
        except Exception as e:
            return common_pb2.HealthResponse(status=f"gitleaks health error: {e}")


async def serve(listen: str = "0.0.0.0:50056"):
    """Create, bind, and start async gRPC server with Gitleaks servicer."""
    server = grpc.aio.server(maximum_concurrent_rpcs=_MAX_CONCURRENT_RPCS)
    validate_pb2_grpc.add_ValidatorServicer_to_server(GitleaksValidatorServicer(), server)
    if ":" in listen:
        _, _, port = listen.rpartition(":")
        server.add_insecure_port(f"[::]:{port}")
    else:
        server.add_insecure_port(listen)
    await server.start()
    return server
