"""
Defines the core data structures for the PLSE v2.0, based on the
strategic framework for a pedagogical, YAML-based pattern library.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Sequence

# --- Schema-aligned Dataclasses ---

class PatternCategory(Enum):
    """Enumeration for the categories of Python patterns."""
    ALGORITHMIC = "algorithmic"
    DATA_STRUCTURE = "data_structure"
    DEEP_LEARNING = "deep_learning" # New category for ML focus
    DATA_PROCESSING = "data_processing"
    ML_CONCEPTS = "ml_concepts"
    # ... add others as needed

@dataclass
class Pedagogy:
    """Defines the educational objective of a pattern."""
    concept: str
    difficulty: str # e.g., "beginner", "intermediate", "advanced"
    related_patterns: List[str] = field(default_factory=list)

@dataclass
class Metadata:
    """Container for all descriptive metadata about the pattern."""
    author: str
    description: str
    tags: List[str]
    pedagogy: Pedagogy

@dataclass
class Parameter:
    """Defines a variable for dynamic code generation."""
    type: str # e.g., "int", "float", "string", "bool", "choice"
    description: str
    default: Any
    constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Components:
    """Architectural blueprint of the code to be generated."""
    imports: str
    model_definition: str
    data_setup: str = ""
    training_loop: str = ""
    evaluation: str = ""

@dataclass
class Validation:
    """Defines methods for verifying the correctness of generated code."""
    linter_checks: bool = True
    unit_test_snippets: List[str] = field(default_factory=list)
    expected_output: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PLSEPattern:
    """
    The top-level dataclass for a single, complete pattern definition,
    loaded from a YAML file. This replaces the simpler CombinatorialPattern.
    """
    plse_version: str
    pattern_id: str
    metadata: Metadata
    instruction: str
    parameters: Dict[str, Parameter]
    components: Components
    validation: Validation = field(default_factory=Validation)

# --- Supporting Dataclasses ---

@dataclass
class ValidationResult:
    """Represents the outcome of a validation check."""
    valid: bool
    code: str
    errors: List[str] = field(default_factory=list)
