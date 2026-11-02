"""Vuototarkistus: python -m pseudo.leak_check <tiedosto-tai-kansio...> [--known known_pii.py]

Paluukoodi 1, jos yksikin tunnettu arvo tai tunnettu muoto löytyy, muuten 0.
"""

import argparse
import base64
import binascii
import re
import runpy
import sys
import zlib
from pathlib import Path

from .core import IMAGE_RE, PSEUDONYM_RE, RULES

TEXT_SUFFIXES = {".xml", ".html", ".txt", ".log", ".json"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}

# RF:n log.html ja report.html tallentavat pitkät merkkijonot zlib-pakattuina ja base64-koodattuina
_RF_BLOB_RE = re.compile(r'"([A-Za-z0-9+/]{8,}={0,2})"')


def _decode_rf_blob(match):
    try:
        return zlib.decompress(base64.b64decode(match.group(1), validate=True)).decode("utf-8")
    except (binascii.Error, zlib.error, UnicodeDecodeError, ValueError):
        return match.group(0)


def readable_text(path):
    """Tiedoston teksti; HTML:ssä pakatut merkkijonot korvataan purettuina."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    if Path(path).suffix.lower() == ".html":
        text = _RF_BLOB_RE.sub(_decode_rf_blob, text)
    return text


def find_leaks(text, known=()):
    """Palauttaa listan (tyyppi, arvo)."""
    findings = [("TUNNETTU", value) for value in known if value and value in text]
    # Jo pseudonymisoidut tunnisteet ja kuvien base64-data eivät ole vuotoja
    text = PSEUDONYM_RE.sub(" ", text)
    text = IMAGE_RE.sub(" ", text)
    for kind, pattern, group in RULES:
        for match in pattern.finditer(text):
            findings.append((kind, match.group(group)))
    return findings


def collect_files(paths):
    """Palauttaa (tarkistettavat tiedostot, tarkistamatta jäävät tiedostot)."""
    checked, skipped = [], []
    for path in map(Path, paths):
        candidates = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.suffix.lower() in TEXT_SUFFIXES:
                checked.append(candidate)
            else:
                skipped.append(candidate)
    return checked, skipped


def load_known(path):
    return [str(value) for value in runpy.run_path(str(path)).get("KNOWN_PII", [])]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m pseudo.leak_check",
        description="Etsii henkilötietoja tiedostoista ja kansioista (rekursiivisesti).",
    )
    parser.add_argument("paths", nargs="+", help="tarkistettavat tiedostot tai kansiot")
    parser.add_argument("--known", help="Python-tiedosto, jonka KNOWN_PII-listan arvot etsitään sellaisinaan")
    args = parser.parse_args(argv)

    missing = [p for p in args.paths if not Path(p).exists()]
    if missing:
        print(f"VIRHE: polkua ei löydy: {', '.join(missing)}", file=sys.stderr)
        return 2
    known = load_known(args.known) if args.known else []

    checked, skipped = collect_files(args.paths)
    for path in skipped:
        reason = "kuvatiedosto" if path.suffix.lower() in IMAGE_SUFFIXES else "ei tekstitiedosto"
        print(f"VAROITUS {path}: {reason}, ei voi tarkistaa – älä jaa tarkistamatta")

    leak_count = 0
    for path in checked:
        for kind, value in find_leaks(readable_text(path), known):
            print(f"VUOTO {path}: {kind}: {value}")
            leak_count += 1

    print(f"Tarkistettu {len(checked)} tiedostoa, ohitettu {len(skipped)}, vuotoja {leak_count}.")
    return 1 if leak_count else 0


if __name__ == "__main__":
    sys.exit(main())
