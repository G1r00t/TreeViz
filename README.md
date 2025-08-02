# TreeViz – Python AST Explorer

**TreeViz** is a web application that allows users to upload Python files and view the Abstract Syntax Tree (AST) structure generated using [Tree-sitter](https://tree-sitter.github.io/tree-sitter/), a fast and efficient parsing system.

## How it Works

This project uses **Tree-sitter** to parse Python source code and generate its Abstract Syntax Tree (AST). Here's how it's set up:

### 1. **Tree-sitter Integration**

- The `tree_sitter` Python bindings are used to load the Tree-sitter grammar for Python.
- A `Parser` object is initialized using this language grammar.
- When a file is uploaded, the source code is parsed into a `tree` object.
- The root node of the tree is recursively traversed to extract:
  - Function definitions
  - Class definitions
  - Import statements
- Each node in the AST includes:
  - Type of construct (e.g., `function_definition`, `import_statement`, `class_definition`)
  - Byte offsets and character positions
  - Structural relationships among nodes

Example of setting up the parser:

```python
from tree_sitter import Language, Parser
import tree_sitter_python as ts_python

PY_LANGUAGE = Language(ts_python.language())
parser = Parser()
parser.set_language(PY_LANGUAGE)
```
### 2. AST Traversal and Node Extraction

The parser output is walked recursively to gather semantic information such as:

- **functions**: names of all functions defined  
- **classes**: names of all class definitions  
- **imports**: all import statements  

The system filters and processes nodes based on types and context to keep the output relevant and clean.

---

## Code Structure

### 🔹 [`main.py`](./main.py)

This file contains the core **Tree-sitter integration** logic:

- Initializes the Tree-sitter parser for Python using `tree_sitter` bindings.
- Defines the `CodeAnalyzer` class, which:
  - Parses a Python file using Tree-sitter.
  - Traverses the resulting AST to extract:
    - Import statements
    - Function definitions
  - Prints a structured tree representation of the AST to the console.

### 🔹 [`app.py`](./app.py)

This is the main **Flask application** file and builds upon `main.py`:

- Imports and extends the `CodeAnalyzer` class with `InteractiveCodeAnalyzer`.
- `InteractiveCodeAnalyzer` adds support for:
  - Direct analysis of **code content** (not just files).
  - Extracting additional constructs like `class_definition`.
  - Constructing a **filtered and annotated AST structure** suitable for frontend visualization.
- Defines REST API endpoints:
  - `/analyze` – Accepts raw code via JSON.
  - `/analyze_file` – Accepts uploaded `.py` files.
  - `/` – Serves the frontend.

This architecture keeps the core AST parsing logic reusable and separate from the web server logic.


## Try It Live
**[https://treeviz.up.railway.app/](https://treeviz.up.railway.app/)**

### What You Can Do:

- Upload a `.py` file directly through the interface.
- View the extracted AST structure (currently limited to Python).
- Internally, your uploaded code is parsed and analyzed using Tree-sitter.

---

## Supported Language

- For now we have python , gonna add more

---

## Tech Stack

- Python (Flask)
- Tree-sitter (via Python bindings)
- Hosted on Railway

