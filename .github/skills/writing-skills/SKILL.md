---
name: writing-skills
description: How to record a new operational learning (how to use a tool, library, API, CLI, or environment quirk) as a reusable skill. Use whenever you just figured something out the hard way, integrated a new dependency, or worked around an environment problem and want the next iteration to skip the pain.
---

# Writing skills (recording operational learnings)

## When to use

After you figure out **how something works operationally** — a library's API, an
external service's auth/rate limits, a CLI invocation, an environment quirk
(paths, GPU, install flags). Capture it so a future iteration references it
instead of re-deriving it.

**Skills hold operational / how-to knowledge only.** Scientific results —
hypotheses, findings, literature synthesis — are *domain knowledge* and go in
`research/`, never here. ("How to install chromadb" → skill. "Clonal-evolution
dynamics" → `research/`.)

## Folder convention

```
.github/skills/<skill-name>/SKILL.md
```

One directory per skill, kebab-case name. Supporting files (scripts, snippets)
can live alongside `SKILL.md` in the same directory.

## Frontmatter (required)

```yaml
---
name: <kebab-case-name>
description: <specific, trigger-rich sentence — this is what Copilot matches on
  to decide when to load the skill. Pack it with the tools/APIs/tasks/symptoms
  it covers so the right trigger words are present.>
---
```

The `description` is the single most important field: it decides whether the
skill loads at the right moment. Be concrete and trigger-rich, not vague.

## Body structure (keep it short and skimmable)

- **When to use** — one or two lines.
- **Key steps** — the minimal working recipe.
- **Gotchas** — the non-obvious failure modes you hit.
- **Docs** — links to fetch live for detail (don't paste whole manuals; fetch
  authoritative docs when you need depth).

## Gotchas

- Don't bloat a skill with full doc dumps — link and fetch instead.
- Update an existing skill rather than creating a near-duplicate.
- If a learning is about *the science*, it does not belong here.
