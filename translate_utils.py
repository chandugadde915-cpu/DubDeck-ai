from __future__ import annotations

from pathlib import Path

from glossary_utils import load_glossary, protect_glossary_terms, restore_glossary_terms


class TranslationError(RuntimeError):
    pass


def _get_translation():
    try:
        import argostranslate.translate
    except ImportError as exc:
        raise TranslationError("Argos Translate is not installed. Run the installer again.") from exc

    installed_languages = argostranslate.translate.get_installed_languages()
    english = next((lang for lang in installed_languages if lang.code == "en"), None)
    hindi = next((lang for lang in installed_languages if lang.code == "hi"), None)
    if not english or not hindi:
        raise TranslationError(
            "Argos English-to-Hindi package is missing. Install it from Argos Translate packages, then restart DubDeck AI."
        )
    translation = english.get_translation(hindi)
    if not translation:
        raise TranslationError("Argos English-to-Hindi translation package is not available.")
    return translation


def translate_text(text: str) -> str:
    if not text.strip():
        return ""
    translation = _get_translation()
    return translation.translate(text)


def translate_with_glossary(text: str, glossary_path: Path) -> str:
    terms = load_glossary(glossary_path)
    protected, placeholders = protect_glossary_terms(text, terms)
    translated = translate_text(protected)
    return restore_glossary_terms(translated, placeholders)


def install_argos_hint() -> str:
    return (
        "Open Python, install argostranslate, then install the English to Hindi package from Argos Translate. "
        "The app cannot download paid or cloud translation services."
    )
