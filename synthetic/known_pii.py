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

REFRESH_TOKEN = "r3fr3shT0k3nSynteettinen99"
# Avainsanan perusteella tunnistettava avain (api_key=, X-API-Key:)
API_KEY = "ak_test_9f8e7d6c5b4a3210ZyXw"
# Sovellustunnus ja -avain (app_id=, app_key=)
APP_ID = "appid_synt_4c3b2a19"
APP_KEY = "appkey_synt_7e6d5c4b3a29"
# AWS:n dokumentaatiossa julkaistu esimerkkiavain, tunnistetaan etuliitteestä
PROVIDER_KEY = "AKIAIOSFODNN7EXAMPLE"
CLIENT_SECRET = "cl1entS3cretSynteettinen42"
PASSWORD = "Salasana!2026synt"
# base64("testaaja:synteettinen")
BASIC_AUTH = "dGVzdGFhamE6c3ludGVldHRpbmVu"

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
    REFRESH_TOKEN,
    API_KEY,
    APP_ID,
    APP_KEY,
    PROVIDER_KEY,
    CLIENT_SECRET,
    PASSWORD,
    BASIC_AUTH,
    PHONE,
    HETU_1900,
    HETU_2000,
]
