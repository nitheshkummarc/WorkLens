"""Shared infrastructure for WorkLens-RedRob: config, models, utils.

`config` is the single source of truth for every numeric scoring constant and
for run-time configuration; `models` holds the Pydantic schemas (interface
contract); `utils` holds generic, domain-free helpers. No domain logic lives
here — only data, schemas, and reusable infrastructure.
"""
