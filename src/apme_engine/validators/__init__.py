"""Validator abstraction: ScanContext and Validator protocol."""

from .base import ScanContext, Validator
from .opa import OpaValidator
from .native import NativeValidator
from .ansible import AnsibleValidator

__all__ = ["ScanContext", "Validator", "OpaValidator", "NativeValidator", "AnsibleValidator"]
