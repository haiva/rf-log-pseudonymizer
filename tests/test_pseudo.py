"""Testit rf-log-pseudonymizerille.

Synteettinen testisarja ajetaan robot.run-funktiolla väliaikaiskansioon ja CLI:n
pseudonymisointi toiseen väliaikaiskansioon. Testit käyttävät vain synteettistä aineistoa.
"""

import base64
import io
import os
import re
import runpy
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SUITE = ROOT / "synthetic" / "synthetic_pii.robot"
KNOWN_FILE = ROOT / "synthetic" / "known_pii.py"
KNOWN = runpy.run_path(str(KNOWN_FILE))
KNOWN_PII = KNOWN["KNOWN_PII"]

TEST_KEY = "testiavain-vain-synteettiselle-aineistolle"
EXPECTED_TYPES = {"JWT", "APIKEY", "SECRET", "TOKEN", "EMAIL", "UUID", "HETU", "PHONE", "IP"}
PSEUDONYM = re.compile(r"(?:<|&lt;)([A-Z]+)_[0-9a-f]{8}(?:>|&gt;)")

# (syöte, odotettu tyyppi, arvo joka ei saa jäädä tekstiin)
RULE_EXAMPLES = [
    ("Bearer " + KNOWN["JWT"], "JWT", KNOWN["JWT"]),
    ("url?access_token=AbCdEf123456&x=1", "TOKEN", "AbCdEf123456"),
    ("Cookie: sid=0123456789abcdef", "TOKEN", "0123456789abcdef"),
    ("Bearer abcdefgh12345678", "TOKEN", "abcdefgh12345678"),
    ('{"refresh_token": "' + KNOWN["REFRESH_TOKEN"] + '"}', "TOKEN", KNOWN["REFRESH_TOKEN"]),
    ("X-Auth-Token: AbCdEf123456", "TOKEN", "AbCdEf123456"),
    ("url?api_key=" + KNOWN["API_KEY"], "APIKEY", KNOWN["API_KEY"]),
    ("X-API-Key: " + KNOWN["API_KEY"], "APIKEY", KNOWN["API_KEY"]),
    ("avain " + KNOWN["PROVIDER_KEY"], "APIKEY", KNOWN["PROVIDER_KEY"]),
    ("avain sk-synteettinen0123456789abcd", "APIKEY", "sk-synteettinen0123456789abcd"),
    ("avain ghp_" + "x1" * 18, "APIKEY", "ghp_" + "x1" * 18),
    ("avain xoxb-1234567890-synteettinen", "APIKEY", "xoxb-1234567890-synteettinen"),
    ('{"client_secret": "' + KNOWN["CLIENT_SECRET"] + '"}', "SECRET", KNOWN["CLIENT_SECRET"]),
    ("&quot;client_secret&quot;: &quot;" + KNOWN["CLIENT_SECRET"] + "&quot;", "SECRET",
     KNOWN["CLIENT_SECRET"]),
    ("user=testaaja password=" + KNOWN["PASSWORD"], "SECRET", KNOWN["PASSWORD"]),
    ("Authorization: Basic " + KNOWN["BASIC_AUTH"], "SECRET", KNOWN["BASIC_AUTH"]),
    ("posti: " + KNOWN["EMAIL"], "EMAIL", KNOWN["EMAIL"]),
    ("id " + KNOWN["USER_UUID"], "UUID", KNOWN["USER_UUID"]),
    ("hetu " + KNOWN["HETU_1900"], "HETU", KNOWN["HETU_1900"]),
    ("hetu " + KNOWN["HETU_2000"], "HETU", KNOWN["HETU_2000"]),
    ("hetu 311299-999A", "HETU", "311299-999A"),  # virheellinen tarkistemerkki
    ("puh. " + KNOWN["PHONE"], "PHONE", KNOWN["PHONE"]),
    ("puh. 0501234567", "PHONE", "0501234567"),
    ("osoitteesta " + KNOWN["IP"] + ".", "IP", KNOWN["IP"]),
]


def run_cli(*args, key=TEST_KEY):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("PSEUDO_KEY", None)
    if key is not None:
        env["PSEUDO_KEY"] = key
    return subprocess.run(
        [sys.executable, "-m", "pseudo", *map(str, args)],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
    )


