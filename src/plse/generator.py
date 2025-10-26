"""
Enhanced PLSEGenerator that integrates with the template-aware validation pipeline.
"""

import random
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from jinja2 import Environment, TemplateSyntaxError

from .patterns import PLSEPattern
from .validation import ValidationPipeline, ValidationResult

class PLSEGenerator:
    """
    Generates Python code by rendering a PLSEPattern with a dynamically
    instantiated parameter context using the Jinja2 templating engine.
    Now with integrated validation.
    """
    def __init__(self, validate: bool = True):
        self.generated_hashes: set[str] = set()
        self.jinja_env = Environment(trim_blocks=True, lstrip_blocks=True)
        self.validate = validate
        if validate:
            self.validation_pipeline = ValidationPipeline()

    def _instantiate_parameters(self, pattern: PLSEPattern) -> Dict[str, Any]:
        """Generates a concrete set of values from the pattern's parameter schema."""
        context = {}
        if not pattern.parameters:
            return context
            
        for name, param in pattern.parameters.items():
            if param.type == "choice":
                options = param.constraints.get("options", [param.default]) if param.constraints else [param.default]
                context[name] = random.choice(options)
            else:
                context[name] = param.default
        return context

    def generate(self, pattern: PLSEPattern, skip_validation: bool = False) -> Optional[Tuple[str, str, List[str]]]:
        """
        Generates a single, unique code example from a given pattern.
        
        Args:
            pattern: The PLSEPattern to generate from
            skip_validation: If True, skips validation (useful for bulk generation)
        
        Returns:
            Tuple of (code, instruction, tests) or None if generation/validation fails
        """
        parameter_context = self._instantiate_parameters(pattern)

        try:
            # Render the instruction separately
            instruction_template = self.jinja_env.from_string(pattern.instruction)
            rendered_instruction = instruction_template.render(parameter_context)

            # Assemble the full code template
            components = pattern.components
            code_parts = filter(None, [
                components.imports,
                components.data_setup,
                components.training_loop,
                components.evaluation,
                components.model_definition
            ])
            full_template_str = "\n\n".join(code_parts)

            # Render the assembled template
            code_template = self.jinja_env.from_string(full_template_str)
            full_code = code_template.render(parameter_context).strip()

            # Render the validation snippets
            rendered_tests = [
                self.jinja_env.from_string(test).render(parameter_context)
                for test in pattern.validation.unit_test_snippets
            ]

        except TemplateSyntaxError as e:
            print(f"Jinja2 template error in pattern '{pattern.pattern_id}': {e}")
            return None
        except Exception as e:
            print(f"Unexpected generation error in '{pattern.pattern_id}': {type(e).__name__}: {e}")
            return None

        # Check for uniqueness
        if not full_code:
            return None
        code_hash = hashlib.md5(full_code.encode()).hexdigest()
        if code_hash in self.generated_hashes:
            return None
        self.generated_hashes.add(code_hash)

        # NEW: Optional validation of generated code
        if self.validate and not skip_validation:
            validation_result = self.validation_pipeline.validate(
                code=full_code,
                tests=rendered_tests
            )
            if not validation_result.valid:
                print(f"Validation failed for pattern '{pattern.pattern_id}':")
                for error in validation_result.errors:
                    print(f"  - {error}")
                return None

        return full_code, rendered_instruction, rendered_tests

    def generate_batch(self, pattern: PLSEPattern, count: int = 10, 
                      validate_sample: bool = True) -> List[Tuple[str, str, List[str]]]:
        """
        Generate multiple unique samples from a pattern.
        
        Args:
            pattern: The PLSEPattern to generate from
            count: Number of samples to attempt generating
            validate_sample: If True, validates the first sample only (for speed)
        
        Returns:
            List of (code, instruction, tests) tuples
        """
        samples = []
        
        for i in range(count):
            # Only validate the first sample to catch pattern-level issues
            skip_validation = (i > 0) if validate_sample else True
            
            result = self.generate(pattern, skip_validation=skip_validation)
            if result:
                samples.append(result)
        
        return samples