#!/usr/bin/env python3
"""Validate effective profile membership across profile inheritance.

Each profile mints its own profile:ProfileClass nodes (nordic:X, entur:X)
that point at the standard class via profile:onClass and carry profile:scope.
Fields are profile:ProfileMember entries linked with profile:memberOf. Entur
inherits Nordic through nordic:extendsProfile. Membership is compared on the
netex: classes the nodes point at.

Exit codes:
  0  inheritance is valid and Entur has no redundant additions
  1  a redundant addition or an invalid profile relation was found
  2  the composed profile graph could not be built
"""
import argparse
import glob
import sys

from rdflib import Graph, URIRef

NETEX = "https://netex-cen.eu/ontology#"
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
PROFILE_CLASS_NODE = URIRef(f"{PROFILE}ProfileClass")
ON_CLASS = URIRef(f"{PROFILE}onClass")
PROFILE_MEMBER = URIRef(f"{PROFILE}ProfileMember")
MEMBER_OF = URIRef(f"{PROFILE}memberOf")
MEMBER_PATH = URIRef(f"{PROFILE}path")
MEMBER_CARDINALITY = URIRef(f"{PROFILE}cardinality")
LEGACY_ENTUR_PROFILE_MEMBER = URIRef(f"{ENTUR}ProfileMember")
LEGACY_NORDIC_SCOPE = URIRef(f"{PROFILE}NordicProfile")


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


def scoped_nodes(graph: Graph, scope: URIRef) -> dict[URIRef, set[URIRef]]:
    """Map each node with this scope to the netex: classes it profiles.

    Older Nordic pins put profile:scope directly on the netex: class; such a
    subject profiles itself, so old and new pins can be compared.
    """
    result: dict[URIRef, set[URIRef]] = {}
    for node in graph.subjects(SCOPE, scope):
        if not isinstance(node, URIRef):
            continue
        targets = {t for t in graph.objects(node, ON_CLASS) if isinstance(t, URIRef)}
        if not targets and str(node).startswith(NETEX):
            targets = {node}
        result[node] = targets
    return result


def scoped_members(graph: Graph, scope: URIRef) -> set[URIRef]:
    return {
        target
        for targets in scoped_nodes(graph, scope).values()
        for target in targets
    }


def fields(graph: Graph, nodes: set[URIRef]) -> dict[URIRef, set[tuple[str, str]]]:
    """(path, cardinality) of the members of each node."""
    result: dict[URIRef, set[tuple[str, str]]] = {node: set() for node in nodes}
    for member in graph.subjects(RDF_TYPE, PROFILE_MEMBER):
        for node in graph.objects(member, MEMBER_OF):
            if node in result:
                result[node].add(
                    (
                        str(graph.value(member, MEMBER_PATH) or ""),
                        str(graph.value(member, MEMBER_CARDINALITY) or ""),
                    )
                )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate effective profile membership.")
    parser.add_argument(
        "--list-nordic-members",
        action="store_true",
        help="Print the inherited Nordic member IRIs, one per line.",
    )
    args = parser.parse_args()

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
    inherited = (
        members(graph, parent_profiles | {LEGACY_NORDIC_SCOPE})
        | scoped_members(graph, NP)
    )

    if args.list_nordic_members:
        for member in sorted(inherited, key=str):
            print(str(member))
        return 0

    if any(graph.subjects(RDF_TYPE, LEGACY_ENTUR_PROFILE_MEMBER)):
        print(
            "ERROR: entur:ProfileMember er erstattet av profile:ProfileMember + profile:memberOf",
            file=sys.stderr,
        )
        return 1

    entur_nodes = scoped_nodes(graph, ENTUR_PROFILE)
    on_netex = sorted(node for node in entur_nodes if str(node).startswith(NETEX))
    if on_netex:
        print(
            "ERROR: profile:scope profile:Entur står direkte på netex:-klasser; "
            "bruk en entur:X profile:ProfileClass-node:",
            file=sys.stderr,
        )
        for node in on_netex:
            print(str(node), file=sys.stderr)
        return 1

    malformed = sorted(
        node
        for node in entur_nodes
        if len(list(graph.objects(node, ON_CLASS))) != 1
        or len(entur_nodes[node]) != 1
        or (node, RDF_TYPE, PROFILE_CLASS_NODE) not in graph
    )
    if malformed:
        print(
            "ERROR: Entur-noder må være profile:ProfileClass med nøyaktig én profile:onClass:",
            file=sys.stderr,
        )
        for node in malformed:
            print(str(node), file=sys.stderr)
        return 1

    # Without Entur scope an entur:X node silently drops out of effective membership.
    unscoped = sorted(
        node
        for node in graph.subjects(RDF_TYPE, PROFILE_CLASS_NODE)
        if str(node).startswith(ENTUR) and node not in entur_nodes
    )
    if unscoped:
        print("ERROR: Entur-eide ProfileClass-noder mangler profile:scope profile:Entur:", file=sys.stderr)
        for node in unscoped:
            print(str(node), file=sys.stderr)
        return 1

    additions = scoped_members(graph, ENTUR_PROFILE)

    undeclared_classes = sorted(
        additions - set(graph.subjects(RDF_TYPE, OWL_CLASS)), key=str
    )
    if undeclared_classes:
        print("ERROR: Entur-scope refererer til klasser som ikke finnes i base/:", file=sys.stderr)
        for class_iri in undeclared_classes:
            print(str(class_iri), file=sys.stderr)
        return 1

    profile_nodes = set(graph.subjects(RDF_TYPE, PROFILE_CLASS_NODE))
    orphans = sorted(
        str(node)
        for member in graph.subjects(RDF_TYPE, PROFILE_MEMBER)
        for node in graph.objects(member, MEMBER_OF)
        if node not in profile_nodes
    )
    if orphans:
        print("ERROR: ProfileMember peker på noe som ikke er en profile:ProfileClass:", file=sys.stderr)
        for node in sorted(set(orphans)):
            print(node, file=sys.stderr)
        return 1

    nordic_nodes = scoped_nodes(graph, NP)
    nordic_fields: dict[URIRef, set[tuple[str, str]]] = {}
    for node, node_fields in fields(graph, set(nordic_nodes)).items():
        for target in nordic_nodes[node]:
            nordic_fields.setdefault(target, set()).update(node_fields)

    # An Entur node on an inherited class is only meaningful if it adds fields.
    redundant: list[str] = []
    for node, node_fields in fields(graph, set(entur_nodes)).items():
        (target,) = entur_nodes[node]
        if target not in inherited:
            continue
        if not node_fields:
            redundant.append(str(target))
        for path, cardinality in sorted(node_fields & nordic_fields.get(target, set())):
            redundant.append(f"{target} {path} {cardinality}")
    redundant.sort()
    effective = inherited | additions

    print(f"profile_chain={','.join(map(str, profile_chain))}")
    print(f"inherited_members={len(inherited)}")
    print(f"entur_additions={len(additions - inherited)}")
    print(f"entur_refinements={len(additions & inherited)}")
    print(f"effective_members={len(effective)}")
    if redundant:
        print("redundant_entur_members:")
        for member in redundant:
            print(member)
        return 1
    print("OK: Entur-allowlisten arver Nordic og har ingen redundante tillegg.")
    return 0


RDF_TYPE = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
OWL_CLASS = URIRef("http://www.w3.org/2002/07/owl#Class")


if __name__ == "__main__":
    sys.exit(main())
