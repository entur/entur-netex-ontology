#!/usr/bin/env python3
"""Validate effective profile membership across profile inheritance.

The Nordic baseline and Entur additions both use profile:scope, with each
profile resource serving as its own scope value. Entur inherits Nordic through
nordic:extendsProfile.

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
ENTUR_PROFILE = URIRef(f"{PROFILE}Entur")
SCOPE = URIRef(f"{PROFILE}scope")
PROFILE_SCOPE_CLASS = URIRef(f"{PROFILE}Scope")
ENTUR_PROFILE_MEMBER = URIRef(f"{ENTUR}ProfileMember")
ENTUR_ON_CLASS = URIRef(f"{ENTUR}onClass")


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


def scoped_members(graph: Graph, scope: URIRef) -> set[URIRef]:
    return {
        subject
        for subject in graph.subjects(SCOPE, scope)
        if isinstance(subject, URIRef)
    }


def main() -> int:
    try:
        graph = load_graph()
    except Exception as exc:
        print(f"ERROR: kunne ikke bygge profilgraf: {exc}", file=sys.stderr)
        return 2

    if (ENTUR_PROFILE, EXTENDS, NP) not in graph:
        print("ERROR: profile:Entur arver ikke profile:NP", file=sys.stderr)
        return 1
    if (ENTUR_PROFILE, RDF_TYPE, PROFILE_CLASS) not in graph:
        print("ERROR: EnturProfile er ikke deklarert som nordic:Profile", file=sys.stderr)
        return 1
    if (ENTUR_PROFILE, RDF_TYPE, PROFILE_SCOPE_CLASS) not in graph:
        print("ERROR: profile:Entur er ikke deklarert som profile:Scope", file=sys.stderr)
        return 1

    legacy_additions = members(
        graph, {ENTUR_PROFILE, URIRef(f"{PROFILE}EnturProfile")}
    )
    if legacy_additions:
        print(
            "ERROR: Entur-klasser bruker fortsatt nordic:inProfile; bruk profile:scope",
            file=sys.stderr,
        )
        return 1

    profile_chain = inherited_profiles(graph, ENTUR_PROFILE)
    parent_profiles = set(profile_chain[1:])
    inherited = members(graph, parent_profiles) | scoped_members(graph, NP)
    additions = scoped_members(graph, ENTUR_PROFILE)

    undeclared_classes = sorted(
        additions - set(graph.subjects(RDF_TYPE, OWL_CLASS)), key=str
    )
    if undeclared_classes:
        print("ERROR: Entur-scope refererer til klasser som ikke finnes i base/:", file=sys.stderr)
        for class_iri in undeclared_classes:
            print(str(class_iri), file=sys.stderr)
        return 1

    field_classes = {
        class_iri
        for member in graph.subjects(RDF_TYPE, ENTUR_PROFILE_MEMBER)
        for class_iri in graph.objects(member, ENTUR_ON_CLASS)
        if isinstance(class_iri, URIRef)
    }
    unscoped_field_classes = sorted(field_classes - additions, key=str)
    if unscoped_field_classes:
        print("ERROR: Entur ProfileMember tilhører ikke en Entur-scope-klasse:", file=sys.stderr)
        for class_iri in unscoped_field_classes:
            print(str(class_iri), file=sys.stderr)
        return 1

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
OWL_CLASS = URIRef("http://www.w3.org/2002/07/owl#Class")


if __name__ == "__main__":
    sys.exit(main())
