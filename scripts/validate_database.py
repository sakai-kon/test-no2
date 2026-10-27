#!/usr/bin/env python3
"""Validate the Grade 7 science/math JSON datasets using only the Python standard library."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_FILES = {
    "science": ROOT / "data" / "science.json",
    "math": ROOT / "data" / "math.json",
}
MANIFEST_FILE = ROOT / "data" / "manifest.json"
SCHEMA_FILE = ROOT / "schema" / "knowledge-item.schema.json"

ITEM_REQUIRED = {
    "id", "unit_code", "unit", "topic", "level", "explanation",
    "key_points", "questions", "subject", "grade", "keywords",
}
QUESTION_REQUIRED = {
    "id", "type", "prompt", "answer", "explanation", "difficulty", "tags",
}


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path.relative_to(ROOT)}: {exc}") from exc


def validate() -> list[str]:
    errors: list[str] = []
    manifest = load_json(MANIFEST_FILE)
    schema = load_json(SCHEMA_FILE)
    allowed_levels = set(schema["properties"]["level"]["enum"])
    all_item_ids: set[str] = set()
    all_question_ids: set[str] = set()
    total_items = 0
    total_questions = 0

    manifest_subjects = {entry["id"]: entry for entry in manifest.get("subjects", [])}

    for subject_id, path in DATA_FILES.items():
        data = load_json(path)
        items = data.get("items")
        if not isinstance(items, list):
            errors.append(f"{path.relative_to(ROOT)}: 'items' must be an array")
            continue

        if data.get("subject") not in {"理科", "数学"}:
            errors.append(f"{path.relative_to(ROOT)}: unexpected subject label")
        if data.get("grade") != 7:
            errors.append(f"{path.relative_to(ROOT)}: expected grade 7")

        subject_items = 0
        subject_questions = 0
        for index, item in enumerate(items):
            location = f"{path.relative_to(ROOT)} items[{index}]"
            missing = ITEM_REQUIRED - item.keys()
            if missing:
                errors.append(f"{location}: missing fields {sorted(missing)}")
                continue

            item_id = item["id"]
            if item_id in all_item_ids:
                errors.append(f"{location}: duplicate item id {item_id}")
            all_item_ids.add(item_id)

            if item["level"] not in allowed_levels:
                errors.append(f"{location}: unsupported level {item['level']!r}")
            if not isinstance(item["key_points"], list) or not item["key_points"]:
                errors.append(f"{location}: key_points must be a non-empty array")
            if not isinstance(item["questions"], list):
                errors.append(f"{location}: questions must be an array")
                continue

            subject_items += 1
            total_items += 1
            for q_index, question in enumerate(item["questions"]):
                q_location = f"{location} questions[{q_index}]"
                q_missing = QUESTION_REQUIRED - question.keys()
                if q_missing:
                    errors.append(f"{q_location}: missing fields {sorted(q_missing)}")
                    continue
                qid = question["id"]
                if qid in all_question_ids:
                    errors.append(f"{q_location}: duplicate question id {qid}")
                all_question_ids.add(qid)
                if not isinstance(question["difficulty"], int) or not 1 <= question["difficulty"] <= 5:
                    errors.append(f"{q_location}: difficulty must be an integer from 1 to 5")
                for field in ("prompt", "answer", "explanation"):
                    if not isinstance(question[field], str) or not question[field].strip():
                        errors.append(f"{q_location}: {field} must be a non-empty string")
                subject_questions += 1
                total_questions += 1

        manifest_entry = manifest_subjects.get(subject_id)
        if not manifest_entry:
            errors.append(f"manifest is missing subject id {subject_id}")
        else:
            if manifest_entry.get("knowledge_items") != subject_items:
                errors.append(
                    f"manifest {subject_id}: knowledge_items says "
                    f"{manifest_entry.get('knowledge_items')}, found {subject_items}"
                )
            if manifest_entry.get("questions") != subject_questions:
                errors.append(
                    f"manifest {subject_id}: questions says "
                    f"{manifest_entry.get('questions')}, found {subject_questions}"
                )

    if manifest.get("total_knowledge_items") != total_items:
        errors.append(
            f"manifest total_knowledge_items says {manifest.get('total_knowledge_items')}, "
            f"found {total_items}"
        )
    if manifest.get("total_questions") != total_questions:
        errors.append(
            f"manifest total_questions says {manifest.get('total_questions')}, "
            f"found {total_questions}"
        )

    if not errors:
        print(
            f"OK: {total_items} knowledge items, {total_questions} questions; "
            "IDs are unique and manifest counts match."
        )
    return errors


def main() -> int:
    try:
        errors = validate()
    except (ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
