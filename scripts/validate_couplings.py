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
BASE_FILES = [f"{SUBMODULE}/netex.ttl", f"{SUBMODULE}/netex-nordic.ttl"]


def is_watched(term) -> bool:
    return isinstance(term, URIRef) and str(term).startswith(WATCHED)


def main() -> int:
    entur_files = sorted(glob.glob("netex-entur*.ttl"))

    composed = Graph()
    for path in BASE_FILES + entur_files:
        composed.parse(path, format="turtle")
    defined = {s for s in composed.subjects() if isinstance(s, URIRef)}

    referenced = set()
    for path in entur_files:
        layer = Graph()
        layer.parse(path, format="turtle")
        for triple in layer:
            for term in triple:
                if is_watched(term):
                    referenced.add(term)

    dangling = sorted(str(t) for t in referenced - defined)
    for iri in dangling:
        print(iri)
    return 1 if dangling else 0


if __name__ == "__main__":
    sys.exit(main())
