"""
Defines the PLSEGenerator, the core engine for synthesizing code using Jinja2.
"""

import random
import hashlib
import autopep8
from typing import Optional, Tuple, Dict, Any, List
from jinja2 import Environment, TemplateSyntaxError

# Import our new, schema-aligned pattern definition
from .patterns import PLSEPattern, Validation

class PLSEGenerator:
    """
    Generates Python code by rendering a PLSEPattern with a dynamically
    instantiated parameter context using the Jinja2 templating engine.
    """

    def __init__(self):
        self.generated_hashes: set[str] = set()
        self.jinja_env = Environment(
            trim_blocks=True, lstrip_blocks=True
        )

    def _instantiate_parameters(self, pattern: PLSEPattern) -> Dict[str, Any]:
        """
        Generates a concrete set of values from the pattern's parameter schema.
        """
        context = {}
        for name, param in pattern.parameters.items():
            if param.type == "choice":
                context[name] = random.choice(param.constraints.get("options", [param.default]))
            # Future parameter types (e.g., "int", "float") would be handled here.
            else:
                context[name] = param.default
        return context

    def generate(self, pattern: PLSEPattern) -> Optional[Tuple[str, str, List[str]]]:
        """
        Generates a single, unique code example from a given pattern.

        Args:
            pattern: The PLSEPattern to render.

        Returns:
            A tuple containing:
            - The final, assembled code string.
            - The rendered instruction string.
            - A list of rendered unit test snippet strings.
            Returns None if generation fails.
        """
        # 1. Create a concrete set of parameters for this instance.
        parameter_context = self._instantiate_parameters(pattern)

        try:
            # 2. Render all components using the Jinja2 engine.
            
            # Render the instruction
            instruction_template = self.jinja_env.from_string(pattern.instruction)
            rendered_instruction = instruction_template.render(parameter_context)

            # Render each architectural code component
            components = pattern.components
            rendered_imports = self.jinja_env.from_string(components.imports).render(parameter_context)
            rendered_model_def = self.jinja_env.from_string(components.model_definition).render(parameter_context)
            rendered_training_loop = self.jinja_env.from_string(components.training_loop).render(parameter_context)
            rendered_evaluation = self.jinja_env.from_string(components.evaluation).render(parameter_context)

            # Render the validation snippets
            rendered_tests = [
                self.jinja_env.from_string(test).render(parameter_context)
                for test in pattern.validation.unit_test_snippets
            ]

        except TemplateSyntaxError as e:
            print(f"Jinja2 template error in pattern '{pattern.pattern_id}': {e}")
            return None

        # 3. Assemble the final code string in a logical order.
        full_code = "\n\n".join(filter(None, [
            rendered_imports,
            rendered_model_def,
            rendered_training_loop,
            rendered_evaluation
        ])).strip()

        # 4. Check for uniqueness.
        code_hash = hashlib.md5(full_code.encode()).hexdigest()
        if code_hash in self.generated_hashes:
            return None  # Duplicate
        self.generated_hashes.add(code_hash)

        # 5. Format the final code.
        try:
            formatted_code = autopep8.fix_code(full_code)
        except (IndentationError, SyntaxError):
            return None # Discard malformed code

        return formatted_code, rendered_instruction, rendered_tests
