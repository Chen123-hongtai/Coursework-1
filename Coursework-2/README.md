# COMP0035 Coursework 2 – Tourism Time-Series ORM

This repository contains a lightweight Python package for Section 2 of COMP0035 Coursework 2.  
It focuses on SQLModel ORM usage, tourism time-series analytics, and high-quality automated tests.

## Features
- SQLModel ORM models for `series_master` and `observations` tables.
- Analytical helpers:
  - `yoy_change` – year-on-year percentage change for a given series/month.
  - `moving_average` – rolling mean for a series (configurable window).
  - `missing_rate` – proportion of NULL values over a date range.
- Pytest suite (12 tests) covering unit and integration scenarios, boundary cases, and NULL handling.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows
pip install -r requirements.txt
pip install -e .
```

## Running Tests
```bash
python -m pytest
```

## Package Layout
- `src/tourism_timeseries/` – ORM models and analytics helpers.
- `tests/` – Pytest suite with GIVEN/WHEN/THEN docstrings.
