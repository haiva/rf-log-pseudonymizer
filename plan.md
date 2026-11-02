# Suunnitelma: rf-log-pseudonymizer

Työkalu, joka pseudonymisoi Robot Frameworkin testitulokset ennen kuin niitä jaetaan eteenpäin,
esimerkiksi AI-analyysiin, toiselle tiimille tai tiketin liitteeksi.

Tämä on hyväksytty toteutussuunnitelma. Toteuta vaiheet kohdan 13 järjestyksessä yhtäjaksoisesti
ja raportoi lopuksi kohdan 14 mukaisesti.

---

## 1. Tavoite ja rajaus

**Tekee**
- Lukee RF:n `output.xml`:n ja kirjoittaa erilliseen kansioon pseudonymisoidun `output.xml`:n
  sekä siitä tuotetut `log.html`:n ja `report.html`:n.
- Tunnistaa ja pseudonymisoi: sähköpostit, IP-osoitteet, UUID-tunnisteet, istunto- ja
  API-tokenit, JWT:t, suomalaiset henkilötunnukset ja matkapuhelinnumerot.
- Poistaa upotetut kuvat (`<img>`-tagit) kaikesta tekstistä.
- Tarkistaa tuloksen vuototarkistuksella ennen jakamista.

**Ei tee**
- Ei muuta alkuperäistä `output.xml`:ää eikä mitään muuta tiedostoa syötekansiossa.
- Ei käsittele muita ajon tiedostoja: `playwright-log.txt`, kuvakaappaustiedostot, tracet,
  videot, xUnit- tai debug-tiedostot. Ne jätetään jakamatta.
- Ei tunnista vapaata tekstiä, kuten nimiä virheilmoituksissa tai käyttäjän syötteissä.

---

## 2. Periaatteet

1. **Oikea data ei kulje agentin kautta.** Kehitys ja testaus tehdään vain synteettisellä
   aineistolla kansiossa `synthetic/`.
2. **Käsitellään kaikki, poikkeukset sallitaan erikseen.** Pseudonymisointi tehdään
   tekstitasolla kaikkeen output.xml:n tekstiin ja attribuutteihin. Vain nimetyt rakenteelliset
   attribuutit ohitetaan (kohta 5).
3. **Pseudonymisointi, ei poisto.** Sama arvo saa saman avaimen kanssa aina saman tunnisteen
   (`<TYYPPI_8hex>`), joten tapahtumaketjut säilyvät. Juridisesti tulos on yhä henkilötietoa.
4. **HMAC-SHA256 avaimella** ympäristömuuttujasta `PSEUDO_KEY`. Ei pelkkää hashia (purettavissa
   sanakirjahyökkäyksellä), ei kovakoodattua avainta, ei oletusavainta.
5. **Testit ennen toteutusta.** Jokaisesta tietotyypistä on synteettinen arvo, ja testi
   epäonnistuu ennen kuin sääntö on olemassa.
6. **Laatu mitataan.** Vuototarkistus palauttaa virhekoodin, jos yksikin tunnettu arvo tai
   tunnettu muoto löytyy.
7. **Testejä tai vuototarkistusta ei heikennetä**, jotta ne menisivät läpi.

---

## 3. Tiedostorakenne

```
rf-log-pseudonymizer/
├── CLAUDE.md                     säännöt Claude Codelle
├── README.md                     käyttöohje
├── plan.md                       tämä suunnitelma
├── requirements.txt              robotframework>=7.0, pytest>=8.0
├── .env.example                  PSEUDO_KEY-mallirivi
├── .gitignore                    .env, .venv/, results/, real_logs/*, välimuistit
├── .claude/settings.json         Read estetty: real_logs/, results/original/, .env
├── pseudo/
│   ├── __init__.py
│   ├── __main__.py               CLI: python -m pseudo <output.xml> --outdir <kansio>
│   ├── core.py                   säännöt, HMAC, tekstin käsittely, laskurit
│   ├── xmlproc.py                output.xml:n tekstitason läpikäynti
│   └── leak_check.py             vuototarkistus: python -m pseudo.leak_check <polku...>
├── synthetic/
│   ├── known_pii.py              synteettiset arvot ja lista KNOWN_PII
│   └── synthetic_pii.robot       RF-testisarja, joka sijoittaa arvot tuloksiin
├── tests/
│   └── test_pseudo.py            pytest-testit
├── scripts/
│   ├── luo_testiaineisto.sh      vaihe 1: synteettinen testiaineisto
│   ├── pseudonymisoi.sh          vaihe 2: pseudonymisointi
│   └── tarkista_vuodot.sh        vaihe 3: vuototarkistus
└── real_logs/README.md           paikka oikeille logeille (gitignored, Claudelta estetty)
```

