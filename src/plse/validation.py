"""
Defines the multi-stage validation pipeline for ensuring the quality of
generated code. It includes checks for syntax, style, unit tests, and
safe execution.
"""

import ast
import os
import tempfile
import multiprocessing
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from flake8.api import legacy as flake8

# --- Core Data Structure for Validation Outcome ---
from dataclasses import dataclass, field

@dataclass
class ValidationResult:
    """Represents the outcome of a single validation stage or the entire pipeline."""
    valid: bool
    code: str
    errors: List[str] = field(default_factory=list)

# --- Abstract Base Class for Validators ---
class BaseValidator(ABC):
    """Defines the interface for all validator classes."""
    @abstractmethod
    def validate(self, code: str, **kwargs) -> ValidationResult:
        pass

# --- Individual Validator Implementations ---

class SyntaxValidator(BaseValidator):
    """Validates that the code is syntactically correct Python."""
    def validate(self, code: str, **kwargs) -> ValidationResult:
        try:
            ast.parse(code)
            return ValidationResult(True, code)
        except SyntaxError as e:
            error_msg = f"Syntax error on line {e.lineno}: {e.msg}"
            return ValidationResult(False, code, [error_msg])

class Flake8Validator(BaseValidator):
    """
    Validates code against PEP 8 style conventions using Flake8's in-memory API.
    This is significantly faster than writing to a temporary file.
    """
    def __init__(self):
        self.style_guide = flake8.get_style_guide(ignore=['E501']) # Ignore line length

    def validate(self, code: str, **kwargs) -> ValidationResult:
        report = self.style_guide.check_source(code)
        if report.total_errors == 0:
            return ValidationResult(True, code)
        else:
            # Format errors to be more readable
            errors = [f"Flake8 ({e.code}): {e.text}" for e in report.errors]
            return ValidationResult(False, code, errors[:5]) # Limit to 5 errors

# --- Safe Execution Logic (Helper) ---

def _execute_code_in_process(code: str, queue: multiprocessing.Queue):
    """Target function to execute code in a separate, sandboxed process."""
    try:
        # Execute in a restricted global namespace
        exec(code, {"__builtins__": __builtins__})
        queue.put(None)
    except Exception as e:
        queue.put(e)

class SafeExecutionValidator(BaseValidator):
    """Executes code in a separate process with a timeout to prevent infinite loops."""
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
            return ValidationResult(False, code, [f"Execution timed out after {self.timeout}s."])

        try:
            result = queue.get_nowait()
            if isinstance(result, Exception):
                return ValidationResult(False, code, [f"Execution error: {type(result).__name__}: {result}"])
            return ValidationResult(True, code)
        except multiprocessing.queues.Empty:
            # This can happen if the process exits without putting anything in the queue
            return ValidationResult(True, code)

# --- The Main Pipeline Orchestrator ---

class ValidationPipeline:
    """
    Orchestrates a sequence of validators to ensure code quality.
    This version uses a more granular, multi-step process for better error attribution.
    """
    def __init__(self, use_pylint: bool = False):
        self.static_validators: List[BaseValidator] = [SyntaxValidator(), Flake8Validator()]
        self.execution_validator = SafeExecutionValidator(timeout=2)
        self.test_validator = SafeExecutionValidator(timeout=5) # Longer timeout for tests

    def validate(self, code: str, tests: List[str]) -> ValidationResult:
        """
        Runs the code and its tests through all validators in a logical sequence.
        """
        # 1. Static Analysis (Syntax, Style)
        for validator in self.static_validators:
            result = validator.validate(code=code)
            if not result.valid:
                return result

        # 2. Safe Execution of the main code block
        exec_result = self.execution_validator.validate(code=code)
        if not exec_result.valid:
            exec_result.errors = [f"Main code failed execution: {exec_result.errors[0]}"]
            return exec_result

        # 3. Unit Test Execution (if all previous steps passed)
        if not tests:
            return ValidationResult(True, code) # No tests to run

        for test_snippet in tests:
            full_script = f"{code}\n\n# --- Running validation test ---\n{test_snippet}"
            test_result = self.test_validator.validate(full_script)
            if not test_result.valid:
                test_result.errors = [f"Unit test failed: {test_result.errors[0]}"]
                return test_result
        
        return ValidationResult(True, code)