#!/usr/bin/env bash
# Vaihe 1: ajaa synteettisen testisarjan ja tuottaa alkuperäiset tulokset.
# Käyttö: bash scripts/luo_testiaineisto.sh [kansio]   (oletus results/original)
# Suhteelliset polut ovat projektin juuresta.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -x .venv/bin/python ]; then PY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe
elif command -v python3 >/dev/null 2>&1 && python3 -c "" >/dev/null 2>&1; then PY=python3
else PY=python
fi

OUT="${1:-results/original}"

# Testisarjassa on tarkoituksella epäonnistuva testi, joten paluukoodi ei kerro virheestä
CMD=("$PY" -m robot --nostatusrc --outputdir "$OUT" synthetic/synthetic_pii.robot)
echo "+ ${CMD[*]}"
"${CMD[@]}"

echo
echo "HUOM: $OUT sisältää synteettisiä henkilötietoja. Sitä ei pseudonymisoida paikallaan eikä jaeta."
echo "Tuotetut tiedostot:"
for f in output.xml log.html report.html; do echo "  $OUT/$f"; done
echo
echo "Seuraava vaihe (vuototarkistus alkuperäiselle, odotus: vuotoja):"
echo "  bash scripts/tarkista_vuodot.sh $OUT --known synthetic/known_pii.py"
