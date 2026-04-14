# CronForge — Smart cron job generator — natural language to cron expressions, validation, scheduling simulation

Smart cron job generator — natural language to cron expressions, validation, scheduling simulation.

## Why CronForge

CronForge exists to make this workflow practical. Smart cron job generator — natural language to cron expressions, validation, scheduling simulation. It favours a small, inspectable surface over sprawling configuration.

## Features

- `CronExpression` — exported from `src/cronforge/core.py`
- Included test suite
- Dedicated documentation folder

## Tech Stack

- **Runtime:** Python
- **Tooling:** Pydantic

## How It Works

The codebase is organised into `docs/`, `src/`, `tests/`. The primary entry points are `src/cronforge/core.py`, `src/cronforge/__init__.py`. `src/cronforge/core.py` exposes `CronExpression` — the core types that drive the behaviour.

## Getting Started

```bash
pip install -e .
```

## Usage

```python
from cronforge.core import CronExpression

instance = CronExpression()
# See the source for the full API
```

## Project Structure

```
CronForge/
├── .env.example
├── CONTRIBUTING.md
├── Makefile
├── README.md
├── docs/
├── pyproject.toml
├── src/
├── tests/
```