#!/usr/bin/env python3
"""Referanse-integritet for Entur-lagene mot det nordiske fundamentet.

Hver netex:/nordic:/profile:-IRI som Entur-lagene REFERERER må være DEFINERT
(opptre som subjekt) i den komponerte grafen: nordisk base + nordisk profil +
Entur-lag. Udefinerte (dangling) referanser skrives til stdout, én per linje,
sortert. Exit 1 hvis noen finnes, ellers 0.

Brukes DIFFERENSIELT i ontology-ingest: kjør mot gammel og ny submodul-pin og
sammenlign. En referanse som er ny i den nye pinnen (definert før, borte etter)
betyr at oppstrøms-bumpen BRØT en kobling. En strammere constraint bryter INGEN
referanse, så den gir ingen ny dangling — top-down-styring slipper gjennom.

Exit-koder (kontrakt mot workflowen):
  0  kjørte, ingen dangling referanser
  1  kjørte, fant dangling referanser (skrevet til stdout, sortert)
  2  kunne IKKE kjøre — en base-/lag-fil mangler eller parser ikke.
Et tomt stdout ved exit 0 betyr «rent»; exit 2 betyr «vet ikke». Fravær av bevis
er ikke bevis på fravær — derfor må 2 aldri tolkes som trygt av kalleren.
"""
import glob
import sys

from rdflib import Graph, URIRef

WATCHED = (
    "https://netex-cen.eu/ontology#",
    "https://netex-cen.eu/nordic#",
    "https://netex-cen.eu/profile#",
)
SUBMODULE = "nordic-netex-ontology"
# Det nordiske fundamentet = generert NeTEx-base (base/*.ttl; netex.ttl er kun en
# owl:imports-header, definisjonene ligger i modulene) + de nordiske overlaysene
# (netex-nordic*.ttl m.fl. i submodul-roten som definerer nordic:/profile:).
BASE_GLOBS = [f"{SUBMODULE}/base/*.ttl", f"{SUBMODULE}/*.ttl"]


def is_watched(term) -> bool:
    return isinstance(term, URIRef) and str(term).startswith(WATCHED)


def base_files() -> list[str]:
    seen: dict[str, None] = {}
    for pattern in BASE_GLOBS:
        for path in glob.glob(pattern):
            seen[path] = None
    return sorted(seen)


def main() -> int:
    entur_files = sorted(glob.glob("netex-entur*.ttl"))
    if not entur_files:
        print("ERROR: fant ingen netex-entur*.ttl å sjekke", file=sys.stderr)
        return 2

    base = base_files()
    if not base:
        print(f"ERROR: fant ingen base-filer under {SUBMODULE}/", file=sys.stderr)
        return 2

    composed = Graph()
    try:
        for path in base + entur_files:
            composed.parse(path, format="turtle")
    except Exception as exc:
        # En manglende/ugyldig base gir INGEN definisjoner, ikke et «rent» sett.
        print(f"ERROR: kunne ikke bygge komponert graf: {exc}", file=sys.stderr)
        return 2
    defined = {s for s in composed.subjects() if isinstance(s, URIRef)}

    referenced = set()
    try:
        for path in entur_files:
            layer = Graph()
            layer.parse(path, format="turtle")
            for triple in layer:
                for term in triple:
                    if is_watched(term):
                        referenced.add(term)
    except Exception as exc:
        print(f"ERROR: kunne ikke lese Entur-lag: {exc}", file=sys.stderr)
        return 2

    dangling = sorted(str(t) for t in referenced - defined)
    for iri in dangling:
        print(iri)
    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())
