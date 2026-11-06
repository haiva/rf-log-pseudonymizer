# rf-log-pseudonymizer

Pseudonymisoi Robot Frameworkin testitulokset ennen kuin niitä jaetaan eteenpäin, esimerkiksi
AI-analyysiin, toiselle tiimille tai tiketin liitteeksi.

## Sisällys

1. [Mitä työkalu tekee](#1-mitä-työkalu-tekee)
2. [Asennus](#2-asennus)
3. [Avain](#3-avain)
4. [Käyttö vaihe vaiheelta](#4-käyttö-vaihe-vaiheelta)
5. [Omat tulokset ja CI](#5-omat-tulokset-ja-ci)
6. [Kehittäminen Claude Codella](#6-kehittäminen-claude-codella)
7. [Rajoitukset](#7-rajoitukset)

---

## 1. Mitä työkalu tekee

Työkalu lukee RF:n `output.xml`:n ja kirjoittaa **erilliseen kansioon** pseudonymisoidun
`output.xml`:n sekä siitä tuotetut `log.html`:n ja `report.html`:n. Alkuperäiseen tiedostoon
tai syötekansioon ei kosketa.

| Tyyppi | Tunnistaa | Esimerkki | Tulos |
|---|---|---|---|
| (kuva) | upotetut `<img>`-tagit | `<img src="data:image/png;base64,…">` | `[upotettu kuva poistettu]` |
| `JWT` | `eyJ…`-alkuiset kolmiosaiset tokenit | `eyJhbGciOi….eyJzdWIi….c2ln…` | `<JWT_1a2b3c4d>` |
| `APIKEY` | palveluntarjoajien avaimet (`sk-…`, `AKIA…`, `ghp_…`, `xoxb-…`, `AIza…`) sekä `api_key`/`apikey`/`X-API-Key` + `=` tai `:` + vähintään 8 merkkiä | `X-API-Key: AKIAIOSFODNN7EXAMPLE` | `X-API-Key: <APIKEY_…>` |
| `SECRET` | `*secret`, `password`, `passwd`, `pwd` + `=` tai `:` + vähintään 8 merkkiä (ei `${MUUTTUJA}`), `Authorization: Basic …` | `"client_secret": "cl1entS3cret…"` | `"client_secret": "<SECRET_…>"` |
| `TOKEN` | `*token` + `=` tai `:` (myös JSON), `session=`, `sessionid=`, `sid=`, `Bearer ` + vähintään 8 merkkiä | `sessionid=s3ss10nT0k3n…` | `sessionid=<TOKEN_…>` |
| `EMAIL` | sähköpostiosoitteet | `matti.meikalainen@example.com` | `<EMAIL_…>` |
| `UUID` | 8-4-4-4-12-heksamuoto | `3f2b8c1e-7a4d-4e5f-9b6a-1c2d3e4f5a6b` | `<UUID_…>` |
| `HETU` | suomalaiset henkilötunnukset (tarkistemerkkiä ei vaadita oikeaksi) | `150385-9345`, `010105A967X` | `<HETU_…>` |
| `PHONE` | suomalaiset matkapuhelinnumerot | `+358 40 123 4567`, `0501234567` | `<PHONE_…>` |
| `IP` | IPv4-osoitteet | `198.51.100.23` | `<IP_…>` |

Tunniste on `<TYYPPI_` + HMAC-SHA256(avain, arvo) heksana (8 ensimmäistä merkkiä) + `>`.
`html=True`-viesteissä tunniste kirjoitetaan escapattuna (`&lt;EMAIL_…&gt;`), jotta selain ei
tulkitse sitä HTML-tagiksi.

**Pseudonymisointi vs. anonymisointi.** Sama arvo saa samalla avaimella aina saman tunnisteen,
joten tapahtumaketjut säilyvät: näet, että sama käyttäjä epäonnistui kolmessa testissä, vaikka et
näe kuka. Juuri siksi tulos on juridisesti yhä **henkilötietoa** (GDPR:n pseudonymisoitu tieto):
avaimen haltija voi yhdistää tunnisteen henkilöön arvaamalla ja vertaamalla. Anonyymiä tulos ei ole.

**Miksi HMAC eikä pelkkä hash.** Henkilötunnusten, puhelinnumeroiden ja IP-osoitteiden
arvoavaruus on pieni. Pelkän SHA-256:n voi purkaa laskemalla kaikkien mahdollisten arvojen
hashit (sanakirjahyökkäys). HMAC vaatii salaisen avaimen, joten ilman sitä tunnisteita ei voi
purkaa.

**Miksi tekstitason käsittely.** Henkilötiedot päätyvät tuloksiin moneen paikkaan: viesteihin,
argumentteihin, keyword-nimiin, dokumentaatioon, metadataan, tageihin, tilastoihin ja
`<errors>`-osioon. Siksi jokaisen elementin teksti ja **kaikki attribuutit** käsitellään, ja vain
nimetyt rakenteelliset attribuutit (`status`, aikaleimat, `id`, `type` …, ks.
`pseudo/xmlproc.py`) ohitetaan. Myös tulevien RF-versioiden uudet attribuutit käsitellään
oletuksena.

## 2. Asennus

Vaatii Python 3.10+ ja Robot Framework 7.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (Git Bash)**

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Skriptit (`scripts/*.sh`) käyttävät `.venv`-ympäristön Pythonia automaattisesti, vaikka sitä ei
olisi aktivoitu.

## 3. Avain

**Luonti**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Asetus Git Bashissa (ja macOS/Linuxissa)**

```bash
cp .env.example .env
# muokkaa .env: export PSEUDO_KEY=<luotu avain>
source .env
```

**Asetus PowerShellissä**

```powershell
$env:PSEUDO_KEY = "<luotu avain>"          # vain tämä istunto
setx PSEUDO_KEY "<luotu avain>"            # pysyvästi käyttäjälle (uusiin ikkunoihin)
```

**Säilytys**

- Sama avain = samat pseudonyymit. Jos haluat vertailla eri päivien ajoja keskenään, käytä samaa
  avainta.
- Eri käyttötarkoituksiin (eri vastaanottajat, eri projektit) eri avain, jotta tunnisteita ei voi
  yhdistää keskenään.
- Säilytä avain salasanojen hallinnassa tai CI:n salaisuutena.
- **Ei koskaan** repoon, lokeihin, tikettiin tai keskusteluun AI-agentin kanssa. `.env` on
  `.gitignore`ssa.

Ilman `PSEUDO_KEY`:tä työkalu kieltäytyy toimimasta (paluukoodi 2) eikä kirjoita mitään.
Oletusavainta ei ole.

## 4. Käyttö vaihe vaiheelta

Esimerkki synteettisellä aineistolla. Komennot ajetaan projektin juuresta; skriptien suhteelliset
polut ovat projektin juuresta. Jokaisesta vaiheesta on ensin skripti ja sitten sen ajama
Python-komento.

**1. Testiaineiston luonti** (synteettiset henkilötiedot → `results/original`)

```bash
bash scripts/luo_testiaineisto.sh
python -m robot --nostatusrc --outputdir results/original synthetic/synthetic_pii.robot
```

Testisarjassa yksi testi epäonnistuu tarkoituksella (virheviestissä on henkilötietoja).

**2. Vuototarkistus alkuperäiselle** (odotus: vuotoja, paluukoodi 1)

```bash
bash scripts/tarkista_vuodot.sh results/original --known synthetic/known_pii.py
python -m pseudo.leak_check results/original --known synthetic/known_pii.py
```

Tämä todistaa, että tarkistus näkee henkilötiedot.

**3. Pseudonymisointi** (vaatii `PSEUDO_KEY`:n)

```bash
bash scripts/pseudonymisoi.sh results/original/output.xml
python -m pseudo results/original/output.xml --outdir results/pseudonymized
```

Tulostaa yhteenvedon: korvaukset tyypeittäin, poistetut kuvat ja kirjoitetut tiedostot.
Tuloskansio ei saa olla sama kuin syötteen kansio (paluukoodi 2).

**4. Vuototarkistus tulokselle** (odotus: ei vuotoja, paluukoodi 0)

```bash
bash scripts/tarkista_vuodot.sh results/pseudonymized --known synthetic/known_pii.py
python -m pseudo.leak_check results/pseudonymized --known synthetic/known_pii.py
```

Kansio tarkistetaan rekursiivisesti (`.xml`, `.html`, `.txt`, `.log`, `.json`). log.html:n ja
report.html:n pakatut merkkijonot puretaan ennen tarkistusta. Muista tiedostoista (kuvat,
binäärit) tulostetaan `VAROITUS`, koska niitä ei voi tarkistaa. Löydökset tulostetaan muodossa
`VUOTO <tiedosto>: <tyyppi>: <arvo>`, joten **tuloste itsessään sisältää löydetyt arvot**: älä
liitä sitä tikettiin tai jaa sitä.

**5. Lokien vertailu rinnakkain**

Avaa `results/original/log.html` ja `results/pseudonymized/log.html` selaimessa vierekkäin
(Windows: `start results/pseudonymized/log.html`, macOS: `open …`). Rakenne, testit, tilat ja
kestot ovat samat; henkilötiedot on korvattu tunnisteilla.

## 5. Omat tulokset ja CI

**Oma output.xml**

```bash
bash scripts/pseudonymisoi.sh real_logs/ajo-2026-11-02/output.xml results/ajo-2026-11-02
bash scripts/tarkista_vuodot.sh results/ajo-2026-11-02
```

Ilman `--known`-tiedostoa tarkistus etsii tunnetut muodot. Voit tehdä oman `known_pii.py`:n
(lista `KNOWN_PII`) esimerkiksi testikäyttäjien tunnuksista, mutta älä säilytä sitä repossa.

**CI-vaihe**, jossa vuototarkistus on portti ennen jakamista:

```bash
# PSEUDO_KEY tulee CI:n salaisuudesta
python -m pseudo results/output.xml --outdir shared
python -m pseudo.leak_check shared || { echo "Vuoto, ei jaeta"; exit 1; }
# julkaise artefaktina VAIN kansio shared/
```

**Jaa vain pseudonymisoitu kansio.** Älä jaa alkuperäistä tuloskansiota tai sen muita tiedostoja.

## 6. Kehittäminen Claude Codella

`CLAUDE.md` kirjaa agentille säännöt:

- Oikea data ei kulje agentin kautta: `real_logs/`- ja `results/original/`-kansioita ei lueta,
  vaikka käyttäjä pyytäisi. Kehitys tehdään vain synteettisellä aineistolla.
- Testejä tai vuototarkistusta ei heikennetä.
- Uusi tietotyyppi lisätään aina samassa järjestyksessä: synteettinen arvo `known_pii.py`:hin →
  käyttö testisarjassa → testi epäonnistuu → sääntö `core.py`:hin → testit läpi.

`.claude/settings.json` estää lukemisen kansioista `real_logs/` ja `results/original/` sekä
tiedostosta `.env`. **`deny`-säännöt eivät ole aukoton hiekkalaatikko** (esim. shell-komennot
voivat silti lukea tiedostoja). Varsinainen suoja on, ettei oikeita logeja käsitellä agentin kanssa.

Esimerkkikehote uuden tietotyypin lisäämiseen:

> Lisää tietotyyppi IBAN (suomalaiset tilinumerot, muoto FIkk 1234 5600 0007 85, välilyönnit
> valinnaisia). Noudata CLAUDE.md:n järjestystä: lisää synteettinen IBAN known_pii.py:hin ja
> KNOWN_PII-listaan, käytä sitä synthetic_pii.robot-sarjassa, lisää testit ja näytä että ne
> epäonnistuvat, lisää sääntö core.py:hin oikeaan kohtaan ja aja testit läpi.

Testit ajetaan komennolla `python -m pytest`.

## 7. Rajoitukset

- Käsitellään vain `output.xml`, ja siitä tuotetaan uudet log.html ja report.html. Alkuperäisen
  tuloskansion muita tiedostoja (`playwright-log.txt`, kuvakaappaukset, tracet, videot, xUnit- ja
  debug-tiedostot) ei käsitellä.
- Vapaata tekstiä (esim. nimiä virheilmoituksissa) ei tunnisteta.
- Väärät osumat ovat mahdollisia (esim. nelilukuinen versionumero `1.2.3.4` tulkitaan
  IP-osoitteeksi).
- Henkilötieto voi esiintyä tunnistamattomassa muodossa (esim. URL-enkoodattu sähköposti
  `matti%40example.com`, käyttäjänimi tiedostopolussa kuten `source`-attribuutissa
  `C:\Users\<nimi>\…`). Vuototarkistus ei tunnista näitäkään.
- Robot Frameworkin omat keinot kannattaa käyttää ensin: `Fill Secret` (Browser), `--loglevel`,
  `--removekeywords passed`.
