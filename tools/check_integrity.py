"""Check the portable planning catalog using only the Python standard library."""

import argparse
import csv
import io
import json
import re
from datetime import date
from pathlib import Path, PurePosixPath


TYPES = {
    "source": ("SRC", {"recorded"}),
    "project": ("PRJ", {"draft", "confirmed", "superseded", "archived"}),
    "idea": ("IDEA", {"draft", "proposed", "confirmed", "superseded", "archived"}),
    "spec": ("SPEC", {"draft", "proposed", "confirmed", "superseded", "archived"}),
    "decision": ("DEC", {"proposed", "confirmed", "superseded", "archived"}),
    "question": ("QUE", {"open", "resolved", "archived"}),
    "dataset": ("DATA", {"draft", "proposed", "confirmed", "superseded", "archived"}),
}
FIELDS = {
    "id", "kind", "status", "title", "path", "summary", "tags",
    "source_ids", "related_ids", "created", "updated",
}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def read_json(path):
    return json.loads(
        path.read_text(encoding="utf-8-sig"),
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
    )


def string_list(value):
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def validate(root):
    root = Path(root).resolve()
    errors = []
    try:
        catalog = read_json(root / "index/catalog.json")
    except (OSError, ValueError) as exc:
        return [f"Cannot read catalog: {exc}"]
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "entries"}:
        return ["Catalog must contain exactly schema_version and entries."]
    if type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        return ["Unsupported schema_version; expected 1."]
    entries = catalog["entries"]
    if not isinstance(entries, list) or not entries:
        return ["Catalog entries must be a nonempty array."]

    by_id = {}
    paths = set()
    for number, entry in enumerate(entries, 1):
        label = f"Entry {number}"
        if not isinstance(entry, dict):
            errors.append(f"{label}: expected an object.")
            continue
        if set(entry) != FIELDS:
            errors.append(f"{label}: fields differ from the catalog contract.")
        for field in FIELDS - {"tags", "source_ids", "related_ids"}:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: {field} must be a nonempty string.")
        for field in ("tags", "source_ids", "related_ids"):
            values = entry.get(field)
            if not string_list(values):
                errors.append(f"{label}: {field} must be an array of nonempty strings.")
            elif len(values) != len(set(values)):
                errors.append(f"{label}: duplicate values in {field}.")

        entry_id = entry.get("id")
        if isinstance(entry_id, str):
            label = entry_id
            if entry_id in by_id:
                errors.append(f"{label}: duplicate ID.")
            else:
                by_id[entry_id] = entry
        kind = entry.get("kind")
        if not isinstance(kind, str) or kind not in TYPES:
            errors.append(f"{label}: unknown kind.")
        else:
            prefix, statuses = TYPES[kind]
            if not isinstance(entry_id, str) or not re.fullmatch(
                rf"{prefix}-(?!0000)[0-9]{{4}}", entry_id
            ):
                errors.append(f"{label}: invalid ID for kind {kind}.")
            status = entry.get("status")
            if not isinstance(status, str) or status not in statuses:
                errors.append(f"{label}: invalid status for kind {kind}.")
        if entry.get("status") == "confirmed" and not entry.get("source_ids"):
            errors.append(f"{label}: confirmed entries require source_ids.")
        if kind == "source" and entry.get("source_ids"):
            errors.append(f"{label}: a source must not derive from another source.")
        if entry.get("status") == "superseded" and not entry.get("related_ids"):
            errors.append(f"{label}: superseded entries require a successor reference.")

        dates = {}
        for field in ("created", "updated"):
            value = entry.get(field)
            try:
                if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                    raise ValueError("Expected YYYY-MM-DD")
                dates[field] = date.fromisoformat(value)
            except ValueError:
                errors.append(f"{label}: invalid {field} date.")
        if len(dates) == 2 and dates["updated"] < dates["created"]:
            errors.append(f"{label}: updated precedes created.")

        path = entry.get("path")
        if not isinstance(path, str) or not path:
            continue
        relative = PurePosixPath(path)
        if (
            "\\" in path or ":" in path or relative.is_absolute()
            or ".." in relative.parts or relative.as_posix() != path
            or not path.startswith("planning/")
        ):
            errors.append(f"{label}: path must be a canonical relative planning/ path.")
            continue
        if path.casefold() in paths:
            errors.append(f"{label}: duplicate path.")
        paths.add(path.casefold())
        target = root / path
        if not target.resolve().is_relative_to(root / "planning"):
            errors.append(f"{label}: path resolves outside planning/.")
            continue
        suffix = target.suffix.lower()
        expected = {".json", ".csv"} if kind == "dataset" else {".md"}
        if suffix not in expected or target.name.lower() == "readme.md":
            errors.append(f"{label}: unsupported file type or navigation README.")
        if not target.is_file():
            errors.append(f"{label}: missing file {path}.")
            continue
        try:
            if suffix == ".json":
                read_json(target)
            else:
                contents = target.read_text(encoding="utf-8-sig")
                if not contents.strip():
                    errors.append(f"{label}: empty file.")
                if suffix == ".csv":
                    rows = csv.reader(io.StringIO(contents, newline=""), strict=True)
                    header = next(rows, [])
                    names = [name.strip() for name in header]
                    if not names or not all(names) or len(names) != len(set(names)):
                        errors.append(f"{label}: CSV headers must be nonempty and unique.")
                    for row in rows:
                        if len(row) != len(header):
                            errors.append(f"{label}: CSV line {rows.line_num} has the wrong field count.")
        except (OSError, ValueError, csv.Error) as exc:
            errors.append(f"{label}: cannot read data: {exc}")

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        label = entry.get("id")
        for field in ("source_ids", "related_ids"):
            refs = entry.get(field)
            if not string_list(refs):
                continue
            for ref in refs:
                if ref == label:
                    errors.append(f"{label}: self reference in {field}.")
                if ref not in by_id:
                    errors.append(f"{label}: missing reference {ref}.")
                elif field == "source_ids" and by_id[ref].get("kind") != "source":
                    errors.append(f"{label}: source_ids must refer to source entries.")
        refs = entry.get("related_ids")
        if entry.get("kind") == "dataset" and string_list(refs):
            if not any(by_id.get(ref, {}).get("kind") == "spec" for ref in refs):
                errors.append(f"{label}: dataset requires a related spec explaining its fields.")

    for path in sorted((root / "planning").rglob("*")):
        if path.is_file() and path.name.lower() != "readme.md":
            relative = path.relative_to(root).as_posix()
            if relative.casefold() not in paths:
                errors.append(f"Unindexed planning file: {relative}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: catalog, files, references, and structured data are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
