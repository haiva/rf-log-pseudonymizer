#!/usr/bin/env bash
# Vaihe 3: vuototarkistus. Paluukoodi 1, jos vuotoja löytyy, muuten 0.
# Käyttö: bash scripts/tarkista_vuodot.sh <tiedosto-tai-kansio...> [--known <tiedosto>]
# Suhteelliset polut ovat projektin juuresta.
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Käyttö: bash scripts/tarkista_vuodot.sh <tiedosto-tai-kansio...> [--known <tiedosto>]" >&2
    exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -x .venv/bin/python ]; then PY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe
elif command -v python3 >/dev/null 2>&1 && python3 -c "" >/dev/null 2>&1; then PY=python3
else PY=python
fi

CMD=("$PY" -m pseudo.leak_check "$@")
echo "+ ${CMD[*]}"
set +e
"${CMD[@]}"
RC=$?
set -e

echo
if [ "$RC" -eq 0 ]; then
    echo "Ei vuotoja."
    echo "Seuraava vaihe: jaa vain pseudonymisoitu kansio (tarkista ensin mahdolliset VAROITUS-rivit)."
elif [ "$RC" -eq 1 ]; then
    echo "VUOTOJA LÖYTYI (paluukoodi 1). Älä jaa näitä tiedostoja."
    echo "Seuraava vaihe, jos tämä oli alkuperäinen tulos:"
    echo "  bash scripts/pseudonymisoi.sh <kansio>/output.xml"
fi
exit "$RC"
