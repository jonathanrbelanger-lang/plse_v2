"""
Defines the multi-stage validation pipeline. This version uses our new
custom, CST-based linter instead of the generic flake8.
"""

import ast
import subprocess
import tempfile
import os
import multiprocessing
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass, field

# Import our new custom linter
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
    """
    A validator that uses our domain-specific, CST-based linter engine.
    This replaces the old Flake8Validator.
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

# ... (The SafeExecutionValidator and its helper function remain unchanged) ...
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
            process.terminate(); process.join()
            return ValidationResult(False, code_to_run, [f"Python execution timed out after {self.timeout}s."])
        try:
            result = queue.get_nowait()
            if isinstance(result, Exception):
                return ValidationResult(False, code_to_run, [f"Python execution error: {type(result).__name__}: {result}"])
            return ValidationResult(True, code_to_run)
        except multiprocessing.queues.Empty:
            return ValidationResult(True, code_to_run)

    def _run_shell_command(self, code_content: str, command: str) -> ValidationResult:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py", dir=".") as f:
            f.write(code_content)
            script_path = f.name
        try:
            final_command = command.replace("{{ SCRIPT_PATH }}", script_path)
            result = subprocess.run(final_command, shell=True, capture_output=True, text=True, timeout=self.timeout + 5)
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