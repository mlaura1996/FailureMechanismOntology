# Changelog

## Unreleased — rules made executable together with HMO

Run with Pellet together with the Historic Masonry Ontology on the
Castelnuovo di Porto case study (seven masonry walls), the ontology as
published made the knowledge base inconsistent, and once that was removed
some behaviour rules never fired. The corrections below are applied by
`tools/fix_fmo_rules.py`, each switchable with `--only`.

All four serialisations (`ontology.ttl`, `.nt`, `.owl`, `.jsonld`) are
regenerated from the corrected graph.

### Corrections

- **G1, example individuals moved out of the ontology.** The file carried
  two individuals of the case study (`WallFacadeA417_a` and its quality
  index), with two different in-plane totals and literals of a type the HMO
  range does not admit. Loaded with HMO they make the knowledge base
  inconsistent. They are now in `examples/castelnuovo_wall_417a.ttl`.
- **G2, threshold literals typed `xsd:float`**, as the HMO totals they are
  compared with. Some thresholds (`"0"`, `"2.5"`) were untyped strings, so
  the rules using them never fired.
- **G3, behaviour classes made contiguous.** Inadequate below the first
  limit, average from the first to the second limit included, good above.
  The vertical classes overlapped at 2.5, and in the in-plane and
  out-of-plane directions the first limit fell in the inadequate class.
  To be reviewed against the MQI limits of Borri et al.
- **G4, one domain per property.** `hasBehaviour`, `hasOccurringMechanism`,
  `hasVulnerability`, `dot:hasDamage` and `hmo:hasMasonryQualityIndex` had
  two `rdfs:domain` axioms (`beo:Wall`, `hmo:MasonryWall`), which OWL reads
  as an intersection. They now have one domain, the union of the two.

### Evidence

Removing one correction at a time:

| removed | result |
|---|---|
| G1 | knowledge base inconsistent |
| G2 | wall 417a (vertical index 1.4) receives no vertical behaviour |
| G3 | a wall with vertical index 2.5 is both inadequate and average; in-plane 3.0 and out-of-plane 4.0 are inadequate |

With all corrections every wall receives exactly one behaviour in each
direction.

### Known limitation (not changed)

SWRL cannot express the absence of a fact, so the partial overturning rules
fire whenever the top restraint is missing, including when the intermediate
one is missing too: a wall with both vulnerabilities is assigned total and
partial overturning. Total overturning is therefore to be read as including
the partial one.
