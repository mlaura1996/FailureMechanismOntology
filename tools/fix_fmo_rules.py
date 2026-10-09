"""Corrects the Failure Mechanism Ontology so that a reasoner can execute it
together with the Historic Masonry Ontology, and records every change.

    python tools/fix_fmo_rules.py <in.ttl> <out.ttl> [--only G1,G2,G3] [--examples <examples.ttl>]

  G1  The ontology file carried two example individuals of the Castelnuovo
      case study (WallFacadeA417_a and its quality index), with two
      different in-plane totals and literals of a type the HMO range does
      not admit. Loaded with HMO, they make the knowledge base inconsistent.
      They are moved out of the ontology (to --examples if given).
  G2  Numeric literals in the rule built-ins typed xsd:float, as the HMO
      totals they are compared with: some thresholds ("0", "2.5") were
      untyped strings, so the rules using them never fired (a vertical
      quality index of 1.4 received no vertical behaviour).
  G3  Behaviour thresholds made contiguous and non-overlapping, as
      inadequate below the first limit, average from the first to the
      second limit included, good above it. The vertical classes overlapped
      at 2.5 (both inadequate and average), and in the in-plane and
      out-of-plane directions the first limit fell in the inadequate class.
      To be checked against the MQI limits of Borri et al.
  G4  Properties declared with two rdfs:domain axioms (beo:Wall and
      hmo:MasonryWall), which OWL reads as an intersection: every HMO wall
      would be inferred a beo:Wall too, and the reverse. The evident intent,
      a wall of either kind, is now one domain, their union.
"""
import sys

import rdflib
from rdflib import RDF, RDFS, OWL, XSD, Literal, URIRef
from rdflib.collection import Collection

S = "http://www.w3.org/2003/11/swrl#"
SB = "http://www.w3.org/2003/11/swrlb#"
FMO = "https://w3id.org/fmo#"
sw = lambda x: URIRef(S + x)
f = lambda x: URIRef(FMO + x)

src, dst = sys.argv[1], sys.argv[2]
only = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
examples_out = sys.argv[sys.argv.index("--examples") + 1] if "--examples" in sys.argv else None
on = lambda x: only is None or x in only

g = rdflib.Graph()
g.parse(src, format="turtle")
log = []


def rule(label):
    hits = [r for r in g.subjects(RDF.type, sw("Imp")) if str(g.value(r, RDFS.label)) == label]
    assert len(hits) == 1, (label, len(hits))
    return hits[0]


def builtins(r):
    return [a for a in Collection(g, g.value(r, sw("body"))) if (a, RDF.type, sw("BuiltinAtom")) in g]


def args_of(a):
    return list(Collection(g, g.value(a, sw("arguments"))))


def set_args(a, values):
    """Replaces the argument list of a built-in atom, removing the old list."""
    node = g.value(a, sw("arguments"))
    while node is not None and node != RDF.nil:
        nxt = g.value(node, RDF.rest)
        g.remove((node, None, None))
        node = nxt
    lst = rdflib.BNode()
    Collection(g, lst, values)
    g.set((a, sw("arguments"), lst))


# --- G1 ------------------------------------------------------------------------
if on("G1"):
    ex = rdflib.Graph()
    for name in ("WallFacadeA417_a", "MQIWallFacadeA417_a"):
        for t in list(g.triples((f(name), None, None))) + list(g.triples((None, None, f(name)))):
            ex.add(t)
            g.remove(t)
    if examples_out:
        ex.bind("fmo", FMO)
        ex.serialize(examples_out, format="turtle", encoding="utf-8")
    log.append(f"G1 moved {len(ex)} triples of the Castelnuovo example individuals out of the ontology"
               + (f" (to {examples_out})" if examples_out else ""))

# --- G2 ------------------------------------------------------------------------
if on("G2"):
    n = 0
    for a in list(g.subjects(RDF.type, sw("BuiltinAtom"))):
        values = args_of(a)
        if any(isinstance(x, Literal) and x.datatype != XSD.float for x in values):
            set_args(a, [Literal(float(x), datatype=XSD.float) if isinstance(x, Literal) else x for x in values])
            n += 1
    log.append(f"G2 numeric literals typed xsd:float in {n} built-in atoms")

# --- G3 ------------------------------------------------------------------------
# (rule label, built-in to replace, by) - first limit closes the average class
CHANGES = [
    ("Inadequate in plane behavior", "lessThanOrEqual", "lessThan"),
    ("Average in plane behaviour", "greaterThan", "greaterThanOrEqual"),
    ("Inadequate out of plane behaviour", "lessThanOrEqual", "lessThan"),
    ("Average out of plane behaviour", "greaterThan", "greaterThanOrEqual"),
    ("Inadequate vertical behaviour", "lessThanOrEqual", "lessThan"),
]
if on("G3"):
    for label, old, new in CHANGES:
        r = rule(label)
        hits = [a for a in builtins(r) if g.value(a, sw("builtin")) == URIRef(SB + old)]
        assert len(hits) == 1, (label, old, len(hits))
        g.set((hits[0], sw("builtin"), URIRef(SB + new)))
    log.append("G3 behaviour classes made contiguous: inadequate < first limit <= average <= second limit < good")

# --- G4 ------------------------------------------------------------------------
if on("G4"):
    fixed = []
    for p in sorted(set(g.subjects(RDFS.domain, None)), key=str):
        domains = [d for d in g.objects(p, RDFS.domain) if isinstance(d, URIRef)]
        if len(domains) < 2:
            continue
        for d in domains:
            g.remove((p, RDFS.domain, d))
        union, members = rdflib.BNode(), rdflib.BNode()
        Collection(g, members, sorted(domains, key=str))
        g.add((union, RDF.type, OWL.Class))
        g.add((union, OWL.unionOf, members))
        g.add((p, RDFS.domain, union))
        fixed.append(str(p).split("#")[-1])
    log.append(f"G4 multiple domains replaced by their union on {len(fixed)} properties: {', '.join(fixed)}")

g.serialize(dst, format="turtle", encoding="utf-8")
print("\n".join(log))
print(f"-> {dst}")
