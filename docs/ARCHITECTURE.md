# CronForge Architecture

## Overview

CronForge is a Python library for generating, validating, and simulating cron expressions. It bridges the gap between human-readable scheduling descriptions and standard cron syntax.

## Module Structure

```
src/cronforge/
├── __init__.py      # Package exports (CronForge, CronExpression)
├── core.py          # Main CronForge class — public API surface
├── config.py        # Configuration, constants, field boundaries, presets
└── utils.py         # Low-level utilities — parsing, NL matching, date math
```

## Component Responsibilities

### `core.py` — CronForge Class

The primary interface. All user-facing methods live here:

| Method            | Purpose                                              |
|-------------------|------------------------------------------------------|
| `from_natural()`  | Convert natural language to a cron expression         |
| `parse()`         | Parse a cron string into a structured CronExpression  |
| `validate()`      | Check if a cron expression is syntactically valid     |
| `next_runs()`     | Compute the next N run times for a schedule           |
| `explain()`       | Produce a human-readable explanation of a cron expr   |
| `to_natural()`    | Best-effort reverse mapping from cron to plain text   |
| `simulate()`      | List all run times within a start/end date range      |
| `common_presets()` | Return a dict of commonly used cron expressions      |

### `config.py` — Configuration & Constants

- **CRON_FIELDS**: Min/max boundaries for each of the five cron fields.
- **DAY_NAMES / MONTH_NAMES**: Mappings from English names to numeric values.
- **WEEKDAY_LABELS**: Reverse mapping for explanation output.
- **PRESETS**: Common cron expressions (hourly, daily, weekly, etc.).
- **CronForgeConfig**: Dataclass for runtime settings (timezone, limits).

### `utils.py` — Parsing & Date Calculation

- **`parse_cron_field()`**: Expands a single field (`*/5`, `1-5`, `0,6`) into a set of integers.
- **`match_natural_language()`**: Iterates registered regex patterns to convert NL to cron.
- **`next_matching_times()`**: Minute-by-minute walk to find upcoming matching datetimes.
- **`expand_cron()`**: Expands all five fields at once.
- **`matches_cron()`**: Tests whether a given datetime satisfies expanded cron sets.

## Data Flow

```
User Input (NL string)
    │
    ▼
match_natural_language()  ──►  Registered regex patterns
    │                           (decorated with @_register)
    ▼
Cron expression string  ──────────────────────────┐
    │                                              │
    ├──► parse()  ──► CronExpression (pydantic)    │
    │                   │                          │
    ├──► validate()     │                          │
    │                   │                          │
    ├──► explain()  ◄───┘                          │
    │                                              │
    ├──► to_natural()                              │
    │                                              │
    ├──► next_runs()  ──► expand_cron()            │
    │                      │                       │
    │                      ▼                       │
    │                 next_matching_times()         │
    │                      │                       │
    │                      ▼                       │
    │                 List[datetime]                │
    │                                              │
    └──► simulate()  ──► next_matching_times()     │
                          (with end boundary)       │
                                                   │
                                                   ▼
                                            common_presets()
                                            (static dict)
```

## Design Decisions

1. **Pydantic for validation**: `CronExpression` uses pydantic field validators to enforce correctness at construction time.

2. **Regex-based NL parsing**: Rather than a full NLP pipeline, we use a registry of compiled regex patterns. This keeps the library dependency-free (beyond pydantic) and fast.

3. **Minute-resolution simulation**: The simulator walks time minute-by-minute. This is simple and correct for standard cron (which has minute granularity). A configurable `max_simulation_results` cap prevents runaway memory usage.

4. **Separation of concerns**: `core.py` is the public API; `utils.py` handles the mechanics. This makes the library easy to extend — adding a new NL pattern requires only a decorated function in `utils.py`.
