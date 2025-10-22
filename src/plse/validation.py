"""
Contains the multi-stage ValidationPipeline and all individual validator classes.
"""
from dataclasses import dataclass, field
from typing import List
import ast
import multiprocessing
from abc import ABC, abstractmethod
from flake8.api import legacy as flake8

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

class Flake8Validator(BaseValidator):
    def __init__(self):
        self.style_guide = flake8.get_style_guide(ignore=['E501', 'W292', 'F841'])

    def validate(self, code: str, **kwargs) -> ValidationResult:
        report = self.style_guide.check_source(code)
        if report.total_errors == 0:
            return ValidationResult(True, code)
        errors = [f"Flake8 ({e.code}): {e.text}" for e in report.errors]
        return ValidationResult(False, code, errors[:5])

def _execute_code_in_process(code: str, queue: multiprocessing.Queue):
    try:
        exec(code, {"__builtins__": __builtins__})
        queue.put(None)
    except Exception as e:
        queue.put(e)

class SafeExecutionValidator(BaseValidator):
    def __init__(self, timeout: int = 2):
        self.timeout = timeout

    def validate(self, code: str, **kwargs) -> ValidationResult:
        queue = multiprocessing.Queue()
        process = multiprocessing.Process(target=_execute_code_in_process, args=(code, queue))
        process.start()
        process.join(timeout=self.timeout)
        if process.is_alive():
            process.terminate(); process.join()
            return ValidationResult(False, code, [f"Execution timed out after {self.timeout}s."])
        try:
            result = queue.get_nowait()
            if isinstance(result, Exception):
                return ValidationResult(False, code, [f"Execution error: {type(result).__name__}: {result}"])
            return ValidationResult(True, code)
        except multiprocessing.queues.Empty:
            return ValidationResult(True, code)

class ValidationPipeline:
    def __init__(self, use_pylint: bool = False):
        self.static_validators: List[BaseValidator] = [SyntaxValidator(), Flake8Validator()]
        self.execution_validator = SafeExecutionValidator(timeout=3)
        self.test_validator = SafeExecutionValidator(timeout=5)

    def validate(self, code: str, tests: List[str]) -> ValidationResult:
        for validator in self.static_validators:
            result = validator.validate(code=code)
            if not result.valid: return result
        
        exec_result = self.execution_validator.validate(code=code)
        if not exec_result.valid:
            exec_result.errors = [f"Main code failed execution: {exec_result.errors[0]}"]
            return exec_result

        if not tests: return ValidationResult(True, code)

        for test_snippet in tests:
            full_script = f"{code}\n\n# --- Running validation test ---\n{test_snippet}"
            test_result = self.test_validator.validate(full_script)
            if not test_result.valid:
                test_result.errors = [f"Unit test failed: {test_result.errors[0]}"]
                return test_result
        
        return ValidationResult(True, code)