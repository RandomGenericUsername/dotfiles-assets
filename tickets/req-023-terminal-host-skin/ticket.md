---
id: req-023
title: "terminal-host skin: opt-in Hyprland-following terminal variant"
kind: requirement
status: in-progress
lane: 2 — bounded implementation
links:
  openspec: none
  bmad: none
worktree: .worktrees/req-023/
branch: ticket/req-023-terminal-host-skin
---

# terminal-host skin: opt-in Hyprland-following terminal variant

## Why

`terminal` is the dense-monospace, square/hairline skin, and its 0px radius /
1px border are an explicit identity: it declares no `[host]` policy, so its
panel geometry never follows Hyprland. A user who wants the terminal look but
wants the panel to sit on the compositor's rounding/border size has no skin to
select. This slice adds `terminal-host`, an **opt-in** variant that keeps every
terminal paint/type/rhythm token and delegates only the panel radius and border
width through the `contracts v0.9.0` `[host]` policy. The original `terminal`
does not change: it stays `[host]`-free and explicit.

Acceptance criteria: five Appearance v2 manifests and eight GTK templates
expand as 5 × 2 modes × 8 templates; `terminal-host` appears in the frozen
manifest set; a supplied host radius/border width resolves into `tokens.json`;
`terminal` remains byte-unchanged and `[host]`-free.

## Requirement

1. Add `skins/manifests/terminal-host.toml`:
   - `name = "terminal-host"`;
   - the same token groups/templates/values as `terminal` (square/hairline
     fallbacks, monospace type, radii/paddings/type scale);
   - an explicit root policy:
     ```toml
     [host]
     inherit = ["surface.panel.radius", "surface.panel.border-width"]
     fallback = "skin"
     ```
   - a header comment recording that this skin intentionally follows Hyprland
     panel geometry while `terminal` remains explicit.
2. Do **not** modify `terminal.toml`, any template, or any existing skin.
3. Update the validator/tests/schema/README/catalog/CHANGELOG/version:
   - five manifests × eight templates expand (10 manifest×mode documents);
   - `terminal-host` is in `frozen.required_files` and the manifest set;
   - host values resolve into the inherited paths only, with the skin fallback
     when the host supplies nothing;
   - the original `terminal` remains `[host]`-free;
   - negative coverage proves an unknown inherited path and a malformed policy
     still fail.
4. Validation: `make validate-skins`, `make test-skins`, `make lint`,
   `make gates-ci` in the foreground; a GTK3 probe for `terminal-host` proves
   the host radius is applied and the card fill is identical to `terminal`.
5. Release `v0.16.0` as an annotated tag on the green closing commit,
   fast-forward to `master`, push `master` and the tag. No runtime,
   provisioning, composition, app or live-state change.

## Acceptance

- [ ] `skins/manifests/terminal-host.toml` exists with the terminal token
      values plus the `[host]` policy documented as opt-in.
- [ ] `terminal.toml`, every template and every other skin are byte-unchanged.
- [ ] Validator reports 5 manifests, 8 templates, 10 expansions and resolves
      host radius/border width into `tokens.json` for `terminal-host`; a
      no-host manifest is unchanged by the same host values.
- [ ] `frozen.required_files` names all five manifests; tests cover the five ×
      eight matrix and the original `terminal` stays `[host]`-free.
- [ ] `make validate-skins`, `make test-skins`, `make lint`, `make gates-ci`
      pass.
- [ ] GTK3 `CssProvider` probe for `terminal-host` applies the host radius and
      computes the same card fill as `terminal`.
- [ ] `v0.16.0` annotated tag is pushed on the fast-forwarded `master` commit.

## Evidence / Verify

- Evidence: `skins/manifests/terminal.toml` (explicit opt-out comment);
  `skins/manifests/glass.toml` and `paper.toml` (the `[host]` policy shape);
  `skins/contracts/appearance-manifest.schema.json` (allowlist/fallback).
- Verify: `make validate-skins`, `make test-skins`, `make lint`,
  `make gates-ci`; GTK3 probe recorded in the outcome.
