"""output.xml:n tekstitason läpikäynti.

Jokaisen elementin text, tail ja kaikki attribuutit käsitellään, lukuun ottamatta
rakenteellisia attribuutteja (SKIP_ATTRIBUTES). Tuntemattomat attribuutit käsitellään.
"""

import xml.etree.ElementTree as ET

# Muoto on säilytettävä, eivätkä nämä voi sisältää henkilötietoja. Pidä lista minimissä.
SKIP_ATTRIBUTES = frozenset({
    "status",
    "start", "elapsed", "starttime", "endtime", "time", "timestamp",
    "level",
    "html",
    "id",
    "type",
    "generator", "generated", "rpa", "schemaversion",
    "pass", "fail", "skip",
    "line",
})


def pseudonymize_tree(tree, pseudonymizer):
    for element in tree.getroot().iter():
        # html="true"-viestit ovat HTML:ää: tunnisteet escapataan, jotta ne näkyvät lokissa
        html = element.tag == "msg" and element.get("html", "").lower() in ("true", "yes")
        element.text = pseudonymizer.process(element.text, html=html)
        element.tail = pseudonymizer.process(element.tail)
        for name, value in list(element.attrib.items()):
            if name not in SKIP_ATTRIBUTES:
                element.set(name, pseudonymizer.process(value))
    return tree


def pseudonymize_file(source, target, pseudonymizer):
    tree = ET.parse(source)
    pseudonymize_tree(tree, pseudonymizer)
    tree.write(target, encoding="UTF-8", xml_declaration=True)
