"""
Defines the multi-stage validation pipeline for ensuring the quality of
generated code. It includes checks for syntax, style, code smells, and
safe execution.
"""

import ast
import os
import tempfile
import multiprocessing
from io import StringIO

# These are external libraries we defined in pyproject.toml
from flake8.api import legacy as flake8
from pylint import lint
from pylint.reporters.text import TextReporter

from .patterns import ValidationResult

# --- Stage 1: Syntax Validation (Fastest) ---

class SyntaxValidator:
    """Validates that the code is syntactically correct Python."""

    def validate(self, code: str) -> ValidationResult:
        try:
            ast.parse(code)
            return ValidationResult(True, code)
        except SyntaxError as e:
            return ValidationResult(False, code, [f"Syntax error: {e}"])

# --- Stage 2: Static Analysis (Style and Code Smells) ---

class Flake8Validator:
    """Validates code against PEP 8 style conventions using Flake8."""

    def validate(self, code: str) -> ValidationResult:
        # The flake8 API is designed to wo"""
Defines the multi-stage validation pipeline for ensuring the quality of
generated code. It includes checks for syntax, style, code smells, and
safe execution.
"""

import ast
import os
import tempfile
import multiprocessing
from io import StringIO

# These are external libraries we defined in pyproject.toml
from flake8.api import legacy as flake8
from pylint import lint
from pylint.reporters.text import TextReporter

from .patterns import ValidationResult

# --- Stage 1: Syntax Validation (Fastest) ---

class SyntaxValidator:
    """Validates that the code is syntactically correct Python."""

    def validate(self, code: str) -> ValidationResult:
        try:
            ast.parse(code)
            return ValidationResult(True, code)
        except SyntaxError as e:
            return ValidationResult(False, code, [f"Syntax error: {e}"])

# --- Stage 2: Static Analysis (Style and Code Smells) ---

class Flake8Validator:
    """Validates code against PEP 8 style conventions using Flake8."""

    def validate(self, code: str) -> ValidationResult:
        # The flake8 API is designed to work with files, so we write the code
        # to a temporary file to be scanned.
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py") as f:
            f.write(code)
            filepath = f.name

        style_guide = flake8.get_style_guide()
        report = style_guide.check_files([filepath])

        os.remove(filepath)  # Clean up the temporary file

        if report.total_errors == 0:
            return ValidationResult(True, code)
        else:
            # Collect the error messages for debugging.
            errors = [f"Flake8: {e}" for e in report.get_statistics('')]
            return ValidationResult(False, code, errors[:5]) # Return first 5 errors

class PylintValidator:
    """Validates code for 'code smells' and deeper issues using Pylint."""

    def validate(self, code: str) -> ValidationResult:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py") as f:
            f.write(code)
            filepath = f.name

        reporter_output = StringIO()
        reporter = TextReporter(reporter_output)

        # Run pylint programmatically.
        lint.Run([filepath], reporter=reporter, exit=False)

        os.remove(filepath)

        output = reporter_output.getvalue()
        # A perfect score or no output means it's valid.
        if "Your code has been rated at 10.00/10" in output or not output.strip():
            return ValidationResult(True, code)
        else:
            # Parse the output to get meaningful error messages.
            errors = [line for line in output.split('\n') if line.strip() and not line.startswith('***')]
            return ValidationResult(False, code, errors[:3]) # Return first 3 errors

# --- Stage 3: Safe Execution (with Timeout) ---

def _execute_code_in_process(code: str, queue: multiprocessing.Queue):
    """
    A target function to execute code in a separate process.
    Communicates results back to the parent via a queue.
    """
    try:
        exec(code, {})
        queue.put(None)  # Signal success
    except Exception as e:
        queue.put(e)  # Put the exception object in the queue to signal failure

class SafeExecutionValidator:
    """
    Validates that the code executes without errors and, crucially, with a timeout
    to prevent infinite loops from halting the entire generator.
    """
    def __init__(self, timeout: int = 2):
        self.timeout = timeout

    def validate(self, code: str) -> ValidationResult:
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_execute_code_in_process, args=(code, queue))

        process.start()
        process.join(timeout=self.timeout)

        if process.is_alive():
            # Process is still running after the timeout.
            process.terminate()
            process.join()
            return ValidationResult(
                False, code, [f"Execution error: Timeout after {self.timeout} seconds (possible infinite loop)."]
            )

        # Process finished, check the queue for an exception.
        try:
            result = queue.get_nowait()
            if isinstance(result, Exception):
                return ValidationResult(False, code, [f"Execution error: {result}"])
            else:
                return ValidationResult(True, code)  # Success
        except multiprocessing.queues.Empty:
            # This can happen in rare cases if the process terminates unexpectedly.
            return ValidationResult(False, code, ["Execution error: Process finished but no result was returned."])

# --- The Main Pipeline Orchestrator ---

class ValidationPipeline:
    """
    Orchestrates a sequence of validators to ensure code quality.
    It follows a fail-fast approach.
    """
    def __init__(self, use_pylint: bool = False):
        """
        Initializes the pipeline with a sequence of validators.

        Args:
            use_pylint (bool): Whether to include the PylintValidator, which is
                               more thorough but significantly slower.
        """
        self.validators = [
            SyntaxValidator(),       # Stage 1 (Fastest)
            Flake8Validator(),       # Stage 2 (Style)
        ]
        if use_pylint:
            self.validators.append(PylintValidator()) # Stage 2.5 (Deep Linting)
        
        self.validators.append(SafeExecutionValidator()) # Stage 3 (Execution)

    def validate(self, code: str) -> ValidationResult:
        """
        Runs the given code through all validators in sequence.

        If any validator fails, the pipeline stops and returns the failure result
        immediately (fail-fast).

        Args:
            code: The code string to validate.

        Returns:
            A ValidationResult object indicating success or the first failure.
        """
        for validator in self.validators:
            result = validator.validate(code)
            if not result.valid:
                return result  # Fail-fast
        return ValidationResult(True, code)rk with files, so we write the code
        # to a temporary file to be scanned.
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py") as f:
            f.write(code)
            filepath = f.name

        style_guide = flake8.get_style_guide()
        report = style_guide.check_files([filepath])

        os.remove(filepath)  # Clean up the temporary file

        if report.total_errors == 0:
            return ValidationResult(True, code)
        else:
            # Collect the error messages for debugging.
            errors = [f"Flake8: {e}" for e in report.get_statistics('')]
            return ValidationResult(False, code, errors[:5]) # Return first 5 errors

class PylintValidator:
    """Validates code for 'code smells' and deeper issues using Pylint."""

    def validate(self, code: str) -> ValidationResult:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".py") as f:
            f.write(code)
            filepath = f.name

        reporter_output = StringIO()
        reporter = TextReporter(reporter_output)

        # Run pylint programmatically.
        lint.Run([filepath], reporter=reporter, exit=False)

        os.remove(filepath)

        output = reporter_output.getvalue()
        # A perfect score or no output means it's valid.
        if "Your code has been rated at 10.00/10" in output or not output.strip():
            return ValidationResult(True, code)
        else:
            # Parse the output to get meaningful error messages.
            errors = [line for line in output.split('\n') if line.strip() and not line.startswith('***')]
            return ValidationResult(False, code, errors[:3]) # Return first 3 errors

# --- Stage 3: Safe Execution (with Timeout) ---

def _execute_code_in_process(code: str, queue: multiprocessing.Queue):
    """
    A target function to execute code in a separate process.
    Communicates results back to the parent via a queue.
    """
    try:
        exec(code, {})
        queue.put(None)  # Signal success
    except Exception as e:
        queue.put(e)  # Put the exception object in the queue to signal failure

class SafeExecutionValidator:
    """
    Validates that the code executes without errors and, crucially, with a timeout
    to prevent infinite loops from halting the entire generator.
    """
    def __init__(self, timeout: int = 2):
        self.timeout = timeout

    def validate(self, code: str) -> ValidationResult:
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_execute_code_in_process, args=(code, queue))

        process.start()
        process.join(timeout=self.timeout)

        if process.is_alive():
            # Process is still running after the timeout.
            process.terminate()
            process.join()
            return ValidationResult(
                False, code, [f"Execution error: Timeout after {self.timeout} seconds (possible infinite loop)."]
            )

        # Process finished, check the queue for an exception.
        try:
            result = queue.get_nowait()
            if isinstance(result, Exception):
                return ValidationResult(False, code, [f"Execution error: {result}"])
            else:
                return ValidationResult(True, code)  # Success
        except multiprocessing.queues.Empty:
            # This can happen in rare cases if the process terminates unexpectedly.
            return ValidationResult(False, code, ["Execution error: Process finished but no result was returned."])

# --- The Main Pipeline Orchestrator ---

class ValidationPipeline:
    """
    Orchestrates a sequence of validators to ensure code quality.
    It follows a fail-fast approach.
    """
    def __init__(self, use_pylint: bool = False):
        """
        Initializes the pipeline with a sequence of validators.

        Args:
            use_pylint (bool): Whether to include the PylintValidator, which is
                               more thorough but significantly slower.
        """
        self.validators = [
            SyntaxValidator(),       # Stage 1 (Fastest)
            Flake8Validator(),       # Stage 2 (Style)
        ]
        if use_pylint:
            self.validators.append(PylintValidator()) # Stage 2.5 (Deep Linting)
        
        self.validators.append(SafeExecutionValidator()) # Stage 3 (Execution)

    def validate(self, code: str) -> ValidationResult:
        """
        Runs the given code through all validators in sequence.

        If any validator fails, the pipeline stops and returns the failure result
        immediately (fail-fast).

        Args:
            code: The code string to validate.

        Returns:
            A ValidationResult object indicating success or the first failure.
        """
        for validator in self.validators:
            result = validator.validate(code)
            if not result.valid:
                return result  # Fail-fast
        return ValidationResult(True, code)
