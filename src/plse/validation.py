"""
Enhanced validation pipeline with Jinja2 template pre-rendering.
This eliminates F821 false positives for template variables.
"""

import ast
import subprocess
import tempfile
import os
import multiprocessing
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass, field
from jinja2 import Environment, TemplateSyntaxError

from .linter import CustomLinter

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
    def __init__(self, use_pylint: bool = False):
        self.static_validators: List[BaseValidator] = [
            SyntaxValidator(),
            CustomLinterValidator()
        ]
        self.execution_validator = SafeExecutionValidator()
        # NEW: Jinja2 environment for template rendering
        self.jinja_env = Environment(trim_blocks=True, lstrip_blocks=True)

    def _render_template_with_defaults(self, template_str: str, parameters: Dict[str, Any]) -> str:
        """
        Renders Jinja2 template variables with their default parameter values.
        This ensures linting sees valid Python code, not template syntax.
        
        Args:
            template_str: Code string potentially containing {{ var }} expressions
            parameters: Dict mapping parameter names to Parameter objects
        
        Returns:
            Rendered code string with all template variables substituted
        """
        # Build context from parameter defaults
        context = {}
        for name, param in parameters.items():
            context[name] = param.default
        
        try:
            template = self.jinja_env.from_string(template_str)
            return template.render(context)
        except TemplateSyntaxError as e:
            # If template has syntax errors, return original and let validation catch it
            return template_str
        except Exception as e:
            # Any other rendering errors, return original
            return template_str

    def validate(self, code: str, tests: List[str] = [], parameters: Dict[str, Any] = None) -> ValidationResult:
        """
        Standard validation pipeline. Now with optional template rendering.
        
        Args:
            code: The code to validate (may contain Jinja2 templates)
            tests: Unit test snippets to run
            parameters: Optional dict of Parameter objects for template rendering
        """
        # NEW: Pre-render templates if parameters are provided
        if parameters:
            code = self._render_template_with_defaults(code, parameters)
            # Also render test snippets
            rendered_tests = []
            for test in tests:
                rendered_tests.append(self._render_template_with_defaults(test, parameters))
            tests = rendered_tests
        
        # Run static validators
        for validator in self.static_validators:
            result = validator.validate(code=code)
            if not result.valid:
                return result
        
        # Run execution validator
        return self.execution_validator.validate(code=code, tests=tests)