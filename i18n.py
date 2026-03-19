import json
import os
from pathlib import Path

_translations: dict = {}
_lang: str = "de"

SUPPORTED_LANGS = ["de", "en", "es"]

def _read_dotenv(path: str = ".env") -> None:
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key, val)
    except FileNotFoundError:
        pass

def load(lang: str | None = None, locales_dir: str | Path = "locales") -> None:
    global _translations, _lang

    _read_dotenv()
    resolved = (lang or os.getenv("DASHBOARD_LANG", "en")).strip().lower()

    if resolved not in SUPPORTED_LANGS:
        print(f"[i18n] unknown language '{resolved}', fallback to 'en'.")
        resolved = "en"

    locale_file = Path(locales_dir) / f"{resolved}.json"

    if not locale_file.exists():
        raise FileNotFoundError(f"[i18n] language file not found: {locale_file}")

    with open(locale_file, encoding="utf-8") as f:
        _translations = json.load(f)

    _lang = resolved
    print(f"[i18n] language loaded: {_lang}")


def t(key: str, **kwargs) -> str:
    parts = key.split(".")
    value = _translations

    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
        if value is None:
            return f"[{key}]" 

    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            return value
 
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return value
    return f"[{key}]"


def get_lang() -> str:
    return _lang