"""Convert between dict violations (validator output) and proto Violation."""

from collections.abc import Mapping

from apme.v1 import common_pb2
from apme.v1.common_pb2 import LineRange, Violation
from apme_engine.engine.models import RemediationClass, ViolationDict

# Map string remediation class to proto enum
_REMEDIATION_CLASS_TO_PROTO = {
    RemediationClass.AUTO_FIXABLE: common_pb2.REMEDIATION_CLASS_AUTO_FIXABLE,  # type: ignore[attr-defined]
    RemediationClass.AI_CANDIDATE: common_pb2.REMEDIATION_CLASS_AI_CANDIDATE,  # type: ignore[attr-defined]
    RemediationClass.MANUAL_REVIEW: common_pb2.REMEDIATION_CLASS_MANUAL_REVIEW,  # type: ignore[attr-defined]
}

# Map proto enum to string remediation class
_PROTO_TO_REMEDIATION_CLASS = {
    common_pb2.REMEDIATION_CLASS_UNSPECIFIED: RemediationClass.AI_CANDIDATE,  # type: ignore[attr-defined]
    common_pb2.REMEDIATION_CLASS_AUTO_FIXABLE: RemediationClass.AUTO_FIXABLE,  # type: ignore[attr-defined]
    common_pb2.REMEDIATION_CLASS_AI_CANDIDATE: RemediationClass.AI_CANDIDATE,  # type: ignore[attr-defined]
    common_pb2.REMEDIATION_CLASS_MANUAL_REVIEW: RemediationClass.MANUAL_REVIEW,  # type: ignore[attr-defined]
}


def violation_dict_to_proto(v: ViolationDict | Mapping[str, str | int | list[int] | bool | None]) -> Violation:
    """Build a proto Violation from a dict with rule_id, level, message, file, line, path.

    Args:
        v: Dict or mapping with rule_id, level, message, file, line (int or [start,end]), path,
           and optional remediation_class.

    Returns:
        Violation proto populated from the dict.
    """
    remediation_class_str = str(v.get("remediation_class") or RemediationClass.AI_CANDIDATE)
    remediation_class_proto = _REMEDIATION_CLASS_TO_PROTO.get(
        remediation_class_str,
        common_pb2.REMEDIATION_CLASS_AI_CANDIDATE,  # type: ignore[attr-defined]
    )

    out = Violation(
        rule_id=str(v.get("rule_id") or ""),
        level=str(v.get("level") or ""),
        message=str(v.get("message") or ""),
        file=str(v.get("file") or ""),
        path=str(v.get("path") or ""),
        remediation_class=remediation_class_proto,
    )
    line = v.get("line")
    if isinstance(line, list | tuple) and len(line) >= 2:
        out.line_range.CopyFrom(LineRange(start=int(line[0]), end=int(line[1])))
    elif isinstance(line, int):
        out.line = line
    return out


def violation_proto_to_dict(v: Violation) -> ViolationDict:
    """Build a dict violation from proto (for CLI output).

    Args:
        v: Violation proto to convert.

    Returns:
        ViolationDict with rule_id, level, message, file, line, path, remediation_class.
    """
    line: int | list[int] | None = v.line if v.HasField("line") else None
    if v.HasField("line_range"):
        line = [v.line_range.start, v.line_range.end]
    remediation_class = _PROTO_TO_REMEDIATION_CLASS.get(
        v.remediation_class,  # type: ignore[attr-defined]
        RemediationClass.AI_CANDIDATE,
    )
    return {
        "rule_id": v.rule_id,
        "level": v.level,
        "message": v.message,
        "file": v.file,
        "line": line,
        "path": v.path,
        "remediation_class": remediation_class,
    }
