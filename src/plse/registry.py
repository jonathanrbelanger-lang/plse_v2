"""
Defines the PatternRegistry, responsible for discovering, loading, and providing
access to all CombinatorialPattern definitions from external YAML files.
"""

import os
import glob
import yaml
import random
from typing import Dict, List, Optional, Tuple

# We need to import our custom dataclasses and enums from the patterns.py file
from .patterns import CombinatorialPattern, PatternCategory

class PatternRegistry:
    """
    A dynamic registry that loads and manages CombinatorialPattern objects
    from a specified directory of YAML files.
    """

    def __init__(self, patterns_dir: str):
        """
        Initializes the registry by loading all patterns from the given directory.

        Args:
            patterns_dir (str): The path to the directory containing pattern.yaml files.
        """
        self.patterns: Dict[str, CombinatorialPattern] = {}
        self._load_patterns_from_files(patterns_dir)

    def _load_patterns_from_files(self, patterns_dir: str):
        """
        Discovers and loads all pattern definitions from YAML files in a directory.
        This is the core of our new modular architecture.
        """
        if not os.path.isdir(patterns_dir):
            print(f"Warning: Patterns directory not found at '{patterns_dir}'. No patterns loaded.")
            return

        # Use glob to find all files ending with .yaml or .yml
        pattern_files = glob.glob(os.path.join(patterns_dir, "*.yaml"))
        pattern_files.extend(glob.glob(os.path.join(patterns_dir, "*.yml")))

        if not pattern_files:
            print(f"Warning: No pattern files (.yaml, .yml) found in '{patterns_dir}'.")
            return

        print(f"Found {len(pattern_files)} pattern files. Loading...")
        for filepath in pattern_files:
            try:
                with open(filepath, 'r') as f:
                    pattern_data = yaml.safe_load(f)

                    # --- Data Validation and Conversion ---
                    # Convert the category string from YAML (e.g., "ALGORITHMIC")
                    # into the actual PatternCategory.ALGORITHMIC enum member.
                    category_str = pattern_data.get("category", "").upper()
                    pattern_data["category"] = PatternCategory[category_str]

                    # Instantiate the dataclass using the loaded data
                    pattern = CombinatorialPattern(**pattern_data)
                    self.register(pattern)
                    print(f"  - Successfully loaded pattern: '{pattern.name}'")

            except yaml.YAMLError as e:
                print(f"Error loading YAML from {filepath}: {e}")
            except KeyError as e:
                # This happens if the YAML is missing a required field or
                # if the category string is invalid.
                print(f"Error processing pattern data from {filepath}: Invalid key or value - {e}")
            except Exception as e:
                print(f"An unexpected error occurred while processing {filepath}: {e}")

    def register(self, pattern: CombinatorialPattern):
        """Registers a single pattern object into the internal dictionary."""
        if pattern.name in self.patterns:
            print(f"Warning: Overwriting pattern with duplicate name '{pattern.name}'.")
        self.patterns[pattern.name] = pattern

    def get(self, name: str) -> Optional[CombinatorialPattern]:
        """Retrieves a pattern by its unique name."""
        return self.patterns.get(name)

    def get_by_category(self, category: PatternCategory) -> List[CombinatorialPattern]:
        """Gets all patterns belonging to a specific category."""
        return [p for p in self.patterns.values() if p.category == category]

    def get_random(self, complexity_range: Tuple[int, int] = (1, 5)) -> Optional[CombinatorialPattern]:
        """
        Gets a random pattern, optionally filtered by a complexity range.
        """
        eligible_patterns = [
            p for p in self.patterns.values()
            if complexity_range[0] <= p.complexity <= complexity_range[1]
        ]
        if not eligible_patterns:
            return None
        return random.choice(eligible_patterns)
