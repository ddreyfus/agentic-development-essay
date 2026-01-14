<!-- @format -->

# Agent Guidelines

## Commands

- **Setup**: `python3 -m venv .venv && source .venv/bin/activate` (Use this first)
- **Install**: `pip install -r requirements.txt` (in activated venv), `npm install` (in /frontend)
- **Run Backend**: `uvicorn app.main:app --reload` (must be run in activated venv)
- **Run Frontend**: `npm run dev` (in /frontend)
- **Test Backend**: `pytest` (must be run in activated venv; run single: `pytest path/to/test.py::test_func`)
- **Test Frontend**: `npm test` (in /frontend)
- **Lint**: `ruff check .` (must be run in activated venv), `npm run lint` (Frontend)

## Code Style & Conventions

- **Python**:
  - Follow PEP 8. Use `snake_case` for variables/functions, `PascalCase` for classes.
  - **Type Hints**: Mandatory for all function arguments and return values.
  - **FastAPI**: Use Pydantic models for schemas. Use dependency injection.
  - **Error Handling**: Use `try/except` blocks; return HTTP exceptions (e.g., `HTTPException`).
- **Frontend (React)**:
  - Use Functional Components and Hooks.
  - Use `camelCase` for variables/functions, `PascalCase` for components.
  - Prefer named exports.
- **General**:
  - **Imports**: Absolute imports preferred. Group standard lib, 3rd party, local.
  - **Comments**: Explain "why", not "what". Docstrings for public modules/functions.
