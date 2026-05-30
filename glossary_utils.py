from __future__ import annotations

import re
from pathlib import Path


def load_glossary(glossary_path: Path) -> list[str]:
    """Load glossary terms, longest first so phrases win over single words."""
    if not glossary_path.exists():
        return []
    terms = [line.strip() for line in glossary_path.read_text(encoding="utf-8").splitlines()]
    terms = [term for term in terms if term and not term.startswith("#")]
    return sorted(set(terms), key=len, reverse=True)


def protect_glossary_terms(text: str, terms: list[str]) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}
    protected = text

    for index, term in enumerate(terms):
        placeholder = f"__DUBDECK_TERM_{index}__"
        pattern = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)

        def remember(match: re.Match[str]) -> str:
            placeholders[placeholder] = match.group(0)
            return placeholder

        protected = pattern.sub(remember, protected)

    return protected, placeholders


def restore_glossary_terms(text: str, placeholders: dict[str, str]) -> str:
    restored = text
    for placeholder, original in placeholders.items():
        restored = restored.replace(placeholder, original)
        restored = restored.replace(placeholder.lower(), original)
    return restored