def run_leak_check(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "pseudo.leak_check", *map(str, args), "--known", str(KNOWN_FILE)],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8",
    )


def readable_text(path):
    """Tiedoston teksti; HTML:stä myös RF:n zlib+base64-pakatut merkkijonot purettuina.

    Tarkoituksella testin oma toteutus, ei työkalun: testi ei luota testattavaan koodiin.
    """
    text = Path(path).read_text(encoding="utf-8")
    decoded = []
    for blob in re.findall(r'"([A-Za-z0-9+/]{8,}={0,2})"', text):
        try:
            decoded.append(zlib.decompress(base64.b64decode(blob)).decode("utf-8"))
        except Exception:
            pass
    return "\n".join([text, *decoded])


@pytest.fixture(scope="session")
def original_dir(tmp_path_factory):
    import robot

    outdir = tmp_path_factory.mktemp("original")
    robot.run(str(SUITE), outputdir=str(outdir), stdout=io.StringIO(), stderr=io.StringIO())
    assert (outdir / "output.xml").exists()
    return outdir


@pytest.fixture(scope="session")
def pseudo_result(original_dir, tmp_path_factory):
    outdir = tmp_path_factory.mktemp("pseudonymized")
    proc = run_cli(original_dir / "output.xml", "--outdir", outdir)
    return outdir, proc


@pytest.fixture(scope="session")
def pseudo_dir(pseudo_result):
    outdir, proc = pseudo_result
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return outdir


def test_alkuperainen_sisaltaa_kaikki_arvot(original_dir):
    xml = (original_dir / "output.xml").read_text(encoding="utf-8")
    log = readable_text(original_dir / "log.html")
    for value in KNOWN_PII:
        assert value in xml, f"aineistosta puuttuu {value}"
        assert value in log, f"log.html:stä puuttuu {value}"


def test_alkuperaisessa_on_pakattu_viesti(original_dir):
    raw = (original_dir / "log.html").read_text(encoding="utf-8")
    decoded = readable_text(original_dir / "log.html")
    # Pitkä viesti on pakattu: sen sisältö löytyy vain purettuna
    assert "vastausrivi vastausrivi" not in raw
    assert "vastausrivi vastausrivi" in decoded


@pytest.mark.parametrize("name", ["output.xml", "log.html", "report.html"])
def test_tuloksessa_ei_tunnettuja_arvoja(pseudo_dir, name):
    text = readable_text(pseudo_dir / name)
    leaked = [value for value in KNOWN_PII if value in text]
    assert not leaked, f"{name} vuotaa: {leaked}"


def test_errors_osio_pseudonymisoitu(pseudo_dir):
    import xml.etree.ElementTree as ET

    errors = ET.parse(pseudo_dir / "output.xml").getroot().find("errors")
    messages = [msg.text or "" for msg in errors.iter("msg")]
    assert messages, "errors-osiossa ei ole viestejä"
    joined = "\n".join(messages)
    assert re.search(r"<EMAIL_[0-9a-f]{8}>", joined)
    assert re.search(r"<IP_[0-9a-f]{8}>", joined)
    assert not [value for value in KNOWN_PII if value in joined]


def test_jokainen_tyyppi_pseudonyymina(pseudo_dir):
    text = (pseudo_dir / "output.xml").read_text(encoding="utf-8")
    found = set(PSEUDONYM.findall(text))
    assert EXPECTED_TYPES <= found, f"puuttuu: {EXPECTED_TYPES - found}"


@pytest.mark.parametrize("text, kind, value", RULE_EXAMPLES)
def test_saannot(text, kind, value):
    from pseudo.core import Pseudonymizer

    result = Pseudonymizer(TEST_KEY).process(text)
    assert value not in result
    assert re.search(rf"<{kind}_[0-9a-f]{{8}}>", result), result


@pytest.mark.parametrize("text", [
    "versio 1.2.3.4.5",                # viisi numeroryhmää ei ole IP
    "kesto 0.000296 s",
    "aika 2026-11-02T10:14:28.504391",
    "token=lyhyt",                     # alle 8 merkkiä
    "password=${PASSWORD}",            # RF-muuttuja ei ole salaisuus
    "Typing password into text field 'id:password'.",
    "Basic authentication enabled",
    "tokens=12345678",
])
def test_ei_vaaria_osumia(text):
    from pseudo.core import Pseudonymizer

    assert Pseudonymizer(TEST_KEY).process(text) == text


