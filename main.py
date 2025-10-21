"""
Main orchestrator for the Python Latent Space Explorer (PLSE) v2.0.
"""

import os
import json
from typing import Dict, Optional

# Import the new, upgraded components
from src.plse.registry import PatternRegistry
from src.plse.generator import PLSEGenerator
from src.plse.validation import ValidationPipeline

class TrainingDataGenerator:
    """
    Orchestrates the end-to-end process of generating, validating, and
    formatting synthetic code examples.
    """

    def __init__(self, patterns_dir: str, use_pylint: bool = False):
        print("Initializing PLSE v2.0 components...")
        self.registry = PatternRegistry(patterns_dir)
        self.generator = PLSEGenerator()
        self.pipeline = ValidationPipeline(use_pylint=use_pylint)
        print("Initialization complete.")

    def generate_example(self) -> Optional[Dict[str, str]]:
        """
        Attempts to generate a single, valid training example.
        """
        # 1. Select a random pattern.
        pattern = self.registry.get_random()
        if not pattern:
            return None

        # 2. Generate code, instruction, and tests from the pattern.
        generation_result = self.generator.generate(pattern)
        if not generation_result:
            return None
        code, instruction, tests = generation_result

        # 3. Validate the generated code AND run its unit tests.
        validation_result = self.pipeline.validate(code, tests)
        if not validation_result.valid:
            # print(f"Validation failed for {pattern.pattern_id}: {validation_result.errors}")
            return None

        # 4. If all checks pass, format the final output.
        # The instruction is now perfectly aligned with the code, no guesswork needed.
        return {
            "instruction": instruction,
            "input": "",
            "output": validation_result.code,
        }

    def generate_dataset(self, n_examples: int, output_file: str):
        """Generates a complete dataset of a specified size."""
        examples = []
        attempts = 0
        max_attempts = n_examples * 200 # Increased attempts as validation is stricter

        print(f"\nGenerating {n_examples} training examples...")
        while len(examples) < n_examples and attempts < max_attempts:
            example = self.generate_example()
            if example:
                examples.append(example)
                if len(examples) % 10 == 0 or len(examples) == n_examples:
                    print(f"  Generated {len(examples)}/{n_examples} examples...")
            attempts += 1

        try:
            with open(output_file, 'w') as f:
                for example in examples:
                    f.write(json.dumps(example) + '\n')
            print(f"\n✅ Successfully saved {len(examples)} examples to {output_file}")
        except IOError as e:
            print(f"\n❌ Error saving dataset to {output_file}: {e}")

        if len(examples) < n_examples:
            print(f"Warning: Could only generate {len(examples)} out of {n_examples} desired examples after {max_attempts} attempts.")

def main():
    """Main entry point for the script."""
    print("=" * 80)
    print("🚀 Starting Python Latent Space Explorer (PLSE) v2.0 🚀")
    print("=" * 80)

    PATTERNS_DIR = "patterns"
    OUTPUT_FILE = "training_dataset.jsonl"
    NUM_EXAMPLES_TO_GENERATE = 100
    USE_PYLINT_VALIDATOR = False

    if not os.path.exists(PATTERNS_DIR):
        print(f"❌ Error: The '{PATTERNS_DIR}' directory was not found.")
        return

    data_generator = TrainingDataGenerator(
        patterns_dir=PATTERNS_DIR,
        use_pylint=USE_PYLINT_VALIDATOR
    )
    data_generator.generate_dataset(
        n_examples=NUM_EXAMPLES_TO_GENERATE,
        output_file=OUTPUT_FILE
    )
    print("\nPLSE run complete.")
    print("=" * 80)

if __name__ == "__main__":
    main()
