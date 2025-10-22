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

    def _render_component(self, template_str: Optional[str], context: Dict[str, Any]) -> str:
        """Safely renders a single Jinja2 template string, handling None."""
        if not template_str:
            return ""
        template = self.jinja_env.from_string(template_str)
        return template.render(context)

    def generate(self, pattern: PLSEPattern) -> Optional[Tuple[str, str, List[str]]]:
        parameter_context = self._instantiate_parameters(pattern)

        try:
            rendered_instruction = self._render_component(pattern.instruction, parameter_context)
            
            components = pattern.components
            rendered_imports = self._render_component(components.imports, parameter_context)
            rendered_data_setup = self._render_component(components.data_setup, parameter_context)
            rendered_model_def = self._render_component(components.model_definition, parameter_context)
            rendered_training_loop = self._render_component(components.training_loop, parameter_context)
            rendered_evaluation = self._render_component(components.evaluation, parameter_context)

            rendered_tests = [
                self._render_component(test, parameter_context)
                for test in pattern.validation.unit_test_snippets
            ]

        except TemplateSyntaxError as e:
            print(f"Jinja2 template error in pattern '{pattern.pattern_id}': {e}")
            return None

        # Assemble the final code string, filtering out empty components.
        code_parts = [
            rendered_imports,
            rendered_data_setup,
            rendered_model_def,
            rendered_training_loop,
            rendered_evaluation
        ]
        full_code = "\n\n".join(part for part in code_parts if part and not part.isspace())

        # Check for uniqueness to avoid duplicates in the dataset
        code_hash = hashlib.md5(full_code.encode()).hexdigest()
        if code_hash in self.generated_hashes:
            return None
        self.generated_hashes.add(code_hash)

        # NOTE: autopep8 formatting is removed for now to simplify dependencies.
        # It can be added back as a post-processing step.
        return full_code, rendered_instruction, rendered_tests