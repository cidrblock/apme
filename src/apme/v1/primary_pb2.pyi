"""Stub for generated primary_pb2 (proto types)."""

from apme.v1.common_pb2 import ValidatorDiagnostics

class ScanOptions:
    ansible_core_version: str
    collection_specs: list[str]
    def __init__(self, **kwargs: object) -> None: ...

class ScanRequest:
    scan_id: str
    project_root: str
    files: list[object]
    options: ScanOptions | None
    def __init__(self, **kwargs: object) -> None: ...
    def HasField(self, field_name: str) -> bool: ...

class ScanResponse:
    def __init__(self, **kwargs: object) -> None: ...

class ScanDiagnostics:
    engine_parse_ms: float
    engine_annotate_ms: float
    engine_total_ms: float
    files_scanned: int
    trees_built: int
    total_violations: int
    validators: list[ValidatorDiagnostics]
    fan_out_ms: float
    total_ms: float
    def __init__(self, **kwargs: object) -> None: ...

class FormatRequest:
    files: list[object]
    def __init__(self, **kwargs: object) -> None: ...

class FormatResponse:
    def __init__(self, **kwargs: object) -> None: ...

class FileDiff:
    def __init__(self, **kwargs: object) -> None: ...
