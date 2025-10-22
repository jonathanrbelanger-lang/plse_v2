# Python Latent Space Explorer (PLSE) v2.0

PLSE v2.0 is a modern synthetic code generation engine designed to create a high-quality, instruction-tuned dataset for training code-intelligent Large Language Models (LLMs).

This project moves beyond scraping public code repositories. Instead, it treats the training dataset as a first-class product, engineered from the ground up to be **pedagogical, architecturally sound, and diverse**. The goal is to train LLMs that don't just write code, but understand how to write *good* code.

## Core Architecture

The engine is built on a flexible, combinatorial, and modular architecture.

*   **Combinatorial Generation**: A powerful Jinja2-based rendering engine creates thousands of unique code snippets by combining variations from a single, well-structured pattern.
*   **Modular YAML Patterns**: All patterns are defined as human-readable `.yaml` files in the `patterns/` directory. This makes the library easy to extend and maintain.
*   **Multi-Stage Validation**: A rigorous pipeline ensures every generated sample is syntactically correct, stylistically compliant (PEP 8), and algorithmically sound via self-contained unit tests.
*   **Robust Instruction Labeling**: A deterministic process creates a specific, accurate, and descriptive instruction for each code snippet, guaranteeing a perfect one-to-one mapping for instruction fine-tuning.

## The Pattern Library: A Curriculum for Code Intelligence

The heart of PLSE is its pattern library. Each pattern is a self-contained, runnable, and testable lesson designed to teach a specific concept. The library is structured as a comprehensive curriculum covering the breadth of modern Python development.

### Current Pattern Categories:

*   **Core Python & Standard Library:**
    *   Fundamental data types (strings, lists, tuples)
    *   Idiomatic control flow (loops, comprehensions)
    *   Robust programming (functions, classes, error handling)
    *   Standard library power tools (`collections`, `itertools`, `argparse`, `logging`)

*   **Scientific Computing & Data Engineering:**
    *   High-performance NumPy and SciPy (Hamiltonian simulation, parallel PSO)
    *   Advanced data processing (NLP vocabulary building, memory-mapped datasets)
    *   Physics-informed feature engineering

*   **Machine Learning & MLOps:**
    *   **PyTorch & PyTorch Lightning:** Best practices for building models (`nn.Module`), data pipelines (`LightningDataModule`), and full training workflows (`LightningModule`).
    *   **Advanced Training:** Techniques like custom loss functions, learning rate schedulers, and gradient clipping.
    *   **Evaluation & Reporting:** Generating classification reports, confusion matrices, and performing statistical hypothesis tests.
    *   **Deployment:** Serving models as a REST API with FastAPI.
    *   **Project Setup:** Reproducible environment setup and dependency management.

*   **Meta-Patterns:**
    *   A unique category of patterns that teach the LLM the schema of the PLSE library itself, enabling it to assist in the creation of new patterns.

## Getting Started

### Prerequisites

*   Python 3.8 or newer.

### Installation

1.  Clone this repository.
2.  Navigate to the root directory (`plse_v2/`).
3.  Create and activate a virtual environment (recommended):
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
4.  Install the project and all its dependencies from `pyproject.toml`:
    ```bash
    pip install .
    ```

## Usage

The primary entry point is the `main.py` script.

1.  **Configure the run**: Open `main.py` and adjust the configuration variables inside the `main()` function.
2.  **Run the generator**: Execute the script from your terminal.
    ```bash
    python3 main.py
    ```
The script will generate a `training_dataset.jsonl` file in your project root.

## Contributing

This project thrives on community contributions to the pattern library. If you have an idea for a pattern that teaches a valuable Python or ML concept, we encourage you to contribute.

Please see our `CONTRIBUTING.md` file for a detailed guide on how to author and submit a new pattern. The core philosophy is that **every pattern is a lesson**, and it must be self-contained, runnable, and include its own validation tests.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.