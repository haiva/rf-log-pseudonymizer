"""Tunnistussäännöt, HMAC-pseudonyymit ja tekstin käsittely."""

import hashlib
import hmac
import re
from collections import Counter

IMAGE_PLACEHOLDER = "[upotettu kuva poistettu]"
IMAGE_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)

# IPv4-osoitteen numeroryhmä 0–255
_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"

# Avainsanan ja arvon välinen erotin: key=, key: , "key": "  (myös HTML-escapattuna)
_SEP = r"""\s*(?:["']|&quot;)?\s*[:=]\s*(?:["']|&quot;)?\s*"""
# Avaimen tai tokenin arvo
_VALUE = r"([A-Za-z0-9._~+/%=-]{8,})"
# Salasanan arvo: myös erikoismerkit, mutta ei RF-muuttujaa ${...} eikä lainausmerkkejä
_SECRET_VALUE = r"""([^\s"'&<>,;${}]{8,})"""

# (tyyppi, säännöllinen lauseke, korvattava ryhmä). Järjestys on merkitsevä: tarkemmat ja
# pidemmät muodot ensin, jotta niiden osat eivät osu yleisempiin sääntöihin.
RULES = [
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), 0),
    # Palveluntarjoajien etuliitteelliset avaimet: OpenAI/Anthropic, AWS, GitHub, Slack, Google
    ("APIKEY", re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,}"
        r"|xox[abprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35})"
    ), 0),
    ("APIKEY", re.compile(rf"(?<![A-Za-z0-9])(?:x-)?api[_-]?key{_SEP}{_VALUE}", re.IGNORECASE), 1),
    ("SECRET", re.compile(r"\bAuthorization:\s*Basic\s+([A-Za-z0-9+/]{8,}={0,2})", re.IGNORECASE), 1),
    ("SECRET", re.compile(
        rf"(?<![A-Za-z0-9])[A-Za-z_-]*(?:secret|password|passwd|pwd){_SEP}{_SECRET_VALUE}",
        re.IGNORECASE,
    ), 1),
    ("TOKEN", re.compile(
        rf"(?:\b(?:sessionid|session|sid)=|(?<![A-Za-z0-9])[A-Za-z_-]*token{_SEP}|\bBearer\s+)"
        rf"{_VALUE}",
        re.IGNORECASE,
    ), 1),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), 0),
    ("UUID", re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    ), 0),
    # ppkkvv + välimerkki + yksilönumero + tarkistemerkki (oikeellisuutta ei vaadita)
    ("HETU", re.compile(
        r"(?<![0-9A-Za-z])(?:0[1-9]|[12]\d|3[01])(?:0[1-9]|1[0-2])\d\d"
        r"[-+A-FU-Y]\d{3}[0-9A-Y](?![0-9A-Za-z])"
    ), 0),
    # +358 tai 0, sitten 4x tai 50, välilyönnit ja väliviivat sallittu
    ("PHONE", re.compile(r"(?<![\w+])(?:\+358[ -]?|0)(?:4\d|50)(?:[ -]?\d){5,8}(?!\d)"), 0),
    # Lauseen loppupiste sallitaan perässä, viides numeroryhmä ei
    ("IP", re.compile(rf"(?<![\d.]){_OCTET}(?:\.{_OCTET}){{3}}(?!\.?\d)"), 0),
]

# Jo pseudonymisoitu tunniste, myös HTML-escapattuna
PSEUDONYM_RE = re.compile(r"(?:<|&lt;)[A-Z]+_[0-9a-f]{8}(?:>|&gt;)")


class Pseudonymizer:
    """Korvaa tunnistetut arvot tunnisteilla <TYYPPI_8hex> ja laskee korvaukset."""

    def __init__(self, key):
        if not key:
            raise ValueError("avain puuttuu")
        self._key = key.encode("utf-8") if isinstance(key, str) else key
        self.counts = Counter()
        self.images_removed = 0

    def pseudonym(self, kind, value):
        digest = hmac.new(self._key, value.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"<{kind}_{digest[:8]}>"

    def process(self, text, html=False):
        """Pseudonymisoi tekstin. html=True escapaa tunnisteet, jotta selain ei tulkitse niitä tageiksi."""
        if not text:
            return text
        text, removed = IMAGE_RE.subn(IMAGE_PLACEHOLDER, text)
        self.images_removed += removed
        for kind, pattern, group in RULES:
            text = pattern.sub(lambda m: self._replace(m, kind, group, html), text)
        return text

    def _replace(self, match, kind, group, html):
        self.counts[kind] += 1
        tag = self.pseudonym(kind, match.group(group))
        if html:
            tag = tag.replace("<", "&lt;").replace(">", "&gt;")
        start = match.start(group) - match.start()
        end = match.end(group) - match.start()
        whole = match.group(0)
        return whole[:start] + tag + whole[end:]
