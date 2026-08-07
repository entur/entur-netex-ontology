# Entur NeTEx Ontology

Entur-specific ontology layers that extend the shared
[Nordic NeTEx Ontology](https://github.com/entur/nordic-netex-ontology).
Models data governance, codespace conventions, service sub-profiles,
and NSR master data ownership as RDF/OWL and SHACL in Turtle format.

## Purpose

The ontology serves two purposes:

- **For humans:** A precise reference for Entur's operational choices — who
  owns which data, which codespaces apply, and what different services
  consume and produce.
- **For machines:** A foundation for service-specific SHACL validation,
  documentation generation, and tooling integration.

## Scope

This repository contains Entur's organisation-specific layers — things that
are **not** part of the shared Nordic agreement, but are necessary for
operators delivering data to Entur.

The shared Nordic foundation lives in the
[`nordic-netex-ontology/`](https://github.com/entur/nordic-netex-ontology)
submodule (the Nordic Profile overlay) and is not modified here. That overlay
in turn builds on the **generated** NeTEx base ontology (`netex:`), which is
projected from the official NeTEx XSD and owned externally (CEN).

**Design principle:** Each layer may tighten constraints via SHACL, but never
loosen constraints from the layer below.

## File Structure

```
entur-netex-ontology/
├── netex-entur.ttl              ← Entur governance (codespaces, data ownership)
├── netex-entur-nsr.ttl          ← NSR service sub-profile (stop places)
├── netex-rolling-stock.ttl      ← Rolling stock service sub-profile
└── nordic-netex-ontology/       ← git submodule (Nordic Profile overlay)
    ├── netex-nordic.ttl         ← Nordic Profile (SHACL constraints, ordering)
    ├── netex-nordic-vocab.ttl   ← Nordic vocabulary (nordic:)
    ├── netex-nordic-model.ttl   ← curated frame containment & specialisation
    ├── netex-transmodel-alignment.ttl ← NeTEx ⇄ Transmodel (skos)
    └── netex-siri-bridge.ttl    ← NeTEx ⇄ SIRI real-time bridges
```

The NeTEx base vocabulary (`netex:`) is **generated** from the NeTEx XSD and
provided externally (CEN-owned) — it is not stored in this repository.

### Import Chain

```
netex: base (generated, external)      ← CEN-owned NeTEx vocabulary
└─ netex-nordic.ttl                    ← Nordic Profile (imports base + nordic vocab)
   └─ netex-entur.ttl                  ← Entur governance
      ├─ netex-entur-nsr.ttl           ← NSR sub-profile
      └─ netex-rolling-stock.ttl       ← Rolling stock sub-profile
```

### What Each File Does

| File | Layer | Contents |
|------|-------|----------|
| `netex:` base (external) | Generated base | OWL classes, properties, XSD cardinality — projected from the NeTEx XSD, CEN-owned |
| `netex-nordic.ttl` | Nordic Profile | SHACL shapes for what the profile allows, requires, and excludes; element ordering |
| `netex-nordic-vocab.ttl` | Nordic vocabulary | `nordic:` terms not derived from the XSD (profile meta-classes, data confidence, ordering, domain chains) |
| `netex-nordic-model.ttl` | Nordic model | Curated frame containment and functional specialisation semantics |
| `netex-transmodel-alignment.ttl` | Alignment | `skos` mapping from generated NeTEx classes to Transmodel concepts |
| `netex-siri-bridge.ttl` | SIRI bridge | Which NeTEx classes are referenced by SIRI real-time services |
| `netex-entur.ttl` | Entur governance | Codespace conventions (NSR, NOG, PEN), data ownership per class, Partner portal modules |
| `netex-entur-nsr.ttl` | NSR sub-profile | Authoritative stop place profile — what Tiamat exports, hierarchy rules, keyList conventions |
| `netex-rolling-stock.ttl` | Rolling stock | Which references/elements the rolling stock service consumes/produces, service-specific SHACL constraints |

## SHACL Validation

SHACL shapes in the service sub-profiles express system-specific constraints
that validation tools can execute directly:

| Constraint | SHACL | Example |
|------------|-------|---------|
| Excluded | `sh:maxCount 0` | Fields the service does not use |
| Allowed | `sh:maxCount 1` | Optional field |
| Required | `sh:minCount 1; sh:maxCount 1` | Field the service requires (even if NP says optional) |
| Type check | `sh:class` | Reference must point to the correct class |

### Shape Naming Convention

| File | Pattern | Example |
|------|---------|---------|
| `netex-entur-nsr.ttl` | `nsr:NSR_{ClassName}Shape` | `nsr:NSR_StopPlaceShape` |
| `netex-rolling-stock.ttl` | `svc:RS_{ClassName}Shape` | `svc:RS_DatedServiceJourneyShape` |

### Layered Validation

Because the files form an import chain, constraints are additive:

1. **XSD** validates basic XML structure
2. **NP shapes** validate Nordic Profile rules (tighter than XSD)
3. **Service shapes** validate system-specific requirements (tighter than NP)

## Extension Model

To add a new service sub-profile, create a new `.ttl` file that imports
`netex-entur.ttl`:

```turtle
@prefix svc: <https://entur.org/service/your-service#> .

<https://entur.org/service/your-service> a owl:Ontology ;
    owl:imports <https://entur.org/ontology> .

svc:YourService a entur:SubProfile ;
    rdfs:label "Your Service" ;
    entur:basedOn profile:NP .
```

## Technology

| Standard | Used for |
|----------|----------|
| RDF/OWL | Classes and properties |
| SHACL | Profile constraints as validatable shapes |
| SKOS | Definitions, notation, and cross-vocabulary mapping |
| Turtle (.ttl) | Serialisation format |

## Prefixes

| Prefix | Namespace |
|--------|-----------|
| `netex:` | `https://netex-cen.eu/ontology#` |
| `nordic:` | `https://netex-cen.eu/nordic#` |
| `profile:` | `https://netex-cen.eu/profile#` |
| `entur:` | `https://entur.org/ontology#` |
| `nsr:` | `https://entur.org/service/nsr#` |
| `svc:` | `https://entur.org/service/rolling-stock#` |
| `sh:` | `http://www.w3.org/ns/shacl#` |

## Tools

The ontology can be consumed by any standard RDF/SHACL tooling, e.g.:

- **pySHACL** — Validate NeTEx data against service shapes
- **Apache Jena** — SPARQL queries
- **TopBraid / Protégé** — Visual exploration and editing
- **Custom scripts/agents** — Import the `.ttl` files via `owl:imports` or load directly

## Further Reading

- [Nordic NeTEx Ontology](https://github.com/entur/nordic-netex-ontology) — The shared Nordic foundation
- [Ontology Guide](https://github.com/entur/nordic-netex-documentation/blob/main/guides/Ontology/Ontology_Guide.md) — Full guide to the ontology's structure
- [W3C RDF Primer](https://www.w3.org/TR/rdf11-primer/) — Introduction to RDF and Turtle syntax
- [W3C SHACL Specification](https://www.w3.org/TR/shacl/) — Shapes Constraint Language
- [Transmodel](https://www.transmodel-cen.eu/) — The conceptual model behind NeTEx
