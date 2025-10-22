# Contributing to PLSE v2.0

First off, thank you for considering contributing! Your contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make will help build a better, more robust dataset for training the next generation of code-intelligent LLMs.

This document provides a set of guidelines for contributing to the Python Latent Space Explorer (PLSE) v2.0.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](LINK_TO_CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior.

*(Note: You will need to create a `CODE_OF_CONDUCT.md` file separately. A standard Contributor Covenant is a good choice.)*

## How Can I Contribute?

The most valuable way to contribute to PLSE is by **expanding the pattern library**. Our engine is robust, but the richness of the generated dataset depends entirely on the quality and diversity of the patterns in the `patterns/` directory.

We welcome contributions of all sizes, from fixing a typo in an existing pattern to authoring a brand new, complex pattern.

### Your First Contribution

Unsure where to start? A great first contribution is to pick a common Python or ML concept that isn't in our library yet, create a new `.yaml` pattern for it, and submit a pull request.

Good first patterns could be:
*   A different sorting algorithm (e.g., Merge Sort).
*   A different data structure from the `collections` module (e.g., `namedtuple`).
*   A common string method (e.g., `.join()` or `.split()`).
*   A basic scikit-learn model (e.g., `LogisticRegression`).

### The Golden Rule: Every Pattern is a Lesson

When authoring a new pattern, always ask yourself: **"What concept does this teach?"**

A good pattern is more than just a code snippet; it's a self-contained, pedagogical lesson. It should be:
1.  **Correct:** It must be syntactically and algorithmically correct.
2.  **Idiomatic:** It should represent the "Pythonic" or "PyTorch-ic" way of doing things.
3.  **Clear:** It should be easy for a human to read and understand.
4.  **Self-Contained:** It should be runnable and testable on its own.

## Writing a New Pattern: The Workflow

Contributing a new pattern is a straightforward process designed to be as easy as possible.

**1. Create Your YAML File**

In the `patterns/` directory, create a new file with a descriptive name (e.g., `python_stdlib_itertools.yaml`).

**2. Author the Pattern**

Fill out the YAML file using the PLSE v2.0 schema. The best way to do this is to copy an existing pattern and modify it. Your pattern **must** include:
*   `plse_version`, `pattern_id`, and all `metadata` fields.
*   A clear, templated `instruction` that describes the task.
*   A `template` containing the runnable code.
*   A `validation` block with `linter_checks: true` and at least one `unit_test_snippets`.

**3. Write a Strong Unit Test**

The `unit_test_snippets` are the most important part of ensuring quality. Your test should:
*   Run the generated code.
*   Use `assert` statements to verify that the code produced the correct output or had the correct side effects.
*   Be robust enough to catch potential errors.

**4. Test Your Pattern Locally**

Before submitting, it's a good idea to test that your pattern can be successfully used by the engine.
*   Set up the project locally (`pip install .`).
*   Modify `main.py` to generate only a few examples (`NUM_EXAMPLES_TO_GENERATE = 10`).
*   Run `python main.py` and ensure that examples from your new pattern are being generated and saved to the output file without errors.

**5. Submit a Pull Request**

Once you are happy with your new pattern, commit the `.yaml` file and submit a pull request to the `main` branch of the repository.

In your pull request description, please explain the concept your pattern teaches and why it's a valuable addition to the library.

## Styleguides

### Python Code

All generated Python code within the `template` and `unit_test_snippets` blocks should adhere to **PEP 8**. Our validation pipeline automatically runs `flake8`, so any non-compliant code will be rejected.

### YAML Files

*   Use **2 spaces** for indentation. Do not use tabs.
*   Use multi-line literal blocks (`|`) for code templates to preserve newlines.
*   Keep lines to a reasonable length to ensure readability.

Thank you again for your interest in contributing!