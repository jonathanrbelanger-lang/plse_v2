"""
Defines the PLSEGenerator, the core engine for synthesizing code using Jinja2.
"""

import random
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from jinja2 import Environment, TemplateSyntaxError

from .patterns import PLSEPattern

class PLSEGenerator:
    """
    Generates Python code by rendering a PLSEPattern with a dynamically
    instantiated parameter context using the Jinja2 templating engine.
    """
    def __init__(self):
        self.generated_hashes: set[str] = set()
        self.jinja_env = Environment(trim_blocks=True, lstrip_blocks=True)

    def _instantiate_parameters(self, pattern: PLSEPattern) -> Dict[str, Any]:
        context = {}
        for name, param in pattern.parameters.items():
            if param.type == "choice":
                options = param.constraints.get("options", [param.default]) if param.constraints else [param.default]
                context[name] = random.choice(options)
            else:
                context[name] = param.default
        return context

    def generate(self, pattern: PLSEPattern) -> Optional[Tuple[str, str, List[str]]]:
        parameter_context = self._instantiate_parameters(pattern)

        try:
            # Render the instruction separately
            instruction_template = self.jinja_env.from_string(pattern.instruction)
            rendered_instruction = instruction_template.render(parameter_context)

            # --- LOGIC FIX: Assemble the full code template BEFORE rendering ---
            components = pattern.components
            full_template_str = "\n\n".join(filter(None, [
                components.imports,
                components.data_setup,
                components.training_loop,
                components.evaluation,
                components.model_definition
            ]))

            # Now, render the single, assembled template
            code_template = self.jinja_env.from_string(full_template_str)
            full_code = code_template.render(parameter_context)

            # Render the validation snippets
            rendered_tests = [
                self.jinja_env.from_string(test).render(parameter_context)
                for test in pattern.validation.unit_test_snippets
            ]

        except TemplateSyntaxError as e:
            print(f"Jinja2 template error in pattern '{pattern.pattern_id}': {e}")
            return None
        except Exception as e:
            print(f"Unexpected generation error in '{pattern.pattern_id}': {e}")
            return None

        # Check for uniqueness
        code_hash = hashlib.md5(full_code.encode()).hexdigest()
        if code_hash in self.generated_hashes:
            return None
        self.generated_hashes.add(code_hash)

        return full_code, rendered_instruction, rendered_tests
