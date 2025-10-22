"""
Defines the Pydantic validation schemas for the PLSE v2.0 pattern library.

These models act as the "gatekeeper" for loading raw YAML data, ensuring that
all patterns conform to the expected structure and data types before they are
processed by the application.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any

# We still need our Enum from the patterns file
from .patterns import PatternCategory

class PedagogySchema(BaseModel):
    concept: str
    difficulty: str
    related_patterns: List[str] = []

class MetadataSchema(BaseModel):
    author: str
    description: str
    tags: List[str]
    pedagogy: PedagogySchema

class ParameterSchema(BaseModel):
    type: str
    description: str
    default: Any
    constraints: Dict[str, Any] = {}

class ValidationSchema(BaseModel):
    linter_checks: bool = True
    unit_test_snippets: List[str] = []
    expected_output: Dict[str, Any] = {}

class PLSEPatternSchema(BaseModel):
    """The top-level Pydantic model for validating a complete pattern.yaml file."""
    plse_version: str
    pattern_id: str
    metadata: MetadataSchema
    instruction: str
    parameters: Dict[str, ParameterSchema] = {}
    template: str
    validation: ValidationSchema = Field(default_factory=ValidationSchema)
    requires: List[str] = []