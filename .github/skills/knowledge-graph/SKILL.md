---
name: knowledge-graph
description: Use PrimeKG (Harvard precision-medicine knowledge graph, 100k+ nodes / 4M+ edges / 29 edge types) as a multi-hop reasoning substrate — drug→target→pathway→disease — instead of flat literature search. Use when a question is relational ("what connects X to Y", "off-label / contraindicated drugs for disease D", "shared targets of drugs A and B") rather than a single lookup.
---

# Knowledge graph (PrimeKG) — multi-hop reasoning

## When to use
The question is **relational / multi-hop**, e.g. "what pathway links gene X to
disease D?", "which drugs are contraindicated for D?", "what do drugs A and B
share?". A flat PubMed/PubTator pass gives mentions; PrimeKG gives typed edges you
can traverse. For single normalized facts, `pubtator_entity` is lighter; for
target–disease *evidence scores*, use `opentargets_associations`. Use PrimeKG when
you need the **graph structure** itself.

## Get the data (one-time, on demand — it is large)
PrimeKG ships as a single CSV from Harvard Dataverse (~hundreds of MB; do NOT add
to core install). Download once into a git-ignored cache, e.g. `data/primekg/`:

```bash
# Fetch the current download URL from the dataset page first (links rotate):
#   https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM
mkdir -p data/primekg
curl -L -o data/primekg/kg.csv "<resolved kg.csv download URL>"
```
Add `data/primekg/` to `.gitignore` (raw data is never committed).

## Query pattern (pandas; cache the load)
The edge table columns are: `relation, display_relation, x_index, x_id, x_type,
x_name, x_source, y_index, y_id, y_type, y_name, y_source`. Each row is one
undirected typed edge between node x and node y.

```python
import pandas as pd
KG = pd.read_csv("data/primekg/kg.csv", low_memory=False)  # load once per process

def neighbors(name, node_type=None, rel=None, limit=30):
    m = (KG.x_name.str.lower() == name.lower()) | (KG.y_name.str.lower() == name.lower())
    sub = KG[m]
    if node_type: sub = sub[(sub.x_type == node_type) | (sub.y_type == node_type)]
    if rel:       sub = sub[sub.display_relation == rel]
    out = []
    for _, r in sub.head(limit).iterrows():
        if r.x_name.lower() == name.lower():
            out.append(f"{r.x_name} --{r.display_relation}--> {r.y_name}  ({r.y_type})")
        else:
            out.append(f"{r.y_name} --{r.display_relation}--> {r.x_name}  ({r.x_type})")
    return "\n".join(out)

# multi-hop: neighbors() of a gene, then neighbors() of each returned disease, etc.
print(neighbors("PARP1"))
```

## Discipline
- It's a curated graph, not ground truth — treat an edge as a **hypothesis to
  verify** (back it with a PMID via `pubmed_search` / `pubtator_annotate` before
  asserting it in a finding).
- Node names need normalizing; if a lookup misses, resolve the name first with
  `pubtator_entity` (concept id) or Open Targets, then match on id/source columns.
- Cache the DataFrame load; re-reading 4M rows every shell call is wasteful — load
  once per script run.
- If you only need one hop of evidence-scored target–disease links, prefer Open
  Targets (`opentargets_associations`) — it's an API, no big download.
