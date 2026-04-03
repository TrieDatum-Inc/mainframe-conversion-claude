---
name: SQLite Test Compatibility Patterns
description: SQLAlchemy model patterns needed to make tests work with SQLite in-memory while still supporting PostgreSQL in production
type: feedback
---

Avoid `server_default=func.now()` on mapped columns — SQLite returns datetime strings without timezone, causing `ValueError: Invalid isoformat string` during result processing.

**Why:** SQLite stores timestamps as plain strings; SQLAlchemy's type processor expects ISO format with timezone offset. The mismatch causes errors when reading back rows.

**How to apply:** Use `nullable=True` on timestamp columns in models; set values explicitly in Python code (`datetime.now(tz=timezone.utc)`). For production-only defaults, use a PostgreSQL migration rather than ORM server_default.

Avoid `JSONB` dialect-specific type in ORM models — use `sqlalchemy.types.JSON` instead.

**Why:** `JSONB` is a PostgreSQL-specific type that causes `CompileError` when SQLite tries to render DDL for tests.

**How to apply:** Import `from sqlalchemy.types import JSON` and use `JSON` in models. PostgreSQL will use JSONB semantics automatically for JSON columns when the dialect is PostgreSQL.