def test_ip_lauseen_lopussa_piste_sailyy():
    from pseudo.core import Pseudonymizer

    result = Pseudonymizer(TEST_KEY).process(f"palvelimella {KNOWN['IP']}.")
    assert re.fullmatch(r"palvelimella <IP_[0-9a-f]{8}>\.", result), result


def test_determinismi_ja_avain(pseudo_dir):
    from pseudo.core import Pseudonymizer

    text = f"{KNOWN['EMAIL']} ja {KNOWN['EMAIL']}"
    first = Pseudonymizer(TEST_KEY).process(text)
    again = Pseudonymizer(TEST_KEY).process(text)
    other = Pseudonymizer("toinen-avain").process(text)
    tags = re.findall(r"<EMAIL_[0-9a-f]{8}>", first)
    assert len(tags) == 2 and tags[0] == tags[1]
    assert first == again
    assert other != first

    # Sama arvo saa saman tunnisteen kaikkialla tuloksessa
    expected = Pseudonymizer(TEST_KEY).pseudonym("EMAIL", KNOWN["EMAIL"])
    output = (pseudo_dir / "output.xml").read_text(encoding="utf-8")
    escaped = expected.replace("<", "&lt;").replace(">", "&gt;")
    assert output.count(escaped) >= 3


def test_kuvat_poistettu(pseudo_result, pseudo_dir):
    _, proc = pseudo_result
    text = (pseudo_dir / "output.xml").read_text(encoding="utf-8")
    assert "data:image" not in text
    assert "&lt;img" not in text
    assert "[upotettu kuva poistettu]" in text
    assert re.search(r"Poistetut kuvat:\s*1\b", proc.stdout), proc.stdout


def test_tulos_on_kelvollinen_rf_tulos(original_dir, pseudo_dir):
    from robot.api import ExecutionResult

    original = ExecutionResult(str(original_dir / "output.xml"))
    pseudo = ExecutionResult(str(pseudo_dir / "output.xml"))
    assert pseudo.statistics.total.total == original.statistics.total.total
    assert pseudo.statistics.total.failed == original.statistics.total.failed
    assert [t.status for t in pseudo.suite.all_tests] == [t.status for t in original.suite.all_tests]
    assert [t.id for t in pseudo.suite.all_tests] == [t.id for t in original.suite.all_tests]
    assert (pseudo_dir / "log.html").exists()
    assert (pseudo_dir / "report.html").exists()


def test_puuttuva_avain(original_dir, tmp_path):
    outdir = tmp_path / "ei_saa_syntya"
    proc = run_cli(original_dir / "output.xml", "--outdir", outdir, key=None)
    assert proc.returncode == 2
    assert "PSEUDO_KEY" in proc.stderr
    assert not outdir.exists()


def test_sama_kansio_kuin_syotteella(original_dir):
    before = {p.name: p.stat().st_mtime_ns for p in original_dir.iterdir()}
    proc = run_cli(original_dir / "output.xml", "--outdir", original_dir)
    assert proc.returncode == 2
    assert {p.name: p.stat().st_mtime_ns for p in original_dir.iterdir()} == before


def test_vuototarkistus(original_dir, pseudo_dir):
    original = run_leak_check(original_dir / "output.xml")
    assert original.returncode == 1, original.stdout + original.stderr
    assert "VUOTO" in original.stdout

    pseudo = run_leak_check(pseudo_dir)
    assert pseudo.returncode == 0, pseudo.stdout + pseudo.stderr


def test_vuototarkistus_kansio_loytaa_kopion(original_dir, pseudo_dir, tmp_path):
    shared = tmp_path / "jaettava"
    shutil.copytree(pseudo_dir, shared)
    (shared / "liitteet").mkdir()
    shutil.copy(original_dir / "output.xml", shared / "liitteet" / "vanha_output.xml")
    proc = run_leak_check(shared)
    assert proc.returncode == 1
    assert "vanha_output.xml" in proc.stdout
