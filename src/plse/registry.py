"""
Discovers, validates, and loads all PLSE patterns from a directory tree.
"""

import os
import yaml
import random
from typing import List, Optional
from pydantic import ValidationError

from .schema import PLSEPatternSchema
from .patterns import PLSEPattern

class PatternRegistry:
    """
    Scans a directory recursively, validates YAML files against the Pydantic
    schema, and loads them into memory as PLSEPattern objects.
    """
    def __init__(self, patterns_dir: str):
        if not os.path.isdir(patterns_dir):
            raise FileNotFoundError(f"The specified patterns directory does not exist: {patterns_dir}")
        self.patterns_dir = patterns_dir
        self.patterns: List[PLSEPattern] = []
        self._load_patterns()

    def _load_patterns(self):
        print(f"🔍 Scanning for patterns in '{self.patterns_dir}' and its subdirectories...")
        loaded_count = 0
        error_count = 0

        for root, _, files in os.walk(self.patterns_dir):
            for filename in files:
                if filename.endswith((".yaml", ".yml")):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            raw_data = yaml.safe_load(f)
                        
                        validated_schema = PLSEPatternSchema(**raw_data)
                        pattern = PLSEPattern.from_schema(validated_schema)
                        
                        self.patterns.append(pattern)
                        loaded_count += 1
                    except ValidationError as e:
                        print(f"  - ❌ FAILED: Schema validation error in '{os.path.basename(file_path)}':")
                        for error in e.errors():
                            loc = " -> ".join(map(str, error['loc']))
                            print(f"    - Field '{loc}': {error['msg']}")
                        error_count += 1
                    except Exception as e:
                        print(f"  - ❌ FAILED: Could not parse or process file '{os.path.basename(file_path)}': {e}")
                        error_count += 1
        
        print(f"\n✅ Scan complete. Loaded {loaded_count} patterns.")
        if error_count > 0:
            print(f"⚠️ Encountered {error_count} errors during loading.")

    def get_random(self) -> Optional[PLSEPattern]:
        if not self.patterns:
            return None
        return random.choice(self.patterns)