"""Synteettiset henkilötiedot testejä varten.

Toimii sekä Robot Frameworkin muuttujatiedostona (synthetic_pii.robot) että testien ja
vuototarkistuksen (--known) lähteenä. Kaikki arvot ovat keksittyjä:
- sähköpostit dokumentaatiotunnuksista example.com / example.org (RFC 2606)
- IP-osoitteet dokumentaatioverkoista 198.51.100.0/24 ja 203.0.113.0/24 (RFC 5737)
- henkilötunnusten yksilönumerot väliltä 900–999 (keinotekoiset tunnukset)
"""

EMAIL = "matti.meikalainen@example.com"
EMAIL2 = "tiina.testaaja@example.org"

IP = "198.51.100.23"
IP2 = "203.0.113.7"

USER_UUID = "3f2b8c1e-7a4d-4e5f-9b6a-1c2d3e4f5a6b"
SESSION_TOKEN = "s3ss10nT0k3nAbCdEf123456"
JWT = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiIzZjJiOGMxZSIsIm5hbWUiOiJTeW50ZWV0dGluZW4ifQ"
    ".c2lnbmF0dXJlLXN5bnRlZXR0aW5lbg"
)

PHONE = "+358 40 123 4567"

# Oikea tarkistemerkki: 1503859345 % 31 -> "5", 010105967 % 31 -> "X"
HETU_1900 = "150385-9345"
HETU_2000 = "010105A967X"

# Pieni (1x1) PNG upotettuna HTML-viestiin. Ei henkilötieto, mutta kuva poistetaan.
IMAGE_HTML = (
    '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAD'
    'UlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="kuvakaappaus">'
)

KNOWN_PII = [
    EMAIL,
    EMAIL2,
    IP,
    IP2,
    USER_UUID,
    SESSION_TOKEN,
    JWT,
    PHONE,
    HETU_1900,
    HETU_2000,
]
