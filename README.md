# llm_world_interface

A robust default Python project template using `uv`.

## Setup

This project uses `uv` for dependency management and includes a bootstrapping script to quickly get you started.

To bootstrap the project, run:

```bash
python bootstrap.py
```

The bootstrap script will:
- **Check for `uv`**: Automatically installs [uv](https://github.com/astral-sh/uv) if it's not already on your system.
- **Rename Project**: Guides you through renaming the project and its Python package from the default `llm_world_interface`.
- **Sync Dependencies**: Installs project dependencies and allows you to select optional extras (e.g., `data`, `ml`, `api`).
- **Reset Git**: Optionally clears the template's git history and initializes a new repository for your project.

### Google Calendar API Setup

To use the Google Calendar connector, you need to generate Google OAuth credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project.
3. Enable the **Google Calendar API** for your project.
4. Configure the OAuth Consent Screen.
5. **Generate OAuth Client Credentials**:
   - In the left sidebar, click the **Credentials** tab.
   - Click **+ Create Credentials** at the top of the page and select **OAuth client ID**.
   - Choose your **Application type** based on your architecture:
     - **Web application**: (Most common) For apps running on a server that require secure server-side handling or frontend routing.
     - **Desktop application**: For local scripts, CLI applications, or native desktop software.
   - **Configure Routing Parameters** (For Web Applications):
     - **Authorized JavaScript origins**: The URL where your app is hosted (e.g., `http://localhost:3000` or `https://myapp.com`).
     - **Authorized redirect URIs**: The precise endpoint on your backend or client where Google should redirect the user after a successful login, carrying the authorization code (e.g., `http://localhost:3000/oauth/callback`).
   - Click **Create**.
6. Download the client secrets JSON file, rename it to `credentials.json`, and place it in the root of this project.

## Usage

Common development tasks can be run using either the `Makefile` (convenient for Unix-like environments and CI) or directly via `uv` (recommended on Windows or when you need to pass additional command-line arguments).

### Development Commands

| Task | Make Command | Direct `uv` Command | Description |
| :--- | :--- | :--- | :--- |
| **Sync Dependencies** | `make install` | `uv sync` | Install or sync project dependencies. |
| **Run CLI** | `make run` | `uv run llm_world_interface` | Run the application command-line interface. |
| **Run GUI** | `make gui` | `uv run chainlit run src/llm_world_interface/app.py` | Launch the Chainlit interactive chat interface. |
| **Run Tests** | `make test` | `uv run pytest` | Run the test suite. |
| **Watch Tests** | `make test-watch` | `uv run ptw` | Run tests in watch mode. |
| **Coverage Report** | `make test-cov` | `uv run pytest --cov=src --cov-report=term-missing` | Run tests and generate coverage. |
| **Lint Code** | `make lint` | `uv run ruff check .` | Check style and quality with Ruff. |
| **Format Code** | `make format` | `uv run ruff format .` | Format code using Ruff. |
| **Type Check** | `make typecheck` | `uv run mypy src` | Run static type analysis with mypy. |

### Passing Arguments

One of the main advantages of running commands directly via `uv` is the ability to easily append any standard command-line arguments. For example:

* **Run a specific test:**
  ```bash
  uv run pytest -k test_some_feature
  ```
* **Auto-fix lint issues:**
  ```bash
  uv run ruff check . --fix
  ```


## Project Structure

```text
.
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile
├── README.md
├── bootstrap.py
├── pyproject.toml
├── uv.lock
├── src/
│   └── llm_world_interface/
│       ├── __init__.py
│       ├── cli.py
│       └── main.py
└── tests/
    ├── __init__.py
    └── test_main.py
```

- `src/`: Core application logic.
- `tests/`: Project tests.
- `pyproject.toml`: Project metadata and dependencies.
- `bootstrap.py`: Interactive setup script.
- `Makefile`: Shortcuts for common tasks.
