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

The shared Nordic foundation (`netex.ttl` and `netex-nordic.ttl`) lives in
the [`nordic-netex-ontology/`](https://github.com/entur/nordic-netex-ontology)
submodule and is not modified here.

**Design principle:** Each layer may tighten constraints via SHACL, but never
loosen constraints from the layer below.

## File Structure

```
entur-netex-ontology/
├── netex-entur.ttl              ← Entur governance (codespaces, data ownership)
├── netex-entur-nsr.ttl          ← NSR stop place register sub-profile
├── netex-entur-pen.ttl          ← PEN rolling stock register (NeTEx alignment, no I/O yet)
├── netex-entur-rolling-stock.ttl ← Rolling stock service (reads NeTEx, TrainElement cutoff)
├── netex-entur-kvoter.ttl       ← Quota service (independent of materiel)
├── netex-entur-produkt.ttl      ← Product service (skeleton)
├── netex-entur-inntektsmodell.ttl ← Income model service (skeleton)
└── nordic-netex-ontology/       ← git submodule
    ├── netex.ttl                ← NeTEx base schema (classes, references)
    └── netex-nordic.ttl         ← Nordic Profile (SHACL constraints)
```

### Import Chain

```
netex.ttl                              ← Base vocabulary
└─ netex-nordic.ttl                    ← Nordic constraints
   └─ netex-entur.ttl                  ← Entur governance
      ├─ netex-entur-nsr.ttl           ← NSR stop place register
      ├─ netex-entur-pen.ttl           ← PEN rolling stock register (NeTEx alignment, no I/O yet)
      ├─ netex-entur-rolling-stock.ttl ← Rolling stock (reads NeTEx, TrainElement cutoff)
      ├─ netex-entur-kvoter.ttl        ← Quota service (peer, no materiel)
      ├─ netex-entur-produkt.ttl       ← Product service (skeleton)
      └─ netex-entur-inntektsmodell.ttl ← Income model service (skeleton)
```

Service sub-profiles are **peers**: they import `netex-entur.ttl` but never
each other. A delivery is validated against `NP + governance + the sub-profiles
relevant to its purpose` — so a quota delivery is never subjected to the
stricter rolling stock shapes.

### What Each File Does

| File | Layer | Contents |
|------|-------|----------|
| `netex.ttl` | Base schema | OWL classes, frame classes, reference metadata, XSD cardinality, SIRI bridges, Transmodel alignment |
| `netex-nordic.ttl` | Nordic Profile | SHACL shapes for what the profile allows, requires, and excludes |
| `netex-entur.ttl` | Entur governance | Codespace conventions (NSR, NOG, PEN), data ownership per class, Partner portal modules |
| `netex-entur-nsr.ttl` | NSR register | Authoritative stop place profile — what Tiamat exports, hierarchy rules, keyList conventions |
| `netex-entur-pen.ttl` | PEN alignment | Register of rolling stock units aligned with NeTEx (TrainElement), each linked to a seat map. Low weight — units and seat maps are free-standing from NeTEx today; tighten here if that changes |
| `netex-entur-rolling-stock.ttl` | Rolling stock | Reads operator NeTEx, validates, and uses the TrainElement register cutoff (PEN codespace) to build compositions; service-specific SHACL constraints |
| `netex-entur-kvoter.ttl` | Quota | Capacity/availability across a departure and its ordered stops, independent of materiel — peer of rolling stock |
| `netex-entur-produkt.ttl` | Product | Skeleton — product catalogue (fare products, sales offers); scope to be confirmed |
| `netex-entur-inntektsmodell.ttl` | Income model | Skeleton — income/revenue model (initial scope: Østlandet); tariff/fare touchpoints to be confirmed |

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
| `netex-entur-rolling-stock.ttl` | `svc:RS_{ClassName}Shape` | `svc:RS_DatedServiceJourneyShape` |
| `netex-entur-kvoter.ttl` | `kvote:Q_{ClassName}Shape` | `kvote:Q_DatedServiceJourneyShape` |

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

svc:YourService a netex:SubProfile ;
    rdfs:label "Your Service" ;
    netex:basedOn profile:NP .
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
| `profile:` | `https://netex-cen.eu/profile#` |
| `entur:` | `https://entur.org/ontology#` |
| `nsr:` | `https://entur.org/service/nsr#` |
| `pen:` | `https://entur.org/service/pen#` |
| `svc:` | `https://entur.org/service/rolling-stock#` |
| `kvote:` | `https://entur.org/service/kvoter#` |
| `produkt:` | `https://entur.org/service/produkt#` |
| `inntekt:` | `https://entur.org/service/inntektsmodell#` |
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
