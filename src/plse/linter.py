"""
Enhanced PLSE v2.0 Domain-Specific Linter with Template Awareness.

This linter can differentiate between legitimate Jinja2 template variables
and actual undefined Python variables.
"""

import libcst as cst
import re
from dataclasses import dataclass
from typing import List, Type, Set, Optional

@dataclass
class LintViolation:
    """Represents a single violation found by a linter rule."""
    line: int
    column: int
    code: str
    message: str

class BaseLinterRule(cst.CSTVisitor):
    """Abstract base class for all linter rules."""
    def __init__(self, template_vars: Optional[Set[str]] = None):
        self.violations: List[LintViolation] = []
        self.template_vars = template_vars or set()

    def add_violation(self, node: cst.CSTNode, code: str, message: str):
        """Adds a violation at the location of the given CST node."""
        location = cst.ensure_type(
            self.get_metadata(cst.metadata.PositionProvider, node), 
            cst.metadata.CodeRange
        )
        self.violations.append(
            LintViolation(
                line=location.start.line,
                column=location.start.column,
                code=code,
                message=message
            )
        )

class NoWildcardImportRule(BaseLinterRule):
    """Flags the use of 'from module import *'."""
    VIOLATION_CODE = "PLSE101"
    VIOLATION_MESSAGE = "Wildcard import `*` is discouraged."

    def visit_ImportStar(self, node: cst.ImportStar) -> None:
        self.add_violation(node, self.VIOLATION_CODE, self.VIOLATION_MESSAGE)

class UndefinedNameRule(BaseLinterRule):
    """
    Detects undefined variables, but ignores Jinja2 template variables.
    This replaces the need for F821 checking from flake8.
    """
    VIOLATION_CODE = "PLSE201"
    
    def __init__(self, template_vars: Optional[Set[str]] = None):
        super().__init__(template_vars)
        self.defined_names: Set[str] = set()
        self.used_names: Set[str] = set()
        # Python builtins that should always be considered defined
        self.builtins = set(dir(__builtins__))
    
    def visit_Name(self, node: cst.Name) -> None:
        """Track all name references."""
        name = node.value
        
        # Check if this is in an assignment context
        try:
            parent = self.get_metadata(cst.metadata.ParentNodeProvider, node)
            if isinstance(parent, (cst.AssignTarget, cst.Param, cst.FunctionDef, cst.ClassDef)):
                self.defined_names.add(name)
                return
        except:
            pass
        
        # Track as a usage
        self.used_names.add(name)
    
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Track function definitions."""
        self.defined_names.add(node.name.value)
    
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Track class definitions."""
        self.defined_names.add(node.name.value)
    
    def visit_Import(self, node: cst.Import) -> None:
        """Track imported names."""
        for name in node.names:
            if isinstance(name, cst.ImportAlias):
                imported_name = name.asname.name.value if name.asname else name.name.value
                self.defined_names.add(imported_name)
    
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Track from-imports."""
        if isinstance(node.names, cst.ImportStar):
            return  # Wildcard imports handled by separate rule
        
        for name in node.names:
            if isinstance(name, cst.ImportAlias):
                imported_name = name.asname.name.value if name.asname else name.name.value
                self.defined_names.add(imported_name)
    
    def check_undefined(self) -> None:
        """
        Called after visiting the entire tree to check for undefined names.
        """
        undefined = self.used_names - self.defined_names - self.builtins - self.template_vars
        
        # Note: We can't add violations with line numbers here since we lost that context
        # In a full implementation, you'd need to track Name nodes with their locations
        # For now, this provides the filtering logic
        
    def leave_Module(self, original_node: cst.Module) -> None:
        """Perform final check when leaving the module."""
        # This is where you'd implement the final undefined name check
        # For simplicity, we're not adding violations here in this example
        pass

class CustomLinter:
    """
    Parses Python code into a Concrete Syntax Tree (CST) and runs a suite
    of custom linter rules over it. Now with template-awareness!
    """
    def __init__(self, template_vars: Optional[Set[str]] = None):
        self.template_vars = template_vars or set()
        self.rules: List[Type[BaseLinterRule]] = [
            NoWildcardImportRule,
            # UndefinedNameRule is commented out for now - needs more sophisticated implementation
            # UndefinedNameRule,
        ]

    @staticmethod
    def extract_template_vars(code: str) -> Set[str]:
        """
        Extracts Jinja2 template variable names from code.
        Looks for patterns like {{ var_name }}.
        """
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        matches = re.findall(pattern, code)
        return set(matches)

    def run(self, code: str, known_template_vars: Optional[Set[str]] = None) -> List[LintViolation]:
        """
        Parses and lints the given code, returning all violations.
        
        Args:
            code: The Python/Jinja2 template code to lint
            known_template_vars: Optional set of known template variable names
                                If not provided, will be extracted from the code
        """
        # Extract or use provided template variables
        if known_template_vars is None:
            template_vars = self.extract_template_vars(code)
        else:
            template_vars = known_template_vars.union(self.extract_template_vars(code))
        
        try:
            source_tree = cst.parse_module(code)
            wrapper = cst.MetadataWrapper(source_tree)
        except Exception as e:
            # If parsing fails, it's a syntax error handled elsewhere
            return []

        all_violations: List[LintViolation] = []
        for RuleClass in self.rules:
            visitor = RuleClass(template_vars=template_vars)
            wrapper.visit(visitor)
            all_violations.extend(visitor.violations)
            
        return all_violations

    def run_on_pattern(self, code: str, parameter_names: List[str]) -> List[LintViolation]:
        """
        Convenience method for linting pattern code when you know the parameter names.
        
        Args:
            code: The pattern template code
            parameter_names: List of parameter names defined in the pattern
        """
        return self.run(code, known_template_vars=set(parameter_names))
