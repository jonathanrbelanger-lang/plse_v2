"""
The PLSE v2.0 Domain-Specific Linter Engine.

This module is built on LibCST to provide a robust, extensible, and
eventually auto-fixing static analysis tool for our generated code.
"""

import libcst as cst
from dataclasses import dataclass
from typing import List, Type

@dataclass
class LintViolation:
    """Represents a single violation found by a linter rule."""
    line: int
    column: int
    code: str
    message: str

class BaseLinterRule(cst.CSTVisitor):
    """Abstract base class for all linter rules."""
    def __init__(self):
        self.violations: List[LintViolation] = []

    def add_violation(self, node: cst.CSTNode, code: str, message: str):
        """Adds a violation at the location of the given CST node."""
        location = cst.ensure_type(self.get_metadata(cst.metadata.PositionProvider, node), cst.metadata.CodeRange)
        self.violations.append(
            LintViolation(
                line=location.start.line,
                column=location.start.column,
                code=code,
                message=message
            )
        )

# --- Example Rule Implementation ---
class NoWildcardImportRule(BaseLinterRule):
    """Flags the use of 'from module import *'."""
    VIOLATION_CODE = "PLSE101"
    VIOLATION_MESSAGE = "Wildcard import `*` is discouraged."

    def visit_ImportStar(self, node: cst.ImportStar) -> None:
        self.add_violation(node, self.VIOLATION_CODE, self.VIOLATION_MESSAGE)

# --- The Linter Engine ---
class CustomLinter:
    """
    Parses Python code into a Concrete Syntax Tree (CST) and runs a suite
    of custom linter rules over it.
    """
    def __init__(self):
        self.rules: List[Type[BaseLinterRule]] = [
            NoWildcardImportRule,
            # Future rules will be added here
        ]

    def run(self, code: str) -> List[LintViolation]:
        """Parses and lints the given code, returning all violations."""
        try:
            # LibCST requires a metadata wrapper to get position info
            source_tree = cst.parse_module(code)
            wrapper = cst.MetadataWrapper(source_tree)
        except Exception as e:
            # If parsing fails, it's a syntax error, which SyntaxValidator will catch.
            # We can return an empty list here.
            return []

        all_violations: List[LintViolation] = []
        for RuleClass in self.rules:
            visitor = RuleClass()
            wrapper.visit(visitor)
            all_violations.extend(visitor.violations)
            
        return all_violations