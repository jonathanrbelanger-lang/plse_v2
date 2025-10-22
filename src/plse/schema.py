"""
Defines the Pydantic validation schemas for the PLSE v2.0 pattern library.

These models act as the "gatekeeper" for loading raw YAML data, ensuring that
all patterns conform to the expected structure and data types before they are
processed by the application.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Any, Optional

class PedagogySchema(BaseModel):
    concept: str
    difficulty: str
    related_patterns: List[str] = Field(default_factory=list)

class MetadataSchema(BaseModel):
    author: str
    description: str
    tags: List[str]
    pedagogy: PedagogySchema

class ParameterSchema(BaseModel):
    type: str
    description: str
    default: Any
    constraints: Optional[Dict[str, Any]] = None

class ComponentsSchema(BaseModel):
    """
    Defines the schema for the architectural blueprint of the code.
    This correctly models the nested 'components' map in our YAML.
    """
    imports: Optional[str] = ""
    model_definition: Optional[str] = None
    data_setup: Optional[str] = None
    training_loop: Optional[str] = None
    evaluation: Optional[str] = None

class ValidationSchema(BaseModel):
    linter_checks: bool = True
    unit_test_snippets: List[str] = Field(default_factory=list)
    expected_output: Optional[Dict[str, Any]] = None

class PLSEPatternSchema(BaseModel):
    """The top-level Pydantic model for validating a complete pattern.yaml file."""
    plse_version: str
    pattern_id: str
    metadata: MetadataSchema
    instruction: str
    
    # STRUCTURAL FIX: Use ComponentsSchema for nested structure
    components: Optional[ComponentsSchema] = None
    # Keep 'template' for backward compatibility with simple patterns
    template: Optional[str] = None
    
    parameters: Optional[Dict[str, ParameterSchema]] = None
    validation: Optional[ValidationSchema] = None
    requires: Optional[List[str]] = None

    @model_validator(mode='after')
    def check_components_or_template(self) -> 'PLSEPatternSchema':
        if self.components is None and self.template is None:
            raise ValueError("A pattern must have either a 'components' map or a 'template' string.")
        
        if self.components is not None and self.template is not None:
            raise ValueError("A pattern cannot have both 'components' and 'template'. Use one or the other.")
        
        # If a simple 'template' is provided, automatically convert it into
        # the 'components' structure for internal consistency.
        if self.template is not None:
            # We'll treat a simple template as the main 'model_definition'
            self.components = ComponentsSchema(imports="", model_definition=self.template)
            self.template = None # Nullify the original template field
            
        return self