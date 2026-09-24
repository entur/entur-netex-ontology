#!/usr/bin/env python3
"""Validate and report effective profile membership across profile inheritance.

The Entur profile declares only its additions. Nordic membership is inherited
through nordic:extendsProfile, so new Nordic allowlist members become visible
without copying them into the Entur ontology.

Exit codes:
  0  inheritance is valid and Entur has no redundant additions
  1  a redundant addition or an invalid profile relation was found
  2  the composed profile graph could not be built
"""
import glob
import sys

from rdflib import Graph, URIRef

NORDIC = "https://netex-cen.eu/nordic#"
PROFILE = "https://netex-cen.eu/profile#"
ENTUR = "https://entur.org/ontology#"
EXTENDS = URIRef(f"{NORDIC}extendsProfile")
IN_PROFILE = URIRef(f"{NORDIC}inProfile")
PROFILE_CLASS = URIRef(f"{NORDIC}Profile")
NP = URIRef(f"{PROFILE}NP")
ENTUR_PROFILE = URIRef(f"{PROFILE}EnturProfile")
# The current Nordic baseline uses profile:NordicProfile for membership while
# profile:NP is the profile instance used by downstream inheritance.
NORDIC_SCOPE = URIRef(f"{PROFILE}NordicProfile")


def load_graph() -> Graph:
    graph = Graph()
    nordic_paths = sorted(glob.glob("nordic-netex-ontology/*.ttl"))
    base_paths = sorted(glob.glob("nordic-netex-ontology/base/*.ttl"))
    entur_paths = sorted(glob.glob("netex-entur*.ttl"))
    if not base_paths or not entur_paths:
        raise FileNotFoundError("fant ikke nødvendige Nordic-base- eller Entur-filer")
    paths = nordic_paths + base_paths + entur_paths
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def inherited_profiles(graph: Graph, profile: URIRef) -> list[URIRef]:
    result: list[URIRef] = []
    pending = [profile]
    seen: set[URIRef] = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        result.append(current)
        pending.extend(
            parent
            for parent in graph.objects(current, EXTENDS)
            if isinstance(parent, URIRef)
        )
    return result


def members(graph: Graph, profiles: set[URIRef]) -> set[URIRef]:
    return {
        subject
        for profile in profiles
        for subject in graph.subjects(IN_PROFILE, profile)
        if isinstance(subject, URIRef)
    }


def main() -> int:
    try:
        graph = load_graph()
    except Exception as exc:
        print(f"ERROR: kunne ikke bygge profilgraf: {exc}", file=sys.stderr)
        return 2

    if (ENTUR_PROFILE, EXTENDS, NP) not in graph:
        print("ERROR: EnturProfile arver ikke profile:NP", file=sys.stderr)
        return 1
    if (ENTUR_PROFILE, RDF_TYPE, PROFILE_CLASS) not in graph:
        print("ERROR: EnturProfile er ikke deklarert som nordic:Profile", file=sys.stderr)
        return 1

    profile_chain = inherited_profiles(graph, ENTUR_PROFILE)
    parent_profiles = set(profile_chain[1:])
    inherited = members(graph, parent_profiles | {NORDIC_SCOPE})
    additions = members(graph, {ENTUR_PROFILE})
    redundant = sorted(inherited & additions, key=str)
    effective = inherited | additions

    print(f"profile_chain={','.join(map(str, profile_chain))}")
    print(f"inherited_members={len(inherited)}")
    print(f"entur_additions={len(additions)}")
    print(f"effective_members={len(effective)}")
    if redundant:
        print("redundant_entur_members:")
        for member in redundant:
            print(str(member))
        return 1
    print("OK: Entur-allowlisten arver Nordic og har ingen redundante tillegg.")
    return 0


RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")


if __name__ == "__main__":
    sys.exit(main())
