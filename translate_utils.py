from __future__ import annotations

import os
from pathlib import Path

from glossary_utils import load_glossary, protect_glossary_terms, restore_glossary_terms


class TranslationError(RuntimeError):
    pass


def _ensure_argos_env() -> None:
    project_dir = Path(__file__).resolve().parent
    cache_dir = project_dir / "temp" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("XDG_CACHE_HOME", str(cache_dir))
    os.environ.setdefault("XDG_DATA_HOME", str(cache_dir / "data"))


def _install_english_hindi_package() -> None:
    _ensure_argos_env()
    try:
        import argostranslate.package
    except ImportError as exc:
        raise TranslationError("Argos Translate is not installed. Run the installer again.") from exc

    argostranslate.package.update_package_index()
    packages = argostranslate.package.get_available_packages()
    package = next(
        (
            item
            for item in packages
            if item.from_code == "en" and item.to_code == "hi"
        ),
        None,
    )
    if package is None:
        raise TranslationError("Argos English-to-Hindi package was not found in the Argos package index.")

    package_path = package.download()
    argostranslate.package.install_from_path(package_path)


def _get_translation():
    _ensure_argos_env()
    try:
        import argostranslate.translate
    except ImportError as exc:
        raise TranslationError("Argos Translate is not installed. Run the installer again.") from exc

    installed_languages = argostranslate.translate.get_installed_languages()
    english = next((lang for lang in installed_languages if lang.code == "en"), None)
    hindi = next((lang for lang in installed_languages if lang.code == "hi"), None)
    if not english or not hindi:
        _install_english_hindi_package()
        installed_languages = argostranslate.translate.get_installed_languages()
        english = next((lang for lang in installed_languages if lang.code == "en"), None)
        hindi = next((lang for lang in installed_languages if lang.code == "hi"), None)
        if not english or not hindi:
            raise TranslationError(
                "Argos English-to-Hindi package is missing. Install it from Argos Translate packages, then restart DubDeck AI."
            )
    translation = english.get_translation(hindi)
    if not translation:
        _install_english_hindi_package()
        installed_languages = argostranslate.translate.get_installed_languages()
        english = next((lang for lang in installed_languages if lang.code == "en"), None)
        hindi = next((lang for lang in installed_languages if lang.code == "hi"), None)
        translation = english.get_translation(hindi) if english and hindi else None
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
