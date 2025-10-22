PLSE v2.0 is a synthetic code generation engine designed to create a high-quality, instruction-tuned dataset for training code-intelligent Large Language Models (LLMs).

This project moves beyond scraping public code repositories. Instead, it treats the training dataset as a first-class product, engineered from the ground up to be pedagogical, architecturally sound, and diverse. The goal is to train LLMs that don't just write code, but understand how to write good code.

# Core Philosophy

Pedagogical by Design: Every generated sample is a 'lesson' teaching a specific concept, from fundamental syntax to advanced architectural patterns.

Quality-Driven Architecture: A multi-stage validation pipeline ensures every generated sample is syntactically correct, stylistically compliant, and algorithmically sound.

Combinatorial Generation: A powerful Jinja2-based engine creates vast diversity from a small set of rich, modular patterns.

Community-Ready and Scalable: A modular, YAML-based pattern library that is easy to extend and maintain.

# The Pattern Library: A Curriculum for Code Intelligence

The heart of PLSE is its pattern library, a comprehensive curriculum designed to teach the breadth of modern Python development. The library is organized into distinct categories, each focusing on a different aspect of software engineering.

Current Pattern Categories:

Best Practices (patterns/): These patterns serve as positive exemplars of high-quality, idiomatic code. They cover a wide range of topics, including:

Core Python & Standard Library: Idiomatic control flow, data structures, and effective use of modules like collections and argparse.

Scientific Computing: High-performance NumPy, SciPy, and data engineering techniques.

Machine Learning: Best practices for PyTorch and PyTorch Lightning, from model definition to full training workflows.

Tradeoff Patterns: A unique category of expert-level patterns that benchmark and explain the nuanced trade-offs between different architectural choices (e.g., list vs. generator, threading vs. multiprocessing).

Anti-Patterns (patterns/anti_patterns/): This is a library of "paired patterns," where each YAML file can generate both a common programming mistake and its corrected, idiomatic solution. This teaches the LLM to identify, explain, and refactor suboptimal code. It covers:

Critical Sins: Foundational bugs like mutable default arguments and data leakage.

Intermediate Mistakes: Performance and memory inefficiencies.

Expert Blind Spots: Subtle MLOps and production issues like training-serving skew.

Orchestration Patterns (patterns/orchestration/): These patterns teach system-level architecture by generating complete, runnable scripts and project artifacts. They move beyond code snippets to teach how software systems are built and deployed. This includes:

ML Pipeline Scripts: Generating train.py, predict.py, and evaluate.py.

API Servers: Creating production-ready FastAPI services.

DevOps & MLOps Artifacts: Generating Dockerfiles, pyproject.toml files, and docker-compose.yml for multi-service applications.

Meta-Patterns (patterns/): A special pattern that teaches the LLM the PLSE schema itself, enabling a flywheel effect where the model can assist in its own data generation.

# Discovering Available Patterns

To see a full, up-to-date catalog of all available patterns, you can run our discovery script:

# Print a list of all patterns to the console
python scripts/list_patterns.py

# Or, generate a Markdown file with the full catalog
python scripts/list_patterns.py --output-markdown

This will create an AVAILABLE_PATTERNS.md file in the project root.

# Getting Started
Prerequisites

Python 3.9 or newer.

Docker (required for validating some orchestration patterns).

# Installation

Clone this repository.

Navigate to the root directory.

# Create and activate a virtual environment (recommended):
python3 -m venv .venv
source .venv/bin/activate

# Install the project and all its dependencies:
pip install -e .

(The -e flag installs the project in "editable" mode, which is recommended for development.)

# Usage

The primary entry point is the main.py script.

Configure the run: Open main.py and adjust the configuration variables inside the main() function (e.g., NUM_EXAMPLES_TO_GENERATE).

# Run the generator: Execute the script from your terminal.
python main.py

The script will scan the patterns/ directory, generate and validate the code samples, and save the final dataset to a training_dataset.jsonl file in your project root.

# Contributing

This project thrives on community contributions to the pattern library. If you have an idea for a pattern that teaches a valuable Python or ML concept, we encourage you to contribute.

Please see our CONTRIBUTING.md file for a detailed guide on how to author and submit a new pattern. The core philosophy is that every pattern is a lesson, and it must be self-contained, runnable, and include its own validation tests.

# License

This project is licensed under the MIT License. See the LICENSE file for details.
