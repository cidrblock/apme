"""Validator abstraction: ScanContext and Validator protocol."""

from .ansible import AnsibleValidator
from .base import ScanContext, Validator
from .native import NativeValidator
from .opa import OpaValidator

__all__ = ["ScanContext", "Validator", "OpaValidator", "NativeValidator", "AnsibleValidator"]