---

## 4. Tunnistussäännöt

Säännöt ovat `core.py`:ssä listana `(tyyppi, säännöllinen lauseke, korvattava ryhmä)`.
Järjestys on merkitsevä: tarkemmat ja pidemmät muodot ensin, jotta niiden osat eivät osu
yleisempiin sääntöihin.

| # | Tyyppi | Tunnistaa | Huomio |
|---|---|---|---|
| 0 | (kuva) | `<img …>`-tagit | Korvataan tekstillä `[upotettu kuva poistettu]` ennen muita sääntöjä. Lasketaan erikseen. |
| 1 | `JWT` | `eyJ…`-alkuiset kolmiosaiset tokenit | Ennen TOKEN-sääntöä, koska JWT on usein `Bearer`-sanan perässä. |
| 2 | `TOKEN` | `token=`, `access_token=`, `session=`, `sessionid=`, `sid=`, `Bearer ` + arvo (vähintään 8 merkkiä) | Korvataan vain arvo, avain säilyy: `token=<TOKEN_…>`. |
| 3 | `EMAIL` | sähköpostiosoitteet | Ennen UUID- ja IP-sääntöjä. |
| 4 | `UUID` | 8-4-4-4-12-heksamuoto | Käyttäjä- ja istuntotunnisteet. |
| 5 | `HETU` | `ppkkvv` + välimerkki (`-`, `+`, `A–F`, `U–Y`) + yksilönumero + tarkistemerkki | Tarkistemerkin oikeellisuutta ei vaadita, jotta myös virheelliset tunnukset tunnistetaan. |
| 6 | `PHONE` | suomalaiset matkapuhelinnumerot (`+358` tai `0`, `4x` tai `50`), välilyönnit sallittu | |
| 7 | `IP` | IPv4 | Lauseen loppupiste sallitaan osoitteen perässä (`…23.`), mutta ei viidettä numeroryhmää. |

Pseudonyymi: `<TYYPPI_` + HMAC-SHA256(avain, arvo) heksana, 8 ensimmäistä merkkiä + `>`.

`core.py` pitää laskuria korvauksista tyypeittäin ja poistetuista kuvista CLI:n yhteenvetoa varten.

---

## 5. Tekstitason käsittely (`xmlproc.py`)

- output.xml jäsennetään Pythonin vakiokirjaston `xml.etree.ElementTree`:llä.
- **Jokaisesta elementistä** käsitellään `text`, `tail` ja **kaikkien attribuuttien arvot**,
  lukuun ottamatta alla lueteltuja. Tuntemattomat ja tulevissa RF-versioissa lisättävät
  attribuutit käsitellään oletuksena.
- Käsittely kattaa siten myös osiot, jotka elementtikohtainen käsittely helposti ohittaa:
  `<errors>` (WARN- ja ERROR-viestit), `<statistics>` (testien ja tagien nimet), `<doc>`,
  `<arg>`, `<status>`-elementtien virheviestit, `<meta>` sekä `name`- ja `source`-attribuutit.

**Ohitettavat attribuutit** (muoto on säilytettävä, eivätkä ne voi sisältää henkilötietoja):

| Attribuutti | Peruste |
|---|---|
| `status` | tila (PASS, FAIL, SKIP, NOT RUN) |
| `start`, `elapsed`, `starttime`, `endtime`, `time`, `timestamp` | aikaleimat ja kestot (RF 7 ja vanhemmat nimet) |
| `level` | lokitaso |
| `html` | totuusarvo |
| `id` | rakenteellinen tunniste (`s1-t2-k3`) |
| `type` | elementin tyyppi (SETUP, FOR, VAR …) |
| `generator`, `generated`, `rpa`, `schemaversion` | output.xml:n otsakkeen metatiedot |
| `pass`, `fail`, `skip` | tilastojen lukumäärät |
| `line` | rivinumero |

Kirjoitus: `ElementTree.write(…, encoding="UTF-8", xml_declaration=True)`.

---

## 6. CLI (`python -m pseudo`)

```
python -m pseudo <output.xml> [--outdir results/pseudonymized]
```

Toiminta järjestyksessä:
1. Tarkistaa, että `PSEUDO_KEY` on asetettu. Jos ei, virhe ja paluukoodi 2 **ennen** kuin mitään
   kirjoitetaan.
2. Tarkistaa, että syöte on olemassa ja on kelvollinen XML-tiedosto.
3. **Kieltäytyy kirjoittamasta samaan kansioon, jossa syöte on** (paluukoodi 2), jotta
   alkuperäiset ja pseudonymisoidut tiedostot eivät sekoitu.
4. Pseudonymisoi ja kirjoittaa `<outdir>/output.xml`.
5. Tuottaa siitä `<outdir>/log.html` ja `<outdir>/report.html` RF:n `ResultWriter`illa
   (`robot.api.ResultWriter`).
6. Tulostaa yhteenvedon: korvaukset tyypeittäin, poistetut kuvat ja kirjoitetut tiedostot.

Paluukoodit: 0 = onnistui, 2 = konfiguraatio- tai syötevirhe.

---

## 7. Vuototarkistus (`python -m pseudo.leak_check`)

```
python -m pseudo.leak_check <tiedosto-tai-kansio...> [--known synthetic/known_pii.py]
```

- Hyväksyy tiedostoja ja **kansioita**. Kansiosta tarkistetaan rekursiivisesti kaikki
  tekstitiedostot (`.xml`, `.html`, `.txt`, `.log`, `.json`), jotta jaettavasta kansiosta ei
  voi jäädä mitään tarkistamatta.
- Etsii samoja muotoja kuin `core.py` (tuo säännöt sieltä) ja ohittaa jo pseudonymisoidut
  tunnisteet `<TYYPPI_8hex>`.
- `--known`: tarkistaa lisäksi Python-tiedoston `KNOWN_PII`-listan arvot sellaisinaan.
- Listaa löydökset muodossa `VUOTO <tiedosto>: <tyyppi>: <arvo>`.
- Paluukoodi 1, jos yksikin osuma löytyy, muuten 0.
- Ilmoittaa, jos kansiossa on kuvatiedostoja, joita ei voi tarkistaa (varoitus, ei virhe).

---

## 8. Synteettinen testiaineisto

**`synthetic/known_pii.py`** (RF-muuttujatiedosto ja testien lähde):
- sähköpostit: `example.com`, `example.org`
- IP-osoitteet: `198.51.100.0/24`, `203.0.113.0/24`
- UUID-käyttäjätunniste, istuntotoken, JWT
- suomalainen matkapuhelinnumero
- henkilötunnukset yksilönumeroilla 900–999 ja **oikealla tarkistemerkillä**, yksi 1900- ja
  yksi 2000-luvun välimerkillä
- lista `KNOWN_PII`, jossa kaikki yllä olevat

**`synthetic/synthetic_pii.robot`** sijoittaa arvot kaikkialle, minne henkilötiedot oikeissa
tuloksissa päätyvät:
- `Log`-viestit (myös URL-parametrit ja `Authorization: Bearer`)
- keywordin argumentit ja embedded-argumenttinen keyword-nimi
- paluuarvo (`${x}=  Set Variable`) ja `VAR`-lause
- epäonnistuvan `Should Be Equal` -tarkistuksen virheviesti
- testin dokumentaatio, jossa IP-osoite on lauseen lopussa ennen pistettä
- suiten metadata
- **WARN-tason viesti** (kopioituu `<errors>`-osioon)
- `Log … html=True` -viestiin upotettu base64-kuva

---

## 9. Testit (`tests/test_pseudo.py`)

Testit ajavat synteettisen testisarjan `robot.run`-funktiolla väliaikaiskansioon ja CLI:n
pseudonymisoinnin toiseen väliaikaiskansioon.

