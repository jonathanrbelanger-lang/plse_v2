"""
Defines the multi-stage validation pipeline for ensuring the quality of
generated code. It includes checks for syntax, style, unit tests, and
safe execution.
"""

import ast
import os
import tempfile
import multiprocessing
from io import StringIO
from typing import List

from flake8.api import legacy as flake8
from pylint import lint
from pylint.reporters.text import TextReporter

from .patterns import ValidationResult

# --- Stage 1: Syntax Validation ---
class SyntaxValidator:
    """Validates that the code is syntactically correct Python."""
    def validate(self, code: str, **kwargs) -> ValidationResult:
        try:
            ast.parse(code)
            return ValidationResult(True, code)
        except SyntaxError as e:
            return ValidationResult(False, code, [f"Syntax error: {e}"])

# --- Stage 2: Static Analysis ---
class Flake8Validator:
    """Validates code against PEP 8 style conventions using Flake8."""
    def validate(self, code: str, **kwargs) -> ValidationResult:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py") as f:
            f.write(code)
            filepath = f.name
        style_guide = flake8.get_style_guide()
        report = style_guide.check_files([filepath])
        os.remove(filepath)
        if report.total_errors == 0:
            return ValidationResult(True, code)
        else:
            errors = [f"Flake8: {e}" for e in report.get_statistics('')]
            return ValidationResult(False, code, errors[:5])

# --- Safe Execution Logic (Helper) ---
def _execute_code_in_process(code: str, queue: multiprocessing.Queue):
    """Target function to execute code in a separate process."""
    try:
        exec(code, {})
        queue.put(None)
    except Exception as e:
        queue.put(e)

class SafeExecutionValidator:
    """Executes code with a timeout to prevent infinite loops."""
    def __init__(self, timeout: int = 2):
        self.timeout = timeout

    def validate(self, code: str, **kwargs) -> ValidationResult:
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_execute_code_in_process, args=(code, queue))
        process.start()
        process.join(timeout=self.timeout)

        if process.is_alive():
            process.terminate()
            process.join()
            return ValidationResult(False, code, [f"Execution timeout after {self.timeout}s."])

        try:
            result = queue.get_nowait()
            if isinstance(result, Exception):
                return ValidationResult(False, code, [f"Execution error: {result}"])
            else:
                return ValidationResult(True, code)
        except multiprocessing.queues.Empty:
            return ValidationResult(False, code, ["Execution error: Process finished unexpectedly."])

# --- Stage 3: Unit Test Validation (New!) ---
class UnitTestValidator:
    """
    Runs the generated unit test snippets against the generated code.
    It reuses the SafeExecutionValidator to run the combined script.
    """
    def __init__(self, timeout: int = 3):
        self.execution_validator = SafeExecutionValidator(timeout)

    def validate(self, code: str, tests: List[str], **kwargs) -> ValidationResult:
        if not tests:
            return ValidationResult(True, code) # No tests to run, so it's valid.

        for test_snippet in tests:
            # Combine the generated code with one of its test snippets
            full_script = f"{code}\n\n# --- Running validation test ---\n{test_snippet}"
            
            # Run the combined script through the safe executor.
            # An AssertionError from a failing test will be caught as an Exception.
            result = self.execution_validator.validate(full_script)
            if not result.valid:
                result.errors = [f"Unit test failed: {result.errors[0]}"]
                return result
        
        return ValidationResult(True, code)

# --- The Main Pipeline Orchestrator ---
class ValidationPipeline:
    """Orchestrates a sequence of validators to ensure code quality."""
    def __init__(self, use_pylint: bool = False):
        # Pylint is not included by default as it's slow.
        # A full implementation would add it here conditionally.
        self.validators = [
            SyntaxValidator(),
            Flake8Validator(),
            UnitTestValidator(), # Add our new unit test validator to the sequence
        ]

    def validate(self, code: str, tests: List[str]) -> ValidationResult:
        """
        Runs the code and its tests through all validators in sequence.
        """
        for validator in self.validators:
            result = validator.validate(code=code, tests=tests)
            if not result.valid:
                return result
        return ValidationResult(True, code)
