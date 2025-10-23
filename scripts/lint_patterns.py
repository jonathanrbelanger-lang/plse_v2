"""
A high-performance, parallel diagnostic script to lint all generated patterns.
"""

import sys
import os
from typing import List, Tuple, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

# Add the project root to the path to allow importing from 'src'
sys.path.insert(0, '.')

try:
    from src.plse.registry import PatternRegistry
    from src.plse.generator import PLSEGenerator
    from src.plse.validation import SyntaxValidator, Flake8Validator
    from src.plse.patterns import PLSEPattern
    from src.plse.schema import PLSEPatternSchema # Import the Pydantic schema
except ImportError as e:
    print(f"FATAL: Could not import PLSE modules. Ensure you have run 'pip install -e .'. Error: {e}")
    sys.exit(1)

# This function must be at the top level to be pickleable by multiprocessing
def check_single_pattern(pattern_dict: Dict) -> Tuple[str, List[str]]:
    """
    Worker function to generate and validate a single pattern.
    Receives a dictionary and correctly reconstructs the nested PLSEPattern object.
    """
    generator = PLSEGenerator()
    validators = [SyntaxValidator(), Flake8Validator()]
    errors: List[str] = []
    pattern_id = pattern_dict.get("pattern_id", "unknown_pattern")

    try:
        # --- BUG FIX: Properly reconstruct the nested dataclass object ---
        # 1. Load the dict into the Pydantic schema for validation.
        schema = PLSEPatternSchema(**pattern_dict)
        # 2. Use our trusted factory method to build the full object.
        pattern = PLSEPattern.from_schema(schema)
        
        generation_result = generator.generate(pattern)
        
        if not generation_result:
            return pattern.pattern_id, ["Generation failed (e.g., Jinja error)."]
            
        code, _, _ = generation_result
        
        for validator in validators:
            result = validator.validate(code)
            if not result.valid:
                errors.extend(result.errors)
                
        return pattern.pattern_id, errors
    except Exception as e:
        # Catch any unexpected errors during reconstruction or validation
        return pattern_id, [f"Worker process failed: {type(e).__name__}: {e}"]


def analyze_and_suggest_fixes(pattern_id: str, errors: List[str]):
    """Analyzes errors and provides actionable suggestions."""
    print(f"  - ❌ {pattern_id} ({len(errors)} errors):")
    for error in errors:
        print(f"    - {error}")
        if "F401" in error and "imported but unused" in error:
            module_name = error.split("'")[1]
            print(f"    💡 SUGGESTION: Remove '{module_name}' from the 'requires' list in the corresponding YAML file.")
        if "F821" in error and "undefined name" in error:
            name = error.split("'")[1]
            print(f"    💡 SUGGESTION: Add the module providing '{name}' to the 'requires' list (e.g., 'numpy as np').")

def main():
    """Main entry point for the parallel linter."""
    print("="*80)
    print("🚀 Starting PLSE High-Performance Pattern Linter 🚀")
    print("="*80)

    try:
        registry = PatternRegistry(patterns_dir="patterns")
    except FileNotFoundError as e:
        print(f"FATAL: {e}")
        sys.exit(1)

    if not registry.patterns:
        print("No patterns found to lint.")
        return

    pattern_dicts = [asdict(p) for p in registry.patterns]
    failed_patterns: Dict[str, List[str]] = {}
    passed_count = 0
    num_workers = min(4, os.cpu_count() or 1)
    print(f"Found {len(registry)} patterns. Starting parallel check with {num_workers} workers...")

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(check_single_pattern, pd): pd for pd in pattern_dicts}
        
        try:
            from tqdm import tqdm
            progress_iterator = tqdm(as_completed(futures), total=len(futures), desc="Linting Patterns")
        except ImportError:
            print("tqdm not found, running without progress bar.")
            progress_iterator = as_completed(futures)

        for future in progress_iterator:
            pattern_id, errors = future.result()
            if errors:
                failed_patterns[pattern_id] = errors
            else:
                passed_count += 1

    print("\n" + "="*80)
    print("📊 Linter Run Summary")
    print("="*80)
    
    if not failed_patterns:
        print(f"🎉 Excellent! All {passed_count} patterns passed static validation.")
    else:
        print(f"✅ {passed_count} patterns passed.")
        print(f"❌ Found issues in {len(failed_patterns)} patterns:")
        for pattern_id in sorted(failed_patterns.keys()):
            errors = failed_patterns[pattern_id]
            analyze_and_suggest_fixes(pattern_id, errors)
            
    print("="*80)

if __name__ == "__main__":
    main()
