"""CLI: python -m pseudo <output.xml> [--outdir results/pseudonymized]"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from .core import Pseudonymizer
from .xmlproc import pseudonymize_file

DEFAULT_OUTDIR = "results/pseudonymized"


def fail(message):
    print(f"VIRHE: {message}", file=sys.stderr)
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m pseudo",
        description="Pseudonymisoi Robot Frameworkin output.xml:n ja tuottaa siitä log.html:n ja report.html:n.",
    )
    parser.add_argument("output_xml", help="pseudonymisoitava output.xml")
    parser.add_argument("--outdir", default=DEFAULT_OUTDIR, help=f"tuloskansio (oletus {DEFAULT_OUTDIR})")
    args = parser.parse_args(argv)

    # 1. Avain ennen kuin mitään kirjoitetaan
    key = os.environ.get("PSEUDO_KEY")
    if not key:
        return fail("ympäristömuuttuja PSEUDO_KEY puuttuu. Katso README.md, kohta Avain.")

    # 2. Syöte on olemassa ja kelvollinen RF:n output.xml
    source = Path(args.output_xml)
    if not source.is_file():
        return fail(f"syötettä ei löydy: {source}")
    try:
        root = ET.parse(source).getroot()
    except ET.ParseError as error:
        return fail(f"syöte ei ole kelvollinen XML-tiedosto: {source} ({error})")
    if root.tag != "robot":
        return fail(f"syöte ei ole Robot Frameworkin output.xml: {source}")

    # 3. Ei samaan kansioon syötteen kanssa
    outdir = Path(args.outdir)
    if outdir.resolve() == source.resolve().parent:
        return fail("tuloskansio ei voi olla sama kuin syötteen kansio. Anna eri --outdir.")

    # 4. Pseudonymisointi
    pseudonymizer = Pseudonymizer(key)
    outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / "output.xml"
    pseudonymize_file(source, target, pseudonymizer)

    # 5. log.html ja report.html pseudonymisoidusta tuloksesta
    from robot.api import ResultWriter

    log, report = outdir / "log.html", outdir / "report.html"
    ResultWriter(str(target)).write_results(log=str(log), report=str(report))

    # 6. Yhteenveto
    print(f"Pseudonymisoitu: {source}")
    print("Korvaukset tyypeittäin:")
    if pseudonymizer.counts:
        for kind, count in sorted(pseudonymizer.counts.items()):
            print(f"  {kind:<6} {count}")
    else:
        print("  (ei korvauksia)")
    print(f"Poistetut kuvat: {pseudonymizer.images_removed}")
    print("Kirjoitetut tiedostot:")
    for path in (target, log, report):
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
