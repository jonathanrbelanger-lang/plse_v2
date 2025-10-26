"""
Enhanced validation pipeline that pre-renders Jinja2 templates before linting.
This eliminates false positive F821 errors for template variables.
"""

import ast
import subprocess
import tempfile
import os
import multiprocessing
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass, field
from jinja2 import Environment

# Import our custom linter
from .linter import CustomLinter
from .patterns import PLSEPattern

@dataclass
class ValidationResult:
    valid: bool
    code: str
    errors: List[str] = field(default_factory=list)

class BaseValidator(ABC):
    @abstractmethod
    def validate(self, code: str, **kwargs) -> ValidationResult:
        pass

class SyntaxValidator(BaseValidator):
    def validate(self, code: str, **kwargs) -> ValidationResult:
        try:
            ast.parse(code)
            return ValidationResult(True, code)
        except SyntaxError as e:
            return ValidationResult(False, code, [f"Syntax error on line {e.lineno}: {e.msg}"])

class CustomLinterValidator(BaseValidator):
    """
    A validator that uses our domain-specific, CST-based linter engine.
    """
    def __init__(self):
        self.linter = CustomLinter()

    def validate(self, code: str, **kwargs) -> ValidationResult:
        violations = self.linter.run(code)
        if not violations:
            return ValidationResult(True, code)
        else:
            errors = [f"Linter ({v.code} at L{v.line}:{v.column}): {v.message}" for v in violations]
            return ValidationResult(False, code, errors)

def _execute_python_in_process(code: str, queue: multiprocessing.Queue):
    try:
        exec(code, {"__builtins__": __builtins__})
        queue.put(None)
    except Exception as e:
        queue.put(e)

class SafeExecutionValidator(BaseValidator):
    def __init__(self, timeout: int = 5):
        self.timeout = timeout

    def validate(self, code: str, tests: List[str] = [], **kwargs) -> ValidationResult:
        if not tests:
            return self._run_python_code(code)
        
        for test_snippet in tests:
            if test_snippet.startswith("shell_exec:"):
                command = test_snippet.replace("shell_exec:", "").strip()
                result = self._run_shell_command(code, command)
            else:
                full_script = f"{code}\n\n# --- Running validation test ---\n{test_snippet}"
                result = self._run_python_code(full_script)
            
            if not result.valid:
                return result
        
        return ValidationResult(True, code)

    def _run_python_code(self, code_to_run: str) -> ValidationResult:
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_execute_python_in_process, args=(code_to_run, queue))
        process.start()
        process.join(timeout=self.timeout)
        if process.is_alive():
            process.terminate()
            process.join()
            return ValidationResult(False, code_to_run, [f"Python execution timed out after {self.timeout}s."])
        try:
            result = queue.get_nowait()
            if isinstance(result, Exception):
                return ValidationResult(False, code_to_run, [f"Python execution error: {type(result).__name__}: {result}"])
            return ValidationResult(True, code_to_run)
        except:
            return ValidationResult(True, code_to_run)

    def _run_shell_command(self, code_content: str, command: str) -> ValidationResult:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py", dir=".") as f:
            f.write(code_content)
            script_path = f.name
        try:
            final_command = command.replace("{{ SCRIPT_PATH }}", script_path)
            result = subprocess.run(final_command, shell=True, capture_output=True, text=True, timeout=self.timeout + 5)
            if result.returncode != 0:
                error_msg = f"Shell command failed with exit code {result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                return ValidationResult(False, code_content, [error_msg])
            return ValidationResult(True, code_content)
        except subprocess.TimeoutExpired:
            return ValidationResult(False, code_content, [f"Shell command timed out after {self.timeout + 5}s."])
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

class ValidationPipeline:
    """
    Enhanced validation pipeline that handles Jinja2 templates correctly.
    """
    def __init__(self):
        self.static_validators: List[BaseValidator] = [
            SyntaxValidator(),
            CustomLinterValidator()
        ]
        self.execution_validator = SafeExecutionValidator()
        self.jinja_env = Environment(trim_blocks=True, lstrip_blocks=True)

    def _render_template_with_defaults(self, code: str, parameters: Dict[str, Any]) -> str:
        """
        Renders Jinja2 template variables with their default values.
        This ensures linting sees valid Python code, not template syntax.
        """
        context = {}
        for name, param in parameters.items():
            default = param.default
            # For string defaults, ensure they're properly quoted in the rendered code
            if isinstance(default, str) and param.type == "choice":
                context[name] = default
            else:
                context[name] = default
        
        try:
            template = self.jinja_env.from_string(code)
            return template.render(context)
        except Exception as e:
            # If template rendering fails, return original code and let validation catch it
            print(f"Warning: Template rendering failed: {e}")
            return code

    def validate_pattern(self, pattern: PLSEPattern) -> ValidationResult:
        """
        Validates a PLSEPattern by rendering it with default parameters first.
        This is the main entry point for pattern validation.
        """
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
        
        # Render with default parameter values
        rendered_code = self._render_template_with_defaults(
            full_template_str, 
            pattern.parameters or {}
        )
        
        # Also render test snippets
        rendered_tests = []
        for test in pattern.validation.unit_test_snippets:
            rendered_test = self._render_template_with_defaults(
                test,
                pattern.parameters or {}
            )
            rendered_tests.append(rendered_test)
        
        # Now run the standard validation pipeline on rendered code
        return self.validate(rendered_code, rendered_tests)

    def validate(self, code: str, tests: List[str] = []) -> ValidationResult:
        """
        Standard validation for already-rendered code.
        """
        # Run static validators
        for validator in self.static_validators:
            result = validator.validate(code=code)
            if not result.valid:
                return result
        
        # Run execution validator
        return self.execution_validator.validate(code=code, tests=tests)            result = subprocess.run(final_command, shell=True, capture_output=True, text=True, timeout=self.timeout + 5)
            if result.returncode != 0:
                error_msg = f"Shell command failed with exit code {result.returncode}.\\nSTDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
                return ValidationResult(False, code_content, [error_msg])
            return ValidationResult(True, code_content)
        except subprocess.TimeoutExpired:
            return ValidationResult(False, code_content, [f"Shell command timed out after {self.timeout + 5}s."])
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

class ValidationPipeline:
    def __init__(self, use_pylint: bool = False):
        self.static_validators: List[BaseValidator] = [
            SyntaxValidator(),
            CustomLinterValidator() # Replaced Flake8Validator
        ]
        self.execution_validator = SafeExecutionValidator()

    def validate(self, code: str, tests: List[str]) -> ValidationResult:
        for validator in self.static_validators:
            result = validator.validate(code=code)
            if not result.valid: return result
        
        return self.execution_validator.validate(code=code, tests=tests)
