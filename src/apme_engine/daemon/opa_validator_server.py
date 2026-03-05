"""OPA validator daemon: gRPC wrapper over OPA REST API (localhost:8181)."""

import json
import sys
from concurrent import futures

import grpc
import requests
from apme.v1 import validate_pb2, validate_pb2_grpc, common_pb2

from apme_engine.daemon.violation_convert import violation_dict_to_proto

OPA_REST_URL = "http://localhost:8181"
OPA_VIOLATIONS_ENDPOINT = "/v1/data/apme/rules/violations"


class OpaValidatorServicer(validate_pb2_grpc.ValidatorServicer):
    """gRPC facade: translates Validate RPCs into OPA REST queries."""

    def Validate(self, request, context):
        violations: list[dict] = []
        try:
            hierarchy_payload = {}
            if request.hierarchy_payload:
                try:
                    hierarchy_payload = json.loads(request.hierarchy_payload)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    sys.stderr.write("OPA wrapper: failed to decode hierarchy_payload\n")
                    return validate_pb2.ValidateResponse(violations=[])

            url = f"{OPA_REST_URL}{OPA_VIOLATIONS_ENDPOINT}"
            r = requests.post(url, json={"input": hierarchy_payload}, timeout=30)

            if r.status_code != 200:
                sys.stderr.write(f"OPA returned HTTP {r.status_code}\n")
                return validate_pb2.ValidateResponse(violations=[])

            data = r.json()
            result = data.get("result", [])
            violations = result if isinstance(result, list) else []
            sys.stderr.write(f"OPA returned {len(violations)} violation(s)\n")
        except Exception as e:
            sys.stderr.write(f"OPA wrapper error: {e}\n")
            return validate_pb2.ValidateResponse(violations=[])

        return validate_pb2.ValidateResponse(
            violations=[violation_dict_to_proto(v) for v in violations]
        )

    def Health(self, request, context):
        try:
            r = requests.get(f"{OPA_REST_URL}/health", timeout=5)
            if r.status_code == 200:
                return common_pb2.HealthResponse(status="ok")
            return common_pb2.HealthResponse(status=f"opa unhealthy: HTTP {r.status_code}")
        except Exception as e:
            return common_pb2.HealthResponse(status=f"opa unreachable: {e}")


def serve(listen: str = "0.0.0.0:50054"):
    """Create and return a gRPC server with OPA servicer (caller must start it)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    validate_pb2_grpc.add_ValidatorServicer_to_server(OpaValidatorServicer(), server)
    if ":" in listen:
        _, _, port = listen.rpartition(":")
        server.add_insecure_port(f"[::]:{port}")
    else:
        server.add_insecure_port(listen)
    return server
