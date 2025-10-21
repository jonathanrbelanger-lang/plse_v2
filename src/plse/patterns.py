"""
Defines the core data structures for the Python Latent Space Explorer (PLSE).

This includes the main `CombinatorialPattern` for defining code generation templates
and the `ValidationResult` for structuring the output of the validation pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

# The original script used an Enum for categories, which was a good design choice.
# We will formalize it here for clarity and type safety.
class PatternCategory(Enum):
    """Enumeration for the categories of Python patterns."""
    ALGORITHMIC = "algorithmic"
    DATA_STRUCTURE = "data_structure"
    FUNCTIONAL = "functional"
    OOP = "oop"
    ASYNC = "async"
    ERROR_HANDLING = "error_handling"
    # We can easily add more categories here in the future.
    FILE_IO = "file_io"
    STANDARD_LIBRARY = "standard_library"

@dataclass
class CombinatorialPattern:
    """
    Defines a code pattern with pools of bindings for combinatorial generation.
    This replaces the old Pattern/PatternVariant system.
    """
    name: str
    category: PatternCategory
    complexity: int  # A 1-5 scale of complexity.
    requires: List[str] = field(default_factory=list)
    template: str = ""
    
    # This is the core architectural change. Instead of a fixed list of variants,
    # we define pools of possible substitutions for each placeholder.
    binding_pools: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """
    Represents the outcome of a validation check from any validator.
    This provides a standardized way to report success or failure.
    """
    valid: bool
    code: str
    errors: List[str] = field(default_factory=list)
