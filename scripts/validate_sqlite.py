#!/usr/bin/env python3
"""Execute and validate SQLite schema, seed, queries, and smoke tests."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class StatementResult:
    source: str
    index: int
    sql_preview: str
    status: str
    columns: list[str]
    row_count: int | None
    rows_preview: list[list[object]]
    error: str | None = None
    assertion: str | None = None


def read_sql(path: Path | None) -> str:
    if path is None:
        return ""
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8")


def iter_statements(sql_text: str) -> Iterable[str]:
    """Split SQL using sqlite3.complete_statement while preserving SQL syntax."""
    buffer: list[str] = []
    for line in sql_text.splitlines(keepends=True):
        buffer.append(line)
        candidate = "".join(buffer).strip()
        if candidate and sqlite3.complete_statement(candidate):
            yield candidate
            buffer.clear()
    remainder = "".join(buffer).strip()
    if remainder:
        # SQLite accepts a final statement without a semicolon.
        yield remainder


def preview(sql: str, limit: int = 180) -> str:
    single_line = " ".join(sql.split())
    return single_line if len(single_line) <= limit else single_line[: limit - 3] + "..."


def check_test_assertion(
    statement: str,
    columns: list[str],
    rows: list[sqlite3.Row | tuple[object, ...]],
) -> tuple[bool, str | None]:
    """Apply optional semantic assertions for statements in tests.sql.

    Supported conventions:
    - PRAGMA foreign_key_check must return zero rows.
    - A SELECT whose first column is named ok/pass/passed or assert_* must
      return exactly one row with a truthy first value.
    Other statements are treated as execution-only smoke tests.
    """
    normalized = " ".join(statement.strip().lower().split())
    if normalized.startswith("pragma foreign_key_check"):
        if rows:
            return False, "PRAGMA foreign_key_check returned violations"
        return True, "foreign_key_check returned no violations"

    first_column = columns[0].strip().lower() if columns else ""
    is_assertion = first_column in {"ok", "pass", "passed"} or first_column.startswith("assert_")
    if not is_assertion:
        return True, None
    if len(rows) != 1:
        return False, "Assertion query must return exactly one row"
    if not bool(rows[0][0]):
        return False, f"Assertion column '{columns[0]}' evaluated to a false value"
    return True, f"Assertion column '{columns[0]}' evaluated to true"


def execute_file(
    conn: sqlite3.Connection,
    path: Path | None,
    label: str,
) -> tuple[list[StatementResult], str | None]:
    results: list[StatementResult] = []
    try:
        text = read_sql(path)
    except OSError as exc:
        return results, str(exc)

    for index, statement in enumerate(iter_statements(text), start=1):
        cursor = conn.cursor()
        try:
            cursor.execute(statement)
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(5) if cursor.description else []
            row_count = len(rows) if cursor.description else cursor.rowcount
            status = "passed"
            error: str | None = None
            assertion: str | None = None

            if label == "tests":
                assertion_ok, assertion = check_test_assertion(statement, columns, rows)
                if not assertion_ok:
                    status = "failed"
                    error = assertion

            result = StatementResult(
                source=label,
                index=index,
                sql_preview=preview(statement),
                status=status,
                columns=columns,
                row_count=row_count,
                rows_preview=[list(row) for row in rows],
                error=error,
                assertion=assertion,
            )
            results.append(result)
            if status == "failed":
                return results, error
        except sqlite3.Error as exc:
            error = str(exc)
            results.append(
                StatementResult(
                    source=label,
                    index=index,
                    sql_preview=preview(statement),
                    status="failed",
                    columns=[],
                    row_count=None,
                    rows_preview=[],
                    error=error,
                )
            )
            return results, error
    return results, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--seed", type=Path)
    parser.add_argument("--queries", type=Path)
    parser.add_argument("--tests", type=Path)
    parser.add_argument("--database", type=Path, help="Optional SQLite DB path; defaults to memory")
    parser.add_argument("--report", type=Path, default=Path("validation-report.json"))
    args = parser.parse_args()

    database = str(args.database) if args.database else ":memory:"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    all_results: list[StatementResult] = []
    failure: str | None = None

    try:
        with sqlite3.connect(database) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("BEGIN")
            for path, label in (
                (args.schema, "schema"),
                (args.seed, "seed"),
                (args.queries, "queries"),
                (args.tests, "tests"),
            ):
                if path is None:
                    continue
                results, error = execute_file(conn, path, label)
                all_results.extend(results)
                if error:
                    failure = f"{label}: {error}"
                    break
            conn.rollback()
    except (OSError, sqlite3.Error) as exc:
        failure = str(exc)

    report = {
        "database": database,
        "status": "failed" if failure else "passed",
        "foreign_keys": True,
        "transaction_rolled_back": True,
        "statement_count": len(all_results),
        "failure": failure,
        "test_conventions": {
            "foreign_key_check": "must return zero rows",
            "assertion_columns": "ok/pass/passed/assert_* must return one truthy value",
        },
        "results": [asdict(result) for result in all_results],
    }
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"SQLite validation: {report['status']}")
    print(f"Statements executed: {len(all_results)}")
    print(f"Report: {args.report.resolve()}")
    if failure:
        print(f"Failure: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
