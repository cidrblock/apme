"""Native validator daemon: gRPC server that runs in-tree Python rules on deserialized scandata."""

import json
import sys
from concurrent import futures

import grpc
import jsonpickle
from apme.v1 import validate_pb2, validate_pb2_grpc, common_pb2

from apme_engine.daemon.violation_convert import violation_dict_to_proto
from apme_engine.validators.base import ScanContext
from apme_engine.validators.native import NativeValidator


class NativeValidatorServicer(validate_pb2_grpc.ValidatorServicer):
    """gRPC adapter: deserializes scandata, runs native rules, returns violations."""

    def Validate(self, request, context):
        try:
            hierarchy_payload = {}
            if request.hierarchy_payload:
                try:
                    hierarchy_payload = json.loads(request.hierarchy_payload)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    sys.stderr.write("Native validator: failed to decode hierarchy_payload\n")

            scandata = None
            if request.scandata:
                try:
                    scandata = jsonpickle.decode(request.scandata.decode("utf-8"))
                except Exception as e:
                    sys.stderr.write(f"Native validator: failed to decode scandata: {e}\n")
                    return validate_pb2.ValidateResponse(violations=[])

            scan_context = ScanContext(
                hierarchy_payload=hierarchy_payload,
                scandata=scandata,
            )
            validator = NativeValidator()
            violations = validator.run(scan_context)
            sys.stderr.write(f"Native validator returned {len(violations)} violation(s)\n")

            return validate_pb2.ValidateResponse(
                violations=[violation_dict_to_proto(v) for v in violations]
            )
        except Exception as e:
            import traceback
            sys.stderr.write(f"Native validator error: {e}\n")
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            return validate_pb2.ValidateResponse(violations=[])

    def Health(self, request, context):
        return common_pb2.HealthResponse(status="ok")


def serve(listen: str = "0.0.0.0:50055"):
    """Create and return a gRPC server with Native servicer (caller must start it)."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    validate_pb2_grpc.add_ValidatorServicer_to_server(NativeValidatorServicer(), server)
    if ":" in listen:
        _, _, port = listen.rpartition(":")
        server.add_insecure_port(f"[::]:{port}")
    else:
        server.add_insecure_port(listen)
    return server
