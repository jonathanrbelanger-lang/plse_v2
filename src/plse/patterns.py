"""
Defines the internal dataclasses used by the PLSE application.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from .schema import PLSEPatternSchema

@dataclass
class Pedagogy:
    concept: str
    difficulty: str
    related_patterns: List[str] = field(default_factory=list)

@dataclass
class Metadata:
    author: str
    description: str
    tags: List[str]
    pedagogy: Pedagogy

@dataclass
class Parameter:
    type: str
    description: str
    default: Any
    constraints: Optional[Dict[str, Any]] = None

@dataclass
class Components:
    imports: str = ""
    model_definition: Optional[str] = None
    data_setup: Optional[str] = None
    training_loop: Optional[str] = None
    evaluation: Optional[str] = None

@dataclass
class Validation:
    linter_checks: bool = True
    unit_test_snippets: List[str] = field(default_factory=list)
    expected_output: Optional[Dict[str, Any]] = None

@dataclass
class PLSEPattern:
    """The internal, validated representation of a single PLSE pattern."""
    plse_version: str
    pattern_id: str
    metadata: Metadata
    instruction: str
    components: Components
    parameters: Dict[str, Parameter] = field(default_factory=dict)
    validation: Validation = field(default_factory=Validation)
    requires: List[str] = field(default_factory=list)

    @classmethod
    def from_schema(cls, schema: PLSEPatternSchema) -> "PLSEPattern":
        pedagogy_obj = Pedagogy(**schema.metadata.pedagogy.model_dump())
        metadata_obj = Metadata(
            author=schema.metadata.author,
            description=schema.metadata.description,
            tags=schema.metadata.tags,
            pedagogy=pedagogy_obj
        )
        params_obj = {
            name: Parameter(**p_data.model_dump())
            for name, p_data in schema.parameters.items()
        } if schema.parameters else {}
        components_obj = Components(**schema.components.model_dump())
        validation_obj = Validation(**schema.validation.model_dump()) if schema.validation else Validation()

        return cls(
            plse_version=schema.plse_version,
            pattern_id=schema.pattern_id,
            metadata=metadata_obj,
            instruction=schema.instruction,
            components=components_obj,
            parameters=params_obj,
            validation=validation_obj,
            requires=schema.requires or []
        )