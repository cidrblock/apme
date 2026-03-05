"""Tests for validator abstraction (ScanContext, OpaValidator, NativeValidator)."""

import pytest

from apme_engine.validators.base import ScanContext
from apme_engine.validators.opa import OpaValidator
from apme_engine.validators.native import NativeValidator


class TestScanContext:
    def test_scan_context_defaults(self):
        ctx = ScanContext(hierarchy_payload={"scan_id": "x"})
        assert ctx.hierarchy_payload["scan_id"] == "x"
        assert ctx.scandata is None
        assert ctx.root_dir == ""

    def test_scan_context_with_scandata(self):
        mock = object()
        ctx = ScanContext(hierarchy_payload={}, scandata=mock, root_dir="/tmp")
        assert ctx.scandata is mock
        assert ctx.root_dir == "/tmp"


class TestOpaValidator:
    def test_opa_validator_run_calls_run_opa(self, opa_bundle_path, sample_hierarchy_payload):
        from unittest.mock import patch
        ctx = ScanContext(hierarchy_payload=sample_hierarchy_payload)
        v = OpaValidator(str(opa_bundle_path))
        with patch("apme_engine.validators.opa.run_opa", return_value=[]) as mock_opa:
            result = v.run(ctx)
        mock_opa.assert_called_once()
        assert mock_opa.call_args[0][0] == sample_hierarchy_payload
        assert mock_opa.call_args[0][1] == str(opa_bundle_path)
        assert result == []

    def test_opa_validator_run_returns_violations(self, sample_hierarchy_payload, tmp_path):
        from unittest.mock import patch
        (tmp_path / "bundle").mkdir()
        ctx = ScanContext(hierarchy_payload=sample_hierarchy_payload)
        v = OpaValidator(str(tmp_path / "bundle"))
        violations = [{"rule_id": "r1", "level": "high", "message": "msg", "file": "f", "line": 1, "path": "p"}]
        with patch("apme_engine.validators.opa.run_opa", return_value=violations):
            result = v.run(ctx)
        assert result == violations


class TestNativeValidator:
    def test_native_empty_context_returns_empty(self):
        ctx = ScanContext(hierarchy_payload={}, scandata=None)
        v = NativeValidator()
        assert v.run(ctx) == []

    def test_native_no_scandata_returns_empty(self):
        ctx = ScanContext(hierarchy_payload={"scan_id": "x"}, scandata=None)
        v = NativeValidator()
        assert v.run(ctx) == []

    def test_native_scandata_without_contexts_returns_empty(self):
        mock_scandata = type("Scandata", (), {"contexts": []})()
        ctx = ScanContext(hierarchy_payload={}, scandata=mock_scandata)
        v = NativeValidator()
        assert v.run(ctx) == []
