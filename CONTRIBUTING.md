# Contributing to CronForge

Thank you for your interest in contributing to CronForge! This guide will help you get started.

## Development Setup

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/officethree/CronForge.git
   cd CronForge
   ```

2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   make install
   ```

3. **Run the test suite** to verify everything works:
   ```bash
   make test
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, ensuring:
   - Code passes linting: `make lint`
   - Type checks pass: `make typecheck`
   - All tests pass: `make test`
   - New features include tests

3. Commit with a clear message:
   ```bash
   git commit -m "feat: add support for biweekly schedules"
   ```

4. Push and open a Pull Request.

## Adding New Natural Language Patterns

To add a new NL pattern, edit `src/cronforge/utils.py`:

1. Add a new function decorated with `@_register(r"your_regex_pattern")`.
2. The function receives a regex match object and returns a cron expression string.
3. Add corresponding tests in `tests/test_core.py`.

Example:

```python
@_register(r"^every\s+other\s+hour$")
def _every_other_hour(m):
    return "0 */2 * * *"
```

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — adding or updating tests
- `refactor:` — code changes that neither fix bugs nor add features
- `chore:` — maintenance tasks

## Code Style

- We use **ruff** for linting and formatting.
- Target Python 3.9+ compatibility.
- Type hints are encouraged for all public APIs.
- Docstrings follow NumPy/Google style.

## Reporting Issues

Please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Python version and OS

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
