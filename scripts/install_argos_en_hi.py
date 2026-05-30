from __future__ import annotations

import os
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_DIR / "temp" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))
os.environ.setdefault("XDG_DATA_HOME", str(CACHE_DIR / "data"))

import argostranslate.package
import argostranslate.translate


def has_english_hindi() -> bool:
    installed_languages = argostranslate.translate.get_installed_languages()
    english = next((lang for lang in installed_languages if lang.code == "en"), None)
    hindi = next((lang for lang in installed_languages if lang.code == "hi"), None)
    return bool(english and hindi and english.get_translation(hindi))


def main() -> int:
    if has_english_hindi():
        print("Argos English-to-Hindi package already installed.")
        return 0

    print("Updating Argos package index...")
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
        print("Could not find Argos English-to-Hindi package in the package index.", file=sys.stderr)
        return 1

    print(f"Downloading {package}...")
    package_path = package.download()
    print("Installing Argos English-to-Hindi package...")
    argostranslate.package.install_from_path(package_path)

    if not has_english_hindi():
        print("Argos English-to-Hindi package install did not verify.", file=sys.stderr)
        return 1

    print("Argos English-to-Hindi package installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
