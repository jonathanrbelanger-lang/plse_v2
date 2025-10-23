# Python Latent Space Explorer (PLSE) v2.0

**A System for Engineering High-Quality, Pedagogical Code Datasets**



PLSE v2.0 is a data engineering framework designed to address a fundamental constraint in the development of code-intelligent Large Language Models: the quality of training data. Moving beyond the limitations of scraping public code repositories, PLSE employs a "pedagogical by design" philosophy to synthetically generate a vast, instruction-tuned dataset of high-quality code examples, anti-patterns, and architectural blueprints.



### Core Philosophy

This project is built on a set of foundational principles that guide every generated example:

*   ✅ **Pedagogical by Design:** Every generated sample is a "lesson" explicitly designed to teach a specific concept, from a simple language feature to a complex architectural pattern.
*   🔬 **Quality-Driven Architecture:** A multi-stage validation pipeline ensures every generated code sample is syntactically correct, stylistically idiomatic, and algorithmically sound.
*   🔀 **Combinatorial Generation:** A powerful Jinja2-based engine creates vast diversity from a small set of rich, modular patterns, allowing us to explore the "latent space" of Python code.
*   🧩 **Community-Ready and Scalable:** The modular, YAML-based pattern library is designed to be easily understood, maintained, and extended by developers.

### Quick Start: Generating Your First Dataset

This guide will walk you through setting up the environment and running the generation engine.

**1. Prerequisites**

Ensure you have `git` and a modern version of Python (`3.10` or newer) installed on your system.

**2. Clone & Setup**

First, clone the repository and navigate into the project directory.

```bash
# Replace with your repository's URL
git clone https://github.com/your-username/plse-v2.git
cd plse-v2

'''

Next, create a virtual environment and install the project in editable mode. This will install all necessary dependencies from pyproject.toml.

'''bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
'''

3. Run the Generation Engine

Execute the main script to start the dataset generation process.


'''bash
python main.py
'''

The script will discover all patterns, initialize the engine, and begin generating examples. By default, it will create 100 examples and save them to training_dataset.jsonl.

4. Verify the Output

You can inspect the generated dataset using standard command-line tools. To pretty-print the first example, you can use a tool like jq.


'''bash
# (Optional) Install jq if you don't have it
# sudo apt-get install jq
'''

'''bash
# Inspect the first line of the output file
head -n 1 training_dataset.jsonl | jq .
'''

# Project Architecture

The PLSE v2.0 system is composed of two main parts: the Core Engine and the Pattern Library.

# The Pattern Library (/patterns)

This is the heart of the project—a collection of YAML files that serve as blueprints for code generation. Each pattern is a self-contained lesson. The library is organized into categories:

/patterns/*.yaml: Best-practice patterns and "tradeoff" patterns that teach expert-level nuance.

/patterns/anti_patterns/*.yaml: Paired patterns that demonstrate a common mistake and its correct solution.

/patterns/orchestration/*.yaml: Advanced patterns that generate complete, runnable scripts and DevOps artifacts (Dockerfile, ci.yml, etc.).

# The Core Engine (src/plse/)

This is the installable Python package that powers the generation process.

schema.py: Defines the Pydantic models that validate the structure of all YAML pattern files.

patterns.py: Defines the internal Python dataclasses the application uses to represent a validated pattern.

registry.py: Discovers, validates, and loads all .yaml patterns from the /patterns directory and its subdirectories.

generator.py: The Jinja2-based engine that renders a pattern with a random parameter context to produce code.

validation.py: The multi-stage pipeline that ensures the quality of generated code through syntax checks, a custom linter, and safe execution of unit tests.

# Developer Workflow

As a contributor to PLSE, your primary workflows will involve creating patterns and validating the library.

# Generating the Dataset

To run the full generation pipeline, simply execute main.py. You can configure the number of examples and the output file directly in the script.

'''bash
python main.py
'''

# Discovering & Linting Patterns

We have two key utility scripts in the /scripts directory to help manage the pattern library.

List All Available Patterns: To get a quick overview of all patterns in the library without crawling the directories, run:

'''bash
python scripts/list_patterns.py
'''

To generate a AVAILABLE_PATTERNS.md file, use the --output-markdown flag.

Lint the Pattern Library: To check all patterns for static errors (like flake8 violations in the generated code), run our high-performance parallel linter:


'''bash
python scripts/lint_patterns.py
'''

This tool will provide a summary of any patterns that need to be fixed.

# Contributing

Contributions are welcome, especially in the form of new patterns. The best way to contribute is to identify a common Python concept, best practice, or anti-pattern that is not yet in our library.

The basic workflow is:

Create a new .yaml file in the appropriate directory (e.g., patterns/anti_patterns/).

Follow the schema defined in src/plse/schema.py. The best way to learn is to study an existing pattern and the meta-pattern (plse.meta.paired_pattern_generator).

Run python scripts/lint_patterns.py to ensure your new pattern generates valid code.

Submit a pull request.

# License

This project is licensed under the MIT License. See the LICENSE file for details.