"""
Defines the PatternRegistry, responsible for discovering, loading, and providing
access to all PLSEPattern definitions from external YAML files.
"""

import os
import glob
import yaml
import random
from typing import Dict, List, Optional
from pydantic import ValidationError

# Import our internal dataclasses for the final objects
from .patterns import PLSEPattern, Metadata, Pedagogy, Parameter, Validation
# Import our new Pydantic schema for validation
from .schema import PLSEPatternSchema

class PatternRegistry:
    """
    A dynamic registry that loads and manages PLSEPattern objects
    from a specified directory of YAML files, with robust schema validation.
    """

    def __init__(self, patterns_dir: str):
        self.patterns: Dict[str, PLSEPattern] = {}
        self._load_patterns_from_files(patterns_dir)

    def _load_patterns_from_files(self, patterns_dir: str):
        if not os.path.isdir(patterns_dir):
            print(f"Warning: Patterns directory not found at '{patterns_dir}'. No patterns loaded.")
            return

        pattern_files = glob.glob(os.path.join(patterns_dir, "*.yaml"))
        pattern_files.extend(glob.glob(os.path.join(patterns_dir, "*.yml")))

        print(f"Found {len(pattern_files)} pattern files. Loading and validating...")
        for filepath in pattern_files:
            try:
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)

                # --- THE NEW VALIDATION STEP ---
                # Parse the raw dictionary with our Pydantic schema.
                # If validation fails, this will raise a `ValidationError`.
                validated_data = PLSEPatternSchema(**data)

                # --- Convert from Pydantic model to internal dataclass ---
                # This keeps the rest of our application decoupled from Pydantic.
                meta_data = validated_data.metadata
                pedagogy_obj = Pedagogy(**meta_data.pedagogy.model_dump())
                metadata_obj = Metadata(
                    author=meta_data.author,
                    description=meta_data.description,
                    tags=meta_data.tags,
                    pedagogy=pedagogy_obj
                )
                params_obj = {
                    name: Parameter(**p_data.model_dump())
                    for name, p_data in validated_data.parameters.items()
                }
                validation_obj = Validation(**validated_data.validation.model_dump())

                pattern = PLSEPattern(
                    plse_version=validated_data.plse_version,
                    pattern_id=validated_data.pattern_id,
                    metadata=metadata_obj,
                    instruction=validated_data.instruction,
                    parameters=params_obj,
                    template=validated_data.template,
                    validation=validation_obj,
                    requires=validated_data.requires
                )
                
                self.register(pattern)
                print(f"  - ✅ SUCCESS: Loaded and validated pattern: '{pattern.pattern_id}'")

            except ValidationError as e:
                # This is our new, powerful exception handler!
                print(f"  - ❌ FAILED: Schema validation error in '{os.path.basename(filepath)}':")
                # Pydantic gives us beautiful, human-readable errors.
                for error in e.errors():
                    loc = " -> ".join(map(str, error['loc']))
                    print(f"    - Field '{loc}': {error['msg']}")
            
            except (yaml.YAMLError, TypeError) as e:
                print(f"  - ❌ FAILED: Could not parse or process file '{os.path.basename(filepath)}': {e}")

    def register(self, pattern: PLSEPattern):
        if pattern.pattern_id in self.patterns:
            print(f"Warning: Overwriting pattern with duplicate ID '{pattern.pattern_id}'.")
        self.patterns[pattern.pattern_id] = pattern

    def get(self, pattern_id: str) -> Optional[PLSEPattern]:
        return self.patterns.get(pattern_id)

    def get_random(self) -> Optional[PLSEPattern]:
        if not self.patterns:
            return None
        return random.choice(list(self.patterns.values()))