| Testi | Todistaa |
|---|---|
| alkuperäinen sisältää kaikki `KNOWN_PII`-arvot | aineisto on kunnossa, muuten muut testit eivät todista mitään |
| tuloksen output.xml, log.html ja report.html eivät sisällä yhtään `KNOWN_PII`-arvoa | ei vuotoja missään tuotetussa tiedostossa |
| `<errors>`-osion viestit on pseudonymisoitu | WARN-viestien vuotoreitti on suljettu |
| jokainen tietotyyppi esiintyy tuloksessa pseudonyyminä | kaikki säännöt ovat käytössä |
| sama arvo saa saman tunnisteen, ja eri avain antaa eri tunnisteet | determinismi ja avaimen merkitys |
| kuvat on poistettu, ja yhteenveto kertoo poistettujen määrän | kuvien käsittely |
| tulos latautuu `robot.api.ExecutionResult`illa; testien määrä ja tilat säilyvät | tulos on kelvollinen RF-tulos |
| puuttuva `PSEUDO_KEY`: virhe eikä tuloskansioon kirjoiteta mitään | turvallinen epäonnistuminen |
| sama tuloskansio kuin syötteellä: virhe | alkuperäiset ja pseudonymisoidut eivät sekoitu |
| vuototarkistus: alkuperäinen → paluukoodi 1, tulos → 0 | tarkistus näkee henkilötiedot |
| vuototarkistus kansiolle löytää tuloskansioon jälkikäteen kopioidun alkuperäisen tiedoston | kansiotarkistus toimii |

---

## 10. Skriptit (bash; Windowsissa Git Bash)

Jokainen skripti:
- käyttää projektin `.venv`-ympäristön Pythonia, jos se on olemassa (`.venv/bin/python` tai
  `.venv/Scripts/python.exe`), muuten `python3` tai `python`
- tulostaa ensin komennon, jonka se ajaa
- tulostaa lopuksi tuottamansa tiedostot ja seuraavan vaiheen komennon

| Skripti | Tekee |
|---|---|
| `scripts/luo_testiaineisto.sh [kansio]` | Ajaa synteettisen testisarjan (oletus `results/original`). Huomauttaa, että tulos sisältää synteettisiä henkilötietoja eikä sitä jaeta. |
| `scripts/pseudonymisoi.sh <output.xml> [kansio]` | Ajaa CLI:n (oletus `results/pseudonymized`) ja näyttää yhteenvedon. Toimii millä tahansa RF:n output.xml:llä. |
| `scripts/tarkista_vuodot.sh <tiedosto-tai-kansio…> [--known <tiedosto>]` | Ajaa vuototarkistuksen ja palauttaa sen paluukoodin. |

---

## 11. README.md

Suomeksi, sisällysluettelolla. Otsikkorakenne:

1. **Mitä työkalu tekee**: tunnistettavat tietotyypit taulukkona esimerkkeineen;
   pseudonymisointi vs. anonymisointi; miksi HMAC eikä pelkkä hash; miksi tekstitason käsittely.
2. **Asennus**: venv ja riippuvuudet, komennot erikseen macOS/Linuxille ja Windowsille (Git Bash).
3. **Avain**:
   - luonti: `python -c "import secrets; print(secrets.token_hex(32))"`
   - asetus Git Bashissa (`.env` + `source .env`) ja PowerShellissä (`$env:` ja `setx`)
   - säilytys: sama avain = samat pseudonyymit; eri käyttötarkoituksiin eri avain; salasanojen
     hallinta tai CI:n salaisuus; ei koskaan repoon, lokeihin tai keskusteluun agentin kanssa.
4. **Käyttö vaihe vaiheelta**: testiaineiston luonti, vuototarkistus alkuperäiselle,
   pseudonymisointi, vuototarkistus tulokselle, lokien vertailu rinnakkain. Jokaisesta
   vaiheesta sekä skripti että sen ajama Python-komento.
5. **Omat tulokset ja CI**: oman output.xml:n pseudonymisointi; CI-vaihe, jossa vuototarkistus
   on portti ennen jakamista; **jaa vain pseudonymisoitu kansio**.
6. **Kehittäminen Claude Codella**: CLAUDE.md:n säännöt, uuden tietotyypin lisäysjärjestys ja
   esimerkkikehote (esim. IBAN-tilinumerot).
7. **Rajoitukset**:
   - Käsitellään vain output.xml, ja siitä tuotetaan uudet log.html ja report.html. Alkuperäisen
     tuloskansion muita tiedostoja (`playwright-log.txt`, kuvakaappaukset, tracet, videot) ei
     käsitellä.
   - Vapaata tekstiä (esim. nimiä) ei tunnisteta.
   - Väärät osumat ovat mahdollisia (esim. nelilukuinen versionumero tulkitaan IP-osoitteeksi).
   - Henkilötieto voi esiintyä tunnistamattomassa muodossa (esim. URL-enkoodattu sähköposti,
     käyttäjänimi tiedostopolussa).
   - Robot Frameworkin omat keinot kannattaa käyttää ensin: `Fill Secret`, `--loglevel`,
     `--removekeywords passed`.

