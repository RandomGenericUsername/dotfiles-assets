# `templates/` — Jinja sources and their variable contracts

This class holds **templates only**. A template's *values* belong to the consumer: this
repository ships what to render and which variables rendering needs, never a rendered file
(spine AD-8, AD-11). A rendered `kitty.conf`, `btop.conf` or `.zshrc` appearing here fails
`make validate`.

## Layout rule: one schema beside every template

```text
templates/
  <group>/<name>.j2        # or .tpl — the Jinja source, body unchanged from where it came
  <group>/<name>.vars.schema.json
```

- The schema file is named after the template: `kitty.conf.j2` ⇄ `kitty.conf.vars.schema.json`.
- A template with no sibling schema is a defect: the consumer has nothing to check its
  supplied values against.
- A schema with no sibling template is a defect too: it describes a contract nothing renders.

## Schema shape

`example.vars.schema.json` in this directory is the **shape**, not a live contract — the
`example.` prefix is deliberate, and no template named `example.j2` ships.

Each real schema is a JSON Schema (draft 2020-12) for the render context, plus three
extensions:

| Key | Meaning |
| --- | --- |
| `schema_major` | integer; the consumer-compatibility version (spine AD-12) — independent of the repo tag |
| `template` | the sibling template's file name, so the pair is checkable without guessing |
| `optional` | the declared complement of JSON Schema's `required` |

`required` names what the consumer **must** supply. It is derived from the variables the
template actually reads — not from the consuming role's whole variable set, which is always
larger and would make every template appear to need everything.

## Rules the validator enforces (with the corpus, in v0.4.0)

`make validate-templates` lands with the templates themselves, because a rule with no corpus
is a rule nobody has seen work. It will assert:

1. every `*.j2` / `*.tpl` has a sibling `*.vars.schema.json`, and vice versa;
2. every `{{ var }}` read by a template appears in its schema (in `properties`);
3. every `required[]` name is a `properties` entry, `required` is non-empty, and no name is
   in both `required` and `optional`;
4. **no `default(` on a required variable** — a fallback on a required value turns "the
   consumer forgot it" into "the file rendered with a wrong value", which is worse than a
   failure;
5. each schema parses as JSON and validates against JSON Schema draft 2020-12.

Until then `make validate` checks only the envelope it can check without a corpus: the shape
file parses as JSON, carries an integer `schema_major`, and declares `required` and `optional`.
That is honest and small; the five rules above are the contract, not decoration.

## What this class is not

- Not a place for values, secrets, host names or per-machine settings.
- Not a place for the *rendered* result (AD-11).
- Not a place for a template that only one consumer can render: the schema is the public
  surface, and it must be sufficient for any consumer to supply a correct context.
