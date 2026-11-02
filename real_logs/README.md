# real_logs/

Paikka oikeille Robot Framework -tuloksille, jotka pseudonymisoidaan ennen jakamista.

- Kansion sisältö on `.gitignore`ssa (tämä README pois lukien), joten oikeat logit eivät päädy
  versionhallintaan.
- Claude Coden lukeminen on estetty `.claude/settings.json`:ssa. Esto ei ole aukoton
  hiekkalaatikko: älä käsittele oikeita logeja agentin kanssa.

Käyttö:

```bash
bash scripts/pseudonymisoi.sh real_logs/<ajo>/output.xml results/<ajo>-pseudonymized
bash scripts/tarkista_vuodot.sh results/<ajo>-pseudonymized
```

Jaa vain pseudonymisoitu kansio.
