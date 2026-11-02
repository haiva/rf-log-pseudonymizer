#!/usr/bin/env bash
# Vaihe 2: pseudonymisoi RF:n output.xml:n ja tuottaa uudet log.html:n ja report.html:n.
# Käyttö: bash scripts/pseudonymisoi.sh <output.xml> [kansio]   (oletus results/pseudonymized)
# Vaatii ympäristömuuttujan PSEUDO_KEY. Suhteelliset polut ovat projektin juuresta.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Käyttö: bash scripts/pseudonymisoi.sh <output.xml> [kansio]" >&2
    exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -x .venv/bin/python ]; then PY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe
elif command -v python3 >/dev/null 2>&1 && python3 -c "" >/dev/null 2>&1; then PY=python3
else PY=python
fi

INPUT="$1"
OUT="${2:-results/pseudonymized}"

CMD=("$PY" -m pseudo "$INPUT" --outdir "$OUT")
echo "+ ${CMD[*]}"
"${CMD[@]}"

echo
echo "Seuraava vaihe (vuototarkistus tulokselle, odotus: ei vuotoja):"
echo "  bash scripts/tarkista_vuodot.sh $OUT --known synthetic/known_pii.py"
