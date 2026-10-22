---
name: Replit Python installation
description: Managed dependency installation with an imported lint-only pyproject.toml.
---

The Replit Python package installer uses `uv add`; an existing lint-only
`pyproject.toml` must have a `[project]` metadata table before installation.
Pass package specifications, not `-r requirements.txt` strings, to the installer.

**Why:** The managed installer rejected requirements-file arguments and then
failed on the imported lint-only configuration. Adding minimal project metadata
allowed installation without changing the application structure.

**How to apply:** Keep requirements-file pins consistent with managed dependency
metadata when changing dependencies. Use the managed installer rather than
creating a separate virtual environment.
