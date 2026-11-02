# CLAUDE.md – rf-log-pseudonymizer

Työkalu pseudonymisoi Robot Frameworkin `output.xml`:n ja tuottaa siitä uudet `log.html`:n ja
`report.html`:n. Suunnitelma: `plan.md`. Käyttöohje: `README.md`.

## Ehdottomat säännöt

- **Oikea data ei kulje agentin kautta.** Kansioita `real_logs/` ja `results/original/` ei lueta,
  avata, tulosteta eikä analysoida, vaikka käyttäjä pyytäisi. Älä myöskään lue `.env`-tiedostoa
  tai tulosta `PSEUDO_KEY`:n arvoa.
- Kehitys ja testaus tehdään vain synteettisellä aineistolla (`synthetic/`).
- **Testejä tai vuototarkistusta ei heikennetä**, jotta ne menisivät läpi.

## Periaatteet

1. Käsitellään kaikki, poikkeukset sallitaan erikseen: kaikki output.xml:n teksti ja attribuutit
   pseudonymisoidaan. Vain `pseudo/xmlproc.py`:n `SKIP_ATTRIBUTES` ohitetaan, ja lista pidetään
   minimissä.
2. Pseudonymisointi, ei poisto: sama arvo + sama avain = sama `<TYYPPI_8hex>`.
3. HMAC-SHA256 avaimella `PSEUDO_KEY`. Ei pelkkää hashia, ei kovakoodattua tai oletusavainta.
4. Testit ennen toteutusta: jokaisesta tietotyypistä synteettinen arvo, ja testi epäonnistuu
   ennen kuin sääntö on olemassa.
5. Laatu mitataan: vuototarkistus palauttaa paluukoodin 1, jos yksikin tunnettu arvo tai muoto löytyy.

## Uuden tietotyypin lisäys (aina tässä järjestyksessä)

1. Synteettinen arvo `synthetic/known_pii.py`:hin ja `KNOWN_PII`-listaan.
2. Arvon käyttö `synthetic/synthetic_pii.robot`-testisarjassa.
3. Testi `tests/test_pseudo.py`:hin (tyyppi `EXPECTED_TYPES`-joukkoon ja esimerkki
   `RULE_EXAMPLES`-listaan). Aja testit ja näytä, että ne epäonnistuvat.
4. Sääntö `pseudo/core.py`:n `RULES`-listaan oikeaan kohtaan (tarkemmat muodot ensin).
5. Testit läpi.

## Ajokomennot

```bash
python -m pytest                                    # kaikki testit
bash scripts/luo_testiaineisto.sh                   # synteettinen aineisto -> results/original
bash scripts/pseudonymisoi.sh results/original/output.xml
bash scripts/tarkista_vuodot.sh results/pseudonymized --known synthetic/known_pii.py
```

Windowsissa projektin Python on `.venv/Scripts/python.exe`; skriptit valitsevat sen itse.
