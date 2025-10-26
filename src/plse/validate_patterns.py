#!/usr/bin/env python3
"""
Quick validation script for PLSE patterns.
Tests that patterns can be rendered with default parameters and pass validation.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# Add project root to path if needed
# sys.path.insert(0, str(Path(__file__).parent.parent))

from plse.registry import PatternRegistry
from plse.generator import PLSEGenerator
from plse.validation import ValidationPipeline

class QuickPatternValidator:
    """Validates all patterns by attempting to generate and validate samples."""
    
    def __init__(self, patterns_dir: str):
        self.patterns_dir = Path(patterns_dir)
        self.registry = PatternRegistry(str(patterns_dir))
        self.generator = PLSEGenerator(validate=False)  # We'll validate manually
        self.pipeline = ValidationPipeline()
        
        self.results = {
            'passed': [],
            'failed': [],
        }
        self.error_types = defaultdict(int)
    
    def validate_pattern_rendering(self, pattern) -> Dict:
        """
        Validate that a pattern can be rendered and validated successfully.
        Tests with default parameter values.
        """
        result = {
            'pattern_id': pattern.pattern_id,
            'status': 'unknown',
            'errors': [],
        }
        
        try:
            # Generate one sample with default parameters
            sample = self.generator.generate(pattern, skip_validation=True)
            
            if sample is None:
                result['status'] = 'failed'
                result['errors'].append("Generation failed (returned None)")
                return result
            
            code, instruction, tests = sample
            
            # Now validate the rendered code (without parameters, since it's already rendered)
            validation_result = self.pipeline.validate(code=code, tests=tests)
            
            if validation_result.valid:
                result['status'] = 'passed'
            else:
                result['status'] = 'failed'
                result['errors'] = validation_result.errors
                
                # Categorize errors
                for error in validation_result.errors:
                    if 'F821' in error or 'undefined' in error.lower():
                        self.error_types['F821_undefined'] += 1
                    elif 'Syntax' in error:
                        self.error_types['syntax'] += 1
                    elif 'Linter' in error:
                        self.error_types['linter'] += 1
                    elif 'execution' in error.lower():
                        self.error_types['execution'] += 1
                    else:
                        self.error_types['other'] += 1
        
        except Exception as e:
            result['status'] = 'failed'
            result['errors'].append(f"Unexpected error: {type(e).__name__}: {str(e)}")
            self.error_types['exception'] += 1
        
        return result
    
    def validate_all(self) -> Dict:
        """Validate all patterns in the registry."""
        print(f"🔍 Found {len(self.registry)} patterns to validate\n")
        
        for i, pattern in enumerate(self.registry, 1):
            print(f"[{i}/{len(self.registry)}] Validating {pattern.pattern_id}...", end=" ")
            
            result = self.validate_pattern_rendering(pattern)
            
            if result['status'] == 'passed':
                print("✅ PASSED")
                self.results['passed'].append(result)
            else:
                print(f"❌ FAILED ({len(result['errors'])} errors)")
                self.results['failed'].append(result)
        
        return self.results
    
    def print_summary(self):
        """Print a summary of validation results."""
        total = len(self.results['passed']) + len(self.results['failed'])
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total patterns: {total}")
        print(f"✅ Passed: {passed} ({100*passed/total:.1f}%)")
        print(f"❌ Failed: {failed} ({100*failed/total:.1f}%)")
        
        if self.error_types:
            print("\nError Breakdown:")
            print("-" * 80)
            for error_type, count in sorted(self.error_types.items(), 
                                           key=lambda x: x[1], 
                                           reverse=True):
                print(f"  {error_type}: {count}")
        
        if self.results['failed']:
            print("\nFailed Patterns:")
            print("-" * 80)
            for result in self.results['failed']:
                print(f"\n📋 {result['pattern_id']}")
                for i, error in enumerate(result['errors'][:3], 1):
                    print(f"   {i}. {error}")
                if len(result['errors']) > 3:
                    print(f"   ... and {len(result['errors']) - 3} more errors")
        
        print("\n" + "=" * 80)

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_patterns.py <patterns_directory>")
        print("\nExample: python validate_patterns.py ./patterns")
        sys.exit(1)
    
    patterns_dir = sys.argv[1]
    
    if not os.path.isdir(patterns_dir):
        print(f"❌ Error: '{patterns_dir}' is not a valid directory")
        sys.exit(1)
    
    print("Starting pattern validation...\n")
    
    validator = QuickPatternValidator(patterns_dir)
    validator.validate_all()
    validator.print_summary()
    
    # Exit with error code if any patterns failed
    if validator.results['failed']:
        sys.exit(1)
    else:
        print("\n🎉 All patterns validated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()