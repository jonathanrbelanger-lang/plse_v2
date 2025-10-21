"""
Defines the PatternRegistry, responsible for discovering, loading, and providing
access to all PLSEPattern definitions from external YAML files.
"""

import os
import glob
import yaml
import random
from typing import Dict, List, Optional, Tuple

# Import the new, more detailed dataclasses
from .patterns import PLSEPattern, Metadata, Pedagogy, Parameter, Components, Validation, PatternCategory

class PatternRegistry:
    """
    A dynamic registry that loads and manages PLSEPattern objects
    from a specified directory of YAML files.
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

        if not pattern_files:
            print(f"Warning: No pattern files (.yaml, .yml) found in '{patterns_dir}'.")
            return

        print(f"Found {len(pattern_files)} pattern files. Loading...")
        for filepath in pattern_files:
            try:
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)

                    # --- New Nested Deserialization Logic ---
                    # We now manually construct the nested dataclasses for validation.
                    
                    meta_data = data.get('metadata', {})
                    pedagogy_obj = Pedagogy(**meta_data.get('pedagogy', {}))
                    metadata_obj = Metadata(
                        author=meta_data.get('author'),
                        description=meta_data.get('description'),
                        tags=meta_data.get('tags', []),
                        pedagogy=pedagogy_obj
                    )

                    params_obj = {
                        name: Parameter(**p_data)
                        for name, p_data in data.get('parameters', {}).items()
                    }

                    components_obj = Components(**data.get('components', {}))
                    validation_obj = Validation(**data.get('validation', {}))

                    pattern = PLSEPattern(
                        plse_version=data.get('plse_version'),
                        pattern_id=data.get('pattern_id'),
                        metadata=metadata_obj,
                        instruction=data.get('instruction'),
                        parameters=params_obj,
                        components=components_obj,
                        validation=validation_obj
                    )
                    
                    self.register(pattern)
                    print(f"  - Successfully loaded pattern: '{pattern.pattern_id}'")

            except (yaml.YAMLError, TypeError, KeyError) as e:
                print(f"Error processing pattern file {filepath}: {e}")

    def register(self, pattern: PLSEPattern):
        """Registers a single pattern object."""
        if pattern.pattern_id in self.patterns:
            print(f"Warning: Overwriting pattern with duplicate ID '{pattern.pattern_id}'.")
        self.patterns[pattern.pattern_id] = pattern

    def get(self, pattern_id: str) -> Optional[PLSEPattern]:
        """Retrieves a pattern by its unique ID."""
        return self.patterns.get(pattern_id)

    def get_random(self) -> Optional[PLSEPattern]:
        """Gets a random pattern from the registry."""
        if not self.patterns:
            return None
        return random.choice(list(self.patterns.values()))