---

## 12. CLAUDE.md ja `.claude/settings.json`

**CLAUDE.md** kirjaa säännöiksi:
- Oikea data ei kulje agentin kautta. Kansioita `real_logs/` ja `results/original/` ei lueta,
  avata, tulosteta eikä analysoida, vaikka käyttäjä pyytäisi.
- Uusi tietotyyppi aina järjestyksessä: synteettinen arvo `known_pii.py`:hin → käyttö
  testisarjassa → testi epäonnistuu → sääntö `core.py`:hin → testit läpi.
- Kohdan 2 periaatteet 2–7.
- Ajokomennot (skriptit ja `python -m pytest`).

**`.claude/settings.json`**:
- `deny`: `Read(./real_logs/**)`, `Read(./results/original/**)`, `Read(./.env)`
- `allow`: `python -m pytest`, skriptit `scripts/*.sh`

README:ssä todetaan, etteivät `deny`-säännöt ole aukoton hiekkalaatikko. Varsinainen suoja on,
ettei oikeita logeja käsitellä agentin kanssa.

---

## 13. Toteutusjärjestys

1. Rakenne, `requirements.txt`, `.gitignore`, `.env.example`, `CLAUDE.md`, `.claude/settings.json`,
   `real_logs/README.md`.
2. Synteettinen aineisto (`synthetic/`). Aja testisarja ja varmista, että arvot näkyvät
   output.xml:ssä.
3. Testit (`tests/test_pseudo.py`). Aja ja **näytä, että ne epäonnistuvat**.
4. `pseudo/core.py`, `pseudo/xmlproc.py`, `pseudo/__main__.py`. Aja testit ja korjaa, kunnes
   ne menevät läpi. Jos jokin vuotaa, kerro ensin mitä ja miksi, ja korjaa sitten.
5. `pseudo/leak_check.py`. Testit läpi.
6. Skriptit (`scripts/`).
7. `README.md`.
8. Loppuajo käyttäjän järjestyksessä:
   1. `bash scripts/luo_testiaineisto.sh`
   2. `bash scripts/tarkista_vuodot.sh results/original --known synthetic/known_pii.py` (odotus: vuotoja)
   3. `bash scripts/pseudonymisoi.sh results/original/output.xml`
   4. `bash scripts/tarkista_vuodot.sh results/pseudonymized --known synthetic/known_pii.py` (odotus: ei vuotoja)

---

## 14. Valmis, kun

- Kaikki testit menevät läpi.
- Vuototarkistus löytää osumia alkuperäisestä ja ei yhtään pseudonymisoidusta kansiosta.
- Pseudonymisoitu output.xml avautuu RF:n työkaluilla, ja log.html ja report.html aukeavat
  selaimessa.
- README:n komennot toimivat sellaisinaan.

**Loppuraportti:** luodut tiedostot, testien tulos, kunkin loppuajon vaiheen tuloste lyhyesti,
CLI:n yhteenveto sekä arvio siitä, mitä työkalu ei vielä kata.

---

## 15. Riskit ja rajoitukset

| Riski | Vaikutus | Hallinta |
|---|---|---|
| Vapaa teksti (nimet) | vuotaa | rajattu pois; README; jatkossa sallittujen kenttien lista tai paikallinen malli |
| Uudet tai muunnellut muodot (URL-enkoodaus, käyttäjänimi polussa) | vuotaa | testiaineiston laajentaminen; vuototarkistus ei tunnista näitä |
| Väärät osumat (versionumero IP:nä) | luettavuus heikkenee | hyväksytään; tapaus testeihin, jos sääntöä tarkennetaan |
| Liian laaja ohitettavien attribuuttien lista | vuotaa | lista pidetään minimissä; tuntemattomat attribuutit käsitellään |
| Liian suppea ohitettavien attribuuttien lista | tulos ei lataudu | ExecutionResult-testi havaitsee |
| Muut ajon tiedostot jaetaan vahingossa | vuotaa | jaetaan vain pseudonymisoitu kansio; kansiotason vuototarkistus |
| Avain vuotaa | pseudonyymit purettavissa arvaamalla | avain salaisuutena; eri käyttötarkoituksiin eri avain |