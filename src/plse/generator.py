"""
Defines the CombinatorialCodeGenerator, the core engine for synthesizing code.
"""

import random
import hashlib
import autopep8
from typing import Optional, Tuple, Dict, Set

# Import our custom pattern definition
from .patterns import CombinatorialPattern

class CombinatorialCodeGenerator:
    """
    Generates Python code snippets by randomly combining bindings from the
    pools defined in a CombinatorialPattern.
    """

    def __init__(self):
        self.generated_hashes: Set[str] = set()

    def generate(self, pattern: CombinatorialPattern) -> Optional[Tuple[str, Dict[str, str]]]:
        """
        Generates a single, unique code snippet from a given pattern.

        This method performs the following steps:
        1. Creates a new "variant" on the fly by selecting one binding from each pool.
        2. Prepends the necessary import statements based on the pattern's 'requires' field.
        3. Substitutes the chosen bindings into the code template.
        4. Checks for uniqueness to avoid generating duplicates.
        5. Formats the code using autopep8.
        6. Returns the final code and the bindings used to create it.

        Args:
            pattern: The CombinatorialPattern to generate code from.

        Returns:
            A tuple containing the generated code string and the dictionary of
            bindings used, or None if generation fails (e.g., duplicate or error).
        """
        if not pattern or not pattern.binding_pools:
            return None

        # 1. Assemble a new, random "variant" on the fly.
        try:
            bindings = {
                key: random.choice(pool)
                for key, pool in pattern.binding_pools.items()
            }
        except IndexError:
            # This handles cases where a user defines a pattern with an empty binding pool.
            print(f"Error: Pattern '{pattern.name}' has an empty binding pool.")
            return None

        # 2. FIX: Implement the unused 'requires' field logic.
        import_statements = [f"import {req}" for req in pattern.requires]
        import_block = "\n".join(import_statements)

        # 3. Combine imports with the main template.
        code_template = pattern.template
        if import_block:
            code = f"{import_block}\n\n{code_template}"
        else:
            code = code_template

        # 4. Perform all substitutions from the generated bindings.
        for var_name, value in bindings.items():
            code = code.replace(f"{{{var_name}}}", str(value))
        
        # 5. Handle "nested" bindings (e.g., a description that uses another placeholder).
        # Running substitutions a second time is a simple and effective way to resolve these.
        for var_name, value in bindings.items():
            code = code.replace(f"{{{var_name}}}", str(value))

        # 6. Check for uniqueness using an MD5 hash.
        code_hash = hashlib.md5(code.encode()).hexdigest()
        if code_hash in self.generated_hashes:
            return None  # This is a duplicate, skip it.
        self.generated_hashes.add(code_hash)

        # 7. FIX: Format code with robust exception handling.
        try:
            # Replaced the unsafe 'except: pass' with specific, meaningful handling.
            formatted_code = autopep8.fix_code(code)
        except (IndentationError, SyntaxError):
            # If autopep8 fails, the generated code is likely malformed. Discard it.
            return None

        # Return both the code and the bindings that created it.
        # This is crucial for our new, robust instruction labeling system.
        return formatted_code, bindings